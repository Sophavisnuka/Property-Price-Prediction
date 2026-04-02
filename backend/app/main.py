from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.route import predict

app = FastAPI()

# Allow frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(predict.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok", "message": "Property Price Prediction API"}