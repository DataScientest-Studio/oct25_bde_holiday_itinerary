# Holiday Itinerary

## Dependencies

1. [Make](https://www.gnu.org/software/make/)
2. [Poetry (version 2.2.1) ()](https://python-poetry.org/) -- python -m pip
   install poetry==2.2.1

### Poetry

Run environment with `eval $(poetry env activate)`

### Development

1. [Pre-commit](https://pre-commit.com/) -- python -m pip install pre-commit==4.2.0

## First steps to create a dataset and load into Neo4j

dataset from datatourisme.fr can be downloaded here: [dataset](https://diffuseur.datatourisme.fr/webservice/b2ea75c3cd910637ff11634adec636ef/2644ca0a-e70f-44d5-90a5-3785f610c4b5)

The .zip archive is around 1 GB large and unzipped around 8 GB

__make_dataset.py__ script takes the directory and converts it to usable csv data with these informations:

| row_name               | description               | example            |
| ---------------------- | ------------------------- | ------------------ |
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

In the example data there is __paris.csv__ where I put POIs that have city == Paris for testing purposes.

File __docker-compose.yml__ contains everything to start Neo4j locally with

```shell
docker-compose up -d
```

Note: in docker-compose the _NEO4J_server_directories_import_ ENV is set to __example_data__ which means only csv files from this directory may be imported to Neo4j.

## Graph mapping

there is at the moment no relationship mapping in for the POIs since there is no routes information between cities or so. This will have to be done in the next steps.

______________________________________________________________________

This project is a starting Pack for MLOps projects based on the subject "movie_recommandation". It's not perfect so feel free to make some modifications on it.

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
