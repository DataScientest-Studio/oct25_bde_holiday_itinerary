import json
import uuid
from datetime import UTC, datetime
from typing import Any

from neo4j import Record, Result
from neo4j_driver import Neo4jDriver

from .status_handler import ProcessLock, get_status_file, get_status_file_content


class Import:
    import_version = str(uuid.uuid4())

    def __init__(self, driver: Neo4jDriver) -> None:
        self.driver = driver

    def execute_query(self, query: str, **kwargs: Any) -> Result:
        with self.driver.driver.session() as session:
            return session.run(query, import_version=self.import_version, **kwargs)

    def single_query(self, query: str, **kwargs: Any) -> Record:
        return self.execute_query(query, **kwargs).single()

    def summary_query(self, query: str, **kwargs: Any) -> Record:
        return self.execute_query(query, **kwargs).sonsume()


def import_types(driver, import_from_dir, import_version) -> dict:
    query = """
        LOAD CSV WITH HEADERS FROM $file AS row
        CALL (row) {
            MERGE (t:Type {id: row['typeId:ID(Type)']})
            SET t.name = row['typeId:ID(Type)'],
                t.importVersion = $import_version,
                t.importedAt = timestamp()
        } IN TRANSACTIONS OF 2000 ROWS
        """
    with driver.driver.session() as session:
        result = session.run(query, import_version=import_version, file=f"file:///{import_from_dir}/type_nodes.csv")
        summary = result.consume()
        counters = summary.counters
    return {
        "message": "import successfull: Types",
        "nodes_created": counters.nodes_created,
        "properties_set": counters.properties_set,
        "file": "type_nodes.csv",
    }


def import_pois(driver, import_from_dir, import_version) -> dict:
    poi_constraint = """
    CREATE CONSTRAINT poi_id IF NOT EXISTS
    FOR (p:POI) REQUIRE p.id IS UNIQUE;
    """

    query = """
    CALL apoc.periodic.iterate(
      "LOAD CSV WITH HEADERS FROM $file AS row RETURN row",
      "MERGE (t:POI {id: row['poiId:ID(POI)']})
       SET t.label = row.label,
           t.comment = row.comment,
           t.description = row.description,
           t.homepage = row.homepage,
           t.city = row.city,
           t.postal_code = row.postal_code,
           t.street = row.street,
           t.latitude = toFloat(row['latitude:FLOAT']),
           t.longitude = toFloat(row['longitude:FLOAT']),
           t.additional_information = row.additional_information,
           t.importVersion = $import_version,
           t.importedAt = timestamp()",

      {
        batchSize: 1000,
        parallel: false,
        params: {
            import_version: $import_version,
            file: $file
            }
      }
    )
    YIELD batches, total, errorMessages, committedOperations
    RETURN batches, total, errorMessages, committedOperations;
    """
    with driver.driver.session() as session:
        session.run(poi_constraint)

    with driver.driver.session() as session:
        result = session.run(query, import_version=import_version, file=f"file:///{import_from_dir}/poi_nodes.csv")
        record = result.single()
        committed = record["committedOperations"]
        errors = record["errorMessages"]
    return {
        "message": "import successfull: Import POI",
        "committed_operations": committed,
        "errors": errors,
        "file": "poi_nodes.csv",
    }


def import_poi_is_a_type_rels(driver, import_from_dir, import_version) -> dict:

    query = """
    CALL apoc.periodic.iterate(
      "LOAD CSV WITH HEADERS FROM $file AS row RETURN row",
      "MATCH (p:POI {id: row[':START_ID(POI)'], importVersion: $import_version})
       MATCH (t:Type {id: row[':END_ID(Type)'], importVersion: $import_version})
       MERGE (p) - [r:IS_A] -> (t)
       SET r.importVersion = $import_version",
      {
        batchSize: 1000,
        parallel: false,
        params: {
            import_version: $import_version,
            file: $file
            }
      }
    )
    YIELD batches, total, errorMessages, committedOperations
    RETURN batches, total, errorMessages, committedOperations;
    """

    with driver.driver.session() as session:
        result = session.run(
            query, import_version=import_version, file=f"file:///{import_from_dir}/poi_is_a_type_rels.csv"
        )
        record = result.single()
        committed = record["committedOperations"]
        errors = record["errorMessages"]
    return {
        "message": "import successfull: Import POI IS_A relationships",
        "committed_operations": committed,
        "errors": errors,
        "file": "poi_is_a_type_rels.csv",
    }


