from typing import Any

import pandas as pd
import streamlit as st
from loguru import logger

from .get_request import get_request


class Itinerary:
    def calculate_itinerary(self):
        st.session_state.ordered_route, st.session_state.distance, st.session_state.route_coords = (
            self.request_itinerary_type(
                st.session_state.itinerary_type,
                st.session_state.route,
                st.session_state.start_city,
                st.session_state.dest_city,
            )
        )
        st.session_state.route = st.session_state.route.sort_values(
            "poiId", key=lambda col: pd.Categorical(col, categories=st.session_state.ordered_route, ordered=True)
        ).reset_index(drop=True)

    def request_itinerary_type(
        self, itinerary_type: str, pois: pd.DataFrame, start: str | None = None, end: str | None = None
    ) -> tuple[pd.DataFrame, float, list[list[float]]]:
        if pois.shape[0] < 3:
            logger.error("At least 3 POIs are needed.")
            raise ValueError("Given POIs are not enough for a route.")
        match itinerary_type:
            case "Round trip":
                return self.roundtrip(pois, start)
            case "One-way trip (fixed start)":
                return self.one_way_trip_flex_end(pois, start)  # type: ignore[arg-type]
            case "One-way trip (fixed end)":
                return self.one_way_trip_flex_fixed_end(pois, start, end)  # type: ignore[arg-type]
            case _:
                raise ValueError(f"'{itinerary_type}' is not a valid itinerary_type.")

    def roundtrip(self, pois: pd.DataFrame, start: str | None = None) -> tuple[pd.DataFrame, float, list[list[float]]]:
        params = self.prepare_params(pois, start)
        itinerary = get_request("/tsp/shortest-round-tour", params)
        itinerary["route"].append(itinerary["route"][0])
        return itinerary["poi_order"], itinerary["total_distance"], itinerary["route"]

    def one_way_trip_flex_end(self, pois: pd.DataFrame, start: str) -> tuple[pd.DataFrame, float, list[list[float]]]:
        pois = pois.drop_duplicates(subset=["poiId", "label"], keep="first")
        params = self.prepare_params(pois, start)
        itinerary = get_request("/tsp/shortest-path-no-return", params)
        return itinerary["poi_order"], itinerary["total_distance"], itinerary["route"]

    def one_way_trip_flex_fixed_end(
        self, pois: pd.DataFrame, start: str, end: str
    ) -> tuple[pd.DataFrame, float, list[list[float]]]:
        pois = pois.drop_duplicates(subset=["poiId", "label"], keep="first")
        params = self.prepare_params(pois, start, end)
        logger.warning(params)
        itinerary = get_request("/tsp/shortest-path-fixed-dest", params)
        return itinerary["poi_order"], itinerary["total_distance"], itinerary["route"]

    def prepare_params(self, pois: pd.DataFrame, start: str | None = None, dest: str | None = None) -> dict[str, Any]:
        if start:
            start = pois.loc[pois["city"] == start, "poiId"].iloc[0]
        if dest:
            dest = pois.loc[pois["city"] == dest, "poiId"].iloc[0]
        poi_ids = pois["poiId"].tolist()
        if start:
            logger.debug(f"Start POI {start} is set. Removing it from existing list.")
            poi_ids.remove(start)
            poi_ids = [start] + poi_ids
        if dest:
            logger.debug(f"End POI {dest} is set. Removing it from existing list.")
            poi_ids.remove(dest)
            poi_ids += [dest]

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
