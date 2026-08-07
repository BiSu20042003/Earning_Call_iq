import torch
import numpy as np
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_PATH = Path(__file__).parent.parent.parent / "ml_models" / "evasion" / "final"

_tokenizer = None
_model = None
_device = None

LABEL2ID = {"DIRECT": 0, "EVASIVE": 1}
ID2LABEL = {0: "DIRECT", 1: "EVASIVE"}


def get_model():
    global _tokenizer, _model, _device
    if _model is None:
        _device    = "cuda" if torch.cuda.is_available() else "cpu"
        _tokenizer = AutoTokenizer.from_pretrained(str(MODEL_PATH))
        _model     = AutoModelForSequenceClassification.from_pretrained(str(MODEL_PATH))
        _model     = _model.to(_device)
        _model.eval()
    return _tokenizer, _model, _device


def predict_evasion(question, answer, threshold=0.40):
    tokenizer, model, device = get_model()
    enc = tokenizer(
        question,
        answer,
        return_tensors = "pt", #Other: tf, np
        truncation   = True,
        max_length   = 512,
    ).to(device)

    with torch.no_grad():
        logits = model(**enc).logits #Others: .hidden_states, .attentions

    probs      = torch.softmax(logits, dim=-1)
    direct_prob = probs[0][0].item()
    evasive_prob = probs[0][1].item()
    prediction = "EVASIVE" if evasive_prob >= threshold else "DIRECT"
  
    confidence = evasive_prob if prediction=="EVASIVE" else direct_prob

    return {
        "label":        prediction,
        "is_evasive":   prediction == "EVASIVE",
        "confidence":   round(confidence, 4),
        "evasive_prob": round(evasive_prob, 4),
        "direct_prob":  round(direct_prob, 4)
    }


def analyze_evasion(qa_pairs, min_confidence=0.70):
    """
    Run evasion detection on all Q&A pairs.
    Returns flagged evasive pairs + summary statistics + prediction for every Q&A.
    """

    flagged = []
    qa_results = []
    total = 0

    for pair in qa_pairs:
        question = pair.get("question", "")
        answer = pair.get("answer", "")

        # if len(question.split()) < 10 or len(answer.split()) < 20:
        #     continue

        total += 1
        result = predict_evasion(question, answer)

        # Store prediction for every Q&A pair
        qa_results.append({
            "analyst": pair.get("analyst", "Unknown"),
            "question": question,
            "answer": answer,
            "label": "Evasive" if result["is_evasive"] else "Direct",
            "confidence": round(result["confidence"], 4),
            "evasive_prob": round(result["evasive_prob"], 4)
        })

        # Store only evasive Q&A pairs separately
        if result["is_evasive"] and result["confidence"] >= min_confidence:
            flagged.append({
                "analyst": pair.get("analyst", "Unknown"),
                "question": question,
                "answer": answer,
                "confidence": round(result["confidence"], 4),
                "evasive_prob": round(result["evasive_prob"], 4)
            })

    evasion_rate = round(len(flagged) / max(total, 1), 4)

    return {
        "evasion_rate": evasion_rate,
        "evasion_count": len(flagged),
        "total_qa_pairs": total,
        "flagged_pairs": flagged,
        "qa_results": qa_results
    }

