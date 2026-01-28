import pandas as pd
from loguru import logger

from .validators import is_column


def remove_poi(df: pd.DataFrame, poi_id: str) -> pd.DataFrame:
    logger.debug(f"Removing row with poiId {poi_id} from DataFrame...")

    is_column("poiId", df)

    df = df[df["poiId"] != poi_id]
    logger.info(f"Removed 'poiId' from {df}")
    return df
