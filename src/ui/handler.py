from json import loads
from typing import Any

import pandas as pd
import streamlit as st
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

    def add_poi(self) -> None:
        logger.debug("Adding POI to route DataFrame.")
        try:
            st.session_state.route = self.add_poi_to_df(
                st.session_state.route,
                st.session_state.selected_poi,
            )
            logger.info("Added point to route POIs DataFrame.")
            st.session_state.overview = self.remove_poi(
                st.session_state.overview,
                st.session_state.selected_poi.poiId,
            )
            logger.info("Removed POI from pois DataFrame.")
        except (KeyError, ValueError) as err:
            logger.error(err)

    def add_poi_to_df(self, df: pd.DataFrame, poi: pd.DataFrame) -> pd.DataFrame:
        logger.debug("Handle add point to dataframe.")

        self.validate_df(df)
        self.validate_poi(poi)

        if poi["poiId"] in df["poiId"].values:
            logger.debug("poiId already in dest.")
            raise ValueError(f"Row with poiId {poi.poiId} already dataframe..")

        df.loc[len(df)] = {col: getattr(poi, col, None) for col in df.columns}
        logger.info("Added point to dataframe.")

        return df

    def validate_df(self, route: pd.DataFrame):
        if "poiId" not in route.columns:
            logger.debug("Dest has no dataframe.")
            raise KeyError(f"Dataframe {route} has no column named 'poiId'.")

    def validate_poi(self, poi: pd.DataFrame):
        if not hasattr(poi, "poiId"):
            logger.debug("Src has no dataframe.")
            raise KeyError(f"Dataframe {poi} has no column named 'poiId'.")

    def delete_poi(self):
        logger.debug("Deleteing POI from route DataFrame.")
        try:
            poi_id = st.session_state.selected_poi["poiId"]
            if st.session_state.route["poiId"].eq(poi_id).any():
                st.session_state.overview = self.add_poi_to_df(st.session_state.overview, st.session_state.selected_poi)
                logger.info("Added point to route POIs DataFrame.")
                st.session_state.route = self.remove_poi(st.session_state.route, poi_id)
            logger.info("Removed POI from route DataFrame.")
        except (KeyError, ValueError) as err:
            logger.error(err)

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

    def calculate_itinerary(self):
        st.session_state.ordered_route, st.session_state.distance = self.request_itinerary_type(
            st.session_state.itinerary_type,
            st.session_state.route,
            st.session_state.start_poi,
            st.session_state.end_poi,
        )
        st.session_state.route = st.session_state.ordered_route

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
                return self.one_way_trip_flex_end(pois, start)  # type: ignore[arg-type]
            case "One-way trip (fixed destination)":
                return self.one_way_trip_flex_fixed_end(pois, start, end)  # type: ignore[arg-type]
            case _:
                raise ValueError(f"'{itinerary_type}' is not a valid itinerary_type.")

    def roundtrip(self, pois: pd.DataFrame, start: str | None = None) -> tuple[pd.DataFrame, float]:
        params = self.prepare_params(pois, start)
        itinerary = handle_get_request("/tsp/shortest-round-tour", params)
        ordered_df = pois.set_index("poiId").loc[itinerary["poi_order"]].reset_index()
        ordered_df = pd.concat(
            [ordered_df, ordered_df.iloc[:1]],
            ignore_index=True,
        )
        return ordered_df, itinerary["total_distance"]

    def one_way_trip_flex_end(self, pois: pd.DataFrame, start: str) -> tuple[pd.DataFrame, float]:
        pois = pois.drop_duplicates(subset=["poiId", "label"], keep="first")
        params = self.prepare_params(pois, start)
        itinerary = handle_get_request("/tsp/shortest-path-no-return", params)
        ordered_df = pois.set_index("poiId").loc[itinerary["poi_order"]].reset_index()
        return ordered_df, itinerary["total_distance"]

    def one_way_trip_flex_fixed_end(self, pois: pd.DataFrame, start: str, end: str) -> tuple[pd.DataFrame, float]:
        pois = pois.drop_duplicates(subset=["poiId", "label"], keep="first")
        params = self.prepare_params(pois, start, end)
        logger.warning(params)
        itinerary = handle_get_request("/tsp/shortest-path-fixed-dest", params)
        ordered_df = pois.set_index("poiId").loc[itinerary["poi_order"]].reset_index()
        return ordered_df, itinerary["total_distance"]

    def prepare_params(
        self, pois: pd.DataFrame, poi_start: str | None = None, poi_end: str | None = None
    ) -> dict[str, Any]:
        if poi_start:
            poi_start = pois.loc[pois["label"] == poi_start, "poiId"].iloc[0]
        if poi_end:
            poi_end = pois.loc[pois["label"] == poi_end, "poiId"].iloc[0]
        poi_ids = pois["poiId"].tolist()
        if poi_start:
            logger.debug(f"Start POI {poi_start} is set. Removing it from existing list.")
            poi_ids.remove(poi_start)
            poi_ids = [poi_start] + poi_ids
        if poi_end:
            logger.debug(f"End POI {poi_end} is set. Removing it from existing list.")
            poi_ids.remove(poi_end)
            poi_ids += [poi_end]

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
