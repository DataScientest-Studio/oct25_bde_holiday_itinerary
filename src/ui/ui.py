import streamlit as st
from handler import Handler
from session_states import init_session_states
from widgets.controls import Controls
from widgets.map import Map
from widgets.poi_overview import PoiOverview
from widgets.pois_overview import PoisOverview
from widgets.route import Route

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
            PoiOverview(self.handler)
        logger.info("Initialized overview sections.")

        map_grid, route = st.columns([6, 2], border=True)
        with map_grid:
            Map()
        with route:
            Route(self.handler)
        logger.info("Initialized route sections.")
        logger.info("Initalized layout.")

    def run(self) -> None:
        logger.info("Starting UI.")
