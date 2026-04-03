"""
preprocess.py
-------------
Matches CSV columns:
  listing_id, city, district, location, property_type,
  rent_price_usd, posted_date, title, source_url
"""

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os

# ── Paths ───────────────────────────────────────────────────────────────────
DATA_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "Khmer24_features.csv")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Column config (edit here if your CSV changes) ───────────────────────────
CATEGORICAL_COLS = [] # Already encoded/dummy in CSV
NUMERICAL_COLS   = [
    "size_sqm", "bedrooms", "bathrooms", "log_size_sqm", 
    "bath_per_bed", "total_rooms", "furnished_score", "district_freq",
    "type_Flat", "type_Flat House", "type_House", "type_Link Villa", 
    "type_Room", "type_Shop", "type_Shophouse", "type_Single Villa", 
    "type_Twin Villa", "type_Unclassified", "type_Villa",
    "size_sqm_was_missing", "bedrooms_was_missing", "bathrooms_was_missing"
]
TARGET_COL       = "rent_price_usd"
DROP_COLS        = ["log_rent", "price_per_sqm", "log_price_per_sqm"]   # Data leakage columns
DATE_COL         = "posted_date"


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    # NEW — tries UTF-8 first, falls back to Windows encoding
    try:
        df = pd.read_csv(path, encoding="utf-8")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1")
    print(f"[preprocess] Loaded {len(df):,} rows, {len(df.columns)} columns")
    print(f"[preprocess] Columns: {list(df.columns)}")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:

    # 1. Drop columns not useful for training
    df = df.drop(columns=[c for c in DROP_COLS if c in df.columns], errors="ignore")

    # 2. Drop rows where target is missing or zero
    before = len(df)
    df = df.dropna(subset=[TARGET_COL])
    df = df[df[TARGET_COL] > 0]
    print(f"[preprocess] Dropped {before - len(df)} rows with missing/zero price")

    # 3. Remove price outliers using IQR (more robust than z-score for skewed data)
    Q1  = df[TARGET_COL].quantile(0.05)
    Q3  = df[TARGET_COL].quantile(0.95)
    IQR = Q3 - Q1
    before = len(df)
    df  = df[(df[TARGET_COL] >= Q1 - 1.5 * IQR) & (df[TARGET_COL] <= Q3 + 1.5 * IQR)]
    print(f"[preprocess] Removed {before - len(df)} price outliers | "
          f"range: ${df[TARGET_COL].min():,.0f} – ${df[TARGET_COL].max():,.0f}")

    # 4. Clean & normalise categoricals
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = (df[col]
                       .fillna("unknown")
                       .astype(str)
                       .str.strip()
                       .str.lower())

    # 5. Extract date features from posted_date
    if DATE_COL in df.columns:
        df[DATE_COL] = pd.to_datetime(df[DATE_COL], errors="coerce")
        df["post_month"]     = df[DATE_COL].dt.month.fillna(0).astype(int)
        df["post_dayofweek"] = df[DATE_COL].dt.dayofweek.fillna(0).astype(int)
        df["post_quarter"]   = df[DATE_COL].dt.quarter.fillna(0).astype(int)
        df = df.drop(columns=[DATE_COL])
        print("[preprocess] Extracted date features: post_month, post_dayofweek, post_quarter")

    return df


def encode_and_scale(df: pd.DataFrame):
    """
    Returns:
        X_train, X_test, y_train, y_test  — numpy arrays
        feature_names                      — list[str]
        encoders                           — dict[str, LabelEncoder]
        scaler                             — StandardScaler
    """
    encoders: dict = {}

    # Label-encode each categorical column
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            encoders[col] = le
            print(f"[preprocess] '{col}' → {len(le.classes_)} unique categories")

    # Date-derived numerics (already integers, no encoder needed)
    date_features = [c for c in ["post_month", "post_dayofweek", "post_quarter"]
                     if c in df.columns]

    # Final feature list = encoded categoricals + date features + numerical features
    feature_cols = [c for c in CATEGORICAL_COLS if c in df.columns] + date_features + [c for c in NUMERICAL_COLS if c in df.columns]
    X = df[feature_cols].values.astype(float)
    y = df[TARGET_COL].values.astype(float)

    # Impute NaNs in the inputs just in case
    from sklearn.impute import SimpleImputer
    imputer = SimpleImputer(strategy='median')
    X = imputer.fit_transform(X)

    print(f"[preprocess] Feature columns: {feature_cols}")
    print(f"[preprocess] Target: {TARGET_COL}  |  "
          f"mean=${y.mean():,.0f}  median=${np.median(y):,.0f}")

    # Train / test split — 80/20
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scale (important even for encoded categoricals with high cardinality)
    scaler  = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    # Persist artifacts for predict.py
    with open(os.path.join(OUTPUT_DIR, "encoders.pkl"),      "wb") as f: pickle.dump(encoders, f)
    with open(os.path.join(OUTPUT_DIR, "scaler.pkl"),        "wb") as f: pickle.dump(scaler, f)
    with open(os.path.join(OUTPUT_DIR, "imputer.pkl"),       "wb") as f: pickle.dump(imputer, f)
    with open(os.path.join(OUTPUT_DIR, "feature_names.pkl"), "wb") as f: pickle.dump(feature_cols, f)

    print(f"[preprocess] Train: {X_train.shape}  |  Test: {X_test.shape}")
    return X_train, X_test, y_train, y_test, feature_cols, encoders, scaler, imputer


def run():
    df = load_data()
    df = clean_data(df)
    return encode_and_scale(df)


if __name__ == "__main__":
    run()
