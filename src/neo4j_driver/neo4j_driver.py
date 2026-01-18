from typing import Any, Dict, List, Literal

from .base import Base
from .city import City
from .tsp import TSP


class Neo4jDriver(Base, City, TSP):
    def __init__(self) -> None:
        self.init_driver()

    def get_poi(self, poi_id: str) -> dict[Any, Any]:
        query = """
            MATCH (p:POI {poiId: $poi_id})
            RETURN p
            LIMIT 1
        """
        poi = self.execute_query(query, poi_id=poi_id)
        return poi[0]["p"] if poi else {}

    def get_filtered_pois(self, locations: list[str] | None, types: list[str] | None, radius: int) -> dict[str, Any]:

        locations = self.normalize_param(locations)
        types = self.normalize_param(types)

        kwargs: dict[str, Any] = {
            "locations": locations or None,
            "types": types or None,
            "radius": radius,
        }

        if radius > 0:
            query = """
                CALL {
                    MATCH (n:POI)-[:IS_A]->(tFilter:POIType)
                    WHERE ($locations IS NULL OR n.city IN $locations)
                        AND ($types IS NULL OR tFilter.typeId IN $types)
                    RETURN n

                    UNION

                    MATCH (c:City)
                    WHERE c.name IN $locations
                    WITH point({latitude: c.latitude, longitude: c.longitude}) AS cityPoint
                    MATCH (n:POI)-[:IS_A]->(tFilter:POIType)
                    WHERE point.distance(
                            cityPoint,
                            point({latitude: n.latitude, longitude: n.longitude})
                          ) <= $radius
                        AND ($types IS NULL OR tFilter.typeId IN $types)
                    RETURN n
                }
                WITH DISTINCT n
                ORDER BY n.city, n.label
                MATCH (n)-[:IS_A]->(tAll:POIType)
                WITH n, collect(DISTINCT tAll.typeId) AS poiTypes
                RETURN collect(n { .*, types: apoc.text.join(poiTypes, ", ") }) AS pois
            """
        else:
            query = """
                MATCH (n:POI)-[:IS_A]->(tFilter:POIType)
                WHERE ($locations IS NULL OR n.city IN $locations)
                    AND ($types IS NULL OR tFilter.typeId IN $types)
                MATCH (n)-[:IS_A]->(tAll:POIType)
                WITH n, collect(DISTINCT tAll.typeId) AS poiTypes
                RETURN collect(n { .*, types: apoc.text.join(poiTypes, ", ") }) AS pois
            """

        result = self.execute_query(query, **kwargs)
        return result[0] if result else []

    def normalize_param(self, values: list[str] | None) -> list[str] | None:
        if not values:
            return None
        cleaned = [v.strip() for v in values if v and v.strip()]
        return cleaned or None

    def get_types(self) -> dict[str, Any]:
        query = "MATCH (t:Type) RETURN t.typeId AS typeId"
        types = self.execute_query(query)
        return {"types": [t["typeId"] for t in types] if types else []}

    def get_city(self, city_id: str) -> dict[str, Any]:
        query = """
        MATCH (c:City {cityId: $city_id})
        RETURN c
        LIMIT 1
        """
        city = self.execute_query(query, city_id=city_id)
        return city[0]["c"] if city else {}

    def get_cities(self) -> dict[str, Any]:
        query = """
        MATCH (n:City)
        RETURN n.name as name, n.population as population, n.latitude as latitude, n.longitude as longitude"""
        cities = self.execute_query(query)
        return {"cities": [c for c in cities] if cities else []}

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

    def get_nearby_points(self, poi_id: str, radius: float) -> dict[str, list[dict[Any, Any]]]:
        query = """
            MATCH (p1:POI {poiId: $poi_id})
            MATCH (p2:POI)
            WHERE p1 <> p2
                AND point.distance(p1.location, p2.location) <= $radius
            RETURN
                p2.poiId AS poiId,
                p2.label AS label,
                p2.comment AS comment,
                p2.description AS description,
                p2.types AS types,
                p2.homepage AS homepage,
                p2.city AS city,
                p2.postal_code AS postal_code,
                p2.street AS street,
                p2.location.latitude AS lat,
                p2.location.longitude AS lon,
                p2.additional_information AS additional_information
        """
        records = self.execute_query(query, poi_id=poi_id, radius=radius)
        return {"nearby": records if records else []}
