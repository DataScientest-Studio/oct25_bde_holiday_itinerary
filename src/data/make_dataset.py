"""
converts a JSON export from datatourisme.fr to usable CSV data to be imported to Neo4j
whole dataset (> 1 GB) can be downloaded here: https://diffuseur.datatourisme.fr/webservice/b2ea75c3cd910637ff11634adec636ef/2644ca0a-e70f-44d5-90a5-3785f610c4b5
"""

import json
import re
import time
from datetime import datetime
from functools import reduce
from operator import getitem
from pathlib import Path
from typing import Any

import pandas as pd

flux_directory = Path("example_data")
output_directory = Path("example_data")

# captures UUID from file name
filename_pattern = re.compile(
    r".*(?P<id>[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}).json"
)

def get_nested(data: dict, path: str, default: Any = None) -> Any:
    """allows to get nested keys from dictionary"""
    path_list = [int(x) if x.isdecimal() else x for x in path.split(".")]
    try:
        return reduce(getitem, path_list, data)
    except (TypeError, AttributeError, KeyError):
        return default

def get_id_from_filename(filename: str) -> str:
    """returns uuid from filename like 0/00/10-000283ba-f94b-3bce-8f57-e5c10bec6cd4.json"""
    return re.search(filename_pattern, filename).group("id")


def get_data_from_poi(id, index_label, d):
    """extracts interesting data from whole set"""
    path_map = {
        "label_en": "rdfs:label.en.0",
        "label_fr": "rdfs:label.fr.0",
        "comment": "rdfs:comment.en.0",
        "description": "hasDescription.0.shortDescription.en.0",
        "types": "@type",
        "homepage": "hasContact.0.foaf:homepage.0",
        "city": "isLocatedAt.0.schema:address.0.schema:addressLocality",
        "postal_code": "isLocatedAt.0.schema:address.0.schema:postalCode",
        "street": "isLocatedAt.0.schema:address.0.schema:streetAddress.0",
        "lat": "isLocatedAt.0.schema:geo.schema:latitude",
        "long": "isLocatedAt.0.schema:geo.schema:longitude",
        "additional_information": "isLocatedAt.0.schema:openingHoursSpecification.0.additionalInformation.en"
    }
    result = {key: get_nested(d, path) for key, path in path_map.items()}
    result["label_index"] = index_label
    result["id"] = id
    return result


def main():
    data = []
    start = time.perf_counter()
    with open(flux_directory / "index.json") as f:
        index_data = json.load(f)
        for item in index_data:
            with open(flux_directory / "objects" / item["file"]) as poi_file:
                data.append(get_data_from_poi(get_id_from_filename(item["file"]), item["label"], json.load(poi_file)))

    df = pd.DataFrame.from_records(data)
    df = df.astype({
        "lat": "float",
        "long": "float",
    })
    df.insert(0, "label", df["label_en"].combine_first(df["label_fr"]).combine_first(df["label_index"]))
    df.drop(columns=["label_en", "label_fr", "label_index"], inplace=True)
    # filter out schema: types and convert to json string
    df["types"] = df["types"].apply(lambda x: ",".join([i for i in x if "schema:" not in i]))
    df.to_csv(output_directory/f"data{datetime.now():%Y-%m-%d_%H-%M}.csv" , index=False)
    end = time.perf_counter()
    print(f"Done in {end - start} seconds")


if __name__ == "__main__":
    main()

