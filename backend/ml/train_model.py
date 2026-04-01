"""
train_model.py
--------------
Train & compare regression models for property RENT price prediction.
Features: city, district, location, property_type (all categorical, label-encoded)
          + date-derived: post_month, post_dayofweek, post_quarter
Target:   rent_price_usd

Run:
  cd backend/ml
  python train_model.py
"""

import pickle, os, time, warnings
import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                              r2_score, mean_absolute_percentage_error)
from sklearn.model_selection import cross_val_score
warnings.filterwarnings("ignore")

from preprocess import run as prepare_data

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Model definitions ────────────────────────────────────────────────────────
# Note: with only categorical features, tree-based models (RF, GBM) tend to
# outperform linear models and SVR significantly.
MODELS = {
    "Linear Regression": LinearRegression(),

    "Ridge Regression": Ridge(alpha=10.0),

    "Random Forest": RandomForestRegressor(
        n_estimators=300,
        max_depth=12,
        min_samples_split=4,
        min_samples_leaf=2,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    ),

    "SVM (SVR)": SVR(
        kernel="rbf",
        C=200,
        epsilon=0.1,
        gamma="scale",
    ),

    "Gradient Boosting": GradientBoostingRegressor(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=5,
        subsample=0.8,
        min_samples_leaf=3,
        random_state=42,
    ),
}


def evaluate(name, model, X_train, X_test, y_train, y_test) -> dict:
    t0 = time.time()
    model.fit(X_train, y_train)
    elapsed = time.time() - t0

    y_pred = model.predict(X_test)

    mae  = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2   = r2_score(y_test, y_pred)
    mape = mean_absolute_percentage_error(y_test, y_pred) * 100

    cv = cross_val_score(model, X_train, y_train, cv=5, scoring="r2", n_jobs=-1)

    print(f"\n{'─' * 52}")
    print(f"  {name}")
    print(f"{'─' * 52}")
    print(f"  MAE    : ${mae:>10,.2f}")
    print(f"  RMSE   : ${rmse:>10,.2f}")
    print(f"  MAPE   :  {mape:>9.2f}%")
    print(f"  R²     :  {r2:>10.4f}")
    print(f"  CV R²  :  {cv.mean():.4f} ± {cv.std():.4f}")
    print(f"  Time   :  {elapsed:.1f}s")

    return {
        "name":       name,
        "model":      model,
        "MAE":        mae,
        "RMSE":       rmse,
        "MAPE":       mape,
        "R2":         r2,
        "CV_R2_mean": cv.mean(),
        "CV_R2_std":  cv.std(),
        "y_pred":     y_pred,
    }


def feature_importance(model, feature_names):
    if not hasattr(model, "feature_importances_"):
        return
    imp   = model.feature_importances_
    pairs = sorted(zip(feature_names, imp), key=lambda x: x[1], reverse=True)
    print("\n[importance] Feature importances:")
    for feat, score in pairs:
        bar = "█" * int(score * 50)
        print(f"  {feat:<20} {score:.4f}  {bar}")


def run():
    print("=" * 60)
    print("  PROPERTY RENT PREDICTION — MODEL TRAINING")
    print("=" * 60)

    X_train, X_test, y_train, y_test, feature_names, encoders, scaler = prepare_data()

    results = []
    for name, model in MODELS.items():
        res = evaluate(name, model, X_train, X_test, y_train, y_test)
        results.append(res)

    # ── Summary table ────────────────────────────────────────────────────────
    df_res = (pd.DataFrame(results)
              .set_index("name")
              .drop(columns=["model", "y_pred"])
              .sort_values("R2", ascending=False))

    print(f"\n\n{'=' * 60}")
    print("  SUMMARY  (sorted by R²)")
    print(f"{'=' * 60}")
    print(df_res.round(4).to_string())

    # ── Pick best ────────────────────────────────────────────────────────────
    best     = max(results, key=lambda r: r["R2"])
    best_mdl = best["model"]
    print(f"\nBest model : {best['name']}  (R² = {best['R2']:.4f})")

    feature_importance(best_mdl, feature_names)

    # ── Warn if R² is low ────────────────────────────────────────────────────
    if best["R2"] < 0.5:
        print("\n R² is below 0.5 — this is expected when training on")
        print("   categorical-only features. Consider adding numeric columns")
        print("   such as bedrooms, floor_area_sqm, or bathrooms to your CSV")
        print("   to significantly improve prediction accuracy.")

    # ── Save all models ──────────────────────────────────────────────────────
    model_path = os.path.join(OUTPUT_DIR, "best_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"model": best_mdl, "model_name": best["name"]}, f)

    for res in results:
        safe = (res["name"].lower()
                .replace(" ", "_")
                .replace("(", "").replace(")", ""))
        with open(os.path.join(OUTPUT_DIR, f"{safe}.pkl"), "wb") as f:
            pickle.dump(res["model"], f)

    print(f"\n💾 Saved best model → {model_path}")
    print(f"💾 All individual models saved in {OUTPUT_DIR}/")

    return best_mdl, feature_names, results


if __name__ == "__main__":
    run()
