"""
Pydantic schemas for request/response validation.
These define exactly what the API accepts and returns.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime


# --- Upload ---

class DocumentResponse(BaseModel):
    id: str
    filename: str
    company_name: Optional[str]
    ticker: Optional[str]
    quarter: Optional[int]
    year: Optional[int]
    page_count: Optional[int]
    word_count: Optional[int]
    uploaded_at: datetime
    is_analyzed: bool

    class Config:
        from_attributes = True


# --- Analysis ---

class SentimentResult(BaseModel):
    positive: float
    negative: float
    neutral:  float


class EvasionResult(BaseModel):
    evasion_rate:   float
    evasion_count:  int
    total_qa_pairs: int
    flagged_pairs:  List[Dict[str, Any]]


class GuidanceClaim(BaseModel):
    metric:          str
    raw_value:       str
    value_low:       Optional[float]
    value_high:      Optional[float]
    value_unit:      str
    target_quarter:  Optional[int]
    target_year:     Optional[int]
    fulfillment_probability: Optional[float]
    raw_sentence:    str


class AnalysisResponse(BaseModel):
    document_id:   str
    sentiment:     SentimentResult
    evasion:       EvasionResult
    guidance:      Optional[List] = None
    risk_score:    float
    analyzed_at:   datetime

    class Config:
        from_attributes = True


# --- Chat ---

class ChatRequest(BaseModel):
    document_id: str
    question:    str


class ChatResponse(BaseModel):
    question: str
    answer:   str
    sources:  List[Dict[str, Any]]


# --- History ---

class HistoryItem(BaseModel):
    document_id:  str
    filename:     str
    ticker:       Optional[str]
    quarter:      Optional[int]
    year:         Optional[int]
    risk_score:   Optional[float]
    analyzed_at:  Optional[datetime]
    uploaded_at:  datetime

    class Config:
        from_attributes = True
