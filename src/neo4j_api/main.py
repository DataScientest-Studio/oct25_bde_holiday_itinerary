from contextlib import asynccontextmanager

from fastapi import FastAPI

from neo4j_driver.neo4j_driver import Neo4jDriver

from .routes import dijkstra, distance, poi, tsp


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.driver = Neo4jDriver()
    yield
    await app.state.driver.close()


app = FastAPI(lifespan=lifespan)


app.include_router(poi.router, prefix="/poi", tags=["POI"])
app.include_router(distance.router, prefix="/distance", tags=["Distance"])
app.include_router(tsp.router, prefix="/tsp", tags=["TSP"])
app.include_router(dijkstra.router, prefix="/dijkstra", tags=["DIJKSTRA"])
