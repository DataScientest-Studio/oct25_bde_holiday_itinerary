from datetime import date

import streamlit as st
from loguru import logger
from ui.handlers import get_request


class Controls:
    def __init__(self) -> None:
        logger.debug("Initializing Controls...")
        st.subheader("Filter")
        self.init_filter("destinations", "/city/all", "cities", "Itinerary Destinations")
        self.init_filter("categories", "/poi/types", "types", "Category of POIs")
        self.init_date("start")
        self.init_date("end")
        self.init_radius_slider()

        logger.info("Initalized Controls.")

    def init_filter(self, key: str, path: str, data_key: str, label: str) -> None:
        logger.debug(f"Initializing {key} filter...")
        try:
            with st.container():
                result = get_request(path)[data_key]
                if key == "destinations":
                    st.session_state.cities = result
                    result = [city["name"] for city in result]
                st.multiselect(label, options=result, key=key)
                logger.info(f"Initalized {key} filter.")
        except Exception as err:
            logger.error(f"Failed to get '{key}' form the server. Error: {err}")

    def init_date(self, name: str) -> None:
        logger.debug(f"Initializing {name} selector...")
        with st.container():
            st.date_input(f"Itinerary {name}", value=date.today(), format="DD/MM/YYYY", key=name)
        logger.info(f"Initalized {name} selector.")

    def init_radius_slider(self) -> None:
        logger.debug("Initializing Radius Slider...")
        with st.container():
            st.slider("Distance from city", min_value=0, max_value=100, key="radius")
        logger.info("Initalized Radius Slider.")
