from fastapi import APIRouter

from neo4j_driver.driver import Neo4jDriver

router = APIRouter()
driver = Neo4jDriver()


@router.get("/distance")  # type: ignore
def get_distance(poi1_id: str, poi2_id: str) -> dict[str, float]:
    return {"distance": driver.calculate_distance_between_two_nodes(poi1_id, poi2_id)}
