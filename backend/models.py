"""
SQLAlchemy table definitions.
Three tables: Document, Analysis, ChatMessage
"""

from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Float,
    Integer, DateTime, JSON, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from backend.database import Base, engine
import uuid


def generate_uuid():
    return str(uuid.uuid4())


class Document(Base):
    """
    Stores metadata about each uploaded transcript PDF.
    """
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    filename = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    ticker = Column(String, nullable=True)
    quarter = Column(Integer, nullable=True)
    year = Column(Integer, nullable=True)
    page_count = Column(Integer, nullable=True)
    word_count = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    is_analyzed = Column(Boolean, default=False)

    # Relationships
    analysis     = relationship("Analysis", back_populates="document", uselist=False)
    chat_messages = relationship("ChatMessage", back_populates="document")


class Analysis(Base):
    """
    Stores the complete ML analysis result for one document.
    Results stored as JSON for flexibility.
    """
    __tablename__ = "analyses"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)

    # Sentiment results
    sentiment_positive = Column(Float, nullable=True)
    sentiment_negative = Column(Float, nullable=True)
    sentiment_neutral = Column(Float, nullable=True)

    # Evasion results
    evasion_rate = Column(Float, nullable=True)
    evasion_count = Column(Integer, nullable=True)
    total_qa_pairs = Column(Integer, nullable=True)

    # Guidance
    guidance_claims = Column(JSON, nullable=True)

    # Fulfillment predictions 
    fulfillment_predictions = Column(JSON, nullable=True)

    # Full raw report (everything combined)
    full_report = Column(JSON, nullable=True)

    # Risk score computed from all signals
    risk_score = Column(Float, nullable=True)

    analyzed_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    document = relationship("Document", back_populates="analysis")


class ChatMessage(Base):
    """
    Stores Q&A chat history for each document.
    """
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(JSON, nullable=True)   # list of source chunks
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    document = relationship("Document", back_populates="chat_messages")


if __name__ == "__main__":

    try:
        # Create all tables
        Base.metadata.create_all(bind=engine)

        print(" Tables created successfully!")
        print(" Models imported successfully!")
        print(" Relationships configured successfully!")
        print(" models.py is working correctly!")

    except Exception as e:
        print(" Model setup failed!")
        print(f"Error: {e}")