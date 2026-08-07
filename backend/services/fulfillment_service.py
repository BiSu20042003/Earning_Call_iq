"""
Guidance fulfillment prediction service.
Loads trained XGBoost model and predicts fulfillment probability
for each extracted guidance claim.
"""

import json
import pickle
import numpy as np
from pathlib import Path

MODEL_PATH = Path(__file__).parent.parent.parent / "ml_models" / "fulfillment_model.pkl"
ENCODER_PATH = Path(__file__).parent.parent.parent / "ml_models" / "metric_encoder.pkl"

_model   = None
_encoder = None

METRIC_CATEGORIES = [
    "Revenue", "Gross Profit", "Gross Margin",
    "Operating Income", "Operating Margin",
    "Net Income", "Net Margin", "EPS",
    "R&D", "Operating Expenses", "EBIT", "EBITDA", "Other"
]


def get_model():
    global _model, _encoder
    if _model is None:
        with open(MODEL_PATH, "rb") as f:
            _model = pickle.load(f)
        with open(ENCODER_PATH, "rb") as f:
            _encoder = pickle.load(f)
    return _model, _encoder


def build_feature_vector(
    claim: dict,
    sentiment: dict,
    evasion_rate: float
) -> list:
    """
    Build feature vector for one guidance claim.
    Must match exactly the features used during XGBoost training.
    """
    model, encoder = get_model()

    # Encode metric as integer
    metric_lower = claim.get("metric", "Other").lower()
    metric_idx   = 12  # default "Other"
    for i, m in enumerate(METRIC_CATEGORIES):
        if m.lower() in metric_lower or metric_lower in m.lower():
            metric_idx = i
            break

    # Encode unit
    unit_map = {"%": 0, "B": 1, "M": 2, "absolute": 3}
    unit_idx = unit_map.get(claim.get("value_unit", "%"), 0)

    val_low  = claim.get("value_low")  or 0.0
    val_high = claim.get("value_high") or val_low
    val_mid  = (val_low + val_high) / 2 if val_high else val_low
    val_range = val_high - val_low if val_high else 0.0

    features = [
        sentiment.get("positive", 0.33),
        sentiment.get("negative", 0.33),
        sentiment.get("neutral",  0.34),
        evasion_rate,
        metric_idx,
        unit_idx,
        val_low,
        val_high,
        val_mid,
        val_range,
        claim.get("confidence", 0.8)
    ]

    return features


def predict_fulfillment(
    claims: list,
    sentiment: dict,
    evasion_rate: float
) -> list:
    """
    Predict fulfillment probability for each guidance claim.
    Returns claims with added fulfillment_probability field.
    """
    return [{"fulfillment_probability": 0.9}] # to be removed
    if not claims:
        return []

    if not MODEL_PATH.exists():
        # Model not trained yet — return 0.5 default
        for claim in claims:
            claim["fulfillment_probability"] = 0.5
        return claims

    model, _ = get_model()

    feature_matrix = np.array([
        build_feature_vector(c, sentiment, evasion_rate)
        for c in claims
    ])

    probabilities = model.predict_proba(feature_matrix)[:, 1]

    enriched_claims = []
    for claim, prob in zip(claims, probabilities):
        enriched = dict(claim)
        enriched["fulfillment_probability"] = round(float(prob), 4)
        enriched_claims.append(enriched)

    return enriched_claims