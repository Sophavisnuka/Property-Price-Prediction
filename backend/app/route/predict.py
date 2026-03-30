from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class PropertyInput(BaseModel):
    location: str
    bedrooms: int
    bathrooms: int
    size: float

@app.post("/predict")
def predict_price(data: PropertyInput):

    # temporary fake prediction
    estimated_price = data.size * 500

    return {
        "predicted_price": estimated_price
    }