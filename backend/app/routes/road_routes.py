from fastapi import APIRouter
from backend.app.controllers.road_controller import get_roads

router = APIRouter()


@router.get("/roads")
def roads():
    return get_roads()