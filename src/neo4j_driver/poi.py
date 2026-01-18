from typing import Any

from loguru import logger


class POI:

    def get_poi(self, poi_id: str) -> dict[Any, Any]:
        logger.info(f"Get POI {poi_id}")
        query = """
            MATCH (p:POI {poiId: $poi_id})
            RETURN p
            LIMIT 1
        """
        poi = self.execute_query(query, poi_id=poi_id)  # type: ignore[attr-defined]
        return poi[0]["p"] if poi else {}
