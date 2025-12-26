from datetime import date

import pandas as pd
import pydeck as pdk
import streamlit as st
from handler import Handler, handle_get_request

from logger import logger


class UI:
    title_name: str = "Holiday Itinerary"
    layout: str = "wide"
    poi_cols: list[str] = [
        "label",
        "city",
        "description",
        "street",
        "postal_code",
        "homepage",
        "additional_information",
        "comment",
        "latitude",
        "longitude",
        "poiId",
    ]
    handler: Handler = Handler()

    def __init__(self) -> None:
        logger.debug("Initializing UI for holiday itinerary...")

        st.set_page_config(page_title=self.title_name, layout=self.layout)
        logger.debug(f"Set page title to '{self.title_name}' and layout style to '{self.layout}'.")

        st.title(self.title_name)
        logger.debug(f"Set title to '{self.title_name}'.")

        self.__init_session_states()
        self.__init_layout()

        logger.success("Initialized UI.")

    def __init_session_states(self) -> None:
        if hasattr(st.session_state, "_initialized"):
            logger.info("session_state already initialized. Skipping...")
            return
        logger.debug("Initializing session states...")
        keys = [
            "cities",
            "destinations",
            "categories",
            "overview",
            "selected_poi",
            "add_point",
            "route",
            "old_params",
            "itinerary-type" "start-poi",
            "end-poi",
        ]
        values = [
            {},
            [],
            [],
            self.init_empty_pois_dataframe(),
            None,
            None,
            self.init_empty_pois_dataframe(),
            {},
            "",
            "",
            "",
        ]
        for key, value in zip(keys, values):
            if not hasattr(st.session_state, key):
                setattr(st.session_state, key, value)
                logger.debug(f"Set {key} to: {getattr(st.session_state, key)}.")

        st.session_state._initialized = True
        logger.info("Initialized session_states.")

    def init_empty_pois_dataframe(self) -> pd.DataFrame:
        df = pd.DataFrame(columns=self.poi_cols)
        df.fillna("", inplace=True)
        return df

    def __init_layout(self) -> None:
        logger.info("Initializing layout...")
        overview, poi_view = st.columns([8, 3], border=True)

        with overview:
            controls, pois_overview = st.columns([2, 7])
            with controls:
                self.__init_controls()
            with pois_overview:
                self.__init_pois_overview_layout()
        with poi_view:
            self.__init_poi_overview_layout()
            self.__init_poi_add_button()
        logger.info("Initialized overview sections.")

        map_grid, route = st.columns([8, 2], border=True)
        with map_grid:
            self.__init_map()
        with route:
            self.__init_route()
        logger.info("Initialized route sections.")
        logger.info("Initalized layout.")

    def __init_poi_add_button(self) -> None:
        logger.debug("Initializing add button...")
        with st.container(horizontal_alignment="right", vertical_alignment="bottom"):
            st.button("Add POI", on_click=self.add_poi)
        logger.info("Initalized add button.")

    def __init_controls(self) -> None:
        logger.debug("Initializing controls...")
        st.subheader("Filter")
        self.__init_filter("destinations", "/city/all", "cities", "Itinerary Destinations")
        self.__init_filter("categories", "/poi/types", "types", "Category of POIs")
        self.__init_date_selector("start")
        self.__init_date_selector("end")
        self.__init_radius_handler()

        logger.info("Initalized controls.")

    def __init_filter(self, key: str, path: str, data_key: str, label: str) -> None:
        logger.debug(f"Initializing {key} filter...")
        try:
            with st.container():
                result = handle_get_request(path)[data_key]
                if key == "destinations":
                    st.session_state.cities = result
                    result = [city["Id"] for city in result]
                st.multiselect(label, options=result, key=key)
                logger.info(f"Initalized {key} filter.")
        except Exception as err:
            logger.error(f"Failed to get '{key}' form the server. Error: {err}")

    def __init_date_selector(self, name: str) -> None:
        logger.debug(f"Initializing {name} selector...")
        with st.container():
            st.date_input(f"Itinerary {name}", value=date.today(), format="DD/MM/YYYY", key=name)
        logger.info(f"Initalized {name} selector.")

    def __init_radius_handler(self) -> None:
        logger.debug("Initializing radius handler...")
        with st.container():
            st.slider("Distance from city", min_value=0, max_value=100, key="radius-filter")
        logger.info("Initalized radius handler.")

    def __init_pois_overview_layout(self) -> None:
        logger.debug("Initializing pois overview...")
        if st.session_state.destinations or st.session_state.categories:
            params = {
                "locations": st.session_state.destinations or "",
                "types": st.session_state.categories or "",
            }
            if params != st.session_state.old_params:
                try:
                    pois = handle_get_request("/poi/filter", params).get("pois", {})
                    st.session_state.overview = (
                        pd.DataFrame(pois, columns=self.poi_cols) if pois else self.init_empty_pois_dataframe()
                    )
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

    def __init_map(self) -> None:
        logger.debug("Initializing map...")

        df_cities = pd.DataFrame(st.session_state.cities)

        min_lat, max_lat = df_cities["lat"].min(), df_cities["lat"].max()
        min_lon, max_lon = df_cities["lon"].min(), df_cities["lon"].max()

        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2

        cities_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_cities,
            get_position="[lon, lat]",
            get_color="[200, 30, 0, 160]",
            get_radius=5000,
            pickable=True,
        )

        r = pdk.Deck(
            layers=[cities_layer],
            initial_view_state=pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=5, height=734),
            tooltip={"text": "{name}"},
        )

        st.pydeck_chart(r, height=734)

        logger.info("initalized map.")

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
            with start:
                st.selectbox(
                    "Start POI",
                    options=self.__generate_possible_nodes("end-poi"),
                    key="start-poi",
                )
            with end:
                st.selectbox(
                    "End POI",
                    options=self.__generate_possible_nodes("start-poi"),
                    key="end-poi",
                )

    def __generate_possible_nodes(self, key_to_exclude) -> list[str]:
        options = st.session_state.route["label"]
        filtered = options[options != st.session_state[key_to_exclude]].tolist()
        if filtered:
            return [""] + filtered
        return filtered

    def __create_route_type_and_submit_button_controller(self) -> None:
        with st.container():
            route, button = st.columns([1, 1], vertical_alignment="bottom")
            with route:
                st.selectbox("Select itinerary type", options=["Roundtour", "Shortestpath"], key="itinerary-type")
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
        pass

    def run(self) -> None:
        logger.info("Starting UI.")
