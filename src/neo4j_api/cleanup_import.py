"""module for cleanup after data import"""

from datetime import datetime, UTC
import json
from src.neo4j_api.status_handler import ProcessLock, get_status_file
import shutil

def remove_old_db_data(driver, current_import_version):
    query = """
    CALL apoc.periodic.iterate(
      "MATCH (n:Poi|Type) WHERE n.importVersion <> $import_version RETURN n",
      "DETACH DELETE n",
      {
        batchSize: 1000,
        parallel: false,
        params: {import_version: $import_version}
      }
    )
    YIELD batches, total, errorMessages, committedOperations
    RETURN batches, total, errorMessages, committedOperations;
"""
    with driver.driver.session() as session:
        result = session.run(query, import_version=current_import_version)
        record = result.single()
        committed = record["committedOperations"]
        errors = record["errorMessages"]

    return {
        "message": f"cleanup successfull: Remove old version data. Keeping only version {current_import_version}",
        "committed": committed,
        "errors": errors,
    }


def perform_cleanup_import(save_dir, zip_file_path, unzipped_data_path, extracted_data_path, driver, import_version):
    with ProcessLock(save_dir, "cleanup"):
        remove_old_db_data(driver, import_version)
        zip_file_path.unlink(missing_ok=True)
        shutil.rmtree(unzipped_data_path, ignore_errors=True)
        shutil.rmtree(extracted_data_path, ignore_errors=True)
        status = {
            "last_cleanup_utc": datetime.now(UTC).isoformat(),
        }
        with open(get_status_file(save_dir, "cleanup"), "w") as f:
            json.dump(status, fp=f)
        return status

