from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.neo4j_driver.neo4j_driver import Neo4jDriver

from .routes import city, data_update, dijkstra, distance, poi, travel, tsp


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.driver = Neo4jDriver()
    yield
    await app.state.driver.close()


app = FastAPI(lifespan=lifespan)


app.include_router(travel.router, prefix="/travel", tags=["Travel"])
app.include_router(city.router, prefix="/city", tags=["City"])
app.include_router(poi.router, prefix="/poi", tags=["POI"])
app.include_router(distance.router, prefix="/distance", tags=["Distance"])
app.include_router(tsp.router, prefix="/tsp", tags=["TSP"])
app.include_router(dijkstra.router, prefix="/dijkstra", tags=["DIJKSTRA"])
app.include_router(data_update.router, prefix="/data", tags=["DATA"])
