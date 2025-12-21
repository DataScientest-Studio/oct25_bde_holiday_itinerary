from json import loads
from typing import Any

import pandas as pd
from requests import get
from requests.models import HTTPError

from logger import logger


def handle_get_request(target: str, query_params: dict[str, str] | None = None) -> dict[str, Any]:
    logger.info(f"Sending GET request to http://neo4j_api:8080{target} with params: {query_params}")
    try:
        response = get(f"http://neo4j_api:8080{target}", params=query_params)
        logger.debug(f"Received response returned status code {response.status_code}")

        match response.status_code:
            case 200:
                logger.success(f"GET request to http://neo4j_api:8080{target} succeeded")
                return loads(response.text)
            case _:
                logger.warning(f"GET request to {target} returned {response.status_code}")
                raise HTTPError(f"Request did not return 200. It returned {response.status_code}.")
    except Exception as err:
        logger.error(f"GET request to http://neo4j_api:8080{target} failed: {err}")
        raise


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

    def remove_poi(self, target: pd.DataFrame, poi_id: str) -> pd.DataFrame:
        logger.debug("Removing row from DataFrame...")
        if "poiId" not in target:
            raise KeyError(f"Dataframe {target} has no column named 'poiId'.")

        target = target[target["poiId"] != poi_id]
        logger.info(f"Removed 'poiId' from {target}")
        return target
