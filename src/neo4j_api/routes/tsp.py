from fastapi import APIRouter, Query

from .driver import Neo4jDriver

router = APIRouter()
driver = Neo4jDriver()


@router.get("/shortest-round-tour")  # type: ignore
def shortest_round_tour(poi_ids: list[str] = Query(...)) -> dict[str, list[str] | float]:
    return driver.shortest_round_tour_visiting_all_nodes(poi_ids)  # type: ignore[no-any-return]


@router.get("/shortest-path-no-return")  # type: ignore
def shortest_path_no_return(poi_ids: list[str] = Query(...)) -> dict[str, list[str] | float]:
    return driver.shortest_path_between_all_nodes_with_fixed_start(poi_ids)  # type: ignore[no-any-return]


@router.get("/shortest-path-fixed-dest")  # type: ignore
def shortest_path_fixed_dest(dest: str, poi_ids: list[str] = Query(...)) -> dict[str, list[str] | float]:
    return driver.shortest_path_between_all_nodes_with_fixed_end(dest, poi_ids)  # type: ignore[no-any-return]
