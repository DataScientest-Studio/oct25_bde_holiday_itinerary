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

        self.__init_session_states()
        self.__init_layout()

        logger.success("Initialized UI.")

    def __init_session_states(self) -> None:
        logger.debug("Initializing session states...")
        keys = ["destinations", "categories", "start", "end"]
        values = [[], [], "", ""]
        for key, value in zip(keys, values):
            if not hasattr(session_state, key):
                setattr(session_state, key, value)
                logger.debug(f"Set {keys} to: {session_state.destinations}.")
            else:
                logger.debug(f"Load previous {key}: {session_state.destinations}.")

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
            destinations, categories, start, end, submit = con.columns([])
            self.__init_filter(destinations, "destinations", "/cities/", "cities", "Itinerary Destinations")
            self.__init_filter(categories, "categories", "/poi/types/", "types", "Category of POIs")
            self.__init_date_selector(start, "start")
            self.__init_date_selector(end, "end")
            if submit.button("Plan Itinerary"):
                self.plan_itinerary()

        logger.info("Initalized controls.")

    def __init_filter(self, cell: columns, key: str, path: str, data_key: str, label: str) -> None:
        logger.debug(f"Initializing {key} filter...")
        try:
            destinations = handle_get_request(path)[data_key]
            cell.multiselect(label, options=destinations, key=key)
            logger.info(f"Initalized {key} filter.")
        except Exception:
            logger.error(f"Failed to get {key} form the server.")

    def __init_date_selector(self, cell: columns, name: str) -> None:
        logger.debug(f"Initializing {name} selector...")
        cell.date_input(f"Itinerary {name}", format="DD/MM/YYYY", key=name)
        logger.info(f"Initalized {name} selector.")

    def plan_itinerary(self) -> None:
        logger.success("You are wonderful. You are capable of pressing a button. Congratulations!")

    def run(self) -> None:
        logger.info("Starting UI.")


app = UI({})
app.run()
