from typing import Any, List, Optional

from fastapi import APIRouter, Query, Request

router = APIRouter()


@router.get("/{city_id}")  # type: ignore[misc]
def get_city(request: Request, city_id: str) -> dict[str, Any]:
    driver = request.app.state.driver
    return driver.get_city(city_id)  # type: ignore


@router.get("/all")  # type: ignore[misc]
def get_cities(request: Request) -> dict[str, Any]:
    driver = request.app.state.driver
    cities = driver.get_cities()  # type: ignore
    print(cities)
    print("HELLLOQ?Q>Q")
    return cities


@router.get("/{city_id}/pois")  # type: ignore[misc]
def get_city_points(
    request: Request, city_id: str, category: Optional[List[str]] = Query(None)
) -> List[dict[str, Any]]:
    driver = request.app.state.driver
    return driver.get_poi_for_city(city_id, category)  # type: ignore


@router.get("/{city_id}/pois_nearby")  # type: ignore[misc]
def get_nearby_city_points(
    request: Request, city_id: str, category: Optional[List[str]] = Query(None)
) -> List[dict[str, Any]]:
    driver = request.app.state.driver
    return driver.get_poi_near_city(city_id, category)  # type: ignore


@router.get("/{city_id}/poi_types")  # type: ignore[misc]
def get_poi_types_for_city(request: Request, city_id: str) -> List[str]:
    driver = request.app.state.driver
    return driver.get_poi_types_for_city(city_id)  # type: ignore


@router.get("/{latitude}/{longitude}")
def get_city_by_coordinates(request: Request, latitude: float, longitude: float) -> dict[str, Any]:
    driver = request.app.state.driver
    return driver.get_nearest_city_by_coordinates(latitude, longitude)
