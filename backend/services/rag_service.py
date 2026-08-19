import os
import json
import time
import hashlib
import torch
import numpy as np
from typing import List, Dict
from dotenv import load_dotenv

# Document Loaders & Splitters
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

# Vector Database & Embeddings
import chromadb
# from chromadb.config import Settings
from sentence_transformers import SentenceTransformer, CrossEncoder

# LLM Integration
from langchain_google_genai import ChatGoogleGenerativeAI

# Load environment configuration
load_dotenv("../.env", override=True)
google_api_key = os.getenv("GEMINI_API_KEY_RAG")

device = "cuda" if torch.cuda.is_available() else "cpu"

# Lazy-loaded Model Singletons
_embedding_model = None
_reranker = None
_chroma_client = None

# In-memory document storage for chunk data and BM25 search objects
_doc_chunks: Dict[str, List[Dict]] = {}
_doc_bm25: Dict[str, BM25Okapi] = {}

RETENTION_DAYS = 15
RETENTION_SECONDS = RETENTION_DAYS * 24 * 60 * 60


def get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(
            "BAAI/bge-small-en-v1.5", 
            device=device
        )
    return _embedding_model


def get_reranker():
    global _reranker
    if _reranker is None:
        _reranker = CrossEncoder(
            "cross-encoder/ms-marco-MiniLM-L6-v2", 
            device=device
        )
    return _reranker


def get_chroma_client():
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.CloudClient(
            api_key=os.getenv("CHROMA_API_KEY"),
            tenant=os.getenv("CHROMA_TENANT"),
            database=os.getenv("CHROMA_DATABASE")
        )
    return _chroma_client



def extract_text_from_file(file_path: str):
    """
    Extracts text from PDF or JSON files and standardizes output into LangChain Document objects.
    """
    # 1. Handle JSON Files
    if file_path.lower().endswith(".json"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, (dict, list)):
            text_content = json.dumps(data, indent=2)
        else:
            text_content = str(data)

        cleaned_text = " ".join(text_content.split())
        
        return [Document(page_content=cleaned_text, metadata={"page": 0})]

    # 2. Handle PDF Files (Existing Logic)
    else:
        loader = PyPDFLoader(file_path)
        docs = loader.load()
        
        for doc in docs:
            doc.page_content = " ".join(doc.page_content.split())
        return docs


