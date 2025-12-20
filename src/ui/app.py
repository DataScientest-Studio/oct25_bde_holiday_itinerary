from json import loads
from typing import Any

from requests import get
from requests.models import HTTPError
from streamlit import columns, container, session_state, set_page_config, title

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

    def __init__(self, pois: dict[str, Any]) -> None:
        logger.debug("Initializing UI for holiday itinerary...")

        set_page_config(page_title=self.title_name, layout=self.layout)
        logger.debug(f"Set page title to '{self.title_name}' and layout style to '{self.layout}'.")

        title(self.title_name)
        logger.debug(f"Set title to '{self.title_name}'.")

        self.__init_layout()

        logger.success("Initialized UI.")

    def __init_session_states(self) -> None:
        logger.debug("Initializing session states...")
        if "destinations" not in session_state:
            session_state.destinations = []

        logger.success("Initialized session_states.")

    def __init_layout(self) -> None:
        logger.debug("Initializing layout...")
        self.__init_controls()
        self.__init_data_layout()
        logger.info("Initalized layout.")

    def __init_data_layout(self) -> None:
        logger.debug("Initializing data section...")
        self.__init_controls()

        logger.info("Initalized data section.")

    def __init_controls(self) -> None:
        logger.debug("Initializing controls...")
        with container as con:
            logger.debug("Created container for controls.")
            destinations, _, _, _, _ = con.columns([])
            self.__init_destination_filter(destinations)

        logger.info("Initalized controls.")

    def __init_destination_filter(self, cell: columns) -> None:
        logger.debug("Initializing destination filter...")
        try:
            destinations = handle_get_request("/city/")["cities"]
            cell.multiselect("Itinerary Destinations", options=destinations, key="destinations")
            logger.info("Initalized destination filter.")
        except Exception:
            logger.error("Failed to get destinations form the server.")

    def run(self) -> None:
        logger.info("Starting UI.")


app = UI({})
app.run()
