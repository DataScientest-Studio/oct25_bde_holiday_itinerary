from typing import Any, Dict, List, Literal

import numpy as np
from loguru import logger

from .city_poi import CityPois


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

    def get_city_pois(self, poi_ids: list[str]) -> list[CityPois]:
        logger.info(f"Getting cities for poiIds {poi_ids}")
        city_pois: list[CityPois] = []
        for poi_id in poi_ids:
            appended = False
            poi = self.get_poi(poi_id)  # type: ignore[attr-defined]
            if not (city := self.get_city(poi["city"])):
                city = self.get_nearest_city_by_coordinates(poi["latitude"], poi["longitude"])["city"]
            for city_poi in city_pois:
                if city_poi.append(city, poi):
                    appended = True
                    break
            if not appended:
                city_pois.append(CityPois(city, poi))
        logger.debug(f"Cities: {city_pois}")
        return city_pois

    def get_city_route(self, cities: list[CityPois]) -> list[list[float]]:
        logger.info("Creating route from city to city...")
        route: list[list[float]] = []
        for city in cities:
            route.append([city.city["longitude"], city.city["latitude"]])
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

    def get_city(self, city_id: str) -> dict[str, Any]:
        logger.info(f"Get city {city_id} from database.")
        query = """
        MATCH (c:City {cityId: $city_id})
        RETURN c
        LIMIT 1
        """
        city = self.execute_query(query, city_id=city_id)  # type: ignore[attr-defined]

        return city[0]["c"] if city else {}

    def get_cities(self) -> dict[str, Any]:
        logger.info("Get all cities from database.")
        query = """
        MATCH (n:City)
        RETURN n.name as name, n.population as population, n.latitude as latitude, n.longitude as longitude"""
        cities = self.execute_query(query)  # type: ignore[attr-defined]

        return {"cities": [c for c in cities] if cities else []}

    def get_nearest_city_by_coordinates(self, lat: float, lon: float) -> dict[str, Any]:
        logger.info(f"Get nearest city by coordinates (lat/lon):({lat}/{lon}).")
        query = """
        MATCH (c:City)
        WITH
            c,
            point({latitude: $latitude, longitude: $longitude}) as p,
            point({latitude: c.latitude, longitude: c.longitude}) as cp
        RETURN c as city, round(point.distance(p, cp)/1000, 2) as distance_km
        ORDER BY distance_km ASC
        LIMIT 1
        """
        result = self.execute_query(query, latitude=lat, longitude=lon)  # type: ignore[attr-defined]
        return result[0]

    def get_route_between_cities(self, start_city: str, end_city: str) -> List[Dict[str, Any]]:
        logger.info(f"Get route between cities {start_city} and {end_city}.")
        query = """
        MATCH (s:City {cityId: $start_city})
        MATCH (t:City {cityId: $end_city})

        CALL gds.shortestPath.dijkstra.stream('city-road-graph', {
            sourceNode: s,
            targetNode: t,
            relationshipWeightProperty: 'km'
        })
        YIELD totalCost, path
        WITH
            totalCost,
            relationships(path) AS roads
        UNWIND range(0, size(roads) - 1) AS i
        WITH
            totalCost,
            startNode(roads[i]).name AS From_City,
            endNode(roads[i]).name AS To_City,
            round(roads[i].cost, 2) AS Distance_km
        RETURN
            From_City,
            To_City,
            Distance_km
        """
        result = self.execute_query(query, start_city=start_city, end_city=end_city)  # type: ignore[attr-defined]
        return result

    def get_roundtrip(
        self, city_id: str, distance: float, distance_tol: float, max_hops: int, sort_distance: Literal["ASC", "DESC"]
    ) -> Dict[str, Any]:
        """quite limited round trip search"""
        query = f"""
        MATCH path = (start:City {{cityId: $city_id}}) - [:ROAD_TO*3..{max_hops}]-> (start)
        WHERE all(n IN nodes(path)[1..-1] WHERE single(m IN nodes(path) WHERE m = n))
        WITH path,
             reduce(total = 0, r IN relationships(path) | total + r.km) AS totalDistance
        WHERE $min_distance <= totalDistance <= $max_distance
        RETURN
            [node IN nodes(path) | node.cityId] AS cities_in_order,
            totalDistance,
            length(path) AS number_of_hops
        ORDER BY totalDistance {sort_distance}
        LIMIT 1;
        """
        result = self.execute_query(  # type: ignore[attr-defined]
            query,
            city_id=city_id,
            min_distance=distance - distance_tol,
            max_distance=distance + distance_tol,
        )
        return result[0]
