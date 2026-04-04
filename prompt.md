You are a data scientist performing Exploratory Data Analysis (EDA)
on a Cambodia rental house dataset scraped from Khmer24.com.

DATASET CONTEXT:
- Source      : Scraped from Khmer24.com (Cambodia real estate platform)
- Location    : Chroy Changvar district, Phnom Penh, Cambodia
- Rows        : 983 listings (after cleaning)
- Target      : rent_price_usd (monthly rent in USD)
- No missing values (already cleaned and imputed)

COLUMNS:
- listing_id       : unique listing ID (string) — drop before modeling
- city             : always "Phnom Penh" — drop before modeling
- district         : location district (string)
- location         : full location string (string)
- property_type    : Villa, Shophouse, Flat, House, Other, Twin Villa
- rent_price_usd   : monthly rent in USD (int) ← TARGET VARIABLE
- size_sqm         : floor area in square meters (float)
- bedrooms         : number of bedrooms (float)
- bathrooms        : number of bathrooms (float)

KEY FACTS ALREADY DISCOVERED:
- rent_price_usd is heavily right-skewed (skew=4.38, kurtosis=30.95)
- Log transformation is REQUIRED before modeling
- Villa = 60.8% of data (dominant property type)
- Median rent = $1,000/month, Mean = $1,831/month
- Price range: $50 – $25,000/month
- Strongest correlations with rent: bathrooms(0.601), bedrooms(0.465), size_sqm(0.435)
- No multicollinearity detected between features
- 112 IQR outliers (11.4%) mostly high-end villas above $4,350/month
- Median price per m² = $6.28

YOUR TASK:
Perform a complete EDA covering all 5 phases below.
For each phase produce:
  1. Python code using pandas, matplotlib, seaborn, scipy
  2. Save all charts to: outputs/charts/
  3. Print key statistics after each chart
  4. Write 2-3 sentence insight explaining what you found
  5. Write 1 sentence business interpretation for pricing

PHASE 1 — UNIVARIATE ANALYSIS
Goal: Understand the distribution of each variable independently.

Tasks:
- Plot rent_price_usd: histogram + KDE overlay + boxplot (3 subplots)
- Plot log1p(rent_price_usd): histogram to confirm normality after transform
- Plot size_sqm, bedrooms, bathrooms: histograms with median line
- Plot property_type: bar chart with count labels
- Plot price_per_sqm = rent / size_sqm: histogram
- Print: mean, median, std, min, max, skewness, kurtosis for rent_price_usd
- Print: value counts and percentages for property_type
- Flag: is log transformation needed? (yes if skew > 1)

Expected insight: rent_price_usd is right-skewed; most rentals
cluster below $2,000/month but a long tail of luxury villas
extends to $25,000/month.

Chart names:
  phase1_rent_distribution.png
  phase1_numeric_distributions.png
  phase1_categorical.png

PHASE 2 — BIVARIATE ANALYSIS
Goal: Understand how each feature relates to rent_price_usd.

Tasks:
- Boxplot: rent_price_usd by property_type (sorted by median)
- Bar chart: median rent per property_type (with value labels)
- Scatter: rent_price_usd vs size_sqm with regression line + r value
- Scatter: rent_price_usd vs bedrooms with regression line + r value
- Scatter: rent_price_usd vs bathrooms with regression line + r value
- Boxplot: rent_price_usd by bedrooms count
- Print: Pearson r and p-value for each numeric feature vs rent
- Print: median rent per property_type sorted descending

Expected insight: Villas command the highest median rent ($1,300).
Bathrooms has the strongest linear relationship with price (r=0.601),
suggesting larger, more premium properties drive price more than
raw bedroom count alone.

Chart names:
  phase2_rent_by_property_type.png
  phase2_rent_vs_numeric.png
  phase2_rent_by_bedrooms.png

PHASE 3 — CORRELATION ANALYSIS
Goal: Quantify relationships between all numeric variables.

Tasks:
- Pearson correlation heatmap of: rent_price_usd, size_sqm,
  bedrooms, bathrooms, price_per_sqm
- Bar chart: correlation of each feature with rent_price_usd
- Scatter matrix (pairplot) of all numeric columns
- Print: full correlation matrix rounded to 3 decimals
- Print: top 3 features most correlated with rent_price_usd
- Flag: any pair with |r| > 0.8 (multicollinearity risk)

