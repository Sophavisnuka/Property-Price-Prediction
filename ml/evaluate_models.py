"""
evaluate_models.py
------------------
Run this AFTER train_model.py.
Generates a visual comparison of all trained models and saves:
  ml/models/model_comparison.png

Usage:
  cd backend/ml
  python evaluate_models.py
"""

import pickle, os, warnings
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from sklearn.metrics import (mean_absolute_error, mean_squared_error,
                              r2_score, mean_absolute_percentage_error)
from sklearn.model_selection import cross_val_score
warnings.filterwarnings("ignore")

# ── Reuse the same preprocess pipeline ─────────────────────────────────────────
from preprocess import run as prepare_data

MODEL_VERSION = "version_number"
MODEL_DIR  = os.path.join(os.path.dirname(__file__), "models", MODEL_VERSION)
OUTPUT_PNG = os.path.join(MODEL_DIR, "model_comparison.png")

MODEL_FILES = {
    "Linear\nRegression": "linear_regression.pkl",
    "Ridge\nRegression":  "ridge_regression.pkl",
    "Elastic\nNet":       "elasticnet.pkl",
    "SVM\n(SVR)":         "svm_svr.pkl",
    "Random\nForest":     "random_forest.pkl",
    "Extra\nTrees":       "extra_trees.pkl",
    "Gradient\nBoosting": "gradient_boosting.pkl",
    "Hist\nGradBoost":    "histgradientboosting.pkl",
}

# ── Color palette ───────────────────────────────────────────────────────────────
BG        = "#0b0802"
CARD      = "#0f0a04"
GOLD      = "#c8963e"
GOLD_PALE = "#9a6d28"
TEXT      = "#e8d5a3"
MUTED     = "#5a4a2e"
BORDER    = "#2a1f10"

COLORS = [
    "#4e8fd4", "#c8963e", "#5cb87a", "#c85e5e",
    "#8f67d9", "#4db0b0", "#d47a4e", "#7b9f35",
]


def load_model(filename):
    path = os.path.join(MODEL_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "rb") as f:
        return pickle.load(f)


def compute_metrics(model, X_train, X_test, y_train, y_test):
    model.fit(X_train, y_train)
    y_pred  = model.predict(X_test)
    mae     = mean_absolute_error(y_test, y_pred)
    rmse    = np.sqrt(mean_squared_error(y_test, y_pred))
    r2      = r2_score(y_test, y_pred)
    mape    = mean_absolute_percentage_error(y_test, y_pred) * 100
    cv      = cross_val_score(model, X_train, y_train, cv=5, scoring="r2", n_jobs=-1)
    return {
        "R²":        round(r2, 4),
        "CV R²":     round(cv.mean(), 4),
        "MAE":       round(mae, 2),
        "RMSE":      round(rmse, 2),
        "MAPE (%)":  round(mape, 2),
        "y_pred":    y_pred,
    }


def style_ax(ax, title="", xlabel="", ylabel=""):
    ax.set_facecolor(CARD)
    ax.tick_params(colors=TEXT, labelsize=9)
    ax.spines[:].set_color(BORDER)
    ax.spines[:].set_linewidth(0.6)
    if title:
        ax.set_title(title, color=GOLD, fontsize=11, fontweight="bold",
                     pad=10, fontfamily="monospace")
    if xlabel: ax.set_xlabel(xlabel, color=MUTED, fontsize=9)
    if ylabel: ax.set_ylabel(ylabel, color=MUTED, fontsize=9)
    ax.grid(axis="y", color=BORDER, linewidth=0.5, linestyle="--", alpha=0.6)
    ax.set_axisbelow(True)


