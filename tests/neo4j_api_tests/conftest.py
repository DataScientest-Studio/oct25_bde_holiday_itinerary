from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.backend.neo4j_api import app


@pytest.fixture
def mock_driver(monkeypatch):
    driver_mock = MagicMock()
    driver_mock.get_poi.return_value = {
        "id": "311be560-f8aa-3c3a-8d06-b24cb6809f57",
        "lat": 48.87621,
        "lon": 2.3392458,
    }
    driver_mock.get_nearby_points.return_value = {
        "nearby": [
            {"id": "311be560-f8aa-3c3a-8d06-b24cb6809f57"},
            {"id": "f10d82ab-7b39-30d1-bad4-3e08d9670926"},
            {"id": "ba53474b-b720-3e97-b475-9eeae5cdac13"},
        ]
    }
    driver_mock.calculate_distance_between_two_nodes.return_value = 100.0
    driver_mock.calculate_shortest_path_from_start_to_dest.return_value = {
        "poi_order": ["6d640ca5-e6df-3506-bfed-007661e44551", "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c"],
        "total_distance": 5510.640487130491,
    }
    driver_mock.calculate_shortest_round_tour.return_value = {
        "poi_order": [
            "6d640ca5-e6df-3506-bfed-007661e44551",
            "8e795fb1-0f36-34ca-ba08-1784a50cefdc",
            "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c",
        ],
        "total_distance": 13121.616547681424,
    }
    driver_mock.calculate_shortest_path_no_return.return_value = {
        "poi_order": [
            "6d640ca5-e6df-3506-bfed-007661e44551",
            "8e795fb1-0f36-34ca-ba08-1784a50cefdc",
            "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c",
        ],
        "total_distance": 7610.976060550933,
    }
    driver_mock.calculate_shortest_path_fixed_dest.return_value = {
        "poi_order": [
            "6d640ca5-e6df-3506-bfed-007661e44551",
            "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c",
            "8e795fb1-0f36-34ca-ba08-1784a50cefdc",
        ],
        "total_distance": 8717.794314578783,
    }
    monkeypatch.setattr("src.neo4j_api.main.Neo4jDriver", lambda: driver_mock)

    app.state.driver = driver_mock
    return driver_mock


@pytest.fixture
def client():
    return TestClient(app)
