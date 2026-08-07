"""
Upload router.
Handles PDF upload, text extraction, document metadata storage.
"""

import uuid
import fitz
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Document
from backend.schemas import DocumentResponse
from backend.services import rag_service

router = APIRouter(prefix="/api", tags=["upload"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/upload", response_model=DocumentResponse)
async def upload_transcript(file = File(...),db:Session= Depends(get_db)):
    """
    Upload a transcript PDF or TXT file.
    Saves file, extracts metadata, indexes for RAG.
    Returns document_id for subsequent analysis and chat requests.
    """
    # Validate file type
    if not file.filename.lower().endswith((".pdf",".json")):
        raise HTTPException(
            status_code = 400,
            detail = "Only PDF & JSON files are supported"
        )

    # Save file
    doc_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{doc_id}_{file.filename}"

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Extract basic metadata from PDF
    page_count = 0
    word_count = 0
    if file.filename.lower().endswith(".pdf"):
        try:
            doc = fitz.open(str(file_path))
            page_count = len(doc)
            full_text  = " ".join(
                page.get_text("text") for page in doc
                )
            word_count = len(full_text.split())
            doc.close()
        except Exception as e:
            print(f"Metadata extraction failed: {e}")

    # Save document record to PostgreSQL
    db_doc = Document(
        id = doc_id,
        filename = file.filename,
        page_count = page_count,
        word_count = word_count)
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)

    # Index document for RAG (background-friendly — runs immediately here)
    try:
        chunks_indexed = rag_service.index_document(doc_id, str(file_path))
        print(f"Indexed {chunks_indexed} chunks for doc {doc_id}")
    except Exception as e:
        db.delete(db_doc)
        db.commit()
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
        status_code=500,
        detail=f"Failed to process and index PDF: {str(e)}"
    )
    return db_doc