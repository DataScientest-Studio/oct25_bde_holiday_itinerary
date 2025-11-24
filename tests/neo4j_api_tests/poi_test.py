import pytest  # noqa F401


def test_get_poi(client, mock_driver):
    response = client.get("/poi?poi_id=311be560-f8aa-3c3a-8d06-b24cb6809f57")
    assert response.status_code == 200
    assert response.json() == {
        "id": "311be560-f8aa-3c3a-8d06-b24cb6809f57",
        "lat": 48.87621,
        "lon": 2.3392458,
    }
    mock_driver.get_poi.assert_called_once_with("311be560-f8aa-3c3a-8d06-b24cb6809f57")


def test_get_nearby_points(client, mock_driver):
    response = client.get("/poi/nearby?poi_id=311be560-f8aa-3c3a-8d06-b24cb6809f56&radius=10")
    assert response.status_code == 200
    assert response.json() == {
        "nearby": [
            {"id": "311be560-f8aa-3c3a-8d06-b24cb6809f57"},
            {"id": "f10d82ab-7b39-30d1-bad4-3e08d9670926"},
            {"id": "ba53474b-b720-3e97-b475-9eeae5cdac13"},
        ]
    }
    mock_driver.get_nearby_points.assert_called_once_with("311be560-f8aa-3c3a-8d06-b24cb6809f56", 10)
