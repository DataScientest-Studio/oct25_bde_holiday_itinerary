from os import environ
from signal import SIGINT, SIGTERM, signal
from sys import exit
from typing import Any

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
            MATCH (p:Poi {id: $poi_id})
            RETURN
                p.id AS id,
                p.comment AS comment,
                p.description AS description,
                p.types AS types,
                p.homepage AS homepage,
                p.city AS city,
                p.postal_code AS postal_code,
                p.street AS street,
                p.location.latitude AS lat,
                p.location.longitude AS lon,
                p.additional_information AS additional_information
            LIMIT 1
        """
        poi = self.execute_query(query, poi_id=poi_id)
        return poi[0] if poi else {}

    def get_nearby_points(self, poi_id: str, radius: float) -> dict[str, list[dict[Any, Any]]]:
        query = """
            MATCH (p1:Poi {id: $poi_id})
            MATCH (p2:Poi)
            WHERE p1 <> p2
              AND point.distance(p1.location, p2.location) <= $radius
            RETURN
                p2.id AS id,
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

    def shortest_path_between_all_nodes_with_fixed_start(self, poi_ids: list[str]) -> dict[str, list[str] | float]:
        weights = self.create_weight_matrix(poi_ids)
        weights[:, 0] = 0
        return self.calculate_tsp(weights, poi_ids)

    def shortest_path_between_all_nodes_with_fixed_end(
        self, poi_ids: list[str], end: str
    ) -> dict[str, list[str] | float]:
        poi_ids.remove(end)
        poi_ids.insert(0, end)
        tsp_result = self.shortest_path_between_all_nodes_with_fixed_start(poi_ids)
        tsp_result["poi_order"] = list(reversed(tsp_result["poi_order"]))  # type: ignore[arg-type]
        return tsp_result

    def shortest_round_tour_visiting_all_nodes(self, poi_ids: list[str]) -> dict[str, list[str] | float]:
        weights = self.create_weight_matrix(poi_ids)
        return self.calculate_tsp(weights, poi_ids)

    def calculate_shortest_path_with_fixed_start_and_fixed_end(
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

    def close(self) -> None:
        if self.driver:
            self.driver.close()

    def handle_exit_signal(self, signal_received: int, frame: Any) -> None:
        print(f"\nSignal {signal_received} received. Closing Neo4j driver...")
        self.close()
        exit(signal_received)
