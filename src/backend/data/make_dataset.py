"""
converts a JSON export from datatourisme.fr to usable CSV data to be imported to Neo4j
whole dataset (> 1 GB) can be downloaded here:
https://diffuseur.datatourisme.fr/webservice/b2ea75c3cd910637ff11634adec636ef/2644ca0a-e70f-44d5-90a5-3785f610c4b5
"""

import json
import re
import time
from functools import reduce
from operator import getitem
from pathlib import Path
from typing import Any

import pandas as pd

flux_directory = Path("../../example_data")
output_directory = Path("../../example_data")

# captures UUID from file name
filename_pattern = re.compile(
    r"(.*/)*(?P<id>[\d]*-[0-9a-f]{8}-[0-9a-f]{4}-[0-5][0-9a-f]{3}-[089ab][0-9a-f]{3}-[0-9a-f]{12}).json"
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
        "additional_information": "isLocatedAt.0.schema:openingHoursSpecification.0.additionalInformation.en",
    }
    result = {key: get_nested(d, path) for key, path in path_map.items()}
    result["label_index"] = index_label
    result["id"] = id
    # escaped " caused some problems with import
    if result["comment"] is not None:
        result["comment"] = result["comment"].replace('\\"', '"')
    if result["description"] is not None:
        result["description"] = result["description"].replace('\\"', '"')
    return result


def create_poi_nodes_df(input_df):
    poi_nodes_df = input_df.drop(columns=["types"]).rename(
        columns={
            "id": "poiId:ID(POI)",
            "lat": "latitude:FLOAT",
            "long": "longitude:FLOAT",
        }
    )
    poi_nodes_df[":LABEL"] = "POI"
    duplicates = poi_nodes_df[poi_nodes_df.duplicated(subset="poiId:ID(POI)", keep=False)].sort_values("poiId:ID(POI)")
    if not duplicates.empty:
        raise Exception("duplicates found in poiID")
    return poi_nodes_df


def create_type_nodes_df(df):
    rels_df = df.explode("types")
    rels_df = rels_df[~rels_df["types"].str.contains("schema:")]
    type_nodes_df = rels_df["types"].unique()
    type_nodes_df = pd.DataFrame(type_nodes_df, columns=["typeId:ID(Type)"])
    type_nodes_df[":LABEL"] = "Type"
    type_nodes_df = type_nodes_df[~type_nodes_df["typeId:ID(Type)"].str.contains("schema:")]
    return type_nodes_df


def create_poi_is_a_type_rels_df(df):
    rels_df = df.explode("types")
    rels_df = rels_df[~rels_df["types"].str.contains("schema:")]
    poi_is_a_type_df = rels_df[["id", "types"]].rename(columns={"id": ":START_ID(POI)", "types": ":END_ID(Type)"})
    poi_is_a_type_df[":TYPE"] = "IS_A"
    return poi_is_a_type_df


def store_nodes_and_edges(df):
    """stores nodes separately from edges for easy neo4j import"""
    poi_nodes_df = create_poi_nodes_df(df)
    poi_nodes_df.to_csv(output_directory / "poi_nodes.csv", index=False)

    type_nodes_df = create_type_nodes_df(df)
    type_nodes_df.to_csv(output_directory / "type_nodes.csv", index=False)

    poi_is_a_type_df = create_poi_is_a_type_rels_df(df)
    poi_is_a_type_df.to_csv(output_directory / "poi_is_a_type_rels.csv", index=False)


def process_data(directory):
    data = []
    with open(directory / "index.json") as f:
        index_data = json.load(f)
        for item in index_data:
            with open(directory / "objects" / item["file"]) as poi_file:
                data.append(
                    get_data_from_poi(get_id_from_filename(item["file"]), item.get("label", None), json.load(poi_file))
                )

    df = pd.DataFrame.from_records(data)
    df = df.astype(
        {
            "lat": "float",
            "long": "float",
        }
    )
    df.insert(0, "label", df["label_en"].combine_first(df["label_fr"]).combine_first(df["label_index"]))
    df.drop(columns=["label_en", "label_fr", "label_index"], inplace=True)
    return df


def main():
    data = []
    start = time.perf_counter()
    with open(flux_directory / "index.json") as f:
        index_data = json.load(f)
        for item in index_data:
            with open(flux_directory / "objects" / item["file"]) as poi_file:
                data.append(get_data_from_poi(get_id_from_filename(item["file"]), item["label"], json.load(poi_file)))

    df = pd.DataFrame.from_records(data)
    df = df.astype(
        {
            "lat": "float",
            "long": "float",
        }
    )
    df.insert(0, "label", df["label_en"].combine_first(df["label_fr"]).combine_first(df["label_index"]))
    df.drop(columns=["label_en", "label_fr", "label_index"], inplace=True)
    store_nodes_and_edges(df)
    end = time.perf_counter()
    print(f"Done in {end - start} seconds")


if __name__ == "__main__":
    main()
