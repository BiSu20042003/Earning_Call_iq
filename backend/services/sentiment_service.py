"""
Sentiment analysis service. Loads fine-tuned FinBERT model once at startup, reuses for all requests.
"""

import torch
import numpy as np
from pathlib import Path
import re
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_PATH = Path(__file__).parent.parent.parent / "ml_models" / "sentiment" / "final"

_tokenizer = None
_model = None
_device = None


def get_model():
    global _tokenizer, _model, _device
    if _model is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
        _tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
        _model = AutoModelForSequenceClassification.from_pretrained(str(MODEL_PATH))
        _model = _model.to(_device)
        _model.eval()
    return _tokenizer, _model, _device


def predict_sentiment_batch(texts, batch_size = 32):
    tokenizer, model, device = get_model()
    all_scores = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        encodings   = tokenizer(
            batch, truncation=True, padding=True,
            max_length=128, return_tensors="pt"
        ).to(device)

        with torch.no_grad():
            logits = model(**encodings).logits

        probs = torch.softmax(logits, dim=-1).cpu().numpy()
        for p in probs:
            all_scores.append({
                "negative": float(p[0]),
                "neutral":  float(p[1]),
                "positive": float(p[2])
            })

    return all_scores


def split_into_chunks(text, max_words= 300):
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        sentence_word_count = len(sentence.split())
        
        if current_word_count + sentence_word_count > max_words and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_word_count = 0
        
        current_chunk.append(sentence)
        current_word_count += sentence_word_count
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
    
    return chunks


def score_text(text, max_words=300):
    if len(text.split()) <= max_words:
        chunks = [text]
    else:
        chunks = split_into_chunks(text, max_words=max_words)
    
    chunk_scores = predict_sentiment_batch(chunks)
    
    avg_negative = np.mean([s["negative"] for s in chunk_scores])
    avg_neutral = np.mean([s["neutral"] for s in chunk_scores])
    avg_positive = np.mean([s["positive"] for s in chunk_scores])
    
    return {
        "negative": float(avg_negative),
        "neutral": float(avg_neutral),
        "positive": float(avg_positive),
        "num_chunks": len(chunks)
    }


def analyze_transcript_sentiment(prepared_remarks, qa_pairs):
    """
    Weighted sentiment: 30% prepared remarks, 70% Q&A answers.
    """
    prepared_texts = [t["text"] for t in prepared_remarks if len(t.get("text","").split()) > 5]
    qa_text   = [p["answer"] for p in qa_pairs if len(p.get("answer","").split()) > 5]

    prepared_scores = [score_text(t) for t in prepared_texts] if prepared_texts else []
    answer_scores   = [score_text(t) for t in qa_text]   if qa_text   else []

    if prepared_scores and answer_scores:
        prep_pos = float(np.mean([s["positive"] for s in prepared_scores]))
        prep_neg = float(np.mean([s["negative"] for s in prepared_scores]))
        prep_neu = float(np.mean([s["neutral"]  for s in prepared_scores]))
        ans_pos  = float(np.mean([s["positive"] for s in answer_scores]))
        ans_neg  = float(np.mean([s["negative"] for s in answer_scores]))
        ans_neu  = float(np.mean([s["neutral"]  for s in answer_scores]))

        return {
            "positive": round(0.3 * prep_pos + 0.7 * ans_pos, 4),
            "negative": round(0.3 * prep_neg + 0.7 * ans_neg, 4),
            "neutral":  round(0.3 * prep_neu + 0.7 * ans_neu, 4),
        }
    elif answer_scores:
        return {
            "positive": round(float(np.mean([s["positive"] for s in answer_scores])), 4),
            "negative": round(float(np.mean([s["negative"] for s in answer_scores])), 4),
            "neutral":  round(float(np.mean([s["neutral"]  for s in answer_scores])), 4),
        }
    else:
        return {"positive": 0.33, "negative": 0.33, "neutral": 0.34}


