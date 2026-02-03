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
src/backend/
├── dataset_import/                 # Dataset ingestion and Neo4j loading pipelines
│   ├── __init__.py
│   ├── cleanup.py                  # Cleanup of temporary files, old imports, and staging artifacts
│   ├── handler.py                  # Main dataset import orchestration entry points
│   ├── neo4j_load.py               # Neo4j bulk import logic (LOAD CSV, batch inserts, APOC helpers)
│   ├── pipeline.py                 # End-to-end dataset import pipeline definition and execution flow
│   └── status_handler.py           # Import status tracking, progress monitoring, and state reporting
│
├── neo4j_api/                      # FastAPI application exposing graph, routing, and data endpoints
│   ├── routes/                     # API route definitions grouped by domain
│   │   ├── city.py                 # City-related endpoints (search, retrieval, metadata)
│   │   ├── data_update.py          # Endpoints to trigger dataset imports and monitor import progress
│   │   ├── dijkstra.py             # Shortest path routing endpoints (Dijkstra-based routing)
│   │   ├── distance.py             # Distance calculation endpoints between graph entities
│   │   ├── poi.py                  # Points of Interest endpoints (search, filtering, retrieval)
│   │   ├── travel.py               # Travel planning and itinerary-related endpoints
│   │   ├── tsp.py                  # Traveling Salesman Problem solver endpoints
│   │   └── __init__.py
│   │
│   ├── __init__.py
│   └── main.py                     # FastAPI application entry point (app creation, middleware, router registration)
│
├── neo4j_driver/                   # Neo4j database access and query abstraction layer
│   ├── __init__.py
│   ├── base.py                     # Base Neo4j connection handling, sessions, and transaction utilities
│   ├── city.py                     # City-related graph queries and database operations
│   ├── city_poi.py                 # City ↔ POI relationship queries and traversal helpers
│   ├── neo4j_driver.py             # Low-level Neo4j driver wrapper and connection lifecycle management
│   ├── poi.py                      # POI-related graph queries and retrieval logic
│   └── tsp.py                      # TSP graph query helpers and optimization query logic
│
└── transformation/                 # Raw dataset transformation and normalization logic
    ├── __init__.py
    ├── datatourisme.py             # DATAtourisme dataset transformation, cleaning, and schema mapping
    └── french_cities.py            # French cities dataset normalization and enrichment logic
```
