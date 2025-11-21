from csv import DictReader
from os import environ
from pathlib import Path

import pytest
from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "test"
TEST_DB = "testdb"
TEST_DATA_DIR = Path("tests/neo4j_driver_tests/data")

environ["NEO4J_URI"] = NEO4J_URI
environ["NEO4J_USER"] = NEO4J_USER
environ["NEO4J_PASSPHRASE"] = NEO4J_PASSWORD


@pytest.fixture(scope="function")
def database():
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    with driver.session(database="system") as session:
        session.run(f"CREATE DATABASE {TEST_DB} IF NOT EXISTS")

    with driver.session(database=TEST_DB) as session:
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

    yield TEST_DB

    with driver.session(database="system") as session:
        session.run(f"DROP DATABASE {TEST_DB} IF EXISTS")
    driver.close()
