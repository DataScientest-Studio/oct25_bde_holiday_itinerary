from typing import Any

from fastapi import FastAPI, Query

from .driver import Neo4jDriver

app = FastAPI()

driver = Neo4jDriver()


@app.get("/poi")  # type: ignore
def get_poi(poi_id: str) -> dict[str, Any]:
    return driver.get_poi(poi_id)


@app.get("/distance")  # type: ignore
def get_distance(poi1_id: str, poi2_id: str) -> dict[str, float]:
    return {"distance": driver.calculate_distance_between_two_nodes(poi1_id, poi2_id)}


@app.get("/nearby")  # type: ignore
def get_nearby_points(poi_id: str, radius: float) -> dict[str, Any]:
    return driver.get_nearby_points(poi_id, radius)


@app.get("/shortest-round-tour-visiting-all-nodes")  # type: ignore
def shortest_round_tour_visiting_all_nodes(poi_ids: list[str] = Query(...)) -> dict[str, list[str] | float]:
    return driver.shortest_round_tour_visiting_all_nodes(poi_ids)


@app.get("/shortest-path-between-all-nodes-with-fixed-start")  # type: ignore
def shortest_path_between_all_nodes_with_fixed_start(poi_ids: list[str] = Query(...)) -> dict[str, list[str] | float]:
    return driver.shortest_path_between_all_nodes_with_fixed_start(poi_ids)


@app.get("/shortest-path-between-all-nodes-with-fixed-end")  # type: ignore
def shortest_path_between_all_nodes_with_fixed_end(
    end: str, poi_ids: list[str] = Query(...)
) -> dict[str, list[str] | float]:
    return driver.shortest_path_between_all_nodes_with_fixed_end(end, poi_ids)
