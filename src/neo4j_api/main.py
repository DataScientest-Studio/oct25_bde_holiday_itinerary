from fastapi import FastAPI

from neo4j_driver.driver import Neo4jDriver

from .routes import dijkstra, distance, poi, tsp

app = FastAPI()


@app.on_event("startup")  # type: ignore[misc]
async def startup_event() -> None:
    app.state.driver = Neo4jDriver()


@app.on_event("shutdown")  # type: ignore[misc]
async def shutdown_event() -> None:
    await app.state.driver.close()


app.include_router(poi.router, prefix="/poi", tags=["POI"])
app.include_router(distance.router, prefix="/distance", tags=["Distance"])
app.include_router(tsp.router, prefix="/tsp", tags=["TSP"])
app.include_router(dijkstra.router, prefix="/dijkstra", tags=["DIJKSTRA"])
