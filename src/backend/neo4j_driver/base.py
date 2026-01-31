import sys
import time
from os import environ
from signal import SIGINT, SIGTERM, signal
from typing import Any

from loguru import logger
from neo4j import GraphDatabase
from neo4j.exceptions import AuthError, ServiceUnavailable


class Base:
    def init_driver(self) -> None:
        logger.info("Initializing Neo4jDriver...")
        uri = environ.get("NEO4J_URI", "bolt://neo4j:7687")
        username = environ.get("NEO4J_USER", "neo4j")
        passphrase = environ.get("NEO4J_PASSPHRASE", "")
        self.driver = GraphDatabase.driver(uri, auth=(username, passphrase))
        logger.info("Setup GraphDatabase driver.")

        signal(SIGINT, self.handle_exit_signal)
        signal(SIGTERM, self.handle_exit_signal)

        try:
            self.wait_for_neo4j()
            self.init_custom_gds_algorithm()
            logger.success("Intitalized Neo4jDriver.")
        except RuntimeError as err:
            logger.error(err)
            logger.info("Could not initialize Neo4jDriver. Exit!")
            sys.exit(1)

    def wait_for_neo4j(self, timeout=600):
        logger.info("Waiting until neo4j database started.")
        start = time.time()

        while True:
            try:
                with self.driver.session() as session:
                    session.run("RETURN 1").consume()
                logger.info("Neo4j is ready")
                return
            except (ServiceUnavailable, AuthError) as e:
                if time.time() - start > timeout:
                    raise RuntimeError("Neo4j did not start in time") from e
                logger.info("Waiting for Neo4j...")
                time.sleep(10)
                logger.debug(f"Time until termination {timeout-(time.time() - start)}s.")

    def init_custom_gds_algorithm(self) -> None:
        logger.info("Initialize custom algorithms.")
        query = """
            CALL gds.graph.project(
                'city-road-graph',
                'City',
                {
                    ROAD_TO: {
                        type: 'ROAD_TO',
                        orientation: 'UNDIRECTED',
                        properties: ['km']
                    }
                }
            )
        """
        self.execute_query(query)
        logger.success("Initialized algorithms.")

    def execute_query(self, query: str, **kwargs: Any) -> list[dict[Any, Any]] | None:
        logger.info("Executing query.")
        logger.debug(f"Query: {query}\nKwargs:{kwargs}.")
        with self.driver.session() as session:
            records = session.run(query, **kwargs)
            return [record.data() for record in records]

    def close(self) -> None:
        logger.info("Closing neo4j ...")
        if self.driver:
            self.driver.close()
            logger.success("Closed neo4j driver.")

    def handle_exit_signal(self, signal_received: int, frame: Any) -> None:
        logger.info(f"\nSignal {signal_received} received. Closing Neo4j driver...")
        self.close()
        exit(signal_received)
