from typing import Any

import numpy as np
from loguru import logger


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
