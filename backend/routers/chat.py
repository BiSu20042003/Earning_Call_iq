"""
Chat router.
Handles RAG-based Q&A for a specific document.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models   import Document, ChatMessage
from backend.schemas  import ChatRequest, ChatResponse
from backend.services import rag_service

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat_with_document(request: ChatRequest,db:Session = Depends(get_db)):
    """
    Ask a question about a specific uploaded document.
    Uses hybrid retrieval + reranking + Groq to answer.
    Saves Q&A to chat history.
    """
    # Verify document exists
    document = db.query(Document).filter(
        Document.id == request.document_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Query RAG pipeline
    result = rag_service.query_document(
        doc_id   = request.document_id,
        question = request.question
    )

    # Save to chat history
    chat_msg = ChatMessage(
        document_id = request.document_id,
        question    = request.question,
        answer      = result["answer"],
        sources     = result["sources"]
    )
    db.add(chat_msg)
    db.commit()

    return ChatResponse(
        question = request.question,
        answer   = result["answer"],
        sources  = result["sources"]
    )


@router.get("/chat/history/{doc_id}")
async def get_chat_history(doc_id,db:Session = Depends(get_db)):
    """Return all past Q&A for a document."""
    messages = db.query(ChatMessage).filter(
        ChatMessage.document_id == doc_id
    ).order_by(ChatMessage.created_at).all()

    return [
        {
            "question":   m.question,
            "answer":     m.answer,
            "sources":    m.sources,
            "created_at": m.created_at
        }
        for m in messages
    ]