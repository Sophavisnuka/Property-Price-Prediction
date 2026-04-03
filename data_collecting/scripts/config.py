import os

USE_MOCK_DATA = True  # False after Member A delivers clean data

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DATA_PATH = os.path.join(BASE_DIR, "data", "mock", "mock_listings.csv") \
            if USE_MOCK_DATA else \
            os.path.join(BASE_DIR, "data", "processed", "clean_listings.csv")

CHARTS_DIR = os.path.join(BASE_DIR, "outputs", "charts")
MODEL_PATH = os.path.join(BASE_DIR, "outputs", "models", "model_final.pkl")

COLUMNS = {
    "price":     "rent_price_usd",
    "city":      "city",
    "location":  "district",
    "type":      "property_type",
    "size":      "size_sqm",
    "bedrooms":  "bedrooms",
    "bathrooms": "bathrooms",
    "furnished": "furnished",
}

CITIES = ["Phnom Penh", "Siem Reap", "Sihanoukville"]
