from typing import Any

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/")  # type: ignore[misc]
def get_poi(request: Request, poi_id: str) -> dict[str, Any]:
    driver = request.app.state.driver
    return driver.get_poi(poi_id)  # type: ignore


@router.get("/nearby")  # type: ignore[misc]
def get_nearby_points(request: Request, poi_id: str, radius: float) -> dict[str, Any]:
    driver = request.app.state.driver
    return driver.get_nearby_points(poi_id, radius)  # type: ignore


@router.get("/types")  # type: ignore[misc]
def get_types(request: Request) -> dict[str, Any]:
    driver = request.app.state.driver
    return driver.get_types()  # type: ignore
