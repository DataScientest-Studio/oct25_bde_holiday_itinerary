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

    def get_filtered_pois(self, locations: list[str] | None, types: list[str] | None, radius: int) -> dict[str, Any]:
        logger.info("Get POIs for ui.")

        locations = self.normalize_param(locations)
        types = self.normalize_param(types)

        kwargs: dict[str, Any] = {
            "locations": locations or None,
            "types": types or None,
            "radius": radius,
        }

        logger.debug(f"POI filters: {kwargs}")

        if radius > 0:
            query = """
                CALL {
                    MATCH (n:POI)-[:IS_A]->(tFilter:POIType)
                    WHERE ($locations IS NULL OR n.city IN $locations)
                        AND ($types IS NULL OR tFilter.typeId IN $types)
                    RETURN n

                    UNION

                    MATCH (c:City)
                    WHERE c.name IN $locations
                    WITH point({latitude: c.latitude, longitude: c.longitude}) AS cityPoint
                    MATCH (n:POI)-[:IS_A]->(tFilter:POIType)
                    WHERE point.distance(
                            cityPoint,
                            point({latitude: n.latitude, longitude: n.longitude})
                          ) <= $radius
                        AND ($types IS NULL OR tFilter.typeId IN $types)
                    RETURN n
                }
                WITH DISTINCT n
                ORDER BY n.city, n.label
                MATCH (n)-[:IS_A]->(tAll:POIType)
                WITH n, collect(DISTINCT tAll.typeId) AS poiTypes
                RETURN collect(n { .*, types: apoc.text.join(poiTypes, ", ") }) AS pois
            """
        else:
            query = """
                MATCH (n:POI)-[:IS_A]->(tFilter:POIType)
                WHERE ($locations IS NULL OR n.city IN $locations)
                    AND ($types IS NULL OR tFilter.typeId IN $types)
                MATCH (n)-[:IS_A]->(tAll:POIType)
                WITH n, collect(DISTINCT tAll.typeId) AS poiTypes
                RETURN collect(n { .*, types: apoc.text.join(poiTypes, ", ") }) AS pois
            """

        result = self.execute_query(query, **kwargs)  # type: ignore[attr-defined]
        return result[0] if result else []  # type: ignore

    def normalize_param(self, values: list[str] | None) -> list[str] | None:
        if not values:
            return None
        cleaned = [v.strip() for v in values if v and v.strip()]
        return cleaned or None

    def get_nearby_points(self, poi_id: str, radius: float) -> dict[str, list[dict[Any, Any]]]:
        logger.info(f"Get POI around POI {poi_id} in a radius of {radius}.")
        query = """
            MATCH (p1:POI {poiId: $poi_id})
            MATCH (p2:POI)
            WHERE p1 <> p2
                AND point.distance(p1.location, p2.location) <= $radius
            RETURN
                p2.poiId AS poiId,
                p2.label AS label,
                p2.comment AS comment,
                p2.description AS description,
                p2.types AS types,
                p2.homepage AS homepage,
                p2.city AS city,
                p2.postal_code AS postal_code,
                p2.street AS street,
                p2.location.latitude AS lat,
                p2.location.longitude AS lon,
                p2.additional_information AS additional_information
        """
        records = self.execute_query(query, poi_id=poi_id, radius=radius)  # type: ignore[attr-defined]
        return {"nearby": records if records else []}
