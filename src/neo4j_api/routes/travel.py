from typing import Any, Dict, List, Literal

from fastapi import APIRouter, Query, Request

router = APIRouter()


@router.get("/between/{start_city}/{end_city}")  # type: ignore[misc]
def get_route_between_cities(request: Request, start_city: str, end_city: str) -> List[Dict[str, Any]]:
    """returns shortest path from start_city to end_city"""
    driver = request.app.state.driver
    return driver.get_route_between_cities(start_city, end_city)  # type: ignore


@router.get("/around/{city_id}")  # type: ignore[misc]
def get_roundtrip(
    request: Request,
    city_id: str,
    distance: float,
    distance_tol: float,
    max_hops: int = Query(..., ge=3, le=10),
    sort_distance: Literal["ASC", "DESC"] = "ASC",
) -> Dict[str, Any]:
    driver = request.app.state.driver
    return driver.get_roundtrip(city_id, distance, distance_tol, max_hops, sort_distance)  # type: ignore
