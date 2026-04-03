import pandas as pd
import numpy as np

# ── Load Data ─────────────────────────────────────────────────
df = pd.read_csv("data_cleaning/Khmer24_cleaned_final.csv")

print("=" * 60)
print("DATASET OVERVIEW")
print("=" * 60)
print(f"  Shape        : {df.shape}")
print(f"  Columns      : {list(df.columns)}")
print(f"  Duplicates   : {df.duplicated().sum()}")
print(f"  dtypes:\n{df.dtypes.to_string()}")



# ── Step 1: Remove Duplicates ─────────────────────────────────
df = df.drop_duplicates().reset_index(drop=True)
print(f"\n  After dedup shape: {df.shape}")



# ── Step 2: Clean rent_price_usd ─────────────────────────────
# Remove "$", "/month", commas, whitespace → convert to float
# print("\n" + "=" * 60)
# print("CLEANING rent_price_usd")
# print("=" * 60)
# print(f"  Sample raw values: {df['rent_price_usd'].dropna().head(5).tolist()}")

# df['rent_price_usd'] = (
#     df['rent_price_usd']
#     .astype(str)
#     .str.replace(r'[\$,/month\s]', '', regex=True)
#     .str.replace('permonth', '', regex=False)
#     .str.strip()
#     .replace('nan', np.nan)
#     .replace('None', np.nan)
#     .replace('POA', np.nan)       # Price on Application
#     .replace('', np.nan)
#     .astype(float)
# )


# ── Step 2: Clean rent_price_usd ─────────────────────────────
print("\n" + "=" * 60)
print("CLEANING rent_price_usd")
print("=" * 60)

# 1. Strip symbols and text
df['rent_price_usd'] = (
    df['rent_price_usd']
    .astype(str)
    .str.replace(r'[\$,/month\s]', '', regex=True)
    .str.replace('permonth', '', regex=False)
    .str.strip()
)

# 2. Convert everything that ISN'T a number to NaN safely
# pd.to_numeric with errors='coerce' turns 'rent_price_usd' or 'POA' into NaN
df['rent_price_usd'] = pd.to_numeric(df['rent_price_usd'], errors='coerce')

# 3. Handle specific string cases if pd.to_numeric missed anything (optional)
df['rent_price_usd'] = df['rent_price_usd'].replace(['nan', 'None', ''], np.nan)

# 4. Remove extreme outliers
before = len(df)
df = df[(df['rent_price_usd'] >= 50) & (df['rent_price_usd'] <= 50000) | df['rent_price_usd'].isna()]
print(f"  Outlier rows removed: {before - len(df)}")



# Remove extreme outliers: price < $50 or > $50,000/month
before = len(df)
df = df[(df['rent_price_usd'] >= 50) & (df['rent_price_usd'] <= 50000) | df['rent_price_usd'].isna()]
print(f"  Outlier rows removed: {before - len(df)}")
print(f"  Price range: ${df['rent_price_usd'].min()} – ${df['rent_price_usd'].max()}")



# ── Step 3: Clean size_sqm, bedrooms, bathrooms ───────────────
print("\n" + "=" * 60)
print("CLEANING NUMERIC COLUMNS")
print("=" * 60)

def clean_numeric(series):
    """Extract first number from strings like '35m²', '4 bedrooms'."""
    return (
        series.astype(str)
        .str.extract(r'(\d+\.?\d*)')[0]
        .replace('nan', np.nan)
        .replace('None', np.nan)
        .astype(float)
    )

df['size_sqm']   = clean_numeric(df['size_sqm'])
df['bedrooms']   = clean_numeric(df['bedrooms'])
df['bathrooms']  = clean_numeric(df['bathrooms'])



# Remove impossible values
df.loc[df['size_sqm'] > 5000, 'size_sqm']     = np.nan   # > 5000m² unrealistic
df.loc[df['bedrooms'] > 20, 'bedrooms']        = np.nan   # > 20 bedrooms unrealistic
df.loc[df['bathrooms'] > 20, 'bathrooms']      = np.nan   # > 20 bathrooms unrealistic
df.loc[df['size_sqm'] < 5, 'size_sqm']         = np.nan   # < 5m² unrealistic



