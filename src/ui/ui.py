import pandas as pd
import streamlit as st
from config import POI_COLUMNS
from handler import Handler, handle_get_request
from map import Map
from session_states import init_session_states
from utils import init_empty_df
from widgets.controls import Controls
from widgets.pois_overview import PoisOverview

from logger import logger


class UI:
    title_name: str = "Holiday Itinerary"
    layout: str = "wide"
    handler: Handler = Handler()

    def __init__(self) -> None:
        logger.debug("Initializing UI for holiday itinerary...")

        st.set_page_config(page_title=self.title_name, layout=self.layout)
        logger.debug(f"Set page title to '{self.title_name}' and layout style to '{self.layout}'.")

        st.title(self.title_name)
        logger.debug(f"Set title to '{self.title_name}'.")

        init_session_states()

        self.__init_layout()

        logger.success("Initialized UI.")

    def __init_layout(self) -> None:
        logger.info("Initializing layout...")
        overview, poi_view = st.columns([8, 3], border=True)

        with overview:
            controls, pois_overview = st.columns([2, 7])
            with controls:
                Controls()
            with pois_overview:
                PoisOverview()
        with poi_view:
            with st.container(border=False, height=500):
                self.__init_poi_overview_layout()
                self.__init_poi_add_button()
        logger.info("Initialized overview sections.")

        map_grid, route = st.columns([6, 2], border=True)
        with map_grid:
            Map()
        with route:
            self.__init_route()
        logger.info("Initialized route sections.")
        logger.info("Initalized layout.")

    def __init_poi_add_button(self) -> None:
        logger.debug("Initializing add button...")
        with st.container(horizontal_alignment="right", vertical_alignment="bottom"):
            st.button("Add POI", on_click=self.add_poi)
        logger.info("Initalized add button.")

    def __init_pois_overview_layout(self) -> None:
        logger.debug("Initializing pois overview...")
        if st.session_state.destinations or st.session_state.categories:
            params = {
                "locations": st.session_state.destinations or "",
                "types": st.session_state.categories or "",
                "radius": st.session_state.radius * 1000,
            }
            if params != st.session_state.old_params:
                try:
                    pois = handle_get_request("/poi/filter", params).get("pois", {})
                    st.session_state.overview = pd.DataFrame(pois, columns=POI_COLUMNS) if pois else init_empty_df()
                    st.session_state.overview.fillna("", inplace=True)
                    st.session_state.old_params = params
                    logger.info("Initalized poi overview.")
                except Exception:
                    logger.error("Failed to get '/poi/filter' form the server.")

        key = "overview-pois"
        _ = st.dataframe(
            st.session_state.overview,
            key=key,
            height=500,
            hide_index=True,
            column_order=["label", "city", "description"],
            column_config={
                "label": st.column_config.TextColumn(
                    "POI",
                    width=100,
                    help="The label of the POI.",
                ),
                "city": st.column_config.TextColumn(
                    "Location",
                    width=100,
                    help="Location of the POI.",
                ),
                "description": st.column_config.TextColumn(
                    "Description",
                    help="Description of the POI.",
                ),
            },
            on_select=lambda: self.select_row(key),
            selection_mode="single-row",
            placeholder="-",
        )

    def __init_poi_overview_layout(self) -> None:
        with st.container(border=False, height=435):
            logger.debug("Initializing pois overview...")
            if st.session_state.selected_poi is None:
                st.subheader("POI Overview")
                return

            poi = st.session_state.selected_poi

            st.subheader(poi["label"])
            st.caption(f"📍 {poi['street']}, {poi['postal_code']} {poi['city']}")
            st.markdown("🌳 **Description**")
            st.write(poi["description"] or "Point of interest has no description.")
            if poi.get("additional_information"):
                st.markdown("ℹ️ **Additional Information**")
                st.write(poi["additional_information"])
            if poi.get("homepage"):
                st.markdown(f"🌐 **Website**: [🌐 Visit website]({poi['homepage']})")
            logger.info("Initalized pois overview.")

    def __init_route(self) -> None:
        logger.debug("Initializing route pois...")
        with st.container():
            key = "route-pois"
            _ = st.dataframe(
                st.session_state.route,
                key=key,
                height=500,
                hide_index=True,
                column_order=["label", "city"],
                column_config={
                    "label": st.column_config.TextColumn(
                        "POI",
                        help="The label of the POI.",
                    ),
                    "city": st.column_config.TextColumn(
                        "Location",
                        help="Location of the POI.",
                    ),
                },
                on_select=lambda: self.select_row(key),
                selection_mode="single-row",
                placeholder="-",
            )
        with st.container():
            self.__init_route_controller()
        logger.info("initalized route pois.")

    def __init_route_controller(self) -> None:
        logger.debug("Initializing route controller...")
        self.__create_start_and_end_node_controller()
        self.__create_route_type_and_submit_button_controller()
        with st.container(horizontal_alignment="right", vertical_alignment="bottom"):
            st.button("Delete POI", on_click=self.delete_poi)
        logger.info("Initialized route controller...")

    def __create_start_and_end_node_controller(self) -> None:
        with st.container():
            start, end = st.columns([1, 1], vertical_alignment="bottom")

            start_options = self.__generate_possible_nodes("end_poi")
            end_options = self.__generate_possible_nodes("start_poi")

            with start:
                st.selectbox(
                    "Start POI",
                    options=start_options,
                    key="start_poi",
                    index=(
                        start_options.index(st.session_state.start_poi)
                        if st.session_state.get("start_poi") in start_options
                        else None
                    ),
                    placeholder="Select start POI",
                )

            with end:
                st.selectbox(
                    "End POI",
                    options=end_options,
                    key="end_poi",
                    index=(
                        end_options.index(st.session_state.end_poi)
                        if st.session_state.get("end_poi") in end_options
                        else None
                    ),
                    placeholder="Select end POI",
                )

    def __generate_possible_nodes(self, key_to_exclude) -> list[str]:
        options = st.session_state.route["label"]
        filtered = options[options != st.session_state[key_to_exclude]].tolist()
        return filtered

    def __create_route_type_and_submit_button_controller(self) -> None:
        with st.container():
            route, button = st.columns([1, 1], vertical_alignment="bottom")
            with route:
                st.selectbox(
                    "Select itinerary type",
                    options=[
                        "Round trip",
                        "One-way trip (flexible end)",
                        "One-way trip (fixed destination)",
                    ],
                    key="itinerary_type",
                )
            with button:
                with st.container(horizontal_alignment="right", vertical_alignment="bottom"):
                    st.button("Calculate route", on_click=self._handle_calculate_itinerary)

    def add_poi(self) -> None:
        logger.debug("Adding POI to route DataFrame.")
        try:
            st.session_state.route = self.handler.add_poi(st.session_state.route, st.session_state.selected_poi)
            logger.info("Added point to route POIs DataFrame.")
            st.session_state.overview = self.handler.remove_poi(
                st.session_state.overview, st.session_state.selected_poi.poiId
            )
            logger.info("Removed POI from pois DataFrame.")
        except (KeyError, ValueError) as err:
            logger.error(err)

    def delete_poi(self):
        logger.debug("Deleteing POI from route DataFrame.")
        try:
            poi_id = st.session_state.selected_poi["poiId"]
            if st.session_state.route["poiId"].eq(poi_id).any():
                st.session_state.overview = self.handler.add_poi(
                    st.session_state.overview, st.session_state.selected_poi
                )
                logger.info("Added point to route POIs DataFrame.")
                st.session_state.route = self.handler.remove_poi(st.session_state.route, poi_id)
            logger.info("Removed POI from route DataFrame.")
        except (KeyError, ValueError) as err:
            logger.error(err)

    def select_row(self, key) -> None:
        df, _ = key.split("-")
        rows = st.session_state[key]["selection"]["rows"]
        if rows is not None:
            index = rows[0]
            st.session_state.selected_poi = st.session_state[df].iloc[index]
            logger.debug(f"Selected row {st.session_state.selected_poi} in dataframe '{df}'")

    def _handle_calculate_itinerary(self):
        st.session_state.ordered_route, st.session_state.distance = self.handler.request_itinerary_type(
            st.session_state.itinerary_type,
            st.session_state.route,
            st.session_state.start_poi,
            st.session_state.end_poi,
        )
        st.session_state.route = st.session_state.ordered_route
        logger.debug(st.session_state.route)

    def run(self) -> None:
        logger.info("Starting UI.")
