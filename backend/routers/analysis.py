"""
Analysis router.
Runs the full ML pipeline on an uploaded document.
"""

import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path
import json
from dotenv import load_dotenv
import os
from backend.database import get_db
from backend.models   import Document, Analysis
from backend.schemas  import AnalysisResponse
from backend.services import (
    sentiment_service,
    evasion_service,
    guidance_service,
    fulfillment_service,
    transcript_parser,
)
from groq import Groq
load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

router = APIRouter(prefix="/api", tags=["analysis"])


def filter_official_guidance(guidance_sentences: list):
    if not guidance_sentences:
        print("Empty guidance_sentences!!")
        return []

    # Pre-filter — no LLM cost for obvious non-guidance sentences
    filtered = [s for s in guidance_sentences if guidance_service.contains_measurable_metric(s)]
    if not filtered:
        print("Empty filtered!!")
        return []

    sentences_text = "\n".join(f"{i+1}. {s}" for i, s in enumerate(filtered))
    prompt = f"""You are a financial analyst extracting verifiable forward guidance from an earnings call transcript.
IMPORTANT: Only extract guidance that is seems a future claim, not a past report. Each sentence should be about future. Otherwise skip it. 

Guidance sentences to analyze:
<guidance_sentences>
{sentences_text}
</guidance_sentences>

For each valid guidance claim,
Transformation Rules:
- Describe the guidance as something the company claimed or expected for a certain upcoming Time Frame.
- Begin with on of "Management expects" or "Management forecasts " or "The company expects".
- Replace first-person pronouns wording such as "we expect", "we believe", "we anticipate", etc with third-person statement.
- Preserve the key guidance metric/outcome and it's targeted time frame as it is said the official .
- Write the main financial metric or business metric in ALL CAPITAL LETTERS.
- Keep the sentence concise.
- Do not add any information that is not present in the original claim.
Examples:
Input: "We expect higher revenue growth in the next quarter."
Output: "Management expects higher REVENUE GROWTH in the next quarter."

Input: "We expect operating margin to improve by 150 basis points."
Output: "The company expects improved OPERATING MARGIN by 150 basis points."

Input: "For the full year, we expect our benefit ratio to be towards the lower end."
Output: "For the full year, Company forecasts their BENEFIT RATIO to be towards the lower end."

Return ONLY a string array of valid claims
Example:
[
  "Management forecasts higher REVENUE GROWTH in next quarter.",
  "Management forecasts improved OPERATING MARGIN by 150 basis points."
]. 
If no valid measurable guidance found, return [].
No other text."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system",
             "content": "You are a strict financial analyst. Follow the instruction to find out genuine future guidance."
            },
            {"role": "user",
             "content": prompt
            }
        ],
        temperature=0.1
    )
    text = response.choices[0].message.content.strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        result = json.loads(text)

        if not isinstance(result, list):
            return []

        cleaned = [
        item.strip()
        for item in result
        if isinstance(item, str) and item.strip()
    ]
        print(len(cleaned))
        return cleaned


    except Exception as e:
        print(f"  Extraction error: {e}")
        return []




def extract_guidance_sentences(text):
    """
    Extract forward-looking guidance sentences from transcript.
    """

    guidance_words = [
        "we expect",
        "we anticipate",
        "we project",
        "we forecast",
        "going forward",
        "outlook",
        "next quarter",
        "full year",
        "full-year",
        "will grow"
    ]

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    guidance_sentences = []
    for sentence in sentences:
        sentence_lower = sentence.lower()
        if len(sentence.split()) <= 8:
            continue
        for word in guidance_words:
            if word in sentence_lower:
                guidance_sentences.append(sentence.strip())
                break

    return guidance_sentences


def compute_risk_score(sentiment, evasion, qa_pairs):
    """
    Compute an overall financial risk score (0-100)
    using a weighted combination of
    negative sentiment and management evasion.

    Higher score = Higher risk.
    """

    negative_sentiment = sentiment.get("negative", 0.0)
    evasion_rate = evasion.get("evasion_rate", 0.0)
    effective_evasion = evasion_rate*min(1,len(qa_pairs)/5)
    risk_score = (
        0.4 * negative_sentiment +
        0.6 * effective_evasion
    ) * 100

    return round(risk_score, 2)


@router.post("/analyze/{doc_id}", response_model=AnalysisResponse)
async def analyze_document(doc_id, db = Depends(get_db)):
    """
    Run full ML analysis pipeline on uploaded document.
    Pipeline:
    1. Extract prepared remarks + Q&A from stored transcript
    2. Sentiment analysis
    3. Evasion detection on all Q&A pairs
    4. Guidance extraction
    5. Fulfillment probability prediction
    6. Risk score aggregation
    7. Save to PostgreSQL
    """
    # Load document
    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")


    upload_dir = Path("uploads")
    files  = list(upload_dir.glob(f"{doc_id}_*"))

    if not files:
        raise HTTPException(status_code=404, detail="Uploaded file not found")

    file_path = files[0]

    raw = transcript_parser.load_transcript(file_path)

    structured_content = raw["structured_content"]

    prepared_remarks, qa_pairs = transcript_parser.split_sections(structured_content)

    # 1. Sentiment
    sentiment_result = sentiment_service.analyze_transcript_sentiment(
        prepared_remarks, qa_pairs
    )

    # 2. Evasion
    evasion_result = evasion_service.analyze_evasion(qa_pairs)

    # 3. Guidance extraction
    prepared_text = " ".join(turn["text"] for turn in prepared_remarks)
    raw_guidance_sentences = transcript_parser.extract_guidance_sentences(prepared_text)
    genuine_guidance_claim = filter_official_guidance(raw_guidance_sentences)

    document.ticker=raw["symbol"]
    document.quarter=raw["quarter"] 
    document.year=raw["year"]
    db.commit()
    db.refresh(document)
    ticker = document.ticker
    quarter = document.quarter
    year = document.year
  
    guidance_claims = guidance_service.extract_guidance(
        genuine_guidance_claim, ticker, quarter, year
    )

    #4. Fulfillment prediction
    enriched_claims = fulfillment_service.predict_fulfillment(
        guidance_claims,
        sentiment_result,
        evasion_result["evasion_rate"]
    )

    # 5. Risk score
    risk_score = compute_risk_score(sentiment_result, evasion_result,qa_pairs)

    # 6. Save to PostgreSQL
    existing = db.query(Analysis).filter(Analysis.document_id == doc_id).first()
    if existing:
        db.delete(existing)
        db.commit()
    analysis = Analysis(
        document_id = doc_id,
        sentiment_positive = sentiment_result["positive"],
        sentiment_negative = sentiment_result["negative"],
        sentiment_neutral = sentiment_result["neutral"],
        evasion_rate = evasion_result["evasion_rate"],
        evasion_count = evasion_result["evasion_count"],
        total_qa_pairs = evasion_result["total_qa_pairs"],
        guidance_claims = guidance_claims,
        fulfillment_predictions = enriched_claims,
        risk_score = risk_score,
        full_report = {
            "sentiment": sentiment_result,
            "evasion": evasion_result,
            "guidance": enriched_claims,
            "claimed_sentences": guidance_claims,
            "risk_score": risk_score
        }
    )
    db.add(analysis)

    document.is_analyzed = True
    db.commit()
    db.refresh(analysis)

    return AnalysisResponse(
        document_id = doc_id,
        sentiment   = sentiment_result,
        evasion     = evasion_result,
        guidance    = enriched_claims,
        risk_score  = risk_score,
        analyzed_at = analysis.analyzed_at
    )