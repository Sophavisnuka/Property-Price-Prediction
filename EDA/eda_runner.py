import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from scipy import stats


sns.set_theme(style="whitegrid", palette="Set2")


def _round_df(df: pd.DataFrame, decimals: int = 2) -> pd.DataFrame:
    out = df.copy()
    numeric_cols = out.select_dtypes(include=[np.number]).columns
    out[numeric_cols] = out[numeric_cols].round(decimals)
    return out


def _annotate_bars(ax, fmt="{:.0f}", rotation=0):
    for patch in ax.patches:
        height = patch.get_height()
        if np.isnan(height):
            continue
        ax.annotate(
            fmt.format(height),
            (patch.get_x() + patch.get_width() / 2.0, height),
            ha="center",
            va="bottom",
            fontsize=9,
            rotation=rotation,
            xytext=(0, 4),
            textcoords="offset points",
        )


def load_and_prepare_data(input_path: Path) -> pd.DataFrame:
    df = pd.read_csv(input_path)

    required_cols = [
        "listing_id",
        "city",
        "district",
        "location",
        "property_type",
        "rent_price_usd",
        "size_sqm",
        "bedrooms",
        "bathrooms",
    ]
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    df = df.copy()
    df["rent_price_usd"] = pd.to_numeric(df["rent_price_usd"], errors="coerce")
    df["size_sqm"] = pd.to_numeric(df["size_sqm"], errors="coerce")
    df["bedrooms"] = pd.to_numeric(df["bedrooms"], errors="coerce")
    df["bathrooms"] = pd.to_numeric(df["bathrooms"], errors="coerce")

    df = df.dropna(subset=["rent_price_usd", "size_sqm", "bedrooms", "bathrooms", "property_type"])
    df = df[df["size_sqm"] > 0].copy()

    df["log_rent"] = np.log1p(df["rent_price_usd"])
    df["price_per_sqm"] = df["rent_price_usd"] / df["size_sqm"]
    df["room_ratio"] = np.where(df["bedrooms"] > 0, df["bathrooms"] / df["bedrooms"], np.nan)
    df["total_rooms"] = df["bedrooms"] + df["bathrooms"]
    df = df.replace([np.inf, -np.inf], np.nan).dropna(subset=["price_per_sqm", "room_ratio"])

    return df


