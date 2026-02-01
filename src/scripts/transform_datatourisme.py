import json
import shutil
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

from backend.transformation import (
    get_data_from_poi,
    get_id_from_filename,
    store_nodes_and_edges,
)

URL = (
    "https://diffuseur.datatourisme.fr/webservice/"
    "b2ea75c3cd910637ff11634adec636ef/"
    "2644ca0a-e70f-44d5-90a5-3785f610c4b5"
)

OUTPUT_DIRECTORY = Path("example_data")
ZIP_PATH = OUTPUT_DIRECTORY / "datatourisme.zip"
FLUX_DIRECTORY = OUTPUT_DIRECTORY / "datatourisme"

IMPORT_DIR = Path("import_data")


def download_file() -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)

    if ZIP_PATH.is_file() and zipfile.is_zipfile(ZIP_PATH):
        print("ZIP already exists, skipping download.")
        return

    print("Downloading DataTourisme ZIP...")
    with requests.get(URL, stream=True, timeout=600) as r:
        r.raise_for_status()
        with open(ZIP_PATH, "wb") as f:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if chunk:
                    f.write(chunk)

    print(f"Downloaded to {ZIP_PATH.resolve()}")


def unzip_file() -> None:
    if FLUX_DIRECTORY.exists():
        print("Flux directory already exists, skipping unzip.")
        return

    print("Extracting ZIP...")
    with zipfile.ZipFile(ZIP_PATH, "r") as zip_ref:
        zip_ref.extractall(FLUX_DIRECTORY)

    print(f"Extracted to {FLUX_DIRECTORY.resolve()}")


def zip_csv_files() -> None:
    for csv_file in IMPORT_DIR.rglob("*.csv"):
        zip_path = csv_file.with_suffix(".zip")
        zip_path.unlink(missing_ok=True)

        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(csv_file, arcname=csv_file.name)

        csv_file.unlink()
        print(f"Created {zip_path}")


def cleanup_flux_directory() -> None:
    if FLUX_DIRECTORY.exists():
        shutil.rmtree(FLUX_DIRECTORY)
        print("Flux directory removed.")


def main():
    """
    converts a JSON export from datatourisme.fr to usable CSV data to be imported to Neo4j
    whole dataset (> 1 GB) can be downloaded here:
    https://diffuseur.datatourisme.fr/webservice/b2ea75c3cd910637ff11634adec636ef/2644ca0a-e70f-44d5-90a5-3785f610c4b5
    """

    start = time.perf_counter()

    download_file()
    unzip_file()

    data = []
    with open(FLUX_DIRECTORY / "index.json") as f:
        index_data = json.load(f)

    for item in index_data:
        with open(FLUX_DIRECTORY / "objects" / item["file"]) as poi_file:
            data.append(
                get_data_from_poi(
                    get_id_from_filename(item["file"]),
                    item["label"],
                    json.load(poi_file),
                )
            )

    df = pd.DataFrame.from_records(data)
    df = df.astype({"lat": "float", "long": "float"})

    df.insert(
        0,
        "label",
        df["label_en"].combine_first(df["label_fr"]).combine_first(df["label_index"]),
    )
    df.drop(columns=["label_en", "label_fr", "label_index"], inplace=True)

    store_nodes_and_edges(df)
    zip_csv_files()
    cleanup_flux_directory()

    elapsed = time.perf_counter() - start
    print(f"Done in {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
