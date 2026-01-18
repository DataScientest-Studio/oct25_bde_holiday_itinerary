import numpy as np
from loguru import logger


class City:
    def get_total_distance_between_cities(self, start: str, dest: str) -> float:
        logger.info(f"Calculating distance between {start} and {dest}.")
        query = """
            MATCH (s:City {cityId: $start})
            MATCH (t:City {cityId: $dest})

            CALL gds.shortestPath.dijkstra.stream(
                'city-road-graph',
                {
                    sourceNode: id(s),
                    targetNode: id(t),
                    relationshipWeightProperty: 'km'
                }
            )
            YIELD totalCost
            RETURN totalCost AS distance;
        """

        result = self.execute_query(query, start=start, dest=dest)  # type: ignore[attr-defined]
        logger.debug(f"Result: {result}")
        logger.info("Calculated distance.")
        return result[0]["distance"] if result else np.inf

    def get_cities_for_poiIds(self, poi_ids: list[str]) -> dict[str, list[str]]:
        logger.info(f"Getting cities for poiIds {poi_ids}")
        query = """
            UNWIND $poiIds AS poiId
            MATCH (p:POI {poiId: poiId})
            WITH DISTINCT p.city AS city
            RETURN collect(city) AS cities
        """
        result = self.execute_query(query, poiIds=poi_ids)  # type: ignore[attr-defined]
        logger.debug(f"Result: {result}")
        return result[0] if result else {"cities": []}

    def get_city_route(self, cities: list[str]) -> list[list[float]]:
        logger.info("Creating route from city to city...")
        route: list[list[float]] = []
        for i in range(len(cities) - 1):
            part = self.get_route(cities[i], cities[i + 1])
            if route and part:
                part = part[1:]
            route.extend([item for item in part])
        logger.debug(f"Route: {route}")
        logger.info("Created route.")
        return route

    def get_route(self, start: str, dest: str) -> list[dict[str, float]]:
        query = """
            MATCH (s:City {cityId: $start})
            MATCH (t:City {cityId: $dest})
            CALL gds.shortestPath.dijkstra.stream(
                'city-road-graph',
                {
                    sourceNode: id(s),
                    targetNode: id(t),
                    relationshipWeightProperty: 'km'
                }
            )
            YIELD nodeIds

            RETURN [nodeId IN nodeIds |
                [
                    gds.util.asNode(nodeId).longitude,
                    gds.util.asNode(nodeId).latitude
                ]
            ] AS coords
        """
        result = self.execute_query(query, start=start, dest=dest)  # type: ignore[attr-defined]
        logger.debug(f"(Start/Dest) = Result: ({start}/{dest}) = {result}")
        return result[0]["coords"] if result else [{}]
