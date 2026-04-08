"""
predict.py
----------
FastAPI route that handles prediction based on Khmer24 features.
"""

import pickle, os, math
from difflib import get_close_matches
import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

router = APIRouter()

# ── paths ─────────────────────────────────────────────────────────────────────
MODEL_VERSION = "version_number"
MODEL_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "ml", "models", MODEL_VERSION)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

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

CLEANED_V4_CSV = os.path.join(PROJECT_ROOT, "data_cleaning", "Khmer24_cleaned_v4.csv")
FEATURE_DATA_CSV = os.path.join(PROJECT_ROOT, "data", "Khmer24_features.csv")
RAW_DATA_CSV = os.path.join(PROJECT_ROOT, "backend", "data", "properties.csv")


def _normalize_text(value: Optional[str]) -> str:
    return str(value or "").strip().lower()


def _clean_geo_text(value: Optional[str]) -> str:
    cleaned = _normalize_text(value)
    for token in ["khan", "sangkat", "district", "city", "province"]:
        cleaned = cleaned.replace(token, " ")
    cleaned = cleaned.replace(",", " ").replace("-", " ")
    cleaned = " ".join(cleaned.split())
    return cleaned


def _is_chroy_chongva_text(value: Optional[str]) -> bool:
    cleaned = _clean_geo_text(value)
    if not cleaned:
        return False
    has_chroy = ("chroy" in cleaned) or ("chrouy" in cleaned)
    has_changva = any(token in cleaned for token in ["changva", "changvar", "chongva", "chongvar"])
    return has_chroy and has_changva


def _normalize_property_type(value: Optional[str]) -> str:
    raw = str(value or "Unclassified").strip().lower()
    alias_map = {
        "apartment": "Flat",
        "condo": "Flat",
        "flat": "Flat",
        "townhouse": "House",
        "link house": "House",
        "link villa": "Link Villa",
        "single villa": "Single Villa",
        "twin villa": "Twin Villa",
        "shophouse": "Shophouse",
        "shop house": "Shophouse",
        "shop": "Shop",
        "room": "Room",
        "house": "House",
        "villa": "Villa",
        "flat house": "Flat House",
        "unclassified": "Unclassified",
    }
    canonical = alias_map.get(raw)
    if canonical:
        return canonical
    return str(value or "Unclassified").strip().title()


def _read_csv_robust(path: str) -> pd.DataFrame:
    last_error = None
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, on_bad_lines="skip")
        except UnicodeDecodeError as err:
            last_error = err
    raise last_error


def _enforce_monotonic_bucket_prices(price_map: dict[int, float]) -> dict[int, float]:
    if not price_map:
        return {}

    fixed = {}
    running = None
    for k in sorted(price_map.keys()):
        value = float(price_map[k])
        running = value if running is None else max(running, value)
        fixed[int(k)] = float(running)
    return fixed


