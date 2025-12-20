from fastapi import APIRouter, Query, Request

router = APIRouter()


@router.get("/")  # type: ignore[misc]
def shortest_path_from_start_to_dest(request: Request, poi_ids: list[str] = Query(...)) -> dict[str, list[str] | float]:
    driver = request.app.state.driver
    return driver.calculate_shortest_path_from_start_to_dest(poi_ids)  # type: ignore[no-any-return]
