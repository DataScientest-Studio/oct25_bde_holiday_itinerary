from pathlib import Path

import pandas as pd

SRC_URL = "https://simplemaps.com/static/data/country-cities/fr/fr.csv"
ROOT = Path(__file__).parent.parent.parent.parent
OUTPUT_DIR = ROOT / "import_data"
CSV_FILE = OUTPUT_DIR / "cities_nodes.csv"


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