# ── Step 4: Clean property_type ──────────────────────────────
print("\n" + "=" * 60)
print("CLEANING property_type")
print("=" * 60)
print(f"  Raw unique values:\n{df['property_type'].value_counts().to_string()}")



# Standardize property type names
type_map = {
    'flat'          : 'Flat',
    'house'         : 'House',
    'villa'         : 'Villa',
    'twin villa'    : 'Twin Villa',
    'link house'    : 'Link House',
    'shophouse'     : 'Shophouse',
    'condo'         : 'Condo',
    'apartment'     : 'Apartment',
}
df['property_type'] = (
    df['property_type']
    .astype(str)
    .str.strip()
    .str.lower()
    .map(type_map)
    .fillna('Other')
)
print(f"\n  Cleaned unique values:\n{df['property_type'].value_counts().to_string()}")



# ── Step 5: Clean furnished ───────────────────────────────────
print("\n" + "=" * 60)
print("CLEANING furnished")
print("=" * 60)
df['furnished'] = (
    df['furnished']
    .astype(str)
    .str.strip()
    .str.title()
    .replace({'Nan': 'Unknown', 'None': 'Unknown', '': 'Unknown'})
)
print(df['furnished'].value_counts().to_string())



# ── Step 6: Missing Value Summary ────────────────────────────
cols = ['size_sqm', 'bedrooms', 'bathrooms']
total = len(df)
print("\n" + "=" * 60)
print("MISSING VALUES BEFORE IMPUTATION")
print("=" * 60)
for col in cols:
    n = df[col].isna().sum()
    print(f"  {col:<12} {n:>4} missing  ({n/total*100:.1f}%)")



# ── Step 7: Drop rows missing ALL three structural columns ────
all_missing_mask = df[cols].isna().all(axis=1)
print(f"\n  Rows missing ALL 3 structural cols: {all_missing_mask.sum()} → dropping")
df = df[~all_missing_mask].reset_index(drop=True)



# ── Step 8: Per-type median imputation + missing flags ────────
print("\n" + "=" * 60)
print("IMPUTATION: Per-type median + missing indicator flags")
print("=" * 60)



# Save which rows were missing BEFORE imputation
for col in cols:
    df[f"{col}_was_missing"] = df[col].isna().astype(int)



# Per-type median imputation with global fallback
print("\n  Medians used per property_type:")
print(
    df.groupby("property_type")[cols]
    .median()
    .round(1)
    .to_string()
)

for col in cols:
    type_medians  = df.groupby("property_type")[col].transform("median")
    global_median = df[col].median()
    df[col] = df[col].fillna(type_medians).fillna(global_median)



# ── Step 9: Final missing check ───────────────────────────────
print("\n" + "=" * 60)
print("MISSING VALUES AFTER IMPUTATION")
print("=" * 60)
for col in cols:
    n = df[col].isna().sum()
    print(f"  {col:<12} {n:>4} missing remaining")

flag_cols = [f"{c}_was_missing" for c in cols]
print(f"\n  Imputed counts:")
print(df[flag_cols].sum().to_string())



# ── Step 10: Final Summary ────────────────────────────────────
print("\n" + "=" * 60)
print("FINAL DATASET SUMMARY")
print("=" * 60)
print(f"  Shape        : {df.shape}")
print(f"  rent_price_usd stats:")
print(df['rent_price_usd'].describe().round(2).to_string())
print(f"\n  size_sqm stats:")
print(df['size_sqm'].describe().round(2).to_string())



# ── Save ──────────────────────────────────────────────────────
output_path = "data_cleaning/Khmer24_cleaned_v2.csv"
df.to_csv(output_path, index=False)
print(f"\n  Saved: {output_path}")
print(f"  Shape: {df.shape}")