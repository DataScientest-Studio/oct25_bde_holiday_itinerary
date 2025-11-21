from fastapi import APIRouter, Query, Request

router = APIRouter()


@router.get("/")  # type: ignore[misc]
def shortest_path_from_start_to_end(request: Request, poi_ids: list[str] = Query(...)) -> dict[str, list[str] | float]:
    driver = request.app.state.driver
    return driver.find_shortest_in_a_set_of_nodes_from_start_to_end(poi_ids)  # type: ignore[no-any-return]