def _build_context_stats() -> dict:
    district_freq_map = {}
    district_price_map = {}
    type_price_map = {}
    type_pps_map = {}
    type_profile_map = {}
    bedroom_price_map = {}
    bedroom_price_map_monotonic = {}
    bathroom_price_map = {}
    bathroom_price_map_monotonic = {}
    dominant_type = "House"
    top_regions = []
    overall_price = 1000.0
    overall_pps_median = 12.0
    overall_size_median = 60.0
    overall_bed_median = 2.0
    overall_bath_median = 2.0
    default_post_month = 6.0
    default_post_dayofweek = 3.0
    default_post_quarter = 2.0
    pps_low = 1.0
    pps_high = 30.0

    source_df = None
    for candidate in (CLEANED_V4_CSV, FEATURE_DATA_CSV, RAW_DATA_CSV):
        if os.path.exists(candidate):
            try:
                source_df = _read_csv_robust(candidate)
                break
            except Exception:
                continue

    if source_df is None or source_df.empty:
        return {
            "district_freq_map": district_freq_map,
            "district_price_map": district_price_map,
            "type_price_map": type_price_map,
            "top_regions": top_regions,
            "overall_price": overall_price,
        }

    if "rent_price_usd" in source_df.columns:
        rent = pd.to_numeric(source_df["rent_price_usd"], errors="coerce")
        source_df = source_df.assign(rent_price_usd=rent)
        source_df = source_df[source_df["rent_price_usd"].notna() & (source_df["rent_price_usd"] > 0)].copy()

    if "size_sqm" in source_df.columns:
        source_df["size_sqm"] = pd.to_numeric(source_df["size_sqm"], errors="coerce")

    if "bedrooms" in source_df.columns:
        source_df["bedrooms"] = pd.to_numeric(source_df["bedrooms"], errors="coerce")

    if "bathrooms" in source_df.columns:
        source_df["bathrooms"] = pd.to_numeric(source_df["bathrooms"], errors="coerce")

    # Keep dataset aligned with project scope (Chroy Chongva only) when possible.
    if not source_df.empty and "district" in source_df.columns:
        in_scope_mask = source_df["district"].map(_is_chroy_chongva_text)
        if in_scope_mask.any():
            source_df = source_df[in_scope_mask].copy()

    # Remove likely sale-like rows from rental context to avoid inflated price anchors.
    if not source_df.empty and "title" in source_df.columns:
        title = source_df["title"].astype(str).str.lower()
        sale_like = title.str.contains(r"\bsale\b|\bsell\b", regex=True, na=False)
        source_df = source_df[~sale_like].copy()

    # Trim extreme tails to keep context robust against noisy listings.
    if not source_df.empty and "rent_price_usd" in source_df.columns:
        q01 = source_df["rent_price_usd"].quantile(0.01)
        q99 = source_df["rent_price_usd"].quantile(0.99)
        source_df = source_df[(source_df["rent_price_usd"] >= q01) & (source_df["rent_price_usd"] <= q99)].copy()

    if not source_df.empty and "district" in source_df.columns:
        district_key = source_df["district"].map(_normalize_text)
        district_freq_map = district_key.value_counts(normalize=True).to_dict()

    if not source_df.empty and "district" in source_df.columns and "rent_price_usd" in source_df.columns:
        by_district = (
            source_df.assign(_district=source_df["district"].map(_normalize_text))
            .groupby("_district", dropna=False)["rent_price_usd"]
            .median()
            .dropna()
        )
        district_price_map = by_district.to_dict()
        top_regions = [
            {"location": k.title(), "price": round(float(v), 2)}
            for k, v in by_district.sort_values(ascending=False).head(6).items()
            if k
        ]

    if not source_df.empty and "property_type" in source_df.columns and "rent_price_usd" in source_df.columns:
        by_type = (
            source_df.assign(_ptype=source_df["property_type"].map(_normalize_property_type))
            .groupby("_ptype", dropna=False)["rent_price_usd"]
            .median()
            .dropna()
        )
        type_price_map = by_type.to_dict()

        type_counts = (
            source_df.assign(_ptype=source_df["property_type"].map(_normalize_property_type))
            ["_ptype"]
            .value_counts()
        )
        if not type_counts.empty:
            dominant_type = str(type_counts.index[0])

    if not source_df.empty and {"property_type", "size_sqm", "rent_price_usd"}.issubset(source_df.columns):
        pps_df = source_df[(source_df["size_sqm"] > 5)].copy()
        if not pps_df.empty:
            pps_df["pps"] = pps_df["rent_price_usd"] / pps_df["size_sqm"]
            pps_df = pps_df[(pps_df["pps"] > 0.5) & (pps_df["pps"] < 300)]
            if not pps_df.empty:
                by_type_pps = (
                    pps_df.assign(_ptype=pps_df["property_type"].map(_normalize_property_type))
                    .groupby("_ptype", dropna=False)["pps"]
                    .median()
                    .dropna()
                )
                type_pps_map = by_type_pps.to_dict()

    if not source_df.empty and "rent_price_usd" in source_df.columns and "bedrooms" in source_df.columns:
        beds = source_df[source_df["bedrooms"].notna()].copy()
        if not beds.empty:
            beds["bedrooms_bucket"] = beds["bedrooms"].round().astype(int).clip(lower=0, upper=12)
            bed_price = beds.groupby("bedrooms_bucket")["rent_price_usd"].median().dropna()
            bedroom_price_map = {int(k): float(v) for k, v in bed_price.to_dict().items()}
            bedroom_price_map_monotonic = _enforce_monotonic_bucket_prices(bedroom_price_map)

    if not source_df.empty and "rent_price_usd" in source_df.columns and "bathrooms" in source_df.columns:
        baths = source_df[source_df["bathrooms"].notna()].copy()
        if not baths.empty:
            baths["bathrooms_bucket"] = baths["bathrooms"].round().astype(int).clip(lower=1, upper=12)
            bath_price = baths.groupby("bathrooms_bucket")["rent_price_usd"].median().dropna()
            bathroom_price_map = {int(k): float(v) for k, v in bath_price.to_dict().items()}
            bathroom_price_map_monotonic = _enforce_monotonic_bucket_prices(bathroom_price_map)

    if not source_df.empty and {"property_type", "size_sqm", "bedrooms", "bathrooms"}.issubset(source_df.columns):
        profile_df = source_df.copy()
        profile_df = profile_df[
            profile_df["size_sqm"].notna() &
            profile_df["bedrooms"].notna() &
            profile_df["bathrooms"].notna()
        ]
        if not profile_df.empty:
            by_type_profile = (
                profile_df.assign(_ptype=profile_df["property_type"].map(_normalize_property_type))
                .groupby("_ptype", dropna=False)
                .agg({
                    "size_sqm": "median",
                    "bedrooms": "median",
                    "bathrooms": "median",
                })
            )
            for ptype, row in by_type_profile.iterrows():
                exp_rooms = max(float(row["bedrooms"]) + float(row["bathrooms"]), 1.0)
                type_profile_map[str(ptype)] = {
                    "size_sqm": float(row["size_sqm"]),
                    "bedrooms": float(row["bedrooms"]),
                    "bathrooms": float(row["bathrooms"]),
                    "size_per_room": float(row["size_sqm"]) / exp_rooms,
                }

    if not source_df.empty and "rent_price_usd" in source_df.columns:
        overall_price = float(source_df["rent_price_usd"].median())

    if not source_df.empty and "size_sqm" in source_df.columns:
        size_valid = source_df["size_sqm"].dropna()
        if not size_valid.empty:
            overall_size_median = float(size_valid.median())

    if not source_df.empty and "bedrooms" in source_df.columns:
        bed_valid = source_df["bedrooms"].dropna()
        if not bed_valid.empty:
            overall_bed_median = float(bed_valid.median())

    if not source_df.empty and "bathrooms" in source_df.columns:
        bath_valid = source_df["bathrooms"].dropna()
        if not bath_valid.empty:
            overall_bath_median = float(bath_valid.median())

    if not source_df.empty and "size_sqm" in source_df.columns and "rent_price_usd" in source_df.columns:
        size = pd.to_numeric(source_df["size_sqm"], errors="coerce")
        valid = size.notna() & (size > 5)
        if valid.any():
            pps = source_df.loc[valid, "rent_price_usd"] / size.loc[valid]
            pps = pps[(pps > 0.5) & (pps < 300)]
            if not pps.empty:
                overall_pps_median = float(pps.median())
                pps_low = float(pps.quantile(0.10))
                pps_high = float(pps.quantile(0.90))
                if pps_high <= pps_low:
                    pps_low, pps_high = 1.0, 30.0

    if not source_df.empty and "posted_date" in source_df.columns:
        parsed_date = pd.to_datetime(source_df["posted_date"], errors="coerce")
        if parsed_date.notna().any():
            default_post_month = float(parsed_date.dt.month.dropna().median())
            default_post_dayofweek = float(parsed_date.dt.dayofweek.dropna().median())
            default_post_quarter = float(parsed_date.dt.quarter.dropna().median())

    district_keys = list(district_freq_map.keys())

    return {
        "district_freq_map": district_freq_map,
        "district_price_map": district_price_map,
        "district_keys": district_keys,
        "type_price_map": type_price_map,
        "type_pps_map": type_pps_map,
        "type_profile_map": type_profile_map,
        "bedroom_price_map": bedroom_price_map,
        "bedroom_price_map_monotonic": bedroom_price_map_monotonic,
        "bathroom_price_map": bathroom_price_map,
        "bathroom_price_map_monotonic": bathroom_price_map_monotonic,
        "dominant_type": dominant_type,
        "top_regions": top_regions,
        "overall_price": overall_price,
        "overall_pps_median": overall_pps_median,
        "overall_size_median": overall_size_median,
        "overall_bed_median": overall_bed_median,
        "overall_bath_median": overall_bath_median,
        "default_post_month": default_post_month,
        "default_post_dayofweek": default_post_dayofweek,
        "default_post_quarter": default_post_quarter,
        "pps_low": pps_low,
        "pps_high": pps_high,
    }


