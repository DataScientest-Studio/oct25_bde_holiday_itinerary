import numpy as np
import pytest  # noqa F401


def test_execute_query(neo4j_driver, csv_file_rows):
    row = csv_file_rows[0]
    query = "MATCH (p:Poi {id: $poi_id}) RETURN p.id AS id"
    result = neo4j_driver.execute_query(query, poi_id=row["id"])
    assert result[0]["id"] == row["id"]


def test_get_poi(neo4j_driver, csv_file_rows):
    row = csv_file_rows[0]
    poi = neo4j_driver.get_poi(row["id"])
    assert poi["id"] == row["id"]
    assert poi["label"] == row["label"]
    assert poi["comment"] == row["comment"]
    assert poi["types"] == row["types"].split(",")
    assert poi["homepage"] == row["homepage"]
    assert poi["city"] == row["city"]
    assert poi["postal_code"] == row["postal_code"]
    assert poi["street"] == row["street"]
    assert poi["lat"] == float(row["lat"])
    assert poi["lon"] == float(row["long"])
    assert poi["additional_information"] == row["additional_information"]


def test_get_nearby_points(neo4j_driver, csv_file_rows):
    poi_id = csv_file_rows[0]["id"]
    nearby = neo4j_driver.get_nearby_points(poi_id, radius=1000)
    assert isinstance(nearby, dict)
    assert "nearby" in nearby
    for poi in nearby["nearby"]:
        assert poi["id"] != poi_id


def test_calculate_distance_between_two_nodes(neo4j_driver, csv_file_rows):
    poi1, poi2 = csv_file_rows[0]["id"], csv_file_rows[1]["id"]
    dist = neo4j_driver.calculate_distance_between_two_nodes(poi1, poi2)
    assert isinstance(dist, float)
    assert dist >= 0


def test_create_weight_matrix(neo4j_driver, csv_file_rows):
    poi_ids = [row["id"] for row in csv_file_rows[:3]]
    weights = neo4j_driver.create_weight_matrix(poi_ids)
    assert isinstance(weights, np.ndarray)
    assert weights.shape == (3, 3)
    for i in range(3):
        assert np.isinf(weights[i][i])


def test_calculate_tsp(neo4j_driver, csv_file_rows):
    poi_ids = [row["id"] for row in csv_file_rows[:3]]
    weights = neo4j_driver.create_weight_matrix(poi_ids)
    result = neo4j_driver.calculate_tsp(weights, poi_ids)
    assert "poi_order" in result and "total_distance" in result
    assert set(result["poi_order"]) == set(poi_ids)
    assert result["total_distance"] >= 0


def test_calculate_shortest_path_no_return(neo4j_driver, csv_file_rows):
    poi_ids = [row["id"] for row in csv_file_rows[:3]]
    result = neo4j_driver.calculate_shortest_path_no_return(poi_ids)
    assert "poi_order" in result
    assert "total_distance" in result


def test_calculate_shortest_round_tour(neo4j_driver, csv_file_rows):
    poi_ids = [row["id"] for row in csv_file_rows[:3]]
    result = neo4j_driver.calculate_shortest_round_tour(poi_ids)
    assert "poi_order" in result
    assert "total_distance" in result


def test_create_and_delete_edges(neo4j_driver, csv_file_rows):
    poi_ids = [row["id"] for row in csv_file_rows[:3]]
    neo4j_driver.create_edges(poi_ids)
    query = "MATCH (p1:Poi)-[e:CONNECTED]->(p2:Poi) RETURN count(e) AS cnt"
    count = neo4j_driver.execute_query(query)[0]["cnt"]
    assert count > 0

    neo4j_driver.delete_edges(poi_ids)
    count_after = neo4j_driver.execute_query(query)[0]["cnt"]
    assert count_after == 0


def test_calculate_shortest_path_from_start_to_dest(neo4j_driver, csv_file_rows):
    poi_ids = [row["id"] for row in csv_file_rows[:3]]
    result = neo4j_driver.calculate_shortest_path_from_start_to_dest(poi_ids)
    assert "poi_order" in result
    assert "total_distance" in result
    assert result["poi_order"][0] == poi_ids[0]
    assert result["poi_order"][-1] == poi_ids[-1]
