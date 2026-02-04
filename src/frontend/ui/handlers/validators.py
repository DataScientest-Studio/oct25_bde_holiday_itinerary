import pandas as pd
from loguru import logger


def is_column(column: str, df: pd.DataFrame):
    if column not in df.columns:
        logger.debug(f"Column {column} is not in df.")
        raise KeyError(f"Dataframe {df} has no column named '{column}'.")


def has_attr(attr: str, poi: pd.DataFrame):
    if not hasattr(poi, attr):
        logger.debug(f"Give poi has no attr {attr}.")
        raise KeyError(f"Poi {poi} has no attribute named '{attr}'.")
