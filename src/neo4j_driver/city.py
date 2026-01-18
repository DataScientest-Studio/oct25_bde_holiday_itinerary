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
