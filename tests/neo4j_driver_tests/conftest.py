from csv import DictReader
from os import environ
from pathlib import Path

import pytest
from neo4j import GraphDatabase

TEST_DATA_DIR = Path("tests/neo4j_driver_tests/data")


@pytest.fixture(scope="session")
def NEO4J_URI():
    neo4j_uri = "bolt://localhost:7687"
    environ["NEO4J_URI"] = neo4j_uri
    return neo4j_uri


@pytest.fixture(scope="session")
def NEO4J_USER():
    neo4j_user = "neo4j"
    environ["NEO4J_USER"] = neo4j_user
    return neo4j_user


@pytest.fixture(scope="session")
def NEO4J_PASSPHRASE():
    neo4j_passphrase = "neo4j-test"
    environ["NEO4J_PASSPHRASE"] = neo4j_passphrase
    return neo4j_passphrase


@pytest.fixture(scope="session")
def NEO4J_DATABASE():
    neo4j_database = "testdb"
    environ["NEO4J_DATABASE"] = neo4j_database
    return neo4j_database


@pytest.fixture(scope="function")
def database(NEO4J_URI, NEO4J_USER, NEO4J_PASSPHRASE, NEO4J_DATABASE):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSPHRASE))
    with driver.session(database="system") as session:
        session.run(f"CREATE DATABASE {NEO4J_DATABASE} IF NOT EXISTS")

    with driver.session(database=NEO4J_DATABASE) as session:
        with open(TEST_DATA_DIR / "paris.csv", newline="", encoding="utf-8") as csvfile:
            reader = DictReader(csvfile)
            for row in reader:
                types_list = [t.strip() for t in row["types"].split(",")] if row.get("types") else []
                session.run(
                    """
                    MERGE (poi:Poi {id: $id})
                    ON CREATE SET
                        poi.label = $label,
                        poi.comment = $comment,
                        poi.description = $description,
                        poi.types = $types,
                        poi.homepage = $homepage,
                        poi.city = $city,
                        poi.postal_code = $postal_code,
                        poi.street = $street,
                        poi.location = point({
                            latitude: $lat,
                            longitude: $lon
                        }),
                        poi.additional_information = $additional_information
                    """,
                    id=row.get("id"),
                    label=row.get("label"),
                    comment=row.get("comment"),
                    description=row.get("description"),
                    types=types_list,
                    homepage=row.get("homepage"),
                    city=row.get("city"),
                    postal_code=row.get("postal_code"),
                    street=row.get("street"),
                    lat=float(row["lat"]) if row.get("lat") else None,
                    lon=float(row["long"]) if row.get("long") else None,
                    additional_information=row.get("additional_information"),
                )

    yield

    with driver.session(database="system") as session:
        session.run(f"DROP DATABASE {NEO4J_DATABASE} IF EXISTS")
    driver.close()
