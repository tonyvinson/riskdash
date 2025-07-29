import json
import time

TEST_KEYWORD_NAME = "Test Keyword"
TEST_MODIFIED_KEYWORD_NAME = "Modified - " + TEST_KEYWORD_NAME


def test_create_keyword(client):
    data = {"name": TEST_KEYWORD_NAME}

    response = client.post("/keywords/", json.dumps(data))
    assert response.status_code == 200


def test_create_duplicate_keyword_raises_409(client):
    data = {"name": TEST_KEYWORD_NAME}

    response = client.post("/keywords/", json.dumps(data))
    assert response.status_code == 200

    # Now attempt to create a keyword with the exact same name - should return status_code 409
    response = client.post("/keywords/", json.dumps(data))
    assert response.status_code == 409
    assert f"Keyword with name '{TEST_KEYWORD_NAME}' already exists" in response.text


def test_get_all_keywords(client):
    data = {"name": TEST_KEYWORD_NAME}

    num_test_objects = 10
    for i in range(num_test_objects):
        data["name"] = data["name"] + f"-{i+1}"
        response = client.post("/keywords/", json.dumps(data))
        assert response.status_code == 200

    response = client.get("/keywords")
    assert response.status_code == 200
    assert len(list(response.json())) == num_test_objects


def test_retreive_keyword_by_id(client):
    data = {"name": TEST_KEYWORD_NAME}

    client.post("/keywords/", json.dumps(data))

    response = client.get("/keywords/1")

    assert response.status_code == 200
    assert response.json()["name"] == TEST_KEYWORD_NAME
    assert response.json()["last_updated_date"] is not None
    assert response.json()["created_date"] is not None
    assert response.json()["created_date"] == response.json()["last_updated_date"]


def test_retreive_keyword_by_id_not_found(client):
    response = client.get("/keywords/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Keyword with id 1 does not exist"


def test_update_keyword(client):
    data = {"name": TEST_KEYWORD_NAME}

    response = client.post("/keywords/", json.dumps(data))
    assert response.status_code == 200

    # Sleep for 1 second to ensure that the updated date would not still
    # equal the created date
    time.sleep(1)

    modification_data = {"name": TEST_MODIFIED_KEYWORD_NAME}
    response = client.put("/keywords/1", json.dumps(modification_data))
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated keyword."

    response = client.get("/keywords/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_KEYWORD_NAME
    assert response.json()["last_updated_date"] is not None
    assert response.json()["created_date"] is not None
    assert response.json()["created_date"] < response.json()["last_updated_date"]


def test_update_keyword_to_duplicate_raises_409(client):
    data = {"name": TEST_KEYWORD_NAME}
    data2 = {"name": "Dog"}

    response = client.post("/keywords/", json.dumps(data))
    assert response.status_code == 200

    response = client.post("/keywords/", json.dumps(data2))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.put("/keywords/1", json.dumps(data2))
    assert response.status_code == 409
    assert f"Keyword with name 'Dog' already exists" in response.text


def test_delete_keyword(client):
    data = {"name": TEST_KEYWORD_NAME}

    response = client.post("/keywords/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/keywords/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_KEYWORD_NAME

    response = client.delete("/keywords/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted keyword."

    response = client.get("/keywords/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Keyword with id 1 does not exist"
