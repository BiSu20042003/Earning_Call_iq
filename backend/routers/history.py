"""
History router.
List and retrieve past analyses.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Document, Analysis
from backend.schemas import HistoryItem

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history", response_model=List[HistoryItem])
async def get_history(db: Session = Depends(get_db)):
    """Return list of all past analyses."""
    documents = db.query(Document).order_by(
        Document.uploaded_at.desc()
    ).all()
    analyses = db.query(Analysis).all()
    analysis_mp = {}
    for analysis in analyses:
        analysis_mp[analysis.document_id] = analysis
    result = []
    
    for doc in documents:
        analysis = analysis_map.get(doc.id)

        result.append(HistoryItem(
            document_id = doc.id,
            filename    = doc.filename,
            ticker      = doc.ticker,
            quarter     = doc.quarter,
            year        = doc.year,
            risk_score  = analysis.risk_score if analysis else None,
            analyzed_at = analysis.analyzed_at if analysis else None,
            uploaded_at = doc.uploaded_at
        ))

    return result


@router.get("/analysis/{doc_id}")
async def get_analysis(doc_id, db: Session = Depends(get_db)):
    """Return saved analysis for a specific document."""
    analysis = db.query(Analysis).filter(
        Analysis.document_id == doc_id
    ).first()

    if not analysis:
        raise HTTPException(
            status_code=404,
            detail="Analysis not found"
        )

    return analysis.full_report


@router.delete("/analysis/{doc_id}")
async def delete_analysis(doc_id: str, db: Session = Depends(get_db)):
    """Delete a document and all its associated data."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if doc:
        db.delete(doc)
        db.commit()
    return {"deleted": doc_id}