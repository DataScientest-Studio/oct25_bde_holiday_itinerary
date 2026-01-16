from typing import Any

import pandas as pd
import streamlit as st
from handlers import get_request
from loguru import logger


class Itinerary:
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
        itinerary = get_request("/tsp/shortest-round-tour", params)
        ordered_df = pois.set_index("poiId").loc[itinerary["poi_order"]].reset_index()
        ordered_df = pd.concat(
            [ordered_df, ordered_df.iloc[:1]],
            ignore_index=True,
        )
        return ordered_df, itinerary["total_distance"]

    def one_way_trip_flex_end(self, pois: pd.DataFrame, start: str) -> tuple[pd.DataFrame, float]:
        pois = pois.drop_duplicates(subset=["poiId", "label"], keep="first")
        params = self.prepare_params(pois, start)
        itinerary = get_request("/tsp/shortest-path-no-return", params)
        ordered_df = pois.set_index("poiId").loc[itinerary["poi_order"]].reset_index()
        return ordered_df, itinerary["total_distance"]

    def one_way_trip_flex_fixed_end(self, pois: pd.DataFrame, start: str, end: str) -> tuple[pd.DataFrame, float]:
        pois = pois.drop_duplicates(subset=["poiId", "label"], keep="first")
        params = self.prepare_params(pois, start, end)
        logger.warning(params)
        itinerary = get_request("/tsp/shortest-path-fixed-dest", params)
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
