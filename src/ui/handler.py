import pandas as pd

from logger import logger


class Handler:

    def __init__(self) -> None:
        logger.info("Initialized UIHandler.")

    def add_poi(self, dest: pd.DataFrame, src: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Handle add point to dataframe.")
        if "poiId" not in dest:
            raise KeyError(f"Dataframe {dest} has no column named 'poiId'.")
        if "poiId" not in src:
            raise KeyError(f"Dataframe {src} has no column named 'poiId'.")
        if (dest["poiId"] == src["poiId"]).any():
            raise ValueError(f"Row with poiId {src['poiId']} already dataframe..")

        dest.loc[len(dest)] = src
        logger.info("Added point to dataframe.")
        return dest

    def remove_poi(self, target: pd.Dataframe, poi_id: str) -> pd.DataFrame:
        logger.debug("Removing row from DataFrame...")
        if "poiId" not in target:
            raise KeyError(f"Dataframe {target} has no column named 'poiId'.")

        target = target[target["poiId"] != poi_id]
        logger.info(f"Removed 'poiId' from {target}")
        return target