Expected insight: Bathrooms (r=0.601) is the single strongest
predictor of rent. No multicollinearity detected between features
(all inter-feature correlations below 0.8), so all features can
safely be included in the model.

Chart names:
  phase3_correlation_heatmap.png
  phase3_scatter_matrix.png

PHASE 4 — MULTIVARIATE ANALYSIS
Goal: Understand interactions between multiple variables simultaneously.

Tasks:
- Scatter: rent_price_usd vs size_sqm colored by property_type
- Scatter: rent_price_usd vs size_sqm colored by bedrooms (colorbar)
- Boxplot: rent_price_usd by bedrooms grouped by property_type
- Heatmap: median rent_price_usd per property_type × bedrooms
- Print: median rent per property_type × bedrooms pivot table

Expected insight: Villas show the widest price variation across
bedroom counts, ranging from $650 to $25,000/month. Size alone
does not fully explain price — property type moderates the
size-price relationship significantly.

Chart names:
  phase4_multivariate_scatter.png
  phase4_heatmap_type_bedrooms.png

PHASE 5 — OUTLIER DETECTION
Goal: Identify and handle extreme rent values.

Tasks:
- Boxplot with IQR fences marked as horizontal lines
- Scatter plot with Z-score outliers highlighted in red
- Histogram with IQR fence lines overlaid
- Apply IQR method: flag rows where rent < Q1-1.5*IQR
  or rent > Q3+1.5*IQR
- Apply Z-score method: flag rows where |z| > 3
- Print: Q1, Q3, IQR, lower fence, upper fence
- Print: count and percentage of outliers by both methods
- Print: top 10 most expensive listings
- Print: top 10 cheapest listings
- Recommend: keep or remove outliers and why

Known values:
  Q1=$600, Q3=$2,100, IQR=$1,500
  Upper fence=$4,350, Lower fence=-$1,650
  IQR outliers=112 (11.4%), Z-score outliers=21 (2.1%)

Expected insight: 112 listings (11.4%) exceed the IQR upper fence
of $4,350/month — almost all are luxury villas. These should be
kept in the dataset but the model should be trained on
log-transformed target to reduce their influence.

Chart names:
  phase5_outlier_detection.png

OUTPUT REQUIREMENTS:
- Save all charts to: outputs/charts/
- Naming: phase{N}_{description}.png
- Figure size: minimum (18, 6) for multi-subplot charts
- Color palette: seaborn Set2 or husl
- All charts must have: title, axis labels, value annotations
- Print a statistics summary after each phase
- Round all printed numbers to 2 decimal places

FINAL DELIVERABLE:
After all 5 phases, print a single summary report containing:

1. TOP FEATURES FOR MODELING (ranked by correlation with rent):
   - bathrooms    : r=0.601
   - bedrooms     : r=0.465
   - size_sqm     : r=0.435
   - price_per_sqm: r=0.285

2. KEY PATTERNS:
   - Rent is right-skewed (skew=4.38) — log transform required
   - Villa dominates (60.8%) and has highest median rent ($1,300)
   - Median rent=$1,000, Mean=$1,831 (luxury villas inflate mean)
   - 112 outliers (11.4%) above $4,350/month
   - No multicollinearity between features

3. DATA QUALITY NOTES:
   - Some villas show 20 bedrooms/$25,000 — verify if real or error
   - Flat listings at $50/month may be data entry errors
   - Dataset is imbalanced: Villa=60.8%, Twin Villa=1.3%

4. FEATURE ENGINEERING BEFORE MODELING:
   - Create: log_rent = log1p(rent_price_usd)
   - Create: price_per_sqm = rent / size_sqm
   - Create: room_ratio = bathrooms / bedrooms
   - Create: total_rooms = bedrooms + bathrooms
   - Encode: property_type → one-hot encoding
   - Drop: listing_id, city (no predictive value)

5. MODEL RECOMMENDATIONS:
   - Target: log1p(rent_price_usd), evaluate with RMSE on original scale
   - Baseline: Linear Regression on log-transformed target
   - Primary: Random Forest or XGBoost/LightGBM
   - Consider: separate models per property_type (especially Villa)

CONSTRAINTS:
- Use only: pandas, numpy, matplotlib, seaborn, scipy
- Do not use: sklearn, statsmodels (reserved for modeling phase)
- Handle any remaining NaN gracefully with dropna()
- Use log scale on y-axis when price range exceeds 100x
- Round all printed statistics to 2 decimal places