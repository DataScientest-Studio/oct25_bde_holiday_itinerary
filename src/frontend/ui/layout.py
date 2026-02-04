import streamlit as st
from loguru import logger
from ui.handlers import Handler
from ui.widgets import Controls, Map, PoiOverview, PoisOverview, Route


class Layout:
    def __init__(self, handler: Handler) -> None:
        logger.debug("Initializing Layout...")
        overview, poi_view = st.columns([8, 3], border=True)

        with overview:
            controls, pois_overview = st.columns([2, 7])
            with controls:
                Controls()
            with pois_overview:
                PoisOverview()
        with poi_view:
            PoiOverview(handler)
        logger.info("Initialized overview sections.")

        map_grid, route = st.columns([4, 2], border=True)
        with map_grid:
            Map()
        with route:
            Route(handler)
        logger.info("Initialized route sections.")
        logger.info("Initalized layout.")
