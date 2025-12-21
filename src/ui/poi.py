from __future__ import annotations

from typing import NamedTuple

import pandas as pd

from logger import logger


class Poi(NamedTuple):
    label: str
    city: str
    description: str
    street: str
    postal_code: str
    homepage: str
    additional_information: str
    comment: str
    latitude: float
    longitude: float
    poiId: str

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> Poi:
        logger.debug("Creating poi from DataFrame...")
        if not isinstance(df, pd.DataFrame):
            logger.warning(f"No DataFrame given, got {type(df)}.")
            raise TypeError("Given argument is not DataFrame.")
        if df.empty:
            logger.error("Poi is empty.")
            raise ValueError("DataFrame is empty. No POI to store.")
        if len(df) != 1:
            logger.error(f"Expected a DataFrame with exactly one row, but got {len(df)}.")
            raise ValueError("Given DataFrame has to much rows.")
        row = df.iloc[0]
        poi = cls(**row.to_dict())

        logger.info("Created poi from Dataframe.")
        return poi
