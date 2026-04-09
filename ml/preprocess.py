"""Feature preparation for Khmer24 rent prediction."""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# ── Paths ───────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "data_cleaning" / "Khmer24_cleaned_v4.csv"
FALLBACK_DATA_PATHS = [
    ROOT_DIR / "data_cleaning" / "Khmer24_cleaned_auto.csv",
    ROOT_DIR / "data" / "Khmer24_features.csv",
    ROOT_DIR / "backend" / "data" / "Khmer24_features.csv",
]
MODEL_VERSION = "version_number"
OUTPUT_DIR = ROOT_DIR / "ml" / "models" / MODEL_VERSION
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Column config ────────────────────────────────────────────────────────────
TARGET_COL = "rent_price_usd"
DATE_COL = "posted_date"
LEAKAGE_COLS = ["log_rent", "price_per_sqm", "log_price_per_sqm"]

TYPE_FEATURES = [
    "type_Flat",
    "type_Flat House",
    "type_House",
    "type_Link Villa",
    "type_Room",
    "type_Shop",
    "type_Shophouse",
    "type_Single Villa",
    "type_Twin Villa",
    "type_Unclassified",
    "type_Villa",
]

BASE_NUMERIC = ["size_sqm", "bedrooms", "bathrooms"]

MODEL_FEATURES = [
    "size_sqm",
    "bedrooms",
    "bathrooms",
    "size_sqm_sq",
    "log_size_sqm",
    "bath_per_bed",
    "total_rooms",
    "size_per_room",
    "room_density",
    "size_room_balance",
    "bedroom_share",
    "bathroom_share",
    "room_value_proxy",
    "bed_bath_interaction",
    "furnished_score",
    "district_freq",
    *TYPE_FEATURES,
    "size_sqm_was_missing",
    "bedrooms_was_missing",
    "bathrooms_was_missing",
    "post_month",
    "post_dayofweek",
    "post_quarter",
]


def _read_csv_robust(path_obj: Path) -> pd.DataFrame:
    last_error = None
    for enc in ("utf-8", "utf-8-sig", "cp1252", "latin-1"):
        try:
            return pd.read_csv(path_obj, encoding=enc)
        except UnicodeDecodeError as err:
            last_error = err
        except pd.errors.ParserError:
            # Some scraped CSV rows are malformed (extra separators); skip bad lines.
            return pd.read_csv(path_obj, encoding=enc, engine="python", on_bad_lines="skip")
    raise last_error


def load_data(path: Path = DATA_PATH) -> pd.DataFrame:
    resolved = path if path.exists() else None
    if resolved is None:
        resolved = next((p for p in FALLBACK_DATA_PATHS if p.exists()), None)

    if resolved is None:
        all_paths = [str(path), *[str(p) for p in FALLBACK_DATA_PATHS]]
        raise FileNotFoundError(f"No data file found. Checked: {all_paths}")

    df = _read_csv_robust(resolved)
    print(f"[preprocess] Loaded file: {resolved}")
    print(f"[preprocess] Shape: {df.shape}")
    return df


