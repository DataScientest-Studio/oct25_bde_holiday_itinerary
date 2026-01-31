# Backend Architecture

The backend is responsible for data ingestion, processing, and graph-based
routing logic. It exposes a REST API used by the frontend and orchestrates the
import of external tourism data into Neo4j.

The system is split into two main components: a **FastAPI service** that handles
HTTP requests and workflow coordination, and a **Neo4j driver layer** that
encapsulates all database access and graph algorithms. This separation keeps API
logic, data processing, and database interactions clearly isolated.

## Table of contents

- [Dependencies](#dependencies)
  - [Neo4j API](#neo4j-api)
  - [Neo4j Driver](#neo4j-driver)
- [Backend Directory Structure](#backend-directory-structure)

## Dependencies

1. **Neo4j API**
   - **[FastAPI](https://fastapi.tiangolo.com/)** (`0.122.0`)\
     Web framework used to expose REST endpoints and orchestrate backend services.
   - **[Uvicorn](https://www.uvicorn.org/)** (`0.38.0`)\
     ASGI server used to run the FastAPI application.
   - **[Pandas](https://pandas.pydata.org/)** (`2.3.3`)\
     Data processing and transformation library used during import and ETL steps.
   - **[tqdm](https://tqdm.github.io/)** (`4.67.1`)\
     Progress bar utility used to track long-running data import operations.
2. **Neo4j Driver**
   - **[Neo4j Python Driver](https://neo4j.com/docs/api/python-driver/current/)** (`6.0.3`)\
     Official Neo4j driver used for database connectivity and query execution.
   - **[NumPy](https://numpy.org/)** (`2.3.5`)\
     Numerical computing library used for distance calculations and graph algorithms.
   - **[python-tsp](https://github.com/fillipe-gsm/python-tsp)** (`0.5.0`)\
     Traveling Salesman Problem solver used for itinerary optimization.

## Configuration & Environment Variables

1. **Neo4j Driver**
   | Variable           | Description                                                                                              |
   | ------------------ | -------------------------------------------------------------------------------------------------------- |
   | `LOG_LEVEL`        | Log level for the application (e.g. `DEBUG`, `INFO`, `WARNING`, `ERROR`). Defaults to `INFO` if not set. |
   | `NEO4J_URI`        | URI for the Neo4j database.                                                                              |
   | `NEO4J_USER`       | Username for Neo4j.                                                                                      |
   | `NEO4J_PASSPHRASE` | Password for Neo4j.                                                                                      |

## Backend Directory Structure

The backend code is located in the [*src/*](./src) directory alongside the frontend
and provides the API and data access layer for the application.

```text
src/
├── neo4j_api/                    # FastAPI application and ETL logic
│   ├── routes/                   # API route definitions
│   │   ├── city.py               # City-related endpoints
│   │   ├── data_update.py        # Endpoints to trigger and monitor data imports
│   │   ├── dijkstra.py           # Shortest-path routing endpoints
│   │   ├── distance.py           # Distance calculation endpoints
│   │   ├── poi.py                # Points of Interest endpoints
│   │   ├── travel.py             # Travel and itinerary-related endpoints
│   │   ├── tsp.py                # Traveling Salesman Problem endpoints
│   │   └── __init__.py
│   │
│   ├── __init__.py
│   ├── main.py                   # FastAPI application entry point
│   ├── status_handler.py         # Shared import and process status handling
│   ├── datatourisme_handler.py   # Download and authentication logic for DATAtourisme
│   ├── data_upload_etl.py        # Data extraction and CSV generation logic
│   ├── import_data.py            # Neo4j import logic (LOAD CSV, APOC)
│   └── cleanup_import.py         # Cleanup of temporary files and old imports
│
├── neo4j_driver/                 # Neo4j database access layer
│   ├── __init__.py
│   ├── base.py                   # Base Neo4j connection and session handling
│   ├── neo4j_driver.py           # Low-level Neo4j driver wrapper
│   ├── city.py                   # City-related database queries
│   ├── poi.py                    # POI-related database queries
│   ├── city_poi.py               # City–POI relationship queries
│   └── tsp.py                    # TSP-related database queries
│
└── ...                           # Frontend code and other services (not shown)
```
