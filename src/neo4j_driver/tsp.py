from typing import Any

import numpy as np
from loguru import logger
from python_tsp.exact import solve_tsp_dynamic_programming


class TSP:
    def create_weight_matrix(self, cities: list[str]) -> np.ndarray[Any, Any]:
        logger.info("Creating weight matrix...")
        logger.debug(f"Cities: {cities}")
        n = len(cities)
        weights: list[list[float]] = np.full((n, n), np.inf)
        for i in range(0, n):
            start = cities[i]
            for j in range(i + 1, n):
                dest = cities[j]
                if start == dest:
                    continue
                weights[i][j] = self.get_total_distance_between_cities(  # type: ignore[attr-defined]
                    start=start, dest=dest
                )
                weights[j][i] = weights[i][j]
        logger.info("Created weight matrix.")
        logger.debug(f"Matrix: {weights}.")
        return weights

    def calculate_shortest_round_tour(self, poi_ids: list[str]) -> dict[str, list[str] | float]:
        logger.info("Calculating round tour...")
        cities = self.get_cities_for_poiIds(poi_ids)["cities"]  # type: ignore[attr-defined]
        weights = self.create_weight_matrix(cities)
        return self.calculate_tsp(weights, cities)

    def calculate_tsp(
        self, weights: np.ndarray[Any, Any], cities: list[str]
    ) -> dict[str, list[str] | float | list[list[float]]]:
        logger.info("Calculated tsp...")
        permutation, distance = solve_tsp_dynamic_programming(weights)
        logger.debug(f"Permuation: {permutation}, distance: {distance}")
        return {
            "city_order": [cities[i] for i in permutation],
            "total_distance": distance,
            "route": self.get_city_route(cities),  # type: ignore[attr-defined]
        }

    def calculate_shortest_path_no_return(self, poi_ids: list[str]) -> dict[str, list[str] | float]:
        logger.info("Calculating round tour with no return and fixed start...")
        cities = self.get_cities_for_poiIds(poi_ids)["cities"]
        weights = self.create_weight_matrix(cities)
        weights[:, 0] = 0
        return self.calculate_tsp(weights, cities)

    def calculate_shortest_path_fixed_dest(self, poi_ids: list[str]) -> dict[str, list[str] | float]:
        logger.info("Calculating round tour with no return and fixed destination...")
        dest = poi_ids.pop()
        logger.debug(f"dest: {dest}")
        poi_ids.insert(0, dest)
        tsp_result = self.calculate_shortest_path_no_return(poi_ids)
        tsp_result["city_order"] = list(reversed(tsp_result["city_order"]))  # type: ignore[arg-type]
        tsp_result["route"] = list(reversed(tsp_result["route"]))  # type: ignore[arg-type]
        return tsp_result