_CONTEXT = _build_context_stats()
_SCOPED_DISTRICT_KEY = next(
    (k for k in _CONTEXT.get("district_keys", []) if _is_chroy_chongva_text(k)),
    "",
)


def _resolve_district_key(*values: Optional[str]) -> str:
    # Project scope is fixed to Chroy Chongva, so we always anchor to that district key.
    if _SCOPED_DISTRICT_KEY:
        return _SCOPED_DISTRICT_KEY

    keys = _CONTEXT.get("district_keys", [])
    if not keys:
        return ""

    cleaned_to_raw = {_clean_geo_text(k): k for k in keys}
    cleaned_keys = list(cleaned_to_raw.keys())

    for raw_value in values:
        candidate = _clean_geo_text(raw_value)
        if not candidate:
            continue

        # Exact cleaned match first.
        if candidate in cleaned_to_raw:
            return cleaned_to_raw[candidate]

        # Partial inclusion catches values like "chroy changvar" vs "chrouy changva phnom penh".
        for ck in cleaned_keys:
            if candidate in ck or ck in candidate:
                return cleaned_to_raw[ck]

        # Fuzzy fallback for small spelling differences.
        close = get_close_matches(candidate, cleaned_keys, n=1, cutoff=0.72)
        if close:
            return cleaned_to_raw[close[0]]

    return ""


