Holiday Itinerary
==============================

## First steps to create a dataset and load into Neo4j
dataset from datatourisme.fr can be downloaded here: [dataset](https://diffuseur.datatourisme.fr/webservice/b2ea75c3cd910637ff11634adec636ef/2644ca0a-e70f-44d5-90a5-3785f610c4b5)

The .zip archive is around 1 GB large and unzipped around 8 GB

__make_dataset.py__ script takes the directory and converts it to usable csv data with these informations:

| row_name               | description               | example            |
|------------------------|---------------------------|--------------------|
| id                     | UUID from datatourisme.fr |                    |
| label                  | name of the POI           |                    |
| comment                | short description         |                    |
| description            | long description          |                    |
| types                  | list of POI types         | Restaurant, Museum |
| homepage               | homepage                  |                    |
| city                   | address part              |                    |
| postal_code            | address part              |                    |
| street                 | address part              |                    |
| lat                    | latitude                  |                    |
| long                   | longitude                 |                    |
| additional_information | some additional info      |                    |

This CSV can be then loaded into Neo4j database with command from __import_to_neo4j.txt__

In the example data there is `france_poi.csv` archive and `france_cities.csv` datasets.

File __docker_compose.yml__ contains everything to start Neo4j locally with
```shell
docker-compose up -d
```
Note: in docker-compose the _NEO4J_server_directories_import_ ENV is set to __example_data__ which means only csv files from this directory may be imported to Neo4j.

## Manual Data Import to Graph
details in `./src/data/import*`
### Import POI
Beware: takes a few minutes!
```cypher
:auto LOAD CSV WITH HEADERS FROM "file:///france_poi.csv" AS row
CALL {
  WITH row
  WITH row, split(row.types, ',') AS typesList

  MERGE (poi:Poi {id: row.id})
    ON CREATE SET
      poi.label                  = row.label,
      poi.comment                = row.comment,
      poi.description            = row.description,
      poi.types                  = typesList,
      poi.homepage               = row.homepage,
      poi.city                   = row.city,
      poi.postal_code            = row.postal_code,
      poi.street                 = row.street,
      poi.x                      = toFloat(row.lat),
      poi.y                      = toFloat(row.long),
      poi.additional_information = row.additional_information
} IN TRANSACTIONS OF 5000 ROWS
```
### Import Cities and Roads
```cypher
CALL apoc.cypher.runFile("file:///cities_roadto.cypher");
```

-------
This project is a starting Pack for MLOps projects based on the subject "movie_recommandation". It's not perfect so feel free to make some modifications on it.

Project Organization
------------

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

--------

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
