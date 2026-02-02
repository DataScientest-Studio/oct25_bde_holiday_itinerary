from os import getenv
from pathlib import Path

import pandas as pd

SRC_URL = "https://simplemaps.com/static/data/country-cities/fr/fr.csv"
ROOT = Path(__file__).parent.parent.parent.parent
IMPORT_DATA_DIR = Path(getenv("NEO4J-INIT-DATA-DIR", "import-data"))
CSV_FILE = IMPORT_DATA_DIR / "cities_nodes.csv"


def create_city_nodes() -> None:
    df = pd.read_csv(SRC_URL)

    city_nodes = pd.DataFrame(
        {
            "cityId:ID(City)": df["city"],
            "name": df["city"],
            "administration": df["admin_name"],
            "population:DOUBLE": df["population"],
            "population_proper:DOUBLE": df["population_proper"],
            "latitude:DOUBLE": df["lat"],
            "longitude:DOUBLE": df["lng"],
            ":LABEL": "City",
        }
    )

    city_nodes.to_csv(CSV_FILE, index=False, quoting=1)  # csv.QUOTE_ALL
