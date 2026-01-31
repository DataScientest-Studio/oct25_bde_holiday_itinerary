import ast

import streamlit as st
from loguru import logger
from ui.handlers import Handler


class PoiOverview:
    def __init__(self, handler: Handler):
        self.handler = handler
        with st.container(border=False, height=500):
            self.init_overview()
            self.add_button()

    def init_overview(self) -> None:
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
                st.write(self.parse_readable_string(poi["additional_information"]))
            if poi.get("homepage"):
                st.markdown(f"🌐 **Website**: [🌐 Visit website]({poi['homepage']})")
            logger.info("Initalized pois overview.")

    def add_button(self) -> None:
        logger.debug("Initializing add button...")
        with st.container(horizontal_alignment="right", vertical_alignment="bottom"):
            st.button("Add POI", on_click=self.handler.add_poi)
        logger.info("Initalized add button.")

    def parse_readable_string(self, raw: str) -> str:
        parsed = ast.literal_eval(raw)
        text = parsed[0]
        text = text.replace("\r\n", "\n").strip()
        return text
