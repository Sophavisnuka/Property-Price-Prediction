import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
import pickle
import os

# ── paths ──────────────────────────────────────────────────────────────────────
DATA_PATH   = os.path.join(os.path.dirname(__file__), "..", "data", "properties.csv")
OUTPUT_DIR  = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── columns you expect in your CSV ────────────────────────────────────────────
# Adjust these to match your actual column names
CATEGORICAL_COLS = ["location", "property_type", "furnishing"]
NUMERICAL_COLS   = ["bedrooms", "bathrooms", "floor_area_sqm", "floor_level",
                    "year_built", "parking_spaces"]
TARGET_COL       = "price"


def load_data(path: str = DATA_PATH) -> pd.DataFrame:
    df = pd.read_csv(path)
    print(f"[preprocess] Loaded {len(df):,} rows, {len(df.columns)} columns")
    return df


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning — extend this as you finish your data cleaning."""

    # 1. Drop duplicates
    before = len(df)
    df = df.drop_duplicates()
    print(f"[preprocess] Dropped {before - len(df)} duplicates")

    # 2. Drop rows where target is missing
    df = df.dropna(subset=[TARGET_COL])

    # 3. Remove obvious outliers (price = 0 or extreme z-score)
    z = np.abs((df[TARGET_COL] - df[TARGET_COL].mean()) / df[TARGET_COL].std())
    df = df[z < 3.5]
    print(f"[preprocess] After outlier removal: {len(df):,} rows")

    # 4. Fill missing numerics with median
    for col in NUMERICAL_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].median())

    # 5. Fill missing categoricals with mode
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].mode()[0])
            df[col] = df[col].astype(str).str.strip().str.lower()

    return df


def encode_and_scale(df: pd.DataFrame):
    """
    Returns:
        X_train, X_test, y_train, y_test  (numpy arrays)
        feature_names                       (list[str])
        encoders                            (dict of LabelEncoders)
        scaler                              (StandardScaler)
    """
    encoders: dict = {}

    # Encode categoricals
    for col in CATEGORICAL_COLS:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col])
            encoders[col] = le

    # Build feature matrix
    feature_cols = [c for c in CATEGORICAL_COLS + NUMERICAL_COLS if c in df.columns]
    X = df[feature_cols].values
    y = df[TARGET_COL].values

    feature_names = feature_cols

    # Train/test split (80/20, stratified split not needed for regression)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Scale features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test  = scaler.transform(X_test)

    # Persist encoders + scaler so predict.py can reuse them
    with open(os.path.join(OUTPUT_DIR, "encoders.pkl"), "wb") as f:
        pickle.dump(encoders, f)
    with open(os.path.join(OUTPUT_DIR, "scaler.pkl"), "wb") as f:
        pickle.dump(scaler, f)
    with open(os.path.join(OUTPUT_DIR, "feature_names.pkl"), "wb") as f:
        pickle.dump(feature_names, f)

    print(f"[preprocess] Features: {feature_names}")
    print(f"[preprocess] Train: {X_train.shape}  Test: {X_test.shape}")

    return X_train, X_test, y_train, y_test, feature_names, encoders, scaler


def run():
    df = load_data()
    df = clean_data(df)
    return encode_and_scale(df)


if __name__ == "__main__":
    run()
