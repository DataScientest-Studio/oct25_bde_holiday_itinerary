from typing import Any

from fastapi import FastAPI

from .driver import Neo4jDriver

app = FastAPI()

driver = Neo4jDriver()


@app.get("/poi")  # type: ignore
def get_poi(poi_id: str) -> dict[str, Any]:
    return driver.get_poi(poi_id)


@app.get("/nearby")  # type: ignore
def get_nearby_points(poi_id: str, radius: float) -> dict[str, Any]:
    return driver.get_nearby_points(poi_id, radius)


@app.get("/calculate-shortest-path")  # type: ignore
def calculate_shortest_path(poi_ids: list[str]) -> dict[str, Any]:
    return driver.calculate_shortest_path(poi_ids)
