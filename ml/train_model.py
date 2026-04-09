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
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge, ElasticNet
from sklearn.compose import TransformedTargetRegressor
from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                              r2_score, mean_absolute_percentage_error)
from sklearn.model_selection import cross_val_score, RandomizedSearchCV
warnings.filterwarnings("ignore")

from preprocess import run as prepare_data

MODEL_VERSION = "version_number"
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "models", MODEL_VERSION)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Model definitions ────────────────────────────────────────────────────────
BASE_MODELS = {
    "Linear Regression": LinearRegression(),

    "Ridge Regression": Ridge(alpha=3.0),

    "ElasticNet": ElasticNet(alpha=0.03, l1_ratio=0.2, random_state=42),

    "Random Forest": RandomForestRegressor(
        n_estimators=400,
        random_state=42,
        n_jobs=-1,
    ),

    "Extra Trees": ExtraTreesRegressor(
        n_estimators=500,
        random_state=42,
        n_jobs=-1,
    ),

    "SVM (SVR)": SVR(
        kernel="rbf",
        C=100,
        epsilon=0.08,
        gamma="scale",
    ),

    "Gradient Boosting": GradientBoostingRegressor(
        random_state=42,
    ),

    "HistGradientBoosting": HistGradientBoostingRegressor(
        random_state=42,
    ),
}


# Hyperparameter search spaces for models that usually benefit from tuning.
TUNE_SPACES = {
    "Random Forest": {
        "regressor__n_estimators": [300, 500, 700],
        "regressor__max_depth": [None, 10, 14, 18],
        "regressor__min_samples_split": [2, 4, 8],
        "regressor__min_samples_leaf": [1, 2, 4],
        "regressor__max_features": ["sqrt", "log2", 0.8],
    },
    "Extra Trees": {
        "regressor__n_estimators": [400, 600, 800],
        "regressor__max_depth": [None, 12, 18, 24],
        "regressor__min_samples_split": [2, 4, 8],
        "regressor__min_samples_leaf": [1, 2, 4],
        "regressor__max_features": ["sqrt", "log2", 0.8],
    },
    "Gradient Boosting": {
        "regressor__n_estimators": [300, 500, 700],
        "regressor__learning_rate": [0.03, 0.05, 0.08],
        "regressor__max_depth": [3, 4, 5],
        "regressor__subsample": [0.7, 0.85, 1.0],
        "regressor__min_samples_leaf": [1, 3, 5],
    },
    "HistGradientBoosting": {
        "regressor__learning_rate": [0.03, 0.05, 0.08],
        "regressor__max_depth": [None, 8, 12],
        "regressor__max_iter": [300, 500, 700],
        "regressor__max_leaf_nodes": [31, 63],
        "regressor__l2_regularization": [0.0, 0.1, 0.5],
    },
    "SVM (SVR)": {
        "regressor__C": [30, 60, 100, 150],
        "regressor__epsilon": [0.03, 0.05, 0.08, 0.12],
        "regressor__gamma": ["scale", "auto"],
    },
}


def _wrap_with_log_target(model):
    return TransformedTargetRegressor(
        regressor=model,
        func=np.log1p,
        inverse_func=np.expm1,
        check_inverse=False,
    )


def maybe_tune_model(name, model, X_train, y_train):
    wrapped = _wrap_with_log_target(model)
    if name not in TUNE_SPACES:
        return wrapped

    print(f"[tune] Running randomized search for {name}...")
    search = RandomizedSearchCV(
        estimator=wrapped,
        param_distributions=TUNE_SPACES[name],
        n_iter=12,
        cv=4,
        scoring="neg_root_mean_squared_error",
        n_jobs=-1,
        random_state=42,
        verbose=0,
    )
    search.fit(X_train, y_train)
    print(f"[tune] Best params for {name}: {search.best_params_}")
    return search.best_estimator_


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

    print(f"\n{'-' * 52}")
    print(f"  {name}")
    print(f"{'-' * 52}")
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
    base_model = getattr(model, "regressor_", model)
    if not hasattr(base_model, "feature_importances_"):
        return
    imp = base_model.feature_importances_
    pairs = sorted(zip(feature_names, imp), key=lambda x: x[1], reverse=True)
    print("\n[importance] Feature importances:")
    for feat, score in pairs:
        bar = "█" * int(score * 50)
        print(f"  {feat:<20} {score:.4f}  {bar}")


def run():
    print("=" * 60)
    print("  PROPERTY RENT PREDICTION — MODEL TRAINING")
    print("=" * 60)

    X_train, X_test, y_train, y_test, feature_names, encoders, scaler, imputer = prepare_data()

    results = []
    for name, base_model in BASE_MODELS.items():
        model = maybe_tune_model(name, base_model, X_train, y_train)
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
    # Force Random Forest to be the chosen best model
    best = next(r for r in results if r["name"] == "Random Forest")
    best_mdl = best["model"]
    print(f"\nBest model (forced): {best['name']}  (R² = {best['R2']:.4f})")

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

    print(f"\nSaved best model → {model_path}")
    print(f"All individual models saved in {OUTPUT_DIR}/")

    return best_mdl, feature_names, results


if __name__ == "__main__":
    run()
