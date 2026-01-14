# Data Import from DATAtourisme.fr

This document describes the process of importing tourism data from [DATAtourisme.fr](https://www.datatourisme.fr/) into the Neo4j database.

## Architecture Overview

The data import is orchestrated by **Apache Airflow**, which triggers various stages of the ETL process exposed through a **FastAPI** application (`neo4j_api`). The data is processed and finally imported into **Neo4j**.

- **Airflow DAG**: `download-trigger` (defined in `airflow/dags/data_download_trigger.py`)
- **FastAPI Endpoints**: Defined in `src/neo4j_api/routes/data_update.py`
- **Database**: Neo4j

## Workflow Steps

The import process consists of several sequential steps, each triggered by Airflow and handled by the API.

### 1. Trigger Download
- **Endpoint**: `GET /data/trigger-download`
- **Description**: Authenticates with DATAtourisme, checks if new data is available based on the last generation date, and starts a background task to download the ZIP file.
- **Key File**: `src/neo4j_api/datatourisme_handler.py`

### 2. Wait for Download
- Airflow polls `GET /data/download/status` until the status is `completed`.

### 3. Trigger Unzip
- **Endpoint**: `GET /data/trigger-unzip`
- **Description**: Unzips the downloaded archive into the designated save directory.
- **Key File**: `src/neo4j_api/data_upload_etl.py`

### 4. Wait for Unzip
- Airflow polls `GET /data/unzip/status` until `completed`.

### 5. Trigger Extract Data
- **Endpoint**: `GET /data/trigger-extract-data`
- **Description**: Processes the unzipped JSON files (via `index.json`), extracts Points of Interest (POIs) and their types, and generates CSV files formatted for Neo4j import.
- **Key Files**: `src/neo4j_api/data_upload_etl.py`, `src/data/make_dataset.py`
- **Generated CSVs**: `poi_nodes.csv`, `type_nodes.csv`, `poi_is_a_type_rels.csv`

### 6. Wait for Extract
- Airflow polls `GET /data/extract/status` until `completed`.

### 7. Trigger Import Data
- **Endpoint**: `GET /data/trigger-import-data`
- **Description**: Loads the generated CSVs into Neo4j using `LOAD CSV` and `apoc.periodic.iterate`. It also creates spatial indices and establishes relationships between POIs and Cities (`IS_IN` or `IS_NEARBY`).
- **Key File**: `src/neo4j_api/import_data.py`

### 8. Wait for Import
- Airflow polls `GET /data/import/status` until `completed`.

### 9. Trigger Cleanup
- **Endpoint**: `GET /data/trigger-import-cleanup`
- **Description**: Removes the temporary ZIP file and extracted folders. In the database, it deletes nodes from previous import versions to keep only the latest data.
- **Key File**: `src/neo4j_api/cleanup_import.py`

### 10. Wait for Cleanup
- Airflow polls `GET /data/cleanup/status` until `completed`.

## Configuration & Environment Variables

The import process requires the following environment variables (configured in `docker-compose.yaml` for the `neo4j_api` service):

| Variable | Description |
| --- | --- |
| `DATATOURISME_FEED` | URL to the data flux (ZIP file). |
| `DATATOURISME_LOGIN_URL` | Login page for authentication. |
| `DATATOURISME_EMAIL` | User email for DATAtourisme. |
| `DATATOURISME_PASSWORD` | User password for DATAtourisme. |
| `DATATOURISME_SAVE_DIR` | Local directory to store downloaded/unzipped data. |
| `DATATOURISME_IMPORT_DIR` | Directory where CSVs are generated (mounted to Neo4j). |
| `NEO4J_URI` | URI for the Neo4j database. |
| `NEO4J_USER` | Username for Neo4j. |
| `NEO4J_PASSPHRASE` | Password for Neo4j. |

## Status and Locks

To prevent concurrent execution of the same process, the system uses lock files:
- Lock files are named `{process}_in_progress.lock` (e.g., `download_in_progress.lock`).
- Status information for each step is persisted in JSON files: `last_{process}.json` (e.g., `last_download.json`).
- If a process is triggered while another is running, the API returns a `409 Conflict`.

## Spatial Indices and Relationships

During the import phase (`src/neo4j_api/import_data.py`), the following actions are performed:
1. **Point Index**: Creates a spatial point for each POI and City.
2. **IS_IN Relationship**: Links a POI to a City if the city name matches.
3. **IS_NEARBY Relationship**: If a POI is not directly in a known City, it is linked to the nearest City within 100km, including the calculated distance.
