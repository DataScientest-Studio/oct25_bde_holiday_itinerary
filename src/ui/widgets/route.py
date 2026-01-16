import streamlit as st
from loguru import logger

from ui.handlers import Handler
from ui.utils import select_overview_df


class Route:
    def __init__(self, handler: Handler) -> None:
        self.handler = handler
        self.route()

    def route(self) -> None:
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
                        width=100,
                        help="The label of the POI.",
                    ),
                    "city": st.column_config.TextColumn(
                        "Location",
                        help="Location of the POI.",
                    ),
                },
                on_select=lambda: select_overview_df(key),
                selection_mode="single-row",
                placeholder="-",
            )
        with st.container():
            self.controller()
        logger.info("initalized route pois.")

    def controller(self) -> None:
        logger.debug("Initializing route controller...")
        self.create_controllers()
        self.create_submit_button()
        with st.container(horizontal_alignment="right", vertical_alignment="bottom"):
            st.button("Delete POI", on_click=self.handler.delete_poi)
        logger.info("Initialized route controller...")

    def create_controllers(self) -> None:
        with st.container():
            start, end = st.columns([1, 1], vertical_alignment="bottom")

            start_options = self.generate_nodes("end_poi")
            end_options = self.generate_nodes("start_poi")

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

    def generate_nodes(self, key_to_exclude) -> list[str]:
        options = st.session_state.route["label"]
        filtered = options[options != st.session_state[key_to_exclude]].tolist()
        return filtered

    def create_submit_button(self) -> None:
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
                    st.button("Calculate route", on_click=self.handler.calculate_itinerary)