def split_docs(documents, chunk_size=512, chunk_overlap=64):
    """
    Splits Document objects using RecursiveCharacterTextSplitter.
    Converts chunked output into indexed chunk dictionaries with metadata.
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len, #512 char
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""]
    )
    
    chunked_docs = text_splitter.split_documents(documents)
    processed_chunks = []
    chunk_id = 0
    for idx, doc in enumerate(chunked_docs):
        # Normalize and align 1-based page indices
        page_num = doc.metadata.get("page", 0) + 1 if "page" in doc.metadata else 1
        
        if len(doc.page_content.strip()) < 30:
            continue
            
        processed_chunks.append({
            "chunk_id": chunk_id,
            "page_num": page_num,
            "text": doc.page_content.strip(),
            "word_count": len(doc.page_content.split())
        })
        chunk_id += 1
    print(f"Total chunks created: {len(processed_chunks)}")
    print(f"Avg words per chunk: {round(np.mean([c['word_count'] for c in processed_chunks]), 1)}")
    return processed_chunks


def calculate_file_hash(file_path: str) -> str:
    """
    Calculate SHA-256 hash of the uploaded file.
    Used to detect duplicate transcripts.
    """
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            sha256.update(block)

    return sha256.hexdigest()


def find_existing_document(file_hash: str):
    client = get_chroma_client()
    now = time.time()

    for collection in client.list_collections():

        if isinstance(collection, str):
            collection = client.get_collection(collection)
        metadata = collection.metadata or {}

        # FIRST CHECK EXPIRY
        expires_at = metadata.get("expires_at")

        if expires_at is not None and float(expires_at) <= now:
            expired_doc_id = metadata.get("doc_id")

            print(f"Deleting expired collection: {collection.name}")
            client.delete_collection(collection.name)

            if expired_doc_id:
                _doc_chunks.pop(expired_doc_id, None)
                _doc_bm25.pop(expired_doc_id, None)
            continue

        # COLLECTION IS VALID → CHECK FILE HASH
        if metadata.get("file_hash") != file_hash:
            continue

        # VALID + MATCHING DOCUMENT FOUND
        doc_id = metadata.get("doc_id")

        result = collection.get(
            include=["documents", "metadatas"]
        )

        documents = result.get("documents", [])
        metadatas = result.get("metadatas", [])

        chunks = []

        for text, chunk_metadata in zip(documents,metadatas):
            chunk_metadata = chunk_metadata or {}

            chunks.append({
                "chunk_id": int(chunk_metadata["chunk_id"]),
                "page_num": int(chunk_metadata["page_num"]),
                "text": text,
                "word_count": int(
                    chunk_metadata["word_count"]
                )
            })

        chunks.sort(key=lambda x: x["chunk_id"])

        # Build BM25 from the stored chunks
        tokenized = [
            c["text"].lower().split()
            for c in chunks
        ]

        bm25 = BM25Okapi(tokenized)

        _doc_chunks[doc_id] = chunks
        _doc_bm25[doc_id] = bm25

        print(f"Existing valid transcript found: {doc_id}")

        return {
            "doc_id": doc_id,
            "collection_name": collection.name,
            "created_at": metadata.get("created_at"),
            "expires_at": expires_at
        }

    return None


def index_document(doc_id, file_path, qa_results: list = None):
    """
    Step 1 (First function called after file upload):
    Index document into ChromaDB + BM25 index for the given doc_id.
    """
    #  Calculate file hash
    file_hash = calculate_file_hash(file_path)

    #  Check if this exact transcript already exists
    existing = find_existing_document(file_hash)

    if existing:
        print(f"Using existing document: " f"{existing['doc_id']}")
        return existing

    emb_model = get_embedding_model()
    client = get_chroma_client()

    # 1. Parse & Chunk Document
    document = extract_text_from_file(file_path)
    chunks = split_docs(document, chunk_size=512, chunk_overlap=64)

    if not chunks:
        raise ValueError("Failed to extract any readable text from the document.")

    current_time = time.time()
    expires_at = current_time + RETENTION_SECONDS
    collection_name = f"doc_{doc_id[:8]}"

    collection = client.create_collection(
    name=collection_name,
    metadata={
        "hnsw:space": "cosine",
        "doc_id": doc_id,
        "file_hash": file_hash,
        "created_at": current_time,
        "expires_at": expires_at
    }
)
    # 3. Embed & Store Chunks
    texts = [c["text"] for c in chunks]
    embeddings = emb_model.encode(
        texts,
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch_chunks = chunks[i:i + batch_size]
        batch_embs = embeddings[i:i + batch_size]
        collection.add(
            ids=[f"chunk_{c['chunk_id']}" for c in batch_chunks],
            embeddings=batch_embs.tolist(),
            documents=[c["text"] for c in batch_chunks],
            metadatas=[{
                "chunk_id": c["chunk_id"],
                "page_num": c["page_num"],
                "word_count": c["word_count"]
            } for c in batch_chunks]
        )

    # 4. Cache BM25 Index and Chunks in memory
    tokenized = [c["text"].lower().split() for c in chunks]
    _doc_chunks[doc_id] = chunks
    _doc_bm25[doc_id] = BM25Okapi(tokenized)

    return len(chunks)

def load_chunks(doc_id: str):
    """
    Load an existing document's chunks from ChromaDB
    and rebuild its BM25 index.
    """

    client = get_chroma_client()
    collection_name = f"doc_{doc_id[:8]}"

    try:
        collection = client.get_collection(collection_name)
    except Exception:
        print(f"Document not found in ChromaDB: {doc_id}")
        return None, None

    # 1. Check expiry
    metadata = collection.metadata or {}

    expires_at = metadata.get("expires_at")
    if expires_at is not None and float(expires_at) <= time.time():
        print(f"Document expired: {doc_id}")

        client.delete_collection(collection.name)
        return None, None

    # 2. Get chunks from ChromaDB
    result = collection.get(
        include=["documents", "metadatas"]
    )

    documents = result.get("documents", [])
    metadatas = result.get("metadatas", [])

    if not documents:
        print(f"No chunks found for document: {doc_id}")
        return None, None

    # 3. Reconstruct chunks
    chunks = []
    for text, metadata in zip(documents, metadatas):
        metadata = metadata or {}
        chunks.append({
            "chunk_id": int(metadata["chunk_id"]),
            "page_num": int(metadata["page_num"]),
            "text": text,
            "word_count": int(metadata["word_count"])
        })

    # Keep original chunk order
    chunks.sort(key=lambda x: x["chunk_id"])

    # 4. Rebuild BM25
    tokenized = [
        c["text"].lower().split()
        for c in chunks
    ]

    bm25 = BM25Okapi(tokenized)
    return chunks, bm25


def query_document(doc_id: str, question: str, top_k: int = 20, top_n: int = 5, alpha: float = 0.6) -> Dict:
    """
    Step 2:
    Runs Hybrid retrieval + Cross-Encoder Reranking + LLM Answer generation.
    """
    emb_model = get_embedding_model()
    reranker = get_reranker()
    client = get_chroma_client()

    chunks = _doc_chunks.get(doc_id)
    bm25 = _doc_bm25.get(doc_id)

    if not chunks or not bm25:
        chunks, bm25 = load_chunks(doc_id)
        
        if not chunks or not bm25:
            return {
                "answer": "Document index not found. Please upload/index the document again.",
                "sources": []
            }

    collection_name = f"doc_{doc_id[:8]}"
    collection = client.get_collection(collection_name)

    # Semantic Retrieval
    q_emb = emb_model.encode(
        question,
        normalize_embeddings=True,
        prompt="Represent this sentence for searching relevant passages: "
    )
    sem_results = collection.query(
        query_embeddings=[q_emb.tolist()],
        n_results=min(top_k, len(chunks))
    )

    semantic_scores = {}
    if sem_results["ids"] and sem_results["distances"]:
        for cid_str, dist in zip(sem_results["ids"][0], sem_results["distances"][0]):
            cid = int(cid_str.replace("chunk_", ""))
            semantic_scores[cid] = 1.0 - dist

    # BM25 Retrieval
    bm25_raw = bm25.get_scores(question.lower().split())
    max_bm25 = max(bm25_raw) if max(bm25_raw) > 0 else 1.0
    bm25_norm = bm25_raw / max_bm25
    
    top_bm25_indices = np.argsort(bm25_norm)[::-1][:top_k]
    top_bm25 = {idx: float(bm25_norm[idx]) for idx in top_bm25_indices}

    # Hybrid Fusion Scorer 
    all_cids = set(semantic_scores.keys()) | set(top_bm25.keys())
    combined = []
    print("Number of chunks:", len(chunks))
    print("Reranked:", all_cids)

    chunk_map = {
        c["chunk_id"]: c
        for c in chunks
    }

    for cid in all_cids:
        if cid not in chunk_map:
            continue
        sem_s = semantic_scores.get(cid, 0.0)
        bm25_s = top_bm25.get(cid, 0.0)
        combined.append({
            **chunks[cid],
            "combined_score": alpha * sem_s + (1.0 - alpha) * bm25_s
        })
        
    combined.sort(key=lambda x: x["combined_score"], reverse=True)
    candidates = combined[:top_k]

    if not candidates:
        return {
            "answer": "No matching content retrieved for this question.",
            "sources": []
        }

    pairs = [(question, c["text"]) for c in candidates]
    rerank_scores = reranker.predict(pairs)
    
    valid_candidates = []
    for i, candidate in enumerate(candidates):
        score = float(rerank_scores[i])
        candidate["rerank_score"] = score
        valid_candidates.append(candidate)

    valid_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
    final_chunks = valid_candidates[:top_n]

    if not final_chunks:
        return {
            "answer": "The uploaded document does not contain relevant information to answer this question.",
            "sources": []
        }

    # Context Construction
    context_parts = [
        f"[Source {i+1} — Page {c['page_num']}]\n{c['text']}"
        for i, c in enumerate(final_chunks)
    ]
    context = "\n\n".join(context_parts)

    system_prompt = """You are a precise financial analyst assistant analyzing earnings call transcripts.

