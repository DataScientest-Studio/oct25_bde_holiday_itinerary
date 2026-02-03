# Production

This documentation describes how the production environment is built, configured,
and operated for this project. It covers deployment setup, runtime configuration,
infrastructure components, and operational requirements needed to run the system
reliably in a production setting.

## Dependencies

All dependencies listed in this document are mandatory for the production environment.
Furthermore the dependencies listed in [README.md](../README.md) are required.
The exact dependency versions are managed via `pyproject.toml` and the lock file.

- **[Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)** (`6.0.3`)\
  Official Neo4j driver used for database connectivity and Cypher query execution.
- **[NumPy](https://numpy.org/)** (`2.3.5`)\
  Numerical computing library used for efficient array operations and algorithm
  support.
- **[python-tsp](https://pypi.org/project/python-tsp/)** (`0.5.0`)\
  Library providing Traveling Salesman Problem solvers used for route optimization.
- **[Uvicorn](https://www.uvicorn.org/)** (`0.38.0`)\
  ASGI server used to run the FastAPI backend in production and development environments.
- **[FastAPI](https://fastapi.tiangolo.com/)** (`0.122.0`, standard extras)\
  High-performance Python web framework used to expose API endpoints for routing
  and itinerary queries.
- **[Pandas](https://pandas.pydata.org/)** (`2.3.3`)\
  Data processing library used for dataset transformation, ETL steps, and data preparation.
- **[tqdm](https://tqdm.github.io/)** (`4.67.1`)\
  Progress bar utility used for monitoring long-running data processing tasks.

## Commands

1. **make run** — Starts the development environment
2. **make down** — Shutdown the development environment and deletes the docker container.
3. **make clean** — Removes all docker container, images and volumes of the development
   environment.
4. **make create-dataset** — Create, the dataset on the production manually.
