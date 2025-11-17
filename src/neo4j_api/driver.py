from os import environ
from signal import SIGINT, SIGTERM, signal
from sys import exit
from typing import Any

from neo4j import GraphDatabase


class Neo4jDriver:
    def __init__(self) -> None:
        uri = environ.get("NEO4J_URI", "bolt://localhost:7687")
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
              AND distance(p1.location, p2.location) <= $radius
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

    def create_edges(self, poi_ids: list[str]) -> None:
        query = """
            MATCH (p1:Poi), (p2:Poi)
            WHERE p1.id < p2.id
              AND p1.id IN $poi_ids
              AND p2.id IN $poi_ids
            MERGE (p1)-[edge:CONNECTED]->(p2)
            ON CREATE SET edge.distance = distance(p1.location, p2.location)
        """
        self.execute_query(query, poi_ids=poi_ids)

    def delete_edges(self, poi_ids: list[str]) -> None:
        query = """
            MATCH (p1:Poi)-[edge:CONNECTED]->(p2:Poi)
            WHERE p1.id IN $poi_ids AND p2.id IN $poi_ids
            DELETE edge
        """
        self.execute_query(query, poi_ids=poi_ids)

    def calculate_shortest_path(self, poi_ids: list[str]) -> dict[str, list[str] | float] | None:
        try:
            self.create_edges(poi_ids)
            query = """
                CALL apoc.algo.travelingSalesman($poi_ids, 'CONNECTED', 'distance')
                YIELD path, weight
                RETURN [node IN nodes(path) | node.id] AS poi_order, weight AS total_distance
            """
            if records := self.execute_query(query, poi_ids=poi_ids):
                return {"poi_order": records[0]["poi_order"], "total_distance": records[0]["total_distance"]}
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
