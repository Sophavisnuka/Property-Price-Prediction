import pickle, os
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# ── Load model artifacts ─────────────────────────────────────────────────────
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models")

def _load(filename):
    path = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing: {path}. Run train_model.py first.")
    with open(path, "rb") as f:
        return pickle.load(f)

_bundle        = _load("best_model.pkl")
_model         = _bundle["model"]
_model_name    = _bundle["model_name"]
_encoders      = _load("encoders.pkl")
_scaler        = _load("scaler.pkl")
_feature_names = _load("feature_names.pkl")

# ── Request schema — matches YOUR CSV columns ────────────────────────────────
class PredictRequest(BaseModel):
    city:          str = Field(..., example="phnom penh")
    district:      str = Field(..., example="toul kork")
    location:      str = Field(..., example="toul kork")
    property_type: str = Field(..., example="apartment")

# ── Response schema ──────────────────────────────────────────────────────────
class PredictResponse(BaseModel):
    predicted_price:  float
    price_range_low:  float
    price_range_high: float
    model_used:       str

# ── Helper: encode one value safely ─────────────────────────────────────────
def _encode(col: str, value: str) -> int:
    le = _encoders.get(col)
    if le is None:
        return 0
    value = str(value).strip().lower()
    if value in le.classes_:
        return int(le.transform([value])[0])
    return 0   # unknown category → fallback

# ── Build feature vector in the same order as training ───────────────────────
def _build_vector(req: PredictRequest) -> np.ndarray:
    import datetime
    now = datetime.datetime.now()

    row = {
        "city":           _encode("city",          req.city),
        "district":       _encode("district",      req.district),
        "location":       _encode("location",      req.location),
        "property_type":  _encode("property_type", req.property_type),
        "post_month":     now.month,
        "post_dayofweek": now.weekday(),
        "post_quarter":   (now.month - 1) // 3 + 1,
    }

    vec = np.array([[row[f] for f in _feature_names]], dtype=float)
    vec = _scaler.transform(vec)
    return vec

# ── Predict endpoint ─────────────────────────────────────────────────────────
@router.post("/predict", response_model=PredictResponse)
def predict_price(req: PredictRequest):
    try:
        X     = _build_vector(req)
        price = float(_model.predict(X)[0])
        return PredictResponse(
            predicted_price  = round(price, 2),
            price_range_low  = round(price * 0.90, 2),
            price_range_high = round(price * 1.10, 2),
            model_used       = _model_name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── Health check ─────────────────────────────────────────────────────────────
@router.get("/predict/health")
def health():
    return {
        "status":   "ok",
        "model":    _model_name,
        "features": _feature_names,
    }

# **Your folder structure should look like this:**
# backend/
#   app/
#     __init__.py        ← make sure this exists (can be empty)
#     main.py            ← updated above
#     route/
#       __init__.py      ← make sure this exists (can be empty)
#       predict.py       ← updated above
#   ml/
#     models/
#       best_model.pkl
#       ...