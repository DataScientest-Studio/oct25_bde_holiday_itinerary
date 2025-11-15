from os import environ
from signal import SIGINT, SIGTERM, signal
from sys import exit
from typing import Any

from neo4j import GraphDatabase, Record

uri = environ.get("NEO4J_URI", "bolt://localhost:7687")
username = environ.get("NEO4J_USER", "neo4j")
passphrase = environ.get("NEO4J_PASSPHRASE", "")


driver = GraphDatabase.driver(uri, auth=(username, passphrase))


def execute_query(query: str, **kwargs: dict[Any, Any]) -> list[Record] | None:
    with driver.session() as session:
        records = session.run(query, kwargs)
        return [record for record in records]


def close_driver() -> None:
    if driver:
        driver.close()


def handle_exit_signal(signal_received: int, frame: Any) -> None:
    print(f"\nSignal {signal_received} received. Closing Neo4j driver...")
    close_driver()
    exit(signal_received)


signal(SIGINT, handle_exit_signal)
signal(SIGTERM, handle_exit_signal)
