from typing import Any

from fastapi import APIRouter

from neo4j_driver.driver import Neo4jDriver

router = APIRouter()
driver = Neo4jDriver()


@router.get("/")  # type: ignore
def get_poi(poi_id: str) -> dict[str, Any]:
    return driver.get_poi(poi_id)  # type: ignore


@router.get("/nearby")  # type: ignore
def get_nearby_points(poi_id: str, radius: float) -> dict[str, Any]:
    return driver.get_nearby_points(poi_id, radius)  # type: ignore