def prepare_point_index(driver, import_version):
    with driver.driver.session() as session:
        session.run(
            """
                    MATCH (n) WHERE (n:POI OR n:City) AND n.location IS NULL
                    SET n.location = point({latitude: n.latitude, longitude: n.longitude})
                """
        )
        # Create the Index
        session.run("CREATE POINT INDEX city_loc_idx IF NOT EXISTS FOR (c:City) ON (c.location)")


def set_is_in_rels(driver, import_version):
    query = """
    CALL apoc.periodic.iterate(
      "MATCH (p:POI {importVersion: $import_version}) WHERE p.city IS NOT NULL RETURN p",
      "MATCH (c:City {name: p.city})
       MERGE (p)-[r:IS_IN]->(c)
       SET r.importVersion = $import_version",
      {
        batchSize: 1000,
        parallel: true,
        params: { import_version: $import_version }
      }
    )
    YIELD batches, total, errorMessages, committedOperations
    RETURN batches, total, errorMessages, committedOperations;
    """
    with driver.driver.session() as session:
        result = session.run(query, import_version=import_version)
        record = result.single()
        committed = record["committedOperations"]
        errors = record["errorMessages"]
    return {
        "message": "import successfull: Create IS_IN relationships",
        "committed_operations": committed,
        "errors": errors,
    }


def set_is_nearby_rels(driver, import_version):
    query = """
        CALL apoc.periodic.iterate(
          "MATCH (p:POI {importVersion: $import_version})
           WHERE NOT (p)-[:IS_IN]->(:City) AND p.location IS NOT NULL
           RETURN p",
          "MATCH (c:City)
           WHERE point.distance(p.location, c.location) < 100000
           WITH p, c, point.distance(p.location, c.location) AS dist
           ORDER BY dist ASC
           WITH p, collect(c)[0] AS nearestCity, collect(dist)[0] AS shortestDist
           WHERE nearestCity IS NOT NULL
           MERGE (p)-[r:IS_NEARBY]->(nearestCity)
           SET r.import_version = $import_version,
               r.distance_km = round(shortestDist/1000.0, 2)",
          {
            batchSize: 1000,
            parallel: false,
            params: { import_version: $import_version }
          }
        )
        YIELD batches, total, errorMessages, committedOperations
        RETURN batches, total, errorMessages, committedOperations;
        """
    with driver.driver.session() as session:
        result = session.run(query, import_version=import_version)
        record = result.single()
        committed = record["committedOperations"]
        errors = record["errorMessages"]
    return {
        "message": "import successfull: Create IS_NEARBY relationships",
        "committed_operations": committed,
        "errors": errors,
    }


def perform_import_data(save_dir, driver, filename):
    with ProcessLock(save_dir, "import"):
        import_version = str(uuid.uuid4())
        status = {
            "last_import_utc": datetime.now(UTC).isoformat(),
            "import_version": import_version,
            "status": "started",
            "steps": {},
        }
        with open(get_status_file(save_dir, "import"), "w") as f:
            json.dump(status, fp=f)

        def update_status_step(step: dict = None, status: str = None):
            current = get_status_file_content(save_dir, "import")
            if step is not None:
                current["steps"] = current["steps"] | step
            if status is not None:
                current["status"] = status
            with open(get_status_file(save_dir, "import"), "w") as f:
                json.dump(current, fp=f)

        try:
            types_import_resp = import_types(driver, filename.name, import_version)
            update_status_step({"import types": types_import_resp})
            poi_import_resp = import_pois(driver, filename.name, import_version)
            update_status_step({"import pois": poi_import_resp})
            poi_is_a_type_rels_import_resp = import_poi_is_a_type_rels(driver, filename.name, import_version)
            update_status_step({"import poi is a type rels": poi_is_a_type_rels_import_resp})
            prepare_point_index(driver, import_version)
            poi_is_in_resp = set_is_in_rels(driver, import_version)
            update_status_step({"set poi IS_IN rels": poi_is_in_resp})
            poi_is_nearby_resp = set_is_nearby_rels(driver, import_version)
            update_status_step({"set poi IS_NEARBY rels": poi_is_nearby_resp})
        except Exception as e:
            status = {
                "last_import_utc": datetime.now(UTC).isoformat(),
                "filename": str(filename),
                "status": "failed",
                "error": str(e),
            }
            with open(get_status_file(save_dir, "import"), "w") as f:
                json.dump(status, fp=f)

        update_status_step(status="finished")