def run():
    print("Loading data and training models for evaluation…")
    X_train, X_test, y_train, y_test, feature_names, encoders, scaler, imputer = prepare_data()

    # Collect metrics for each model
    names, metrics_list = [], []
    for label, fname in MODEL_FILES.items():
        model = load_model(fname)
        if model is None:
            print(f"  ⚠ Skipping {label.replace(chr(10),' ')} — .pkl not found. Run train_model.py first.")
            continue
        print(f"  Evaluating {label.replace(chr(10),' ')}…")
        m = compute_metrics(model, X_train, X_test, y_train, y_test)
        names.append(label)
        metrics_list.append(m)

    if not names:
        print("No models found. Run train_model.py first.")
        return

    n      = len(names)
    x      = np.arange(n)
    colors = COLORS[:n]

    # ── Canvas ──────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(16, 11), facecolor=BG)
    fig.suptitle("Model Comparison — Property Price Prediction",
                 color=GOLD, fontsize=16, fontweight="bold",
                 fontfamily="monospace", y=0.97)

    gs = GridSpec(2, 3, figure=fig, hspace=0.52, wspace=0.38,
                  left=0.06, right=0.97, top=0.91, bottom=0.07)

    # ── 1. R² bar chart ─────────────────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 0])
    r2_vals  = [m["R²"]    for m in metrics_list]
    cv_vals  = [m["CV R²"] for m in metrics_list]
    bars = ax1.bar(x - 0.2, r2_vals, 0.35, color=colors, alpha=0.9, label="Test R²")
    ax1.bar(x + 0.2, cv_vals, 0.35, color=colors, alpha=0.45, label="CV R²")
    ax1.set_xticks(x); ax1.set_xticklabels(names, fontsize=8)
    ax1.set_ylim(0, 1.05)
    ax1.axhline(1.0, color=BORDER, linewidth=0.5, linestyle=":")
    style_ax(ax1, title="R² Score  (higher = better)", ylabel="R²")
    for bar, val in zip(bars, r2_vals):
        ax1.text(bar.get_x() + bar.get_width()/2, val + 0.01,
                 f"{val:.3f}", ha="center", va="bottom",
                 color=TEXT, fontsize=8, fontfamily="monospace")
    ax1.legend(fontsize=7, facecolor=CARD, edgecolor=BORDER,
               labelcolor=TEXT, loc="lower right")

    # ── 2. MAE bar chart ─────────────────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 1])
    mae_vals = [m["MAE"] for m in metrics_list]
    bars2 = ax2.bar(x, mae_vals, 0.5, color=colors, alpha=0.9)
    ax2.set_xticks(x); ax2.set_xticklabels(names, fontsize=8)
    style_ax(ax2, title="MAE  (lower = better)", ylabel="Mean Absolute Error ($)")
    for bar, val in zip(bars2, mae_vals):
        ax2.text(bar.get_x() + bar.get_width()/2, val * 1.01,
                 f"${val:,.0f}", ha="center", va="bottom",
                 color=TEXT, fontsize=8, fontfamily="monospace")

    # ── 3. RMSE bar chart ────────────────────────────────────────────────────────
    ax3 = fig.add_subplot(gs[0, 2])
    rmse_vals = [m["RMSE"] for m in metrics_list]
    bars3 = ax3.bar(x, rmse_vals, 0.5, color=colors, alpha=0.9)
    ax3.set_xticks(x); ax3.set_xticklabels(names, fontsize=8)
    style_ax(ax3, title="RMSE  (lower = better)", ylabel="Root Mean Squared Error ($)")
    for bar, val in zip(bars3, rmse_vals):
        ax3.text(bar.get_x() + bar.get_width()/2, val * 1.01,
                 f"${val:,.0f}", ha="center", va="bottom",
                 color=TEXT, fontsize=8, fontfamily="monospace")

    # ── 4. Actual vs Predicted scatter (best model) ──────────────────────────────
    best_idx   = int(np.argmax(r2_vals))
    best_name  = names[best_idx].replace("\n", " ")
    best_pred  = metrics_list[best_idx]["y_pred"]
    best_color = colors[best_idx]

    ax4 = fig.add_subplot(gs[1, 0:2])
    ax4.scatter(y_test, best_pred, color=best_color, alpha=0.55, s=22, edgecolors="none")
    lims = [min(y_test.min(), best_pred.min()), max(y_test.max(), best_pred.max())]
    ax4.plot(lims, lims, color=GOLD, linewidth=1.2, linestyle="--", alpha=0.7, label="Perfect fit")
    style_ax(ax4,
             title=f"Actual vs Predicted — {best_name}  ★ Best Model",
             xlabel="Actual Price ($)",
             ylabel="Predicted Price ($)")
    ax4.set_xlim(lims); ax4.set_ylim(lims)
    ax4.legend(fontsize=8, facecolor=CARD, edgecolor=BORDER, labelcolor=TEXT)
    ax4.grid(axis="both", color=BORDER, linewidth=0.5, linestyle="--", alpha=0.6)

    # Annotate R² on scatter
    ax4.text(0.04, 0.93, f"R² = {r2_vals[best_idx]:.4f}",
             transform=ax4.transAxes, color=GOLD,
             fontsize=10, fontfamily="monospace",
             bbox=dict(boxstyle="round,pad=0.4", facecolor=CARD, edgecolor=BORDER))

    # ── 5. MAPE comparison ───────────────────────────────────────────────────────
    ax5 = fig.add_subplot(gs[1, 2])
    mape_vals = [m["MAPE (%)"] for m in metrics_list]
    bars5 = ax5.barh(x, mape_vals, 0.5, color=colors, alpha=0.9)
    ax5.set_yticks(x); ax5.set_yticklabels(names, fontsize=8)
    ax5.invert_yaxis()
    ax5.set_facecolor(CARD)
    ax5.tick_params(colors=TEXT, labelsize=9)
    ax5.spines[:].set_color(BORDER); ax5.spines[:].set_linewidth(0.6)
    ax5.set_title("MAPE %  (lower = better)", color=GOLD,
                  fontsize=11, fontweight="bold", pad=10, fontfamily="monospace")
    ax5.set_xlabel("Mean Absolute Percentage Error (%)", color=MUTED, fontsize=9)
    ax5.grid(axis="x", color=BORDER, linewidth=0.5, linestyle="--", alpha=0.6)
    ax5.set_axisbelow(True)
    for bar, val in zip(bars5, mape_vals):
        ax5.text(val + 0.1, bar.get_y() + bar.get_height()/2,
                 f"{val:.2f}%", va="center", color=TEXT,
                 fontsize=8, fontfamily="monospace")

    # ── Legend strip at bottom ───────────────────────────────────────────────────
    patches = [mpatches.Patch(color=colors[i], label=names[i].replace("\n", " "))
               for i in range(n)]
    fig.legend(handles=patches, loc="lower center", ncol=n,
               facecolor=CARD, edgecolor=BORDER, labelcolor=TEXT,
               fontsize=9, framealpha=0.9,
               bbox_to_anchor=(0.5, 0.0))

    os.makedirs(MODEL_DIR, exist_ok=True)
    plt.savefig(OUTPUT_PNG, dpi=150, bbox_inches="tight", facecolor=BG)
    plt.close()
    print(f"\n✅ Chart saved → {OUTPUT_PNG}")
    print(f"   Best model  : {best_name}  (R² = {r2_vals[best_idx]:.4f})")


if __name__ == "__main__":
    run()
