from os import environ
from signal import SIGINT, SIGTERM, signal
from sys import exit
from typing import Any

from neo4j import GraphDatabase, Record


class Neo4jDriver:
    def __init__(self) -> None:
        uri = environ.get("NEO4J_URI", "bolt://localhost:7687")
        username = environ.get("NEO4J_USER", "neo4j")
        passphrase = environ.get("NEO4J_PASSPHRASE", "")
        self.driver = GraphDatabase.driver(uri, auth=(username, passphrase))

        signal(SIGINT, self.handle_exit_signal)
        signal(SIGTERM, self.handle_exit_signal)

    def execute_query(self, query: str, **kwargs: Any) -> list[Record] | None:
        with self.driver.session() as session:
            records = session.run(query, kwargs)
            return [record for record in records]

    def get_nearby_points(self, poi_id: str, radius: float) -> list[Record] | None:
        query = """
            MATCH (p1:Poi {id: $poi_id})
            MATCH (p2:Poi)
            WHERE p1 <> p2
              AND distance(p1.location, p2.location) <= $radius
            RETURN
                p2.id AS id,
                p2.label AS label,
                p2.location.latitude AS lat,
                p2.location.longitude AS lon
        """
        if records := self.execute_query(query, poi_id=poi_id, radius=radius):
            return [dict(record) for record in records]
        return None

    def close(self) -> None:
        if self.driver:
            self.driver.close()

    def handle_exit_signal(self, signal_received: int, frame: Any) -> None:
        print(f"\nSignal {signal_received} received. Closing Neo4j driver...")
        self.close()
        exit(signal_received)
