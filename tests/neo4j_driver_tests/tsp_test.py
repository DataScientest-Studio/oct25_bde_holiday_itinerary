import pytest  # noqa F401


def test_shortest_round_tour(client, mock_driver):
    response = client.get(
        "/tsp/shortest-round-tour?"
        "poi_ids=6d640ca5-e6df-3506-bfed-007661e44551"
        "&poi_ids=8e795fb1-0f36-34ca-ba08-1784a50cefdc"
        "&poi_ids=0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c"
    )
    assert response.status_code == 200
    assert response.json() == {
        "poi_order": [
            "6d640ca5-e6df-3506-bfed-007661e44551",
            "8e795fb1-0f36-34ca-ba08-1784a50cefdc",
            "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c",
        ],
        "total_distance": 13121.616547681424,
    }
    mock_driver.calculate_shortest_round_tour.assert_called_once_with(
        [
            "6d640ca5-e6df-3506-bfed-007661e44551",
            "8e795fb1-0f36-34ca-ba08-1784a50cefdc",
            "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c",
        ]
    )


def test_shortest_path_no_return(client, mock_driver):
    response = client.get(
        "/tsp/shortest-path-no-return?"
        "poi_ids=6d640ca5-e6df-3506-bfed-007661e44551"
        "&poi_ids=8e795fb1-0f36-34ca-ba08-1784a50cefdc"
        "&poi_ids=0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c"
    )
    assert response.status_code == 200
    assert response.json() == {
        "poi_order": [
            "6d640ca5-e6df-3506-bfed-007661e44551",
            "8e795fb1-0f36-34ca-ba08-1784a50cefdc",
            "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c",
        ],
        "total_distance": 7610.976060550933,
    }
    mock_driver.calculate_shortest_path_no_return.assert_called_once_with(
        [
            "6d640ca5-e6df-3506-bfed-007661e44551",
            "8e795fb1-0f36-34ca-ba08-1784a50cefdc",
            "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c",
        ]
    )


def test_shortest_path_fixed_dest(client, mock_driver):
    response = client.get(
        "/tsp/shortest-path-fixed-dest?"
        "poi_ids=6d640ca5-e6df-3506-bfed-007661e44551"
        "&poi_ids=8e795fb1-0f36-34ca-ba08-1784a50cefdc"
        "&poi_ids=0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c"
        "&dest=8e795fb1-0f36-34ca-ba08-1784a50cefdc"
    )
    assert response.status_code == 200
    assert response.json() == {
        "poi_order": [
            "6d640ca5-e6df-3506-bfed-007661e44551",
            "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c",
            "8e795fb1-0f36-34ca-ba08-1784a50cefdc",
        ],
        "total_distance": 8717.794314578783,
    }
    mock_driver.calculate_shortest_path_fixed_dest.assert_called_once_with(
        "8e795fb1-0f36-34ca-ba08-1784a50cefdc",
        [
            "6d640ca5-e6df-3506-bfed-007661e44551",
            "8e795fb1-0f36-34ca-ba08-1784a50cefdc",
            "0b155dd7-9f4b-3b69-a221-42b4ae3c0f4c",
        ],
    )
