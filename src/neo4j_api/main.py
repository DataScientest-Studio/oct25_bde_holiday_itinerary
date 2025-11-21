from fastapi import FastAPI

from .routes import dijkstra, distance, poi, tsp

app = FastAPI()

app.include_router(poi.router, prefix="/poi", tags=["POI"])
app.include_router(distance.router, prefix="/distance", tags=["Distance"])
app.include_router(tsp.router, prefix="/tsp", tags=["TSP"])
app.include_router(dijkstra.router, prefix="/dijkstra", tags=["DIJKSTRA"])
