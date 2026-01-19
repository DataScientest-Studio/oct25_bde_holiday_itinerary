from typing import List

from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

router = APIRouter()


class TSPResponse(BaseModel):
    poi_order: List[str]
    total_distance: float
    route: List[List[float]]


@router.get("/shortest-round-tour", response_model=TSPResponse)  # type: ignore[misc]
def shortest_round_tour(
    request: Request, poi_ids: list[str] = Query(...)
) -> dict[str, list[str] | float | list[list[float]]]:
    driver = request.app.state.driver
    return driver.calculate_shortest_round_tour(poi_ids)  # type: ignore[no-any-return]


@router.get("/shortest-path-no-return", response_model=TSPResponse)  # type: ignore[misc]
def shortest_path_no_return(
    request: Request, poi_ids: list[str] = Query(...)
) -> dict[str, list[str] | float | list[list[float]]]:
    driver = request.app.state.driver
    return driver.calculate_shortest_path_no_return(poi_ids)  # type: ignore[no-any-return]


@router.get("/shortest-path-fixed-dest", response_model=TSPResponse)  # type: ignore[misc]
def shortest_path_fixed_dest(
    request: Request, poi_ids: list[str] = Query(...)
) -> dict[str, list[str] | float | list[list[float]]]:
    driver = request.app.state.driver
    return driver.calculate_shortest_path_fixed_dest(poi_ids)  # type: ignore[no-any-return]
