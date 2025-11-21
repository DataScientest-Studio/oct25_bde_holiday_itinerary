from fastapi import APIRouter, Query

from .driver import Neo4jDriver

router = APIRouter()
driver = Neo4jDriver()


@router.get("/shortest-path")  # type: ignore
def shortest_path_from_start_to_end(poi_ids: list[str] = Query(...)) -> dict[str, list[str] | float]:
    return driver.find_shortest_in_a_set_of_nodes_from_start_to_end(poi_ids)  # type: ignore[no-any-return]
