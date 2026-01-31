from typing import Any, List

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

    def get_types(self) -> dict[str, Any]:
        logger.info("Get all possible types.")
        query = "MATCH (t:Type) RETURN t.typeId AS typeId"
        types = self.execute_query(query)  # type: ignore[attr-defined]

        return {"types": [t["typeId"] for t in types] if types else []}

    def get_poi_for_city(self, city_id: str, categories: List | None = None) -> List[dict[str, Any]]:
        logger.info(f"Get all pois in city {city_id}.")
        query = """
        MATCH (c:City {cityId: $city_id}) <- [r:IS_IN] - (p:POI) - [is_a:IS_A] -> (t:POIType)
        WHERE $categories IS NULL or t.typeId in $categories
        RETURN p, collect(distinct t.typeId) as types
        """
        pois = self.execute_query(query, city_id=city_id, categories=categories)  # type: ignore[attr-defined]
        return [p["p"] | {"types": p["types"]} for p in pois] if pois else [{}]

    def get_poi_near_city(self, city_id: str, categories: List | None = None) -> List[dict[str, Any]]:
        logger.info(f"Get all pois near city {city_id}.")
        query = """
        MATCH (c:City {cityId: $city_id}) <- [r:IS_NEARBY] - (p:POI) - [is_a:IS_A] -> (t:POIType)
        WHERE $categories IS NULL or t.typeId in $categories
        RETURN p, r.km as distance_km, collect(distinct t.typeId) as types
        ORDER BY distance_km ASC
        """
        pois = self.execute_query(query, city_id=city_id, categories=categories)  # type: ignore[attr-defined]
        return [p["p"] | {"distance_km": p["distance_km"], "types": p["types"]} for p in pois] if pois else [{}]

    def get_poi_types_for_city(self, city_id: str, categories: List | None = None) -> List[str]:
        logger.info(f"Get POI types for city {city_id}.")
        query = """
        MATCH (c:City {cityId: $city_id}) <- [r:IS_IN] - (p:POI) - [is_a:IS_A] -> (t:POIType)
        RETURN collect(distinct t.typeId) as types
        """
        result = self.execute_query(query, city_id=city_id)  # type: ignore[attr-defined]
        return result[0]["types"]

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
