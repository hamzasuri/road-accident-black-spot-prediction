from fastapi import APIRouter
from backend.app.controllers.prediction_controller import predict

router = APIRouter()


@router.post("/predict")
def prediction(data: dict):
    return predict(data)