def phase_1_univariate(df: pd.DataFrame, chart_dir: Path):
    print("\n" + "=" * 80)
    print("PHASE 1 — UNIVARIATE ANALYSIS")
    print("=" * 80)

    rent_stats = {
        "mean": df["rent_price_usd"].mean(),
        "median": df["rent_price_usd"].median(),
        "std": df["rent_price_usd"].std(),
        "min": df["rent_price_usd"].min(),
        "max": df["rent_price_usd"].max(),
        "skewness": df["rent_price_usd"].skew(),
        "kurtosis": df["rent_price_usd"].kurtosis(),
    }

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    sns.histplot(df["rent_price_usd"], bins=40, kde=True, ax=axes[0], color="#4C78A8")
    axes[0].axvline(rent_stats["median"], color="red", linestyle="--", linewidth=1.5, label="Median")
    axes[0].set_title("Rent Distribution (Histogram + KDE)")
    axes[0].set_xlabel("rent_price_usd")
    axes[0].set_ylabel("Count")
    axes[0].legend()
    axes[0].text(
        0.98,
        0.95,
        f"Skew: {rent_stats['skewness']:.2f}",
        transform=axes[0].transAxes,
        ha="right",
        va="top",
        fontsize=10,
        bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray"),
    )

    sns.boxplot(y=df["rent_price_usd"], ax=axes[1], color="#72B7B2")
    axes[1].set_title("Rent Boxplot")
    axes[1].set_ylabel("rent_price_usd")

    sns.histplot(df["log_rent"], bins=40, kde=True, ax=axes[2], color="#F58518")
    axes[2].set_title("log1p(Rent) Distribution")
    axes[2].set_xlabel("log1p(rent_price_usd)")
    axes[2].set_ylabel("Count")

    fig.tight_layout()
    fig.savefig(chart_dir / "phase1_rent_distribution.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("[Chart Saved] phase1_rent_distribution.png")
    print("Rent stats:")
    for k, v in rent_stats.items():
        print(f"  {k:<10}: {v:.2f}")

    fig, axes = plt.subplots(2, 2, figsize=(18, 10))
    numeric_cols = ["size_sqm", "bedrooms", "bathrooms", "price_per_sqm"]
    titles = ["Size (sqm)", "Bedrooms", "Bathrooms", "Price per sqm"]

    for ax, col, title in zip(axes.ravel(), numeric_cols, titles):
        sns.histplot(df[col], bins=35, kde=True, ax=ax, color="#54A24B")
        med = df[col].median()
        ax.axvline(med, color="red", linestyle="--", linewidth=1.5, label=f"Median: {med:.2f}")
        ax.set_title(f"{title} Distribution")
        ax.set_xlabel(col)
        ax.set_ylabel("Count")
        ax.legend()

    fig.tight_layout()
    fig.savefig(chart_dir / "phase1_numeric_distributions.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("[Chart Saved] phase1_numeric_distributions.png")
    print("Numeric medians:")
    for col in numeric_cols:
        print(f"  {col:<13}: {df[col].median():.2f}")

    fig, ax = plt.subplots(1, 1, figsize=(18, 6))
    type_counts = df["property_type"].value_counts().sort_values(ascending=False)
    sns.barplot(x=type_counts.index, y=type_counts.values, ax=ax, color=sns.color_palette("Set2")[0])
    _annotate_bars(ax)
    ax.set_title("Property Type Counts")
    ax.set_xlabel("property_type")
    ax.set_ylabel("Count")
    ax.tick_params(axis="x", rotation=20)

    fig.tight_layout()
    fig.savefig(chart_dir / "phase1_categorical.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    type_percent = (type_counts / len(df) * 100).round(2)
    print("[Chart Saved] phase1_categorical.png")
    print("Property type distribution (%):")
    print(pd.DataFrame({"count": type_counts, "percent": type_percent}).to_string())

    log_needed = rent_stats["skewness"] > 1
    print(f"\nLog transformation needed? {'YES' if log_needed else 'NO'}")

    print("\nInsight:")
    print("Rent distribution is strongly right-skewed with a long luxury tail, while most listings cluster in lower rent bands.")
    print("After log1p transformation, the target becomes much closer to symmetric, which is better for many regression models.")
    print("Property type is imbalanced, with Villa dominating the sample and likely driving the upper tail of rent.")
    print("Business interpretation: Pricing benchmarks should be segmented by property type because category mix strongly shifts average market rent.")


def phase_2_bivariate(df: pd.DataFrame, chart_dir: Path):
    print("\n" + "=" * 80)
    print("PHASE 2 — BIVARIATE ANALYSIS")
    print("=" * 80)

    median_type = (
        df.groupby("property_type")["rent_price_usd"].median().sort_values(ascending=False)
    )
    sorted_types = median_type.index.tolist()

    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    sns.boxplot(data=df, x="property_type", y="rent_price_usd", order=sorted_types, ax=axes[0], color=sns.color_palette("Set2")[1])
    axes[0].set_title("Rent by Property Type (Boxplot)")
    axes[0].set_xlabel("property_type")
    axes[0].set_ylabel("rent_price_usd")
    axes[0].tick_params(axis="x", rotation=20)

    sns.barplot(x=median_type.index, y=median_type.values, ax=axes[1], color=sns.color_palette("husl")[2])
    _annotate_bars(axes[1], fmt="{:.0f}")
    axes[1].set_title("Median Rent by Property Type")
    axes[1].set_xlabel("property_type")
    axes[1].set_ylabel("Median rent_price_usd")
    axes[1].tick_params(axis="x", rotation=20)

    fig.tight_layout()
    fig.savefig(chart_dir / "phase2_rent_by_property_type.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("[Chart Saved] phase2_rent_by_property_type.png")
    print("Median rent by property_type:")
    print(median_type.round(2).to_string())

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    features = ["size_sqm", "bedrooms", "bathrooms"]
    corr_results = {}

    for ax, feature in zip(axes, features):
        sns.regplot(data=df, x=feature, y="rent_price_usd", scatter_kws={"alpha": 0.5}, line_kws={"color": "red"}, ax=ax)
        r_val, p_val = stats.pearsonr(df[feature], df["rent_price_usd"])
        corr_results[feature] = (r_val, p_val)
        ax.set_title(f"Rent vs {feature}")
        ax.set_xlabel(feature)
        ax.set_ylabel("rent_price_usd")
        ax.text(
            0.05,
            0.95,
            f"r={r_val:.2f}\np={p_val:.2e}",
            transform=ax.transAxes,
            ha="left",
            va="top",
            bbox=dict(facecolor="white", alpha=0.8, edgecolor="gray"),
        )

    fig.tight_layout()
    fig.savefig(chart_dir / "phase2_rent_vs_numeric.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("[Chart Saved] phase2_rent_vs_numeric.png")
    print("Pearson correlations with rent:")
    for feature, (r_val, p_val) in corr_results.items():
        print(f"  {feature:<10}: r={r_val:.2f}, p={p_val:.2e}")

    fig, ax = plt.subplots(1, 1, figsize=(18, 6))
    bedroom_int = df["bedrooms"].round().astype(int)
    bedroom_order = sorted(bedroom_int.unique())
    sns.boxplot(x=bedroom_int, y=df["rent_price_usd"], order=bedroom_order, ax=ax, color=sns.color_palette("Set2")[2])
    ax.set_title("Rent by Bedroom Count")
    ax.set_xlabel("bedrooms")
    ax.set_ylabel("rent_price_usd")

    fig.tight_layout()
    fig.savefig(chart_dir / "phase2_rent_by_bedrooms.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("[Chart Saved] phase2_rent_by_bedrooms.png")
    print("Bedroom count summary:")
    print(bedroom_int.value_counts().sort_index().to_string())

    print("\nInsight:")
    print("Property type shows clear pricing tiers, with premium categories exhibiting higher medians and wider spread.")
    print("Bathrooms and bedrooms have stronger linear relationships with rent than raw size in this sample.")
    print("Bedroom-based boxplots indicate stepwise price increases, but variance grows quickly for larger properties.")
    print("Business interpretation: Pricing strategy should prioritize bathroom and bedroom configuration as key value drivers for listing valuation.")


def phase_3_correlation(df: pd.DataFrame, chart_dir: Path) -> pd.Series:
    print("\n" + "=" * 80)
    print("PHASE 3 — CORRELATION ANALYSIS")
    print("=" * 80)

    numeric_cols = ["rent_price_usd", "size_sqm", "bedrooms", "bathrooms", "price_per_sqm"]
    corr_matrix = df[numeric_cols].corr(method="pearson")

    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    sns.heatmap(corr_matrix, annot=True, fmt=".2f", cmap="YlGnBu", ax=axes[0])
    axes[0].set_title("Correlation Heatmap")

    corr_with_rent = corr_matrix["rent_price_usd"].drop("rent_price_usd").sort_values(ascending=False)
    sns.barplot(x=corr_with_rent.index, y=corr_with_rent.values, ax=axes[1], color=sns.color_palette("husl")[3])
    _annotate_bars(axes[1], fmt="{:.2f}")
    axes[1].set_title("Feature Correlation with rent_price_usd")
    axes[1].set_xlabel("Feature")
    axes[1].set_ylabel("Pearson r")

    fig.tight_layout()
    fig.savefig(chart_dir / "phase3_correlation_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("[Chart Saved] phase3_correlation_heatmap.png")
    print("Correlation matrix (rounded):")
    print(corr_matrix.round(3).to_string())

    pairplot = sns.pairplot(df[numeric_cols], corner=True, diag_kind="hist", plot_kws={"alpha": 0.4, "s": 25})
    pairplot.fig.suptitle("Scatter Matrix of Numeric Features", y=1.02)
    pairplot.savefig(chart_dir / "phase3_scatter_matrix.png", dpi=200, bbox_inches="tight")
    plt.close(pairplot.fig)

    print("[Chart Saved] phase3_scatter_matrix.png")
    top3 = corr_with_rent.head(3)
    print("Top 3 correlated features with rent_price_usd:")
    print(top3.round(3).to_string())

    abs_corr = corr_matrix.abs()
    upper_triangle = abs_corr.where(np.triu(np.ones(abs_corr.shape), k=1).astype(bool))
    high_pairs = upper_triangle.stack()[upper_triangle.stack() > 0.8]
    if len(high_pairs) == 0:
        print("Multicollinearity risk (|r| > 0.8): None")
    else:
        print("Multicollinearity risk pairs (|r| > 0.8):")
        print(high_pairs.round(3).to_string())

    print("\nInsight:")
    print("Bathrooms is the strongest numeric correlate with rent in this dataset, followed by bedrooms and size.")
    print("The heatmap and pairwise plots show meaningful but not extreme inter-feature relationships.")
    print("No severe multicollinearity appears among numeric predictors at the 0.8 threshold.")
    print("Business interpretation: A compact model using structural attributes can explain pricing direction without severe redundancy across inputs.")

    return corr_with_rent


def phase_4_multivariate(df: pd.DataFrame, chart_dir: Path):
    print("\n" + "=" * 80)
    print("PHASE 4 — MULTIVARIATE ANALYSIS")
    print("=" * 80)

    fig, axes = plt.subplots(1, 2, figsize=(18, 6))

    sns.scatterplot(
        data=df,
        x="size_sqm",
        y="rent_price_usd",
        hue="property_type",
        alpha=0.6,
        ax=axes[0],
    )
    axes[0].set_title("Rent vs Size Colored by Property Type")
    axes[0].set_xlabel("size_sqm")
    axes[0].set_ylabel("rent_price_usd")

    scatter = axes[1].scatter(
        df["size_sqm"],
        df["rent_price_usd"],
        c=df["bedrooms"],
        cmap="viridis",
        alpha=0.6,
        s=35,
    )
    axes[1].set_title("Rent vs Size Colored by Bedrooms")
    axes[1].set_xlabel("size_sqm")
    axes[1].set_ylabel("rent_price_usd")
    cbar = fig.colorbar(scatter, ax=axes[1])
    cbar.set_label("bedrooms")

    fig.tight_layout()
    fig.savefig(chart_dir / "phase4_multivariate_scatter.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("[Chart Saved] phase4_multivariate_scatter.png")
    print("Scatter stats: size and rent ranges")
    print(f"  size_sqm range: {df['size_sqm'].min():.2f} to {df['size_sqm'].max():.2f}")
    print(f"  rent range    : {df['rent_price_usd'].min():.2f} to {df['rent_price_usd'].max():.2f}")

    bedroom_int = df["bedrooms"].round().astype(int)
    pivot = (
        df.assign(bedrooms_int=bedroom_int)
        .pivot_table(index="property_type", columns="bedrooms_int", values="rent_price_usd", aggfunc="median")
        .sort_index()
    )

    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    sns.boxplot(data=df.assign(bedrooms_int=bedroom_int), x="bedrooms_int", y="rent_price_usd", hue="property_type", ax=axes[0])
    axes[0].set_title("Rent by Bedrooms grouped by Property Type")
    axes[0].set_xlabel("bedrooms")
    axes[0].set_ylabel("rent_price_usd")
    axes[0].legend(title="property_type", bbox_to_anchor=(1.02, 1), loc="upper left")

    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="magma", ax=axes[1])
    axes[1].set_title("Median Rent by Property Type x Bedrooms")
    axes[1].set_xlabel("bedrooms")
    axes[1].set_ylabel("property_type")

    fig.tight_layout()
    fig.savefig(chart_dir / "phase4_heatmap_type_bedrooms.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    print("[Chart Saved] phase4_heatmap_type_bedrooms.png")
    print("Median rent pivot table:")
    print(_round_df(pivot.fillna(np.nan), 2).to_string())

    print("\nInsight:")
    print("Price dispersion grows when conditioning on both property type and room configuration, especially for Villa-like categories.")
    print("The type-bedroom heatmap shows that size alone cannot explain rent; category context shifts expected pricing bands.")
    print("Bedroom increments do not produce a uniform rent increase across all property types.")
    print("Business interpretation: Pricing models and benchmarks should be segmented by property type and bedroom tier rather than relying on global averages.")


def phase_5_outliers(df: pd.DataFrame, chart_dir: Path):
    print("\n" + "=" * 80)
    print("PHASE 5 — OUTLIER DETECTION")
    print("=" * 80)

    rent = df["rent_price_usd"]
    q1 = rent.quantile(0.25)
    q3 = rent.quantile(0.75)
    iqr = q3 - q1
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    zscores = np.abs(stats.zscore(rent, nan_policy="omit"))
    iqr_mask = (rent < lower_fence) | (rent > upper_fence)
    z_mask = zscores > 3

    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    sns.boxplot(y=rent, ax=axes[0], color="#72B7B2")
    axes[0].axhline(lower_fence, color="red", linestyle="--", linewidth=1.3, label="Lower fence")
    axes[0].axhline(upper_fence, color="red", linestyle="--", linewidth=1.3, label="Upper fence")
    axes[0].set_title("Boxplot with IQR Fences")
    axes[0].set_ylabel("rent_price_usd")
    axes[0].legend()

    idx = np.arange(len(df))
    axes[1].scatter(idx[~z_mask], rent[~z_mask], s=20, alpha=0.5, label="Normal", color="#4C78A8")
    axes[1].scatter(idx[z_mask], rent[z_mask], s=30, alpha=0.8, label="|z| > 3", color="red")
    axes[1].set_title("Z-score Outliers")
    axes[1].set_xlabel("Index")
    axes[1].set_ylabel("rent_price_usd")
    axes[1].legend()

    sns.histplot(rent, bins=40, kde=True, ax=axes[2], color="#F58518")
    axes[2].axvline(lower_fence, color="red", linestyle="--", linewidth=1.3, label="Lower fence")
    axes[2].axvline(upper_fence, color="red", linestyle="--", linewidth=1.3, label="Upper fence")
    axes[2].set_title("Histogram with IQR Fences")
    axes[2].set_xlabel("rent_price_usd")
    axes[2].set_ylabel("Count")
    axes[2].legend()

    fig.tight_layout()
    fig.savefig(chart_dir / "phase5_outlier_detection.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    iqr_count = int(iqr_mask.sum())
    z_count = int(z_mask.sum())
    iqr_pct = iqr_count / len(df) * 100
    z_pct = z_count / len(df) * 100

    print("[Chart Saved] phase5_outlier_detection.png")
    print(f"Q1: {q1:.2f}")
    print(f"Q3: {q3:.2f}")
    print(f"IQR: {iqr:.2f}")
    print(f"Lower fence: {lower_fence:.2f}")
    print(f"Upper fence: {upper_fence:.2f}")
    print(f"IQR outliers: {iqr_count} ({iqr_pct:.2f}%)")
    print(f"Z-score outliers: {z_count} ({z_pct:.2f}%)")

    top_expensive = df.nlargest(10, "rent_price_usd")[["listing_id", "property_type", "size_sqm", "bedrooms", "bathrooms", "rent_price_usd"]]
    top_cheapest = df.nsmallest(10, "rent_price_usd")[["listing_id", "property_type", "size_sqm", "bedrooms", "bathrooms", "rent_price_usd"]]

    print("\nTop 10 most expensive listings:")
    print(_round_df(top_expensive, 2).to_string(index=False))
    print("\nTop 10 cheapest listings:")
    print(_round_df(top_cheapest, 2).to_string(index=False))

    recommendation = (
        "Keep outliers for market realism but train models on log_rent to reduce sensitivity to luxury-tail values."
    )

    print("\nInsight:")
    print("IQR flags a broad premium tail while Z-score captures only the most extreme price spikes.")
    print("Most high-end outliers align with larger villa-like inventory, indicating market segmentation rather than random noise.")
    print("Low-end observations should be manually verified for potential data-entry anomalies.")
    print(f"Business interpretation: {recommendation}")

    return {
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "lower_fence": lower_fence,
        "upper_fence": upper_fence,
        "iqr_count": iqr_count,
        "iqr_pct": iqr_pct,
        "z_count": z_count,
        "z_pct": z_pct,
    }


def final_summary(df: pd.DataFrame, corr_with_rent: pd.Series, outlier_stats: dict):
    print("\n" + "=" * 80)
    print("FINAL SUMMARY REPORT")
    print("=" * 80)

    corr_rank = corr_with_rent.sort_values(ascending=False)

    print("1. TOP FEATURES FOR MODELING (ranked by correlation with rent):")
    for feature, value in corr_rank.items():
        print(f"   - {feature:<12}: r={value:.3f}")

    villa_share = (df["property_type"].eq("Villa").mean() * 100)
    villa_median = df.loc[df["property_type"].eq("Villa"), "rent_price_usd"].median()

    print("\n2. KEY PATTERNS:")
    print(f"   - Rent is right-skewed (skew={df['rent_price_usd'].skew():.2f}) — log transform required")
    print(f"   - Villa dominates ({villa_share:.1f}%) and has highest median rent (${villa_median:.0f})")
    print(f"   - Median rent=${df['rent_price_usd'].median():.0f}, Mean=${df['rent_price_usd'].mean():.0f} (luxury tail inflates mean)")
    print(f"   - {outlier_stats['iqr_count']} IQR outliers ({outlier_stats['iqr_pct']:.1f}%) above ${outlier_stats['upper_fence']:.0f}/month")
    print("   - No multicollinearity detected above |r| > 0.8 among numeric features")

    high_bed_luxury = df[(df["bedrooms"] >= 15) & (df["rent_price_usd"] >= 20000)]
    cheap_flats = df[(df["property_type"] == "Flat") & (df["rent_price_usd"] <= 100)]
    twin_share = df["property_type"].eq("Twin Villa").mean() * 100

    print("\n3. DATA QUALITY NOTES:")
    print(f"   - Potential luxury anomalies (>=15 bedrooms and >=$20k): {len(high_bed_luxury)} rows")
    print(f"   - Potential low-price flat anomalies (<= $100): {len(cheap_flats)} rows")
    print(f"   - Dataset imbalance remains (Villa={villa_share:.1f}%, Twin Villa={twin_share:.1f}%)")

    print("\n4. FEATURE ENGINEERING BEFORE MODELING:")
    print("   - Create: log_rent = log1p(rent_price_usd)")
    print("   - Create: price_per_sqm = rent / size_sqm")
    print("   - Create: room_ratio = bathrooms / bedrooms")
    print("   - Create: total_rooms = bedrooms + bathrooms")
    print("   - Encode: property_type using one-hot encoding")
    print("   - Drop: listing_id, city before fitting model")

    print("\n5. MODEL RECOMMENDATIONS:")
    print("   - Target: log1p(rent_price_usd), then back-transform for RMSE reporting")
    print("   - Baseline: Linear Regression on engineered numeric and encoded categorical features")
    print("   - Primary: Random Forest or gradient-boosting tree model")
    print("   - Optional: train a separate model for Villa due to class dominance and broader price variance")


def run_eda(input_path: Path, output_dir: Path):
    output_dir.mkdir(parents=True, exist_ok=True)
    df = load_and_prepare_data(input_path)

    print(f"Loaded dataset: {input_path}")
    print(f"Rows: {len(df)}, Columns: {len(df.columns)}")
    print(f"Charts output directory: {output_dir}")

    phase_1_univariate(df, output_dir)
    phase_2_bivariate(df, output_dir)
    corr_with_rent = phase_3_correlation(df, output_dir)
    phase_4_multivariate(df, output_dir)
    outlier_stats = phase_5_outliers(df, output_dir)
    final_summary(df, corr_with_rent, outlier_stats)


def main():
    project_root = Path(__file__).resolve().parent.parent
    default_input = project_root / "data_cleaning" / "Khmer24_cleaned_v4.csv"
    default_output = project_root / "outputs" / "charts"

    parser = argparse.ArgumentParser(description="Run complete 5-phase EDA for Khmer24 rental dataset.")
    parser.add_argument("--input", type=Path, default=default_input, help="Path to cleaned CSV file")
    parser.add_argument("--output", type=Path, default=default_output, help="Directory to save chart images")
    args = parser.parse_args()

    run_eda(args.input, args.output)


if __name__ == "__main__":
    main()
