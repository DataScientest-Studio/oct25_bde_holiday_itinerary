from datetime import date
from json import loads
from typing import Any

import pandas as pd
import streamlit as st
from requests import get
from requests.models import HTTPError
from st_aggrid import AgGrid

from logger import logger


def handle_get_request(target: str, query_params: dict[str, str] | None = None) -> dict[str, Any]:
    logger.info(f"Sending GET request to http://neo4j_api:8080{target} with params: {query_params}")
    try:
        response = get(f"http://neo4j_api:8080{target}", params=query_params)
        logger.debug(f"Received response returned status code {response.status_code}")

        match response.status_code:
            case 200:
                logger.success(f"GET request to http://neo4j_api:8080{target} succeeded")
                return loads(response.text)
            case _:
                logger.warning(f"GET request to {target} returned {response.status_code}")
                raise HTTPError(f"Request did not return 200. It returned {response.status_code}.")
    except Exception as e:
        logger.error(f"GET request to http://neo4j_api:8080{target} failed: {e}")
        raise


class UI:
    title_name: str = "Holiday Itinerary"
    layout: str = "wide"

    def __init__(self, pois: dict[str, Any] = {}) -> None:
        logger.debug("Initializing UI for holiday itinerary...")
        self.pois = pois

        st.set_page_config(page_title=self.title_name, layout=self.layout)
        logger.debug(f"Set page title to '{self.title_name}' and layout style to '{self.layout}'.")

        st.title(self.title_name)
        logger.debug(f"Set title to '{self.title_name}'.")

        self.__init_session_states()
        self.__init_layout()

        logger.success("Initialized UI.")

    def __init_session_states(self) -> None:
        logger.debug("Initializing session states...")
        keys = ["destinations", "categories", "pois"]
        values = [[], [], pd.DataFrame(self.pois)]
        for key, value in zip(keys, values):
            if not hasattr(st.session_state, key):
                setattr(st.session_state, key, value)
                logger.debug(f"Set {keys} to: {st.session_state.destinations}.")
            else:
                logger.debug(f"Load previous {key}: {st.session_state.destinations}.")

        logger.success("Initialized session_states.")

    def __init_layout(self) -> None:
        logger.debug("Initializing layout...")
        with st.container() as con:
            logger.debug("Created container for controls and poi overview.")
            self.__init_controls(con)
            self.__init_poi_overview_layout(con)
        logger.info("Initalized layout.")

    def __init_controls(self, con: st.container) -> None:
        logger.debug("Initializing controls...")

        destinations, categories, start, end = st.columns([2, 2, 1, 1])
        self.__init_filter(destinations, "destinations", "/city/all", "cities", "Itinerary Destinations")
        self.__init_filter(categories, "categories", "/poi/types", "types", "Category of POIs")
        self.__init_date_selector(start, "start")
        self.__init_date_selector(end, "end")

        logger.info("Initalized controls.")

    def __init_filter(self, cell: st.columns, key: str, path: str, data_key: str, label: str) -> None:
        logger.debug(f"Initializing {key} filter...")
        try:
            destinations = handle_get_request(path)[data_key]
            cell.multiselect(label, options=destinations, key=key)
            logger.info(f"Initalized {key} filter.")
        except Exception as e:
            logger.error(f"Failed to get '{key}' form the server. Error: {e}")

    def __init_date_selector(self, cell: st.columns, name: str) -> None:
        logger.debug(f"Initializing {name} selector...")
        cell.date_input(f"Itinerary {name}", value=date.today(), format="DD/MM/YYYY", key=name)
        logger.info(f"Initalized {name} selector.")

    def __init_poi_overview_layout(self, con: st.container) -> None:
        logger.debug("Initializing poi overview...")
        if not st.session_state.destinations and not st.session_state.categories:
            st.session_state.pois = pd.DataFrame({})
        try:
            params = {
                "locations": ",".join(st.session_state.destinations) or "",
                "types": ",".join(st.session_state.categories) or "",
            }
            pois = handle_get_request("/poi/filter", params).get("pois", [])
            st.session_state.pois = pd.DataFrame(pois)
            logger.info("Initalized poi overview.")
        except Exception:
            logger.error("Failed to get '/poi/filter' form the server.")
        finally:
            AgGrid(st.session_state)

    def run(self) -> None:
        logger.info("Starting UI.")


app = UI({})
app.run()
