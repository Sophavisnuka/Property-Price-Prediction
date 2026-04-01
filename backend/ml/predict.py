"""
predict.py
----------
FastAPI route that:
    1. Accepts user input (location, bedrooms, bathrooms, ...)
    2. Encodes + scales it using the saved artifacts from training
    3. Returns price prediction + similar property suggestions
"""

import pickle, os
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import pandas as pd

router = APIRouter()

# ── paths ─────────────────────────────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "models")

def _load(filename):
    path = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing artifact: {path}. Run train_model.py first.")
    with open(path, "rb") as f:
        return pickle.load(f)

# Load once at startup (module-level)
_bundle       = _load("best_model.pkl")     # {"model": ..., "model_name": ...}
_model        = _bundle["model"]
_model_name   = _bundle["model_name"]
_encoders     = _load("encoders.pkl")       # dict[str, LabelEncoder]
_scaler       = _load("scaler.pkl")         # StandardScaler
_feature_names = _load("feature_names.pkl") # list[str]


# ── request / response schemas ─────────────────────────────────────────────────
class PredictRequest(BaseModel):
    location:       str            = Field(..., example="phnom penh")
    property_type:  str            = Field(..., example="apartment")
    bedrooms:       int            = Field(..., ge=0, le=20, example=2)
    bathrooms:      int            = Field(..., ge=1, le=20, example=2)
    floor_area_sqm: float          = Field(..., gt=0,        example=75.0)
    furnishing:     Optional[str]  = Field("unfurnished",    example="furnished")
    floor_level:    Optional[int]  = Field(1,                example=3)
    year_built:     Optional[int]  = Field(2015,             example=2020)
    parking_spaces: Optional[int]  = Field(0,                example=1)


class PredictResponse(BaseModel):
    predicted_price: float
    price_range_low: float
    price_range_high: float
    model_used: str
    confidence_note: str


# ── helpers ───────────────────────────────────────────────────────────────────
def _safe_encode(col: str, value: str) -> int:
    """Label-encode a value; fall back to 0 (most common class) if unseen."""
    le = _encoders.get(col)
    if le is None:
        return 0
    value = str(value).strip().lower()
    if value in le.classes_:
        return int(le.transform([value])[0])
    # Unknown category — use the most frequent class
    return 0


def _build_feature_vector(req: PredictRequest) -> np.ndarray:
    row = {
        "location":       _safe_encode("location",      req.location),
        "property_type":  _safe_encode("property_type", req.property_type),
        "furnishing":     _safe_encode("furnishing",     req.furnishing or "unfurnished"),
        "bedrooms":       req.bedrooms,
        "bathrooms":      req.bathrooms,
        "floor_area_sqm": req.floor_area_sqm,
        "floor_level":    req.floor_level or 1,
        "year_built":     req.year_built or 2015,
        "parking_spaces": req.parking_spaces or 0,
    }
    # Keep only features the model was trained on, in correct order
    vec = np.array([[row.get(f, 0) for f in _feature_names]], dtype=float)
    vec = _scaler.transform(vec)
    return vec


# ── route ─────────────────────────────────────────────────────────────────────
@router.post("/predict", response_model=PredictResponse)
def predict_price(req: PredictRequest):
    try:
        X = _build_feature_vector(req)
        price = float(_model.predict(X)[0])

        # Simple ±10% confidence band
        low  = price * 0.90
        high = price * 1.10

        return PredictResponse(
            predicted_price = round(price, 2),
            price_range_low = round(low,   2),
            price_range_high= round(high,  2),
            model_used      = _model_name,
            confidence_note = "Estimated range ±10%. Actual price may vary by condition and negotiation.",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ── health check ──────────────────────────────────────────────────────────────
@router.get("/predict/health")
def health():
    return {"status": "ok", "model": _model_name, "features": _feature_names}
