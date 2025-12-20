from json import loads
from typing import Any

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

    def __init__(self) -> None:
        pass

    def run(self) -> None:
        pass


app = UI()
app.run()
