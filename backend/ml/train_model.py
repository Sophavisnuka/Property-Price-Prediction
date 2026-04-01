"""
train_model.py
--------------
Train & compare multiple regression models for property price prediction.
Saves the best model as models/best_model.pkl.

Algorithms tested:
    - SVM (SVR)
    - Random Forest
    - Gradient Boosting (bonus)
    - Linear Regression (baseline)
"""

import pickle, os, time
import numpy as np
import pandas as pd
from sklearn.svm import SVR
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import (mean_absolute_error, mean_squared_error, r2_score, mean_absolute_percentage_error)
from sklearn.model_selection import GridSearchCV, cross_val_score

from preprocess import run as prepare_data   # reuse preprocess pipeline

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── model definitions ──────────────────────────────────────────────────────────
MODELS = {
    "Linear Regression": LinearRegression(),

    "Random Forest": RandomForestRegressor(
        n_estimators=200,
        max_depth=None,
        min_samples_split=5,
        min_samples_leaf=2,
        max_features="sqrt",
        random_state=42,
        n_jobs=-1,
    ),

    "SVM (SVR)": SVR(
        kernel="rbf",
        C=100,
        epsilon=0.1,
        gamma="scale",
    ),

    "Gradient Boosting": GradientBoostingRegressor(
        n_estimators=300,
        learning_rate=0.05,
        max_depth=4,
        subsample=0.8,
        random_state=42,
    ),
}

# ── optional: hyperparameter grids for GridSearchCV ───────────────────────────
# Set TUNE = True to run a grid search on SVM & RF (takes longer)
TUNE = False

PARAM_GRIDS = {
    "SVM (SVR)": {
        "C":       [10, 100, 500],
        "epsilon": [0.05, 0.1, 0.5],
        "kernel":  ["rbf", "poly"],
    },
    "Random Forest": {
        "n_estimators": [100, 200, 300],
        "max_depth":    [None, 10, 20],
        "max_features": ["sqrt", "log2"],
    },
}


def evaluate(name: str, model, X_train, X_test, y_train, y_test) -> dict:
    """Fit, evaluate, and return a metrics dict."""
    t0 = time.time()
    model.fit(X_train, y_train)
    train_time = time.time() - t0

    y_pred = model.predict(X_test)

    mae   = mean_absolute_error(y_test, y_pred)
    rmse  = np.sqrt(mean_squared_error(y_test, y_pred))
    r2    = r2_score(y_test, y_pred)
    mape  = mean_absolute_percentage_error(y_test, y_pred) * 100

    # 5-fold CV on full training data (R²)
    cv_scores = cross_val_score(model, X_train, y_train, cv=5, scoring="r2", n_jobs=-1)

    print(f"\n{'─'*50}")
    print(f"  {name}")
    print(f"{'─'*50}")
    print(f"  MAE   : {mae:>12,.2f}")
    print(f"  RMSE  : {rmse:>12,.2f}")
    print(f"  MAPE  : {mape:>11.2f}%")
    print(f"  R²    : {r2:>12.4f}")
    print(f"  CV R² : {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
    print(f"  Time  : {train_time:.2f}s")

    return {
        "name": name, "model": model,
        "MAE": mae, "RMSE": rmse, "MAPE": mape,
        "R2": r2, "CV_R2_mean": cv_scores.mean(),
    }


def tune_model(name, model, param_grid, X_train, y_train):
    """Run GridSearchCV and return the best estimator."""
    print(f"\n[tune] GridSearchCV → {name}")
    gs = GridSearchCV(model, param_grid, cv=5, scoring="r2", n_jobs=-1, verbose=1)
    gs.fit(X_train, y_train)
    print(f"[tune] Best params : {gs.best_params_}")
    print(f"[tune] Best CV R²  : {gs.best_score_:.4f}")
    return gs.best_estimator_


def feature_importance(model, feature_names: list[str], top_n: int = 10):
    """Print feature importances for tree-based models."""
    if hasattr(model, "feature_importances_"):
        imp = model.feature_importances_
        pairs = sorted(zip(feature_names, imp), key=lambda x: x[1], reverse=True)
        print(f"\n[importance] Top {top_n} features:")
        for feat, score in pairs[:top_n]:
            bar = "█" * int(score * 60)
            print(f"  {feat:<25} {score:.4f}  {bar}")


def run():
    print("=" * 60)
    print("  PROPERTY PRICE PREDICTION — MODEL TRAINING")
    print("=" * 60)

    # 1. Prepare data
    X_train, X_test, y_train, y_test, feature_names, encoders, scaler = prepare_data()

    # 2. (Optional) tune SVM and RF before benchmarking
    if TUNE:
        for name, param_grid in PARAM_GRIDS.items():
            MODELS[name] = tune_model(name, MODELS[name], param_grid,
                                      X_train, y_train)

    # 3. Train & evaluate all models
    results = []
    for name, model in MODELS.items():
        res = evaluate(name, model, X_train, X_test, y_train, y_test)
        results.append(res)

    # 4. Summary table
    df_res = pd.DataFrame(results).set_index("name").drop(columns="model")
    df_res = df_res.sort_values("R2", ascending=False)
    print(f"\n\n{'='*60}")
    print("  COMPARISON SUMMARY (sorted by R²)")
    print(f"{'='*60}")
    print(df_res.round(4).to_string())

    # 5. Pick best model (highest R²)
    best = max(results, key=lambda r: r["R2"])
    best_model = best["model"]
    print(f"\n✅ Best model: {best['name']}  (R² = {best['R2']:.4f})")

    # 6. Feature importance
    feature_importance(best_model, feature_names)

    # 7. Save best model
    model_path = os.path.join(OUTPUT_DIR, "best_model.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({"model": best_model, "model_name": best["name"]}, f)
    print(f"\n💾 Saved best model → {model_path}")

    # Also save individual models in case you want to compare later
    for res in results:
        safe_name = res["name"].lower().replace(" ", "_").replace("(","").replace(")","")
        path = os.path.join(OUTPUT_DIR, f"{safe_name}.pkl")
        with open(path, "wb") as f:
            pickle.dump(res["model"], f)

    return best_model, feature_names


if __name__ == "__main__":
    run()