def _compute_average_market_price(district_key: str, ptype: str) -> float:
    price = _CONTEXT["district_price_map"].get(district_key)
    if price is None:
        price = _CONTEXT["type_price_map"].get(ptype)
    if price is None:
        price = _CONTEXT["overall_price"]
    return float(price)


def _nearest_bucket_price(price_map: dict, value: float, minimum_key: int = 0) -> Optional[float]:
    if not price_map:
        return None

    keys = [int(k) for k in price_map.keys()]
    if not keys:
        return None

    target = max(int(round(float(value))), minimum_key)
    nearest = min(keys, key=lambda k: abs(k - target))
    return float(price_map.get(nearest))


def _compute_relation_anchor(req: "PredictRequest", district_key: str, ptype: str, average_market_price: float) -> float:
    size_sqm = max(float(req.size_sqm), 1.0)
    components = [float(average_market_price)]
    weights = [0.30]

    type_pps = _CONTEXT.get("type_pps_map", {}).get(ptype)
    if type_pps is not None:
        components.append(size_sqm * float(type_pps))
        weights.append(0.30)

    bed_price = _nearest_bucket_price(_CONTEXT.get("bedroom_price_map_monotonic", {}), req.bedrooms, minimum_key=0)
    if bed_price is not None:
        components.append(bed_price)
        weights.append(0.20)

    bath_price = _nearest_bucket_price(_CONTEXT.get("bathroom_price_map_monotonic", {}), req.bathrooms, minimum_key=1)
    if bath_price is not None:
        components.append(bath_price)
        weights.append(0.20)

    weighted_anchor = np.average(np.array(components, dtype=float), weights=np.array(weights, dtype=float))
    return float(weighted_anchor)


def _compute_relation_coherence(req: "PredictRequest", ptype: str) -> float:
    profile = _CONTEXT.get("type_profile_map", {}).get(ptype, {})

    expected_size = float(profile.get("size_sqm", _CONTEXT.get("overall_size_median", 60.0)))
    expected_bed = max(float(profile.get("bedrooms", _CONTEXT.get("overall_bed_median", 2.0))), 0.5)
    expected_bath = max(float(profile.get("bathrooms", _CONTEXT.get("overall_bath_median", 2.0))), 1.0)

    expected_rooms = max(expected_bed + expected_bath, 1.0)
    expected_size_per_room = max(expected_size / expected_rooms, 1.0)

    actual_size = max(float(req.size_sqm), 1.0)
    actual_bed = max(float(req.bedrooms), 0.0)
    actual_bath = max(float(req.bathrooms), 1.0)
    actual_rooms = max(actual_bed + actual_bath, 1.0)
    actual_size_per_room = max(actual_size / actual_rooms, 1.0)

    room_ratio = actual_rooms / expected_rooms
    bed_ratio = (actual_bed + 0.5) / (expected_bed + 0.5)
    bath_ratio = (actual_bath + 0.5) / (expected_bath + 0.5)
    size_room_ratio = actual_size_per_room / expected_size_per_room

    mismatch = (
        abs(math.log(max(room_ratio, 1e-6))) +
        abs(math.log(max(bed_ratio, 1e-6))) +
        abs(math.log(max(bath_ratio, 1e-6))) +
        abs(math.log(max(size_room_ratio, 1e-6)))
    )

    coherence = float(np.exp(-0.28 * mismatch))
    return float(np.clip(coherence, 0.35, 1.0))


