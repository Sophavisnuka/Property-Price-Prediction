"""
predict.py
----------
FastAPI route that handles prediction based on Khmer24 features.
"""

import pickle, os, math
import numpy as np
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# ── paths ─────────────────────────────────────────────────────────────────────
# Depending on where this file is, adjust the relative path to your ml/models directory
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "models")

def _load(filename):
    path = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing artifact: {path}. Run train_model.py first.")
    with open(path, "rb") as f:
        return pickle.load(f)

# Load once at startup
_bundle       = _load("best_model.pkl")     
_model        = _bundle["model"]
_model_name   = _bundle["model_name"]
_encoders     = _load("encoders.pkl")       
_scaler       = _load("scaler.pkl")         
_imputer      = _load("imputer.pkl")        # NEW: Load imputer
_feature_names = _load("feature_names.pkl") 


# ── request / response schemas ─────────────────────────────────────────────────
class PredictRequest(BaseModel):
    size_sqm:       float          = Field(..., gt=0, example=75.0)
    bedrooms:       int            = Field(..., ge=0, example=2)
    bathrooms:      int            = Field(..., ge=1, example=2)
    property_type:  str            = Field(..., example="Villa") # e.g. "Flat", "Villa", "Condo"
    furnishing:     Optional[str]  = Field("unfurnished", example="furnished")
    # You can add district or location here if you want to calculate district_freq


class PredictResponse(BaseModel):
    predicted_price: float
    price_range_low: float
    price_range_high: float
    model_used: str
    confidence_note: str


# ── helpers ───────────────────────────────────────────────────────────────────
def _build_feature_vector(req: PredictRequest) -> np.ndarray:
    # 1. Basic properties
    size_sqm = req.size_sqm
    bedrooms = req.bedrooms
    bathrooms = req.bathrooms
    
    # 2. Engineered features
    log_size_sqm = math.log1p(size_sqm) if size_sqm > 0 else 0
    bath_per_bed = bathrooms / bedrooms if bedrooms > 0 else bathrooms
    total_rooms = bedrooms + bathrooms
    
    # Furnished score (basic binary map for example purposes)
    furnished_score = 1 if str(req.furnishing).lower() in ["furnished", "fully furnished"] else 0
    
    # District freq (fallback average if user district isn't provided/known)
    district_freq = 0.5 
    
    # Missing value flags
    size_sqm_was_missing = 0
    bedrooms_was_missing = 0
    bathrooms_was_missing = 0

    # 3. Compile base dictionary
    row = {
        "size_sqm": size_sqm,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "log_size_sqm": log_size_sqm,
        "bath_per_bed": bath_per_bed,
        "total_rooms": total_rooms,
        "furnished_score": furnished_score,
        "district_freq": district_freq,
        "size_sqm_was_missing": size_sqm_was_missing,
        "bedrooms_was_missing": bedrooms_was_missing,
        "bathrooms_was_missing": bathrooms_was_missing
    }
    
    # 4. Generate dummy variables for property_type
    # Example: If req.property_type is "Villa", we set "type_Villa" = 1, others = 0
    prefix = f"type_{req.property_type}"
    for f in _feature_names:
        if f.startswith("type_"):
            row[f] = 1 if f == prefix else 0

    # 5. Keep only features the model was trained on, in correct order
    vec = np.array([[row.get(f, 0) for f in _feature_names]], dtype=float)
    
    # 6. Apply Imputer and Scaler
    vec = _imputer.transform(vec)
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
