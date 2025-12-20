from json import loads
from typing import Any

import streamlit as st
from requests import get
from requests.models import HTTPError

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

    def __init__(self) -> None:
        logger.debug("Initializing UI for holiday itinerary ... ")

        st.set_page_config(page_title=self.title_name, layout=self.layout)
        logger.debug(f"Set page title to '{self.title_name}' and layout to '{self.layout}'.")

        st.title(self.title_name)
        logger.debug(f"Set title to '{self.title_name}'.")

        logger.success("Initialized UI.")

    def run(self) -> None:
        logger.info("Starting UI.")


app = UI()
app.run()