def _estimate_expected_pps(req: "PredictRequest", ptype: str) -> float:
    base_pps = _CONTEXT.get("type_pps_map", {}).get(ptype)
    if base_pps is None:
        base_pps = _CONTEXT.get("overall_pps_median")

    if base_pps is None:
        overall_size = max(float(_CONTEXT.get("overall_size_median", 60.0)), 1.0)
        base_pps = float(_CONTEXT.get("overall_price", 1000.0)) / overall_size

    profile = _CONTEXT.get("type_profile_map", {}).get(ptype, {})
    expected_size_per_room = float(profile.get("size_per_room", 0.0))
    if expected_size_per_room <= 0:
        expected_rooms = max(
            float(_CONTEXT.get("overall_bed_median", 2.0)) + float(_CONTEXT.get("overall_bath_median", 2.0)),
            1.0,
        )
        expected_size_per_room = max(float(_CONTEXT.get("overall_size_median", 60.0)) / expected_rooms, 1.0)

    actual_rooms = max(float(req.bedrooms) + float(req.bathrooms), 1.0)
    actual_size_per_room = max(float(req.size_sqm) / actual_rooms, 1.0)

    density_ratio = actual_size_per_room / expected_size_per_room
    density_factor = float(np.clip(np.power(max(density_ratio, 1e-6), 0.18), 0.88, 1.16))

    expected_bed = float(profile.get("bedrooms", _CONTEXT.get("overall_bed_median", 2.0)))
    expected_bath = float(profile.get("bathrooms", _CONTEXT.get("overall_bath_median", 2.0)))
    bed_delta = float(req.bedrooms) - expected_bed
    bath_delta = float(req.bathrooms) - expected_bath
    room_premium = float(np.clip(1.0 + (0.08 * bed_delta) + (0.05 * bath_delta), 0.82, 1.45))

    return float(base_pps) * density_factor * room_premium


def _calibrate_price(raw_price: float, req: "PredictRequest", district_key: str, ptype: str) -> tuple[float, float, float]:
    average_market_price = _compute_average_market_price(district_key, ptype)
    relation_anchor = _compute_relation_anchor(req, district_key, ptype, average_market_price)
    relation_coherence = _compute_relation_coherence(req, ptype)

    price = (relation_coherence * float(raw_price)) + ((1.0 - relation_coherence) * relation_anchor)

    # Regularize predicted price-per-sqm to keep size sensitivity stable.
    size_for_bounds = max(float(req.size_sqm), 1.0)
    expected_pps = _estimate_expected_pps(req, ptype)
    pred_pps = max(price / size_for_bounds, 0.01)

    pps_low_raw = float(_CONTEXT.get("pps_low", 1.0))
    pps_high_raw = float(_CONTEXT.get("pps_high", 30.0))
    overall_pps = float(_CONTEXT.get("overall_pps_median", expected_pps))

    # Keep lower bound realistic for small units; raw pps_low from sparse slices can be too high.
    pps_low = max(0.8, min(pps_low_raw, overall_pps * 0.75))
    pps_high = max(pps_low + 2.0, max(pps_high_raw, overall_pps * 1.8))

    corridor_low = max(pps_low, expected_pps * 0.72)
    corridor_high = min(pps_high, expected_pps * 1.35)
    if corridor_high <= corridor_low:
        corridor_low, corridor_high = pps_low, pps_high

    stabilized_pps = (0.60 * pred_pps) + (0.40 * expected_pps)
    stabilized_pps = float(np.clip(stabilized_pps, corridor_low, corridor_high))
    price = stabilized_pps * size_for_bounds

    # Apply a smooth room premium so adding rooms does not reduce price at fixed size.
    room_multiplier = 1.0 + (0.060 * max(float(req.bedrooms) - 1.0, 0.0)) + (0.040 * max(float(req.bathrooms) - 1.0, 0.0))
    price *= float(np.clip(room_multiplier, 1.0, 1.55))

    # Clip to plausible local price-per-sqm bounds.
    min_reasonable = max(50.0, size_for_bounds * pps_low)
    max_reasonable = max(min_reasonable + 50.0, size_for_bounds * pps_high)
    price = float(np.clip(price, min_reasonable, max_reasonable))

    return price, average_market_price, relation_coherence


