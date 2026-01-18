from typing import Any, Dict, List, Literal

from .base import Base
from .city import City
from .poi import POI
from .tsp import TSP


class Neo4jDriver(Base, City, POI, TSP):
    def __init__(self) -> None:
        self.init_driver()

    def get_types(self) -> dict[str, Any]:
        query = "MATCH (t:Type) RETURN t.typeId AS typeId"
        types = self.execute_query(query)
        return {"types": [t["typeId"] for t in types] if types else []}

    def get_poi_for_city(self, city_id: str, categories: List | None = None) -> List[dict[str, Any]]:
        query = """
        MATCH (c:City {cityId: $city_id}) <- [r:IS_IN] - (p:POI) - [is_a:IS_A] -> (t:POIType)
        WHERE $categories IS NULL or t.typeId in $categories
        RETURN p, collect(distinct t.typeId) as types
        """
        pois = self.execute_query(query, city_id=city_id, categories=categories)
        return [p["p"] | {"types": p["types"]} for p in pois] if pois else [{}]

    def get_poi_near_city(self, city_id: str, categories: List | None = None) -> List[dict[str, Any]]:
        query = """
        MATCH (c:City {cityId: $city_id}) <- [r:IS_NEARBY] - (p:POI) - [is_a:IS_A] -> (t:POIType)
        WHERE $categories IS NULL or t.typeId in $categories
        RETURN p, r.km as distance_km, collect(distinct t.typeId) as types
        ORDER BY distance_km ASC
        """
        pois = self.execute_query(query, city_id=city_id, categories=categories)
        return [p["p"] | {"distance_km": p["distance_km"], "types": p["types"]} for p in pois] if pois else [{}]

    def get_nearest_city_by_coordinates(self, lat: float, lon: float) -> dict[str, Any]:
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
        result = self.execute_query(query, latitude=lat, longitude=lon)
        return result[0]

    def get_poi_types_for_city(self, city_id: str, categories: List | None = None) -> List[str]:
        query = """
        MATCH (c:City {cityId: $city_id}) <- [r:IS_IN] - (p:POI) - [is_a:IS_A] -> (t:POIType)
        RETURN collect(distinct t.typeId) as types
        """
        result = self.execute_query(query, city_id=city_id)
        return result[0]["types"]

    def get_route_between_cities(self, start_city: str, end_city: str) -> List[Dict[str, Any]]:
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
        result = self.execute_query(query, start_city=start_city, end_city=end_city)
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
        result = self.execute_query(
            query,
            city_id=city_id,
            min_distance=distance - distance_tol,
            max_distance=distance + distance_tol,
        )
        return result[0]
