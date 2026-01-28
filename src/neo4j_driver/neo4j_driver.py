from .base import Base
from .city import City
from .poi import POI
from .tsp import TSP


class Neo4jDriver(Base, City, POI, TSP):
    def __init__(self) -> None:
        self.init_driver()
