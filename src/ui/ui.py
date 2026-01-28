import streamlit as st

from logger import logger
from ui.handlers import Handler
from ui.layout import Layout
from ui.session_states import init_session_states


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

        Layout(self.handler)

        logger.success("Initialized UI.")

    def run(self) -> None:
        logger.info("Starting UI.")
