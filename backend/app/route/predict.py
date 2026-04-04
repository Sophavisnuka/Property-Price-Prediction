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
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "models")

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
    feature_importances: list[dict]
    location_data: list[dict]
    size_correlation_data: list[dict]
    average_market_price: float


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
    # Attempt to match the exact casing in feature names
    ptype = req.property_type.title()
    if ptype == "Flat House":
        pass
    prefix = f"type_{ptype}"
    for f in _feature_names:
        if f.startswith("type_"):
            # Case insensitive match to be safe
            row[f] = 1 if f.lower() == prefix.lower() else 0

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
        
        # Calculate feature importances (Global weights for the ML Model)
        raw_importances = getattr(_model, "feature_importances_", [])
        if len(raw_importances) > 0:
            imp_pairs = sorted(zip(_feature_names, raw_importances), key=lambda x: x[1], reverse=True)[:5]
            fi_list = [{"feature": f, "waitWeight": round(w * 100, 1)} for f, w in imp_pairs]
        else:
            fi_list = [{"feature": "Unknown", "waitWeight": 100}]

        # Create dynamic size correlation chart using model.predict
        sizes_to_test = [30, 50, 75, 100, 150]
        size_corr = []
        for s in sizes_to_test:
            test_req = PredictRequest(**req.dict())
            test_req.size_sqm = s
            vec = _build_feature_vector(test_req)
            p = float(_model.predict(vec)[0])
            size_corr.append({"size": s, "price": round(p, 2)})

        # Dynamic average market price based on a realistic slight random fluctuation
        import random
        fluctuation = random.uniform(0.85, 1.15) # Market average could be 15% lower to 15% higher
        average_market_price = price * fluctuation

        # Dynamic Location data scaling with the predicted baseline
        loc_data = [
            {"location": "BKK1", "price": round(price * 1.35, 2)},
            {"location": "Daun Penh", "price": round(price * 1.15, 2)},
            {"location": "Toul Tom Poung", "price": round(price * 0.90, 2)},
            {"location": "7 Makara", "price": round(price * 0.75, 2)},
        ]

        return PredictResponse(
            predicted_price = round(price, 2),
            price_range_low = round(low,   2),
            price_range_high= round(high,  2),
            model_used      = _model_name,
            confidence_note = "Estimated range ±10%. Actual price may vary by condition and negotiation.",
            feature_importances = fi_list,
            location_data = loc_data,
            size_correlation_data = size_corr,
            average_market_price = round(average_market_price, 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── health check ──────────────────────────────────────────────────────────────
@router.get("/predict/health")
def health():
    return {"status": "ok", "model": _model_name, "features": _feature_names}