def _predict_price_for_request(req: "PredictRequest") -> tuple[float, float, float]:
    X = _build_feature_vector(req)
    raw_price = float(_model.predict(X)[0])
    district_key = _resolve_district_key(req.district, req.location, req.city)
    ptype = _normalize_property_type(req.property_type)
    return _calibrate_price(raw_price, req, district_key, ptype)


def _enforce_room_monotonicity(req: "PredictRequest", price: float) -> float:
    adjusted = float(price)

    max_bed = max(int(req.bedrooms), 0)
    max_bath = max(int(req.bathrooms), 1)
    monotonic_grid: dict[tuple[int, int], float] = {}

    for b in range(0, max_bed + 1):
        for bt in range(1, max_bath + 1):
            payload = req.dict()
            payload["bedrooms"] = b
            payload["bathrooms"] = bt
            step_req = PredictRequest(**payload)
            raw_step_price, _, _ = _predict_price_for_request(step_req)
            step_price = float(raw_step_price)

            if b > 0:
                step_price = max(step_price, monotonic_grid[(b - 1, bt)] * 1.01)
            if bt > 1:
                step_price = max(step_price, monotonic_grid[(b, bt - 1)] * 1.005)

            monotonic_grid[(b, bt)] = step_price

    adjusted = max(adjusted, monotonic_grid[(max_bed, max_bath)])

    return float(adjusted)


def _pick_reference_property_type(current_ptype: str) -> str:
    price_map = _CONTEXT.get("type_price_map", {})
    if not price_map:
        return current_ptype

    dominant = str(_CONTEXT.get("dominant_type", "")).strip()
    if dominant and dominant != current_ptype:
        return dominant

    candidates = [ptype for ptype in price_map.keys() if ptype != current_ptype]
    if not candidates:
        return current_ptype

    current_price = float(price_map.get(current_ptype, _CONTEXT.get("overall_price", 1000.0)))
    candidates.sort(key=lambda p: abs(float(price_map.get(p, current_price)) - current_price), reverse=True)
    return str(candidates[0])


def _build_dynamic_feature_impacts(req: "PredictRequest", base_price: float) -> list[dict]:
    ptype = _normalize_property_type(req.property_type)
    profile = _CONTEXT.get("type_profile_map", {}).get(ptype, {})

    ref_size = float(profile.get("size_sqm", _CONTEXT.get("overall_size_median", max(req.size_sqm, 6.0))))
    if abs(ref_size - float(req.size_sqm)) < 2.0:
        ref_size = max(6.0, float(req.size_sqm) * 0.75)

    ref_bed = int(round(profile.get("bedrooms", _CONTEXT.get("overall_bed_median", max(req.bedrooms, 1)))))
    if ref_bed == int(req.bedrooms):
        ref_bed = int(req.bedrooms) + 1 if int(req.bedrooms) < 8 else max(0, int(req.bedrooms) - 1)

    ref_bath = int(round(profile.get("bathrooms", _CONTEXT.get("overall_bath_median", max(req.bathrooms, 1)))))
    ref_bath = max(ref_bath, 1)
    if ref_bath == int(req.bathrooms):
        ref_bath = int(req.bathrooms) + 1 if int(req.bathrooms) < 8 else max(1, int(req.bathrooms) - 1)

    ref_ptype = _pick_reference_property_type(ptype)

    scenario_overrides = [
        ("Property Type", {"property_type": ref_ptype}),
        ("Size (sqm)", {"size_sqm": round(ref_size, 2)}),
        ("Bedrooms", {"bedrooms": ref_bed}),
        ("Bathrooms", {"bathrooms": ref_bath}),
    ]

    impacts = []
    for label, overrides in scenario_overrides:
        payload = req.dict()
        payload.update(overrides)
        test_req = PredictRequest(**payload)
        alt_price, _, _ = _predict_price_for_request(test_req)
        impacts.append((label, abs(base_price - alt_price)))

    total_impact = sum(v for _, v in impacts)
    if total_impact <= 0:
        return [
            {"feature": "Size (sqm)", "waitWeight": 35.0},
            {"feature": "Property Type", "waitWeight": 30.0},
            {"feature": "Bedrooms", "waitWeight": 20.0},
            {"feature": "Bathrooms", "waitWeight": 15.0},
        ]

    return [
        {
            "feature": label,
            "waitWeight": round((impact / total_impact) * 100.0, 1),
        }
        for label, impact in sorted(impacts, key=lambda x: x[1], reverse=True)
    ]


