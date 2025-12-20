from fastapi import APIRouter, Query, Request
from loguru import logger  # noqa: F401

router = APIRouter()


@router.get("/shortest-round-tour")  # type: ignore[misc]
def shortest_round_tour(request: Request, poi_ids: list[str] = Query(...)) -> dict[str, list[str] | float]:
    driver = request.app.state.driver
    return driver.calculate_shortest_round_tour(poi_ids)  # type: ignore[no-any-return]


@router.get("/shortest-path-no-return")  # type: ignore[misc]
def shortest_path_no_return(request: Request, poi_ids: list[str] = Query(...)) -> dict[str, list[str] | float]:
    driver = request.app.state.driver
    return driver.calculate_shortest_path_no_return(poi_ids)  # type: ignore[no-any-return]


@router.get("/shortest-path-fixed-dest")  # type: ignore[misc]
def shortest_path_fixed_dest(
    request: Request, dest: str, poi_ids: list[str] = Query(...)
) -> dict[str, list[str] | float]:
    driver = request.app.state.driver
    return driver.calculate_shortest_path_fixed_dest(dest, poi_ids)  # type: ignore[no-any-return]
