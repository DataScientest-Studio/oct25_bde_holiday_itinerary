from os import environ

from neo4j import GraphDatabase

uri = environ.get("NEO4J_URI", "bolt://localhost:7687")
username = environ.get("NEO4J_USER", "neo4j")
passphrase = environ.get("NEO4J_PASSPHRASE", "")


driver = GraphDatabase.driver(uri, auth=(username, passphrase))
