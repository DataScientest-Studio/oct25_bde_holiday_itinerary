from typing import Any

from fastapi import FastAPI

from .driver import Neo4jDriver

app = FastAPI()

driver = Neo4jDriver()


@app.get("/poi")  # type: ignore
def get_poi(poi_id: str) -> dict[str, Any]:
    return driver.get_poi(poi_id)