def _normalize_property_type(series: pd.Series) -> pd.Series:
    mapped = (
        series.fillna("Unclassified")
        .astype(str)
        .str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.title()
    )

    # Normalize common variants so one-hot columns remain stable.
    alias_map = {
        "Apartment": "Flat",
        "Condo": "Flat",
        "Link House": "House",
        "Townhouse": "House",
        "Other": "Unclassified",
    }
    mapped = mapped.replace(alias_map)
    valid = {c.replace("type_", "") for c in TYPE_FEATURES}
    return mapped.where(mapped.isin(valid), "Unclassified")


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df = df.drop(columns=[c for c in LEAKAGE_COLS if c in df.columns], errors="ignore")

    if TARGET_COL not in df.columns:
        raise ValueError(f"Missing target column: {TARGET_COL}")

    # Ensure expected numeric columns exist.
    for col in BASE_NUMERIC:
        if col not in df.columns:
            df[col] = np.nan

    # Keep missing indicators from raw values before imputation.
    raw_missing = {col: df[col].isna() for col in BASE_NUMERIC}

    for col in BASE_NUMERIC:
        df[col] = _to_numeric(df[col])

    df[TARGET_COL] = (
        df[TARGET_COL]
        .astype(str)
        .str.replace(r"[\$,]|/month|permonth", "", regex=True)
        .str.strip()
    )
    df[TARGET_COL] = _to_numeric(df[TARGET_COL])

    df = df.dropna(subset=[TARGET_COL]).copy()
    df = df[(df[TARGET_COL] >= 50) & (df[TARGET_COL] <= 500000)].copy()

    ptype = _normalize_property_type(df.get("property_type", pd.Series("Unclassified", index=df.index)))

    # Median imputation by type with global fallback keeps signal while being robust.
    for col in BASE_NUMERIC:
        type_medians = df.groupby(ptype)[col].transform("median")
        global_median = df[col].median()
        df[col] = df[col].fillna(type_medians).fillna(global_median)

    # Sanity bounds.
    df["size_sqm"] = df["size_sqm"].clip(lower=8, upper=2000)
    df["bedrooms"] = df["bedrooms"].clip(lower=0, upper=20)
    df["bathrooms"] = df["bathrooms"].clip(lower=1, upper=20)

    # Core engineered features.
    total_rooms = (df["bedrooms"] + df["bathrooms"]).clip(lower=1)
    df["log_size_sqm"] = np.log1p(df["size_sqm"].clip(lower=0))
    df["size_sqm_sq"] = np.square(df["size_sqm"].clip(lower=0))
    df["bath_per_bed"] = np.where(df["bedrooms"] > 0, df["bathrooms"] / df["bedrooms"], df["bathrooms"])
    df["total_rooms"] = df["bedrooms"] + df["bathrooms"]
    df["size_per_room"] = df["size_sqm"] / total_rooms
    df["room_density"] = total_rooms / df["size_sqm"].clip(lower=1)
    df["size_room_balance"] = np.log1p(df["size_per_room"].clip(lower=0))
    df["bedroom_share"] = df["bedrooms"] / total_rooms
    df["bathroom_share"] = df["bathrooms"] / total_rooms
    # Sublinear size component keeps size important but lets room counts influence model more.
    df["room_value_proxy"] = np.sqrt(df["size_sqm"].clip(lower=1)) * ((0.60 * df["bedrooms"]) + (0.55 * df["bathrooms"]) + 1.0)
    df["bed_bath_interaction"] = df["bedrooms"] * df["bathrooms"]

    # Remove structurally implausible layouts that often come from noisy scraped rows
    # and can invert bedroom/bathroom price signal during training.
    plausible_layout_mask = df["size_per_room"] >= 8.0
    df = df[plausible_layout_mask].copy()

    # Auxiliary features used by the API builder.
    furnished = df.get("furnished", pd.Series("unknown", index=df.index)).astype(str).str.lower().str.strip()
    df["furnished_score"] = furnished.isin(["furnished", "fully furnished"]).astype(float)

    district = df.get("district", pd.Series("unknown", index=df.index)).astype(str).str.strip().str.lower()
    freq_map = district.value_counts(normalize=True)
    df["district_freq"] = district.map(freq_map).fillna(0.5)

    for col in BASE_NUMERIC:
        df[f"{col}_was_missing"] = raw_missing[col].reindex(df.index, fill_value=False).astype(float)

    # Stable one-hot columns for known property groups.
    dummies = pd.get_dummies(ptype, prefix="type")
    for col in TYPE_FEATURES:
        if col in dummies.columns:
            df[col] = dummies[col].astype(float)
        else:
            df[col] = pd.Series(0.0, index=df.index, dtype=float)

    # Date-derived features (filled with zeros if unavailable).
    if DATE_COL in df.columns:
        parsed = pd.to_datetime(df[DATE_COL], errors="coerce")
        df["post_month"] = parsed.dt.month.fillna(0).astype(float)
        df["post_dayofweek"] = parsed.dt.dayofweek.fillna(0).astype(float)
        df["post_quarter"] = parsed.dt.quarter.fillna(0).astype(float)
    else:
        df["post_month"] = 0.0
        df["post_dayofweek"] = 0.0
        df["post_quarter"] = 0.0

    # Robust outlier filtering in log-space to stabilize skewed rent distributions.
    log_target = np.log1p(df[TARGET_COL])
    q1 = log_target.quantile(0.25)
    q3 = log_target.quantile(0.75)
    iqr = q3 - q1
    target_mask = (log_target >= q1 - 1.5 * iqr) & (log_target <= q3 + 1.5 * iqr)

    # Remove unrealistic rent-per-size spikes that usually come from noisy listings.
    price_per_sqm = df[TARGET_COL] / df["size_sqm"].clip(lower=1)
    pps_low = price_per_sqm.quantile(0.01)
    pps_high = price_per_sqm.quantile(0.99)
    pps_mask = (price_per_sqm >= pps_low) & (price_per_sqm <= pps_high)

    before = len(df)
    df = df[target_mask & pps_mask].copy()

    df = df.replace([np.inf, -np.inf], np.nan)

    for col in MODEL_FEATURES:
        if col not in df.columns:
            df[col] = 0.0

    print(f"[preprocess] Rows after cleaning: {len(df):,} (removed {before - len(df):,} outliers)")
    return df


def encode_and_scale(df: pd.DataFrame):
    feature_cols = [c for c in MODEL_FEATURES if c in df.columns]
    X = df[feature_cols].astype(float).values
    y = df[TARGET_COL].astype(float).values

    # Stratify by rent bins when possible for more stable train/test splits.
    stratify_bins = None
    try:
        bins = pd.qcut(y, q=10, duplicates="drop")
        if len(pd.unique(bins)) > 1:
            stratify_bins = bins
    except ValueError:
        stratify_bins = None

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=stratify_bins,
    )

    imputer = SimpleImputer(strategy="median")
    X_train = imputer.fit_transform(X_train)
    X_test = imputer.transform(X_test)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    encoders = {}
    with open(OUTPUT_DIR / "encoders.pkl", "wb") as f:
        pickle.dump(encoders, f)
    with open(OUTPUT_DIR / "scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)
    with open(OUTPUT_DIR / "imputer.pkl", "wb") as f:
        pickle.dump(imputer, f)
    with open(OUTPUT_DIR / "feature_names.pkl", "wb") as f:
        pickle.dump(feature_cols, f)

    print(f"[preprocess] Feature count: {len(feature_cols)}")
    print(f"[preprocess] Features: {feature_cols}")
    print(f"[preprocess] Train: {X_train.shape} | Test: {X_test.shape}")
    return X_train, X_test, y_train, y_test, feature_cols, encoders, scaler, imputer


def run():
    df = load_data()
    df = clean_data(df)
    return encode_and_scale(df)


if __name__ == "__main__":
    run()

