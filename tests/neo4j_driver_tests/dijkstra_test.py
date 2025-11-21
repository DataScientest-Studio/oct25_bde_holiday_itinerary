import pytest  # noqa F401


def test_shortest_path_from_start_to_dest(client, mock_driver):
    response = client.get(
        "/dijkstra?"
        "poi_ids=6d640ca5-e6df-3506-bfed-007661e44551"
        "&poi_ids=8e795fb1-0f36-34ca-ba08-1784a50cefdc"
        "&poi_ids=0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c"
    )
    assert response.status_code == 200
    assert response.json() == {
        "poi_order": ["6d640ca5-e6df-3506-bfed-007661e44551", "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c"],
        "total_distance": 5510.640487130491,
    }
    mock_driver.calculate_shortest_path_from_start_to_dest.assert_called_once_with(
        [
            "6d640ca5-e6df-3506-bfed-007661e44551",
            "8e795fb1-0f36-34ca-ba08-1784a50cefdc",
            "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c",
        ]
    )
