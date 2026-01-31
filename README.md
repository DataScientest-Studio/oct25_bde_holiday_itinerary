# Holiday Itinerary

This repository contains a full-stack holiday itinerary planning application
with a clear separation between frontend and backend responsibilities.

## Frontend

The frontend is implemented using **Streamlit** and provides a user interface
for planning holiday trips. Users can select destinations, explore nearby
points of interest (POIs), and navigate routes derived from the underlying
data model.

The frontend communicates exclusively with the backend API and does not
access the database directly.

Detailed information about the architecture can be found in
[docs/frontend-architecture.md](docs/frontend-architecture.md).

## Backend

The backend is responsible for all data access, processing and orchestration
and consists of the following components:

- **API Layer**\
  A Python-based API that exposes read-only endpoints for querying itinerary,
  routing and POI data.
- **Driver Layer**\
  A dedicated Neo4j driver module that encapsulates all database access and
  Cypher queries, isolating graph-specific logic from the API layer.
- **Data Layer**\
  A Neo4j graph database modeling cities, roads and points of interest to enable
  relationship-heavy queries and routing use cases.
- **Data Synchronization**\
  Apache Airflow is used to periodically synchronize and reconcile external
  tourism datasets with the Neo4j graph, ensuring data consistency over time.

The entire system is containerized using Docker and Docker Compose to provide
a reproducible and environment-independent setup.

Detailed information about the architecture can be found in docs/backend-architecture.md.

## Dependencies