# ── request / response schemas ─────────────────────────────────────────────────
class PredictRequest(BaseModel):
    size_sqm:       float          = Field(..., gt=0, example=75.0)
    bedrooms:       int            = Field(..., ge=0, example=2)
    bathrooms:      int            = Field(..., ge=1, example=2)
    property_type:  str            = Field(..., example="Villa") # e.g. "Flat", "Villa", "Condo"
    furnishing:     Optional[str]  = Field("unfurnished", example="furnished")
    city:           Optional[str]  = Field("", example="Phnom Penh")
    district:       Optional[str]  = Field("", example="Khan Chroy Changvar")
    location:       Optional[str]  = Field("", example="Sangkat Chroy Changvar")


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
    size_sqm_sq = size_sqm ** 2
    bath_per_bed = bathrooms / bedrooms if bedrooms > 0 else bathrooms
    total_rooms = bedrooms + bathrooms
    safe_rooms = total_rooms if total_rooms > 0 else 1
    size_per_room = size_sqm / safe_rooms
    room_density = safe_rooms / max(size_sqm, 1.0)
    size_room_balance = math.log1p(max(size_per_room, 0.0))
    bedroom_share = bedrooms / safe_rooms
    bathroom_share = bathrooms / safe_rooms
    room_value_proxy = math.sqrt(max(size_sqm, 1.0)) * ((0.60 * bedrooms) + (0.55 * bathrooms) + 1.0)
    bed_bath_interaction = bedrooms * bathrooms
    
    # Furnished score (basic binary map for example purposes)
    furnished_score = 1 if str(req.furnishing).lower() in ["furnished", "fully furnished"] else 0
    
    district_key = _resolve_district_key(req.district, req.location, req.city)
    district_freq = _CONTEXT["district_freq_map"].get(district_key, 0.5)

    post_month = float(_CONTEXT.get("default_post_month", 6.0))
    post_dayofweek = float(_CONTEXT.get("default_post_dayofweek", 3.0))
    post_quarter = float(_CONTEXT.get("default_post_quarter", 2.0))
    
    # Missing value flags
    size_sqm_was_missing = 0
    bedrooms_was_missing = 0
    bathrooms_was_missing = 0

    # 3. Compile base dictionary
    row = {
        "size_sqm": size_sqm,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "size_sqm_sq": size_sqm_sq,
        "log_size_sqm": log_size_sqm,
        "bath_per_bed": bath_per_bed,
        "total_rooms": total_rooms,
        "size_per_room": size_per_room,
        "room_density": room_density,
        "size_room_balance": size_room_balance,
        "bedroom_share": bedroom_share,
        "bathroom_share": bathroom_share,
        "room_value_proxy": room_value_proxy,
        "bed_bath_interaction": bed_bath_interaction,
        "furnished_score": furnished_score,
        "district_freq": district_freq,
        "size_sqm_was_missing": size_sqm_was_missing,
        "bedrooms_was_missing": bedrooms_was_missing,
        "bathrooms_was_missing": bathrooms_was_missing,
        "post_month": post_month,
        "post_dayofweek": post_dayofweek,
        "post_quarter": post_quarter,
    }
    
    # 4. Generate dummy variables for property_type
    # Attempt to match the exact casing in feature names
    ptype = _normalize_property_type(req.property_type)
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
        district_key = _resolve_district_key(req.district, req.location, req.city)
        ptype = _normalize_property_type(req.property_type)

        X = _build_feature_vector(req)
        raw_price = float(_model.predict(X)[0])
        price, average_market_price, relation_coherence = _calibrate_price(raw_price, req, district_key, ptype)
        price = _enforce_room_monotonicity(req, price)

        # Request-specific impact profile so bars change with user input.
        fi_list = _build_dynamic_feature_impacts(req, price)

        # Create dynamic size correlation chart using model.predict
        sizes_to_test = [30, 50, 75, 100, 150]
        size_corr = []
        for s in sizes_to_test:
            test_req = PredictRequest(**req.dict())
            test_req.size_sqm = s
            p, _, _ = _predict_price_for_request(test_req)
            size_corr.append({"size": s, "price": round(p, 2)})

        # Simple ±10% confidence band
        low = price * 0.90
        high = price * 1.10

        if _CONTEXT["top_regions"]:
            loc_data = _CONTEXT["top_regions"][:4]
        else:
            loc_data = [
                {"location": "Sample A", "price": round(price * 1.10, 2)},
                {"location": "Sample B", "price": round(price * 1.00, 2)},
                {"location": "Sample C", "price": round(price * 0.90, 2)},
                {"location": "Sample D", "price": round(price * 0.80, 2)},
            ]

        return PredictResponse(
            predicted_price = round(price, 2),
            price_range_low = round(low,   2),
            price_range_high= round(high,  2),
            model_used      = _model_name,
            confidence_note = f"Estimated range ±10%. Relation coherence for this layout: {relation_coherence * 100:.0f}%.",
            feature_importances = fi_list,
            location_data = loc_data,
            size_correlation_data = size_corr,
            average_market_price = round(float(average_market_price), 2)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ── health check ──────────────────────────────────────────────────────────────
@router.get("/predict/health")
def health():
    return {"status": "ok", "model": _model_name, "features": _feature_names}


# ── stats ─────────────────────────────────────────────────────────────────────
_DATA_CSV = CLEANED_V4_CSV

def _load_df() -> pd.DataFrame:
    for candidate in (_DATA_CSV, RAW_DATA_CSV):
        if os.path.exists(candidate):
            return _read_csv_robust(candidate)
    raise FileNotFoundError("No stats CSV found for dashboard.")

@router.get("/stats")
def get_stats():
    try:
        df = _load_df()
        df = df[df["rent_price_usd"] > 0].dropna(subset=["rent_price_usd"])

        # 1. Price distribution (bucket counts)
        buckets = [0, 200, 400, 600, 800, 1000, 1500, 2000, 3000, 5000, 999999]
        labels  = ["<$200", "$200-400", "$400-600", "$600-800", "$800-1k",
                   "$1k-1.5k", "$1.5k-2k", "$2k-3k", "$3k-5k", ">$5k"]
        df["bucket"] = pd.cut(df["rent_price_usd"], bins=buckets, labels=labels, right=False)
        price_dist = (
            df["bucket"].value_counts().reindex(labels, fill_value=0)
            .reset_index().rename(columns={"bucket": "range", "count": "count"})
            .to_dict(orient="records")
        )

        # 2. Average price by district (top 8)
        by_district = (
            df.groupby("district")["rent_price_usd"]
            .mean().round(0).sort_values(ascending=False).head(8)
            .reset_index().rename(columns={"district": "location", "rent_price_usd": "avg_price"})
            .to_dict(orient="records")
        )

        # 3. Bedrooms vs average price
        by_bedrooms = (
            df[df["bedrooms"].notna() & (df["bedrooms"] <= 8)]
            .groupby("bedrooms")["rent_price_usd"]
            .mean().round(0).reset_index()
            .rename(columns={"bedrooms": "bedrooms", "rent_price_usd": "avg_price"})
            .sort_values("bedrooms")
            .to_dict(orient="records")
        )

        # 4. Average price by property type
        by_type = (
            df.groupby("property_type")["rent_price_usd"]
            .mean().round(0).sort_values(ascending=False)
            .reset_index().rename(columns={"property_type": "type", "rent_price_usd": "avg_price"})
            .to_dict(orient="records")
        )

        return {
            "price_distribution": price_dist,
            "avg_price_by_district": by_district,
            "avg_price_by_bedrooms": by_bedrooms,
            "avg_price_by_type": by_type,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
