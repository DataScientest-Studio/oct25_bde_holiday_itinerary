from os import environ
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
