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
        if "poiId" not in dest.columns:
            logger.debug("Dest has no dataframe.")
            raise KeyError(f"Dataframe {dest} has no column named 'poiId'.")
        if not hasattr(src, "poiId"):
            logger.debug("Src has no dataframe.")
            raise KeyError(f"Dataframe {src} has no column named 'poiId'.")
        if src["poiId"] in dest["poiId"].values:
            logger.debug("poiId already in dest.")
            raise ValueError(f"Row with poiId {src.poiId} already dataframe..")

        dest.loc[len(dest)] = {col: getattr(src, col, None) for col in dest.columns}
        logger.info("Added point to dataframe.")
        return dest

    def remove_df_from_df(self, target: pd.DataFrame, src: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Removing df from df...")
        poi_ids = src["poi_id"].tolist()
        for poi_id in poi_ids:
            self.remove_poi(target, poi_id)
        logger.info(f"Removed poiIds {poi_ids} from target.")
        return target

    def remove_poi(self, target: pd.DataFrame, poi_id: str) -> pd.DataFrame:
        logger.debug(f"Removing row with poiId {poi_id} from DataFrame...")
        if "poiId" not in target.columns:
            logger.debug("Target has no dataframe.")
            raise KeyError(f"Dataframe {target} has no column named 'poiId'.")

        target = target[target["poiId"] != poi_id]
        logger.info(f"Removed 'poiId' from {target}")
        return target

    def request_itinerary_type(
        self, itinerary_type: str, pois: pd.DataFrame, start: str | None = None, end: str | None = None
    ) -> tuple[pd.DataFrame, float]:
        if pois.shape[0] < 3:
            logger.error("At least 3 POIs are needed.")
            raise ValueError("Given POIs are not enough for a route.")
        match itinerary_type:
            case "Round trip":
                return self.roundtrip(pois, start)
            case "One-way trip (flexible end)":
                pass
            case "One-way trip (fixed destination)":
                pass
            case _:
                raise ValueError(f"'{itinerary_type}' is not a valid itinerary_type.")
        return pois, 0.0

    def roundtrip(self, pois: pd.DataFrame, start: str | None = None) -> tuple[pd.DataFrame, float]:
        params = self.prepare_params(pois, start)
        itinerary = handle_get_request("/tsp/shortest-round-tour", params)
        ordered_df = pois.set_index("poiId").loc[itinerary["poi_order"]].reset_index()
        return ordered_df, itinerary["total_distance"]

    def prepare_params(self, pois: pd.DataFrame, poi_id: str | None = None) -> dict[str, Any]:
        if poi_id:
            poi_id = pois.loc[pois["label"] == poi_id, "poiId"].iloc[0]
        poi_ids = pois["poiId"].tolist()
        if poi_id:
            logger.debug(f"Start/End POI {poi_id} is set. Removing it from existing list.")
            poi_ids.remove(poi_id)
            poi_ids = [poi_id] + poi_ids
        logger.info("Created parameter for trip tour.")
        return {"poi_ids": poi_ids}

    def node_is_valid(self, pois: pd.DataFrame, poi: str | None) -> bool:
        if not poi:
            logger.error(f"POI '{poi}' is not a valid poiId.")
            return False

        if poi not in pois["poiId"].values:
            logger.error(f"POI '{poi}' is not in the DataFrame.")
            return False

        return True
