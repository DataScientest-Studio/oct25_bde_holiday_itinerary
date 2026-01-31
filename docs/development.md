# Development

## Dependencies

- **[pre-commit](https://pre-commit.com/)** (`4.2.0`)\
  Git hooks framework used to enforce code quality checks before commits.
- **[Black](https://black.readthedocs.io/)** (`25.11.0`)\
  Opinionated Python code formatter.
- **[isort](https://pycqa.github.io/isort/)** (`7.0.0`)\
  Import sorting and organization tool.
- **[Flake8](https://flake8.pycqa.org/)** (`7.3.0`)\
  Linting tool for style, complexity, and error detection.
- **[MyPy](https://mypy-lang.org/)** (`1.18.2`)\
  Static type checker for Python.
- **[Pytest](https://docs.pytest.org/)** (`9.0.1`)\
  Testing framework for unit and integration tests.
- **[Requests](https://docs.python-requests.org/)** (`2.32.5`)\
  HTTP client used for integration and API testing.
- **[Matplotlib](https://matplotlib.org/)** (`3.10.8`)\
  Plotting library used for data visualization and analysis.
- **[Basemap](https://matplotlib.org/basemap/)** (`2.0.0`)\
  Geospatial plotting toolkit used for map-based visualizations.

## Pre-commit

The project uses **pre-commit** to automatically enforce code formatting,
linting, and basic consistency checks before commits are created.

It applies to Python source code and Markdown files and helps catch common
issues early, keeping the codebase consistent across frontend and backend.

## Poetry

The project uses **Poetry** for dependency management and virtual environment
isolation.

Poetry ensures consistent dependency versions across frontend, backend, and
development tooling, and is also used by pre-commit hooks to run tools inside
the correct virtual environment.

## Tests

Tests can be executed using `make tests`, which runs the test commands defined
in the `tests/` target of the Makefile.

## GitHub Actions

GitHub Actions are used to automatically validate the project on every push and
pull request to the `master` branch.

- **Lint**: Runs all `pre-commit` hooks using Python 3.13 to enforce formatting
  and code quality.
- **Test**: Executes the test suite in a Docker-enabled environment via
  `make tests`.

## Logging

The project uses a shared logging setup based on **Loguru**, which is imported by
both the frontend and backend.

The logger provides consistent formatting and log levels across all components
and also intercepts Python’s standard `logging` module so that third-party
libraries and internal code use the same output.

Logging behavior can be configured via environment variables:

- **LOG_LEVEL** – Sets the minimum log level (compatible with standard Python
  logging levels).
- **LOG_HI** – Enables or disables colored and formatted console output.

All application code should use the shared `logger` instance instead of defining
custom logging configurations.

## Manual Data Import

Dataset from datatourisme.fr can be downloaded here:

- [dataset](https://diffuseur.datatourisme.fr/webservice/b2ea75c3cd910637ff11634adec636ef/2644ca0a-e70f-44d5-90a5-3785f610c4b5)
- [latest dataset](https://diffuseur.datatourisme.fr/flux/24943/download/complete)

The .zip archive is around 1 GB large and unzipped around 8 GB.

The **make_dataset.py** script takes the directory and converts it into CSV files
that can be directly imported by Neo4j.

File `poi_nodes.csv` contains information about the POI except for the `types`
field.\
Types is a list of roughly 350 unique type descriptions. Therefore, the types
are mapped using the **Super-Node Pattern**, where for every type a node is
created and every POI node gets a relationship to it.

Files `type_nodes.csv` and `poi_is_a_type_rels.csv` contain the type nodes and
their relationships.

If you need to import data manually using `neo4j-admin`:

1. Download and extract new feed data into `example_data` and create the dataset
   using `make_dataset.py`
2. Stop Neo4j:
   ```shell
   docker compose down
   ```
3. If the `docker compose up` command has not been executed yet and no volume
   exists, create it:
   ```shell
   docker volume create neo4j_data
   ```
4. Import the data from the project root directory:
   ```shell
   docker run --rm \
       --volume=$PWD/example_data:/import \
       --volume=$(docker volume inspect -f '{{.Mountpoint}}' neo4j_data):/data \
       neo4j:2025.10.1 \
       neo4j-admin database import full --overwrite-destination \
           --multiline-fields=true \
           --nodes="POI=/import/poi_nodes.zip" \
           --nodes="Type=/import/type_nodes.zip" \
           --relationships="IS_A=/import/poi_is_a_type_rels.zip" \
           --nodes="City=/import/cities_nodes.zip" \
           --relationships="ROAD_TO=/import/roads_rels.zip"
   ```
5. Create `IS_IN` relationships:
   ```cypher
   CALL apoc.periodic.iterate(
     "MATCH (p:POI {importVersion: $import_version}) WHERE p.city IS NOT NULL RETURN p",
     "MATCH (c:City {name: p.city})
      MERGE (p)-[r:IS_IN]->(c)
      SET r.importVersion = $import_version",
     {
       batchSize: 2000,
       parallel: true,
       params: { import_version: $import_version }
     }
   )
   YIELD batches, total, errorMessages, committedOperations
   RETURN batches, total, errorMessages, committedOperations;
   ```
6. Create `IS_NEARBY` relationships:
   ```cypher
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
          r.distance_km = round(shortestDist / 1000.0, 2)",
     {
       batchSize: 1000,
       parallel: false,
       params: { import_version: $import_version }
     }
   )
   YIELD batches, total, errorMessages, committedOperations
   RETURN batches, total, errorMessages, committedOperations;
   ```
