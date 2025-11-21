import pytest  # noqa F401


def test_get_poi(client, mock_driver):
    response = client.get(
        "/distance?poi1_id=311be560-f8aa-3c3a-8d06-b24cb6809f57&poi2_id=541be560-f8aa-3c3a-8d06-b24cb6809f57"
    )
    assert response.status_code == 200
    assert response.json() == {"distance": 100.0}
    mock_driver.calculate_distance_between_two_nodes.assert_called_once_with(
        "311be560-f8aa-3c3a-8d06-b24cb6809f57", "541be560-f8aa-3c3a-8d06-b24cb6809f57"
    )
