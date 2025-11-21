from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/")  # type: ignore[misc]
def get_distance(request: Request, poi1_id: str, poi2_id: str) -> dict[str, float]:
    return {"distance": request.app.state.driver.calculate_distance_between_two_nodes(poi1_id, poi2_id)}
