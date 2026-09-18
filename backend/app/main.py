from fastapi import FastAPI
from backend.app.routes.prediction_routes import router as prediction_router
from backend.app.routes.road_routes import router as road_router

app = FastAPI()

app.include_router(prediction_router)
app.include_router(road_router)


@app.get("/")
def home():
    return {
        "message": "Road Accident API is Running"
    }