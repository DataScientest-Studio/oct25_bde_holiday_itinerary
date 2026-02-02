import sys
import time
from os import environ
from signal import SIGINT, SIGTERM, signal
from typing import Any

from loguru import logger
from neo4j import GraphDatabase


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
            logger.success("Intitalized Neo4jDriver.")
        except RuntimeError as err:
            logger.error(err)
            logger.info("Could not initialize Neo4jDriver. Exit!")
            sys.exit(1)

    def wait_for_neo4j(self, timeout=600):
        logger.info("Waiting until neo4j database is ONLINE...")
        start = time.time()

        while True:
            try:
                with self.driver.session(database="system") as session:
                    result = session.run(
                        """
                        SHOW DATABASE neo4j
                        YIELD currentStatus
                        WHERE currentStatus = 'online'
                        RETURN 1
                    """
                    )
                    if result.single():
                        logger.success("Neo4j database is ONLINE")
                        return
            except Exception:
                pass

            if time.time() - start > timeout:
                raise RuntimeError("Neo4j database did not become online in time")

            logger.debug(f"Time until termination {timeout-(time.time() - start)}s.")
            time.sleep(10)

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
