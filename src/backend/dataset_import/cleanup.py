import json
import shutil
from datetime import UTC, datetime
from pathlib import Path

from neo4j_driver.neo4j_driver import Neo4jDriver

from .status_handler import ProcessLock, get_status_file

CLEANUP_QUERY = """
CALL apoc.periodic.iterate(
  "MATCH (n:POI|Type) WHERE n.importVersion <> $import_version RETURN n",
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


def remove_old_db_data(driver: Neo4jDriver, import_version: str) -> dict:
    with driver.driver.session() as session:
        record = session.run(CLEANUP_QUERY, import_version=import_version).single()

    return {
        "message": ("Cleanup successful: removed old version data. " f"Keeping only version {import_version}"),
        "committed": record["committedOperations"] if record else 0,
        "errors": record["errorMessages"] if record else [],
    }


def perform_cleanup_import(
    save_dir: Path,
    zip_file_path: Path,
    unzipped_data_path: Path,
    extracted_data_path: Path,
    driver: Neo4jDriver,
    import_version: str,
) -> dict:
    """Run database and filesystem cleanup after an import."""
    with ProcessLock(save_dir, "cleanup"):
        remove_old_db_data(driver, import_version)
        cleanup_files(zip_file_path, unzipped_data_path, extracted_data_path)
        return write_cleanup_status(save_dir)


def cleanup_files(zip_file_path: Path, unzipped_data_path: Path, extracted_data_path: Path) -> None:
    """Remove temporary files and directories created during import."""
    zip_file_path.unlink(missing_ok=True)
    shutil.rmtree(unzipped_data_path, ignore_errors=True)
    shutil.rmtree(extracted_data_path, ignore_errors=True)


def write_cleanup_status(save_dir: Path) -> dict:
    """Persist cleanup metadata to the status file."""
    status = {"last_cleanup_utc": datetime.now(UTC).isoformat()}
    status_file = get_status_file(save_dir, "cleanup")

    with open(status_file, "w") as f:
        json.dump(status, f)

    return status
