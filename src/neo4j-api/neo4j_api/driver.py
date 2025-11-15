from os import environ
from typing import Any

from neo4j import GraphDatabase

uri = environ.get("NEO4J_URI", "bolt://localhost:7687")
username = environ.get("NEO4J_USER", "neo4j")
passphrase = environ.get("NEO4J_PASSPHRASE", "")


driver = GraphDatabase.driver(uri, auth=(username, passphrase))


def execute_query(query: str, **kwargs: dict[Any, Any]) -> list[Any] | None:
    with driver.session() as session:
        result = session.run(query, kwargs)
        return [record for record in result]