- **[Python](https://www.python.org/)** (`>=3.13.0,<3.14`)\
  Core runtime used across the project.
- **[Loguru](https://loguru.readthedocs.io/)** (`0.7.3`)\
  Shared logging framework used by both frontend and backend.
- **[Neo4j](https://neo4j.com/)** (`5.x`)\
  Graph database used for storing cities, POIs, and routing data.
- **[Docker](https://www.docker.com/)**\
  Container runtime used to run services consistently across environments.
- **[Docker Compose](https://docs.docker.com/compose/)**\
  Tooling to orchestrate multi-service setups such as Neo4j and backend APIs.
- **[Make](https://www.gnu.org/software/make/)**\
  Task runner used to standardize common development and test commands.

## Build & Execution Process

The project is fully containerized and designed to be executed consistently across
development and production-like environments.

- Docker images define all runtime dependencies
- Docker Compose orchestrates Neo4j, backend services, and orchestration components
- Make targets provide a simplified interface for common build and run tasks

Detailed run instructions will be added once the setup is finalized.

## Underlying Data Structure

The system uses a Neo4j graph database to model cities, roads and points of interest
for itinerary planning and routing.

### Core Entities

- **City**\
  Represents French cities with population and geographic coordinates.
- **Roads (`ROAD_TO`)**\
  A synthetic road network connecting cities based on geographic proximity,
  ensuring full graph connectivity for routing algorithms.
- **Point of Interest (POI)**\
  Tourist attractions, restaurants and rooms imported from DATAtourisme.fr.
- **Type**\
  POI categories modeled as nodes (Super-Node Pattern) to support multiple and
  overlapping classifications.

### Spatial Relationships

- **IS_IN** — Links POIs located inside a city
- **IS_NEARBY** — Links POIs outside city limits to the nearest city

A detailed explanation of dataset creation, graph algorithms, and import steps
is available in\
**[`docs/cities-roads-dataset.md`](docs/cities-roads-dataset.md)** and\
**[`docs/data-structure.md`](docs/data-structure.md)**.

## Data Import Pipeline

The project supports both automated and manual ingestion of tourism data
into Neo4j.

### Overview

- **Automated ETL**\
  An Apache Airflow DAG triggers a FastAPI-based pipeline to download,
  process, and import the latest DATAtourisme dataset into Neo4j.
- **Manual Import**\
  For local development or recovery scenarios, datasets can be processed
  manually and imported using `neo4j-admin`.

All steps include data extraction, transformation into Neo4j-compatible CSVs,
and creation of spatial relationships between POIs and cities.

A full, step-by-step description of the ETL process, dataset formats,
and manual import commands is available in\
**[`docs/data-import.md`](docs/data-import.md)**.

______________________________________________________________________

Starting the DB with docker-compose uses the `EXTENSION_SCRIPT` ENV which runs `import_script.sh` from `init` directory.
This makes initial data import automatically done once.
The only manual work needed at this moment is to create `gds` projections needed for some API requests:

```cypher
CALL gds.graph.exists('city-road-graph') YIELD exists
WITH exists
WHERE NOT exists

CALL gds.graph.project(
  'city-road-graph',
  'City',
  {
    ROAD_TO: {
      orientation: 'UNDIRECTED',
      properties: 'km'
    }
  }
)
YIELD graphName, nodeCount, relationshipCount
RETURN graphName, nodeCount, relationshipCount;
```

## Start neo4j

File __docker_compose.yml__ contains everything to start Neo4j locally with

```shell
docker-compose up -d
```

Note: in docker-compose the _NEO4J_server_directories_import_ ENV is set to __example_data__ which means only csv files from this directory may be imported to Neo4j.

## Test your neo4j

After executing `docker compose up -d` command go to `localhost:7474` and connect to the database (no auth required).
Try some of these requests:

get all types:\
`match(t:Type) return t.typeId as type`

count of POI in Paris:\
`match (p:POI {city: "Paris"}) return count(p)`

get distribution of POI types in Lyon:

```
 match (p:POI {city: "Lyon"}) - [r:IS_A] -> (t:Type)
 with t, count(*) as cnt
 return t.typeId, cnt order by cnt desc
```

get restaurants in Avignon:\
`MATCH (p:POI {city: "Avignon"})-[r:IS_A]->(t:Type {typeId: "Restaurant"}) return p`

______________________________________________________________________

## Neo4j Driver

To access the database with Python code, you need to initialize the
`Neo4jDriver` class, located in the module `src/neo4j_driver`. You can
configure the driver using the following environment variables:

- **NEO4J_URI** — Sets the URI of the database. Default: `bolt://neo4j:7687`.
- **NEO4J_USER** — Sets the username to access the database. Default: `neo4j`.
- **NEO4J_PASSPHRASE** — Sets the passphrase to access the database. Default:
  no passphrase.

## Neo4j API

To access the driver via the `Neo4jApi`, the following endpoints are defined:

- **/poi** -- Takes `poi_id: str` as a parameter and returns a JSON dict
  with all information about the POI, e.g. `{"id":"...", "label":"...", ...}`.
- **/poi/nearby** -- Takes `poi_id: str` and `radius: int` as parameters
  and returns a JSON dict with all POIs located within the radius around the
  given POI, e.g. `{"nearby": [ ... ]}`.
- **/distance** -- Takes `poi1_id: str` and `poi2_id: str` as parameters
  and returns a JSON dict with the distance, e.g. `{"distance": 234.12}`.
- **/tsp/shortest-round-tour** -- Takes a list of `poi_ids: list[str]` as
  a parameter and returns a JSON dict with the optimized POI order,
  e.g. `{"poi_order": [ ... ]}`.
- **/tsp/shortest-path-no-return** -- Takes a list of `poi_ids: list[str]`
  as a parameter and returns a JSON dict with the optimized POI order,
  e.g. `{"poi_order": [ ... ]}`.
- **/tsp/shortest-path-fixed-dest** -- Takes a list of `poi_ids: list[str]`
  and `dest: str` as parameters and returns a JSON dict with the optimized
  POI order ending at the fixed destination, e.g. `{"poi_order": [ ... ]}`.
- **/dijkstra** -- Takes a list of `poi_ids: list[str]` as a parameter
  and returns a JSON dict with the POI order along the shortest path,
  e.g. `{"poi_order": [ ... ]}`.

## Project Organization

```
├── LICENSE
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── logs               <- Logs from training and predicting
│
├── models             <- Trained and serialized models, model predictions, or model summaries
│
├── notebooks          <- Jupyter notebooks. Naming convention is a number (for ordering),
│                         the creator's initials, and a short `-` delimited description, e.g.
│                         `1.0-jqp-initial-data-exploration`.
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
├── requirements.txt   <- The requirements file for reproducing the analysis environment, e.g.
│                         generated with `pip freeze > requirements.txt`
│
├── src                <- Source code for use in this project.
│   ├── __init__.py    <- Makes src a Python module
│   │
│   ├── data           <- Scripts to download or generate data
│   │   └── make_dataset.py
│   │
│   ├── features       <- Scripts to turn raw data into features for modeling
│   │   └── build_features.py
│   │
│   ├── models         <- Scripts to train models and then use trained models to make
│   │   │                 predictions
│   │   ├── predict_model.py
│   │   └── train_model.py
│   │
│   ├── visualization  <- Scripts to create exploratory and results oriented visualizations
│   │   └── visualize.py
│   └── config         <- Describe the parameters used in train_model.py and predict_model.py
```

______________________________________________________________________

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