Your job is to answer questions about the transcript using ONLY the provided context. Or if speaker does not provide any context and asked irrelevant questions then reply as chatbot.
IMPORTANT EDGE CASE:
 If the question is unrelated to the transcript and is a general knowledge or conversational question (e.g., greetings, programming, finance concepts, mathematics, definitions, etc.), answer it using your own knowledge.
- Never use your own knowledge to fill gaps or make assumptions about the transcript.
Rules:
- Answer directly and specifically from the context
- If the answer contains specific numbers, metrics, or quotes — include them exactly
- Answer ONLY using the retrieved context.
- If the information is absent, explicitly say:
   "The uploaded transcript does not contain this information."
- Never infer financial facts.
- Always mention which source/page you found the answer in
- If the context does not contain enough information to answer — say so clearly
- Never make up information not present in the context
- Never fabricate speaker statements.
- Keep answers concise but complete."""

    user_message = f"Question: {question}\n\nContext from transcript:\n{context}\n\nAnswer the question based on the context above."

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-3.5-flash", 
            google_api_key=google_api_key,
            temperature=0.1,
    )

        response = llm.invoke([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ])
        content = response.content

        if isinstance(content, list):
            answer = "".join(
                item["text"] if isinstance(item, dict) else str(item)
                for item in content
            )
        else:
            answer = content
        return {
            "answer": answer.strip(),
            "sources": [
                {
                    "page_num": c["page_num"],
                    "chunk_id": c["chunk_id"],
                    "text_preview": c["text"][:200],
                    "rerank_score": round(c["rerank_score"], 4)
                }
                for c in final_chunks
            ]
        }

    except Exception as e:
        return {
            "answer": f"Error communicating with LLM service: {str(e)}",
            "sources": []
        }
