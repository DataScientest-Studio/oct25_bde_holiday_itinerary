from os import environ
from signal import SIGINT, SIGTERM, signal
from sys import exit
from typing import Any, Dict, List, Literal

import numpy as np
from neo4j import GraphDatabase
from python_tsp.exact import solve_tsp_dynamic_programming


class Neo4jDriver:
    def __init__(self) -> None:
        uri = environ.get("NEO4J_URI", "bolt://neo4j:7687")
        username = environ.get("NEO4J_USER", "neo4j")
        passphrase = environ.get("NEO4J_PASSPHRASE", "")
        self.driver = GraphDatabase.driver(uri, auth=(username, passphrase))

        signal(SIGINT, self.handle_exit_signal)
        signal(SIGTERM, self.handle_exit_signal)

    def execute_query(self, query: str, **kwargs: Any) -> list[dict[Any, Any]] | None:
        with self.driver.session() as session:
            records = session.run(query, **kwargs)
            return [record.data() for record in records]

    def get_poi(self, poi_id: str) -> dict[Any, Any]:
        query = """
            MATCH (p:POI {poiId: $poi_id})
            RETURN p
            LIMIT 1
        """
        poi = self.execute_query(query, poi_id=poi_id)
        return poi[0]["p"] if poi else {}

    def get_filtered_pois(self, locations: list[str], types: list[str]) -> dict[str, Any]:
        query = "MATCH (n:POI) "
        conditions = []
        kwargs = {}

        print(locations)

        locations = [s for s in locations if s.strip()]
        types = [s for s in types if s.strip()]

        def get_conditions(filter: list[str], name: str):
            if filter:
                conditions.append(f"n.city IN ${name}")
                kwargs[name] = filter

        get_conditions(locations, "locations")
        get_conditions(types, "types")
        if conditions:
            query += "WHERE " + " AND ".join(conditions) + " "
        query += "RETURN collect(properties(n)) AS pois"

        result = self.execute_query(query, **kwargs)
        return result[0] if result else []  # type: ignore[return-value]

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
        query = "MATCH (n:City) RETURN n.cityId as Id, n.latitude as lat, n.longitude as lon"
        cities = self.execute_query(query)
        return {"cities": [c["cityId"] for c in cities] if cities else []}

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
            MATCH (p1:Poi {id: $poi_id})
            MATCH (p2:Poi)
            WHERE p1 <> p2
                AND point.distance(p1.location, p2.location) <= $radius
            RETURN
                p2.id AS id,
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

    def calculate_distance_between_two_nodes(self, poi1_id: str, poi2_id: str) -> float:
        query = """
            MATCH(p1:Poi {id: $poi1_id})
            MATCH(p2:Poi {id: $poi2_id})
            RETURN point.distance(p2.location, p1.location) AS distance
        """
        if result := self.execute_query(query, poi1_id=poi1_id, poi2_id=poi2_id):
            return result[0]["distance"]  # type: ignore[no-any-return]
        # TODO: handle not existing node
        return np.inf  # type: ignore[no-any-return]

    def create_weight_matrix(self, poi_ids: list[str]) -> np.ndarray[Any, Any]:
        n = len(poi_ids)
        weights: list[list[float]] = np.full((n, n), np.inf)
        for i in range(0, n):
            for j in range(0, n):
                if i == j:
                    continue
                weights[i][j] = self.calculate_distance_between_two_nodes(poi1_id=poi_ids[i], poi2_id=poi_ids[j])
        return weights

    def calculate_tsp(self, weights: np.ndarray[Any, Any], poi_ids: list[str]) -> dict[str, list[str] | float]:
        permutation, distance = solve_tsp_dynamic_programming(weights)
        return {"poi_order": [poi_ids[i] for i in permutation], "total_distance": distance}

    def calculate_shortest_path_no_return(self, poi_ids: list[str]) -> dict[str, list[str] | float]:
        weights = self.create_weight_matrix(poi_ids)
        weights[:, 0] = 0
        return self.calculate_tsp(weights, poi_ids)

    def calculate_shortest_path_fixed_dest(self, dest: str, poi_ids: list[str]) -> dict[str, list[str] | float]:
        poi_ids.remove(dest)
        poi_ids.insert(0, dest)
        tsp_result = self.calculate_shortest_path_no_return(poi_ids)
        tsp_result["poi_order"] = list(reversed(tsp_result["poi_order"]))  # type: ignore[arg-type]
        return tsp_result

    def calculate_shortest_round_tour(self, poi_ids: list[str]) -> dict[str, list[str] | float]:
        weights = self.create_weight_matrix(poi_ids)
        return self.calculate_tsp(weights, poi_ids)

    def shortest_path_between_all_nodes_with_fixed_start_and_fixed_end(
        self, poi_ids: list[str], end: str
    ) -> dict[str, list[str] | float]:
        # Does not work. Never will.
        poi_ids.remove(end)
        weights_to_end = [self.calculate_distance_between_two_nodes(poi1_id=end, poi2_id=node) for node in poi_ids]
        total_distance = np.inf
        for _ in poi_ids:
            weights = self.create_weight_matrix(poi_ids)
            permutation, distance = solve_tsp_dynamic_programming(weights)
            if distance + weights_to_end[permutation[-1]] < total_distance:
                total_distance = distance + weights_to_end
                # Need to modify value of weight smart. But how. Probably own algorithm.

        return self.calculate_tsp(weights, poi_ids)

    def create_edges(self, poi_ids: list[str]) -> None:
        query = """
            MATCH (p1:Poi), (p2:Poi)
            WHERE p1.id <> p2.id
                AND p1.id IN $poi_ids
                AND p2.id IN $poi_ids
            MERGE (p1)-[edge:CONNECTED]->(p2)
            SET edge.distance = point.distance(p1.location, p2.location)
        """
        self.execute_query(query, poi_ids=poi_ids)

    def delete_edges(self, poi_ids: list[str]) -> None:
        query = """
            MATCH (p1:Poi)-[edge:CONNECTED]->(p2:Poi)
            WHERE p1.id IN $poi_ids AND p2.id IN $poi_ids
            DELETE edge
        """
        self.execute_query(query, poi_ids=poi_ids)

    def calculate_shortest_path_from_start_to_dest(self, poi_ids: list[str]) -> dict[str, list[str] | float]:
        try:
            start = poi_ids[0]
            end = poi_ids[-1]
            self.create_edges(poi_ids)
            query = """
                MATCH (start:Poi {id: $start})
                MATCH (end:Poi {id: $end})
                CALL apoc.algo.dijkstra(start, end, 'CONNECTED>', 'distance') YIELD path, weight
                RETURN path, weight
            """
            if result := self.execute_query(query, start=start, end=end):
                poi_order = []
                for node in result[0]["path"]:
                    if isinstance(node, dict):
                        poi_order.append(node["id"])
                return {"poi_order": poi_order, "total_distance": result[0]["weight"]}
            return {"poi_order": [], "total_distance": 0.0}

        finally:
            self.delete_edges(poi_ids)

    def close(self) -> None:
        if self.driver:
            self.driver.close()

    def handle_exit_signal(self, signal_received: int, frame: Any) -> None:
        print(f"\nSignal {signal_received} received. Closing Neo4j driver...")
        self.close()
        exit(signal_received)
