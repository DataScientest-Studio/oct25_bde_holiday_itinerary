from typing import Any

from loguru import logger


class CityPois:
    city: dict[str, Any]
    pois: list[dict[str, Any]]

    def __init__(self, city: dict[str, Any], poi: dict[str, Any]) -> None:
        self.city = city
        self.pois = [poi]

    def append(self, city: dict[str, Any], poi: dict[str, Any]) -> bool:
        logger.info("Trying to append poi to CityPois Instance.")
        if self.city["cityId"] == city["cityId"]:
            self.pois.append(poi)
            return True
        return False
