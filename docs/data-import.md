# Data Import from DATAtourisme

This document describes the automated pipeline used to import tourism data
from [DATAtourisme.fr](https://www.datatourisme.fr/) into a [Neo4j](https://neo4j.com/)
database, including orchestration, processing, and cleanup steps.

## Table of contents

- [Architecture Overview](#architecture-overview)
  - [Dependencies](#dependencies)
- [Workflow Steps](#workflow-steps)
  - [1. Trigger Download](#1-trigger-download)
  - [2. Wait for Download Completion](#2-wait-for-download-completion)
  - [3. Trigger Unzip](#3-trigger-unzip)
  - [4. Wait for Unzip](#4-wait-for-unzip)
  - [5. Trigger Extract Data](#5-trigger-extract-data)
  - [6. Wait for Extract](#6-wait-for-extract)
  - [7. Trigger Import Data](#7-trigger-import-data)
  - [8. Wait for Import](#8-wait-for-import)
  - [9. Trigger Cleanup](#9-trigger-cleanup)
  - [10. Wait for Cleanup](#10-wait-for-cleanup)
- [Configuration & Environment Variables](#configuration--environment-variables)
- [Status and Locks](#status-and-locks)
- [Spatial Indices and Relationships](#spatial-indices-and-relationships)
- [Manual Import (Advanced)](#manual-import-advanced)

## Architecture Overview

The data import is orchestrated by **Apache Airflow**, which triggers various stages
of the ETL process exposed through a **FastAPI** application (`neo4j_api`). The
data is processed and finally imported into **Neo4j**.

### Dependencies

All dependencies listed in this document are mandatory for the production environment.
Furthermore the dependencies listed in [README.md](../README.md) and [production.md](production.md)
are required. The exact dependency versions are managed via `pyproject.toml`
and the lock file.

- **[Apache Airflow](https://airflow.apache.org/)**\
  Orchestrates the data download and processing pipeline via scheduled DAGs
  (defined in `airflow/dags/data_download_trigger.py`).

## Workflow Steps

The following steps are executed sequentially for each import run.

### 1. Trigger Download

- **Endpoint**: `GET /data/trigger-download`
- **Description**: Authenticates with DATAtourisme, checks if new data is available
  based on the last generation date, and starts a background task to download the
  ZIP file.
- **Key File**: `src/neo4j_api/datatourisme_handler.py`

### 2. Wait for Download Completion

- Airflow polls `GET /data/download/status` until the status is `completed`.

### 3. Trigger Unzip

- **Endpoint**: `GET /data/trigger-unzip`
- **Description**: Unzips the downloaded archive into the designated save directory.
- **Key File**: `src/neo4j_api/data_upload_etl.py`

### 4. Wait for Unzip

- Airflow polls `GET /data/unzip/status` until `completed`.

### 5. Trigger Extract Data

- **Endpoint**: `GET /data/trigger-extract-data`
- **Description**: Processes the unzipped JSON files (via `index.json`), extracts
  Points of Interest (POIs) and their types, and generates CSV files formatted for
  Neo4j import.
- **Key Files**: `src/neo4j_api/data_upload_etl.py`, `src/data/make_dataset.py`
- **Generated CSVs**: `poi_nodes.csv`, `type_nodes.csv`, `poi_is_a_type_rels.csv`

### 6. Wait for Extract

- Airflow polls `GET /data/extract/status` until `completed`.

### 7. Trigger Import Data

- **Endpoint**: `GET /data/trigger-import-data`
- **Description**: Loads the generated CSVs into Neo4j using `LOAD CSV` and `apoc.periodic.iterate`.
  It also creates spatial indices and establishes relationships between POIs and
  Cities (`IS_IN` or `IS_NEARBY`).
- **Key File**: `src/neo4j_api/import_data.py`

### 8. Wait for Import

- Airflow polls `GET /data/import/status` until `completed`.

### 9. Trigger Cleanup

- **Endpoint**: `GET /data/trigger-import-cleanup`
- **Description**: Removes the temporary ZIP file and extracted folders. In the
  database, it deletes nodes from previous import versions to keep only the latest
  data.
- **Key File**: `src/neo4j_api/cleanup_import.py`

### 10. Wait for Cleanup

- Airflow polls `GET /data/cleanup/status` until `completed`.

## Configuration & Environment Variables

The import process uses the following environment variables, all defined in
`docker-compose.yaml` for the `neo4j_api` service.

| Variable                  | Description                                                                                                                       |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| `DATATOURISME_FEED`       | URL to the data flux (ZIP file).                                                                                                  |
| `DATATOURISME_LOGIN_URL`  | Login page for authentication.                                                                                                    |
| `DATATOURISME_EMAIL`      | User email for DATAtourisme.                                                                                                      |
| `DATATOURISME_PASSWORD`   | User password for DATAtourisme.                                                                                                   |
| `DATATOURISME_VERIFY_SSL` | (Optional) Whether to verify SSL certificates (default: `true`). Set to `false` if you encounter certificate verification errors. |
| `DATATOURISME_SAVE_DIR`   | Local directory to store downloaded/unzipped data.                                                                                |
| `DATATOURISME_IMPORT_DIR` | Directory where CSVs are generated (mounted to Neo4j).                                                                            |
| `LOG_LEVEL`               | Log level for the application (e.g. `DEBUG`, `INFO`, `WARNING`, `ERROR`). Defaults to `INFO` if not set.                          |
| `NEO4J_URI`               | URI for the Neo4j database.                                                                                                       |
| `NEO4J_USER`              | Username for Neo4j.                                                                                                               |
| `NEO4J_PASSPHRASE`        | Password for Neo4j.                                                                                                               |

## Status and Locks

To prevent concurrent execution of the same process, the system uses lock files:

- Lock files are named `{process}_in_progress.lock` (e.g., `download_in_progress.lock`).
- Status information for each step is persisted in JSON files: `last_{process}.json`
  (e.g., `last_download.json`).
- If a process is triggered while another is running, the API returns a `409 Conflict`.

## Spatial Indices and Relationships

During the import phase (`src/neo4j_api/import_data.py`), the following actions
are performed:

1. **Point Index**: Creates a spatial point for each POI and City.
2. **IS_IN Relationship**: Links a POI to a City if the city name matches.
3. **IS_NEARBY Relationship**: If a POI is not directly in a known City, it is
   linked to the nearest City within 100km, including the calculated distance.

## Manual Import (Advanced)

For development or recovery scenarios, datasets can be imported manually
using `neo4j-admin`.

This process includes:

- Converting DATAtourisme JSON data into Neo4j-compatible CSV files
- Importing nodes and relationships offline
- Creating spatial relationships (`IS_IN`, `IS_NEARBY`)

A complete step-by-step guide, including commands and Cypher scripts, is
available in\
**[`docs/development.md`](../docs/development.md)**.
