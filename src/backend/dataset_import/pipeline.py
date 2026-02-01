"""functions related to data upload"""

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from data.make_dataset import create_poi_is_a_type_rels_df, create_poi_nodes_df, create_type_nodes_df, process_data

from .status_handler import ProcessLock, get_status_file


def unzip_data(file_path, save_dir, extract_to):
    """Unzip saved data"""
    with ProcessLock(save_dir, "unzip"):
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            extract_to.mkdir(exist_ok=True)
            zip_ref.extractall(path=extract_to)

        status = {
            "last_unzip_utc": datetime.now(UTC).isoformat(),
            "filename": str(extract_to),
        }
        with open(get_status_file(save_dir, "unzip"), "w") as f:
            json.dump(status, fp=f)
    return extract_to


def perform_extract_data(data_path: Path, save_dir: Path, import_dir: Path):
    with ProcessLock(save_dir, "extract"):
        df = process_data(data_path)
        poi_nodes_df = create_poi_nodes_df(df)
        type_nodes_df = create_type_nodes_df(df)
        poi_is_a_type_df = create_poi_is_a_type_rels_df(df)

        dir_name = data_path.name
        import_dir_name = import_dir / dir_name
        import_dir_name.mkdir(parents=False, exist_ok=True)

        poi_nodes_df.to_csv(import_dir_name / "poi_nodes.csv", index=False)
        type_nodes_df.to_csv(import_dir_name / "type_nodes.csv", index=False)
        poi_is_a_type_df.to_csv(import_dir_name / "poi_is_a_type_rels.csv", index=False)

        status = {
            "last_extract_utc": datetime.now(UTC).isoformat(),
            "filename": str(import_dir_name),
        }
        with open(get_status_file(save_dir, "extract"), "w") as f:
            json.dump(status, fp=f)
        return status
