import json
import time

TEST_FREQUENCY_NAME = "First Frequency"
TEST_FREQUENCY_DESCRIPTION = "Frequency for Testing"
TEST_MODIFIED_FREQUENCY_NAME = "Modified -" + TEST_FREQUENCY_NAME
TEST_MODIFIED_FREQUENCY_DESCRIPTION = "Modified -" + TEST_FREQUENCY_DESCRIPTION


def test_create_frequency(client):
    data = {"name": TEST_FREQUENCY_NAME, "description": TEST_FREQUENCY_DESCRIPTION}

    response = client.post("/frequencies/", json.dumps(data))
    assert response.status_code == 200


def test_create_duplicate_frequency_raises_409(client):
    data = {"name": TEST_FREQUENCY_NAME, "description": TEST_FREQUENCY_DESCRIPTION}

    response = client.post("/frequencies/", json.dumps(data))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.post("/frequencies/", json.dumps(data))
    assert response.status_code == 409
    assert f"Frequency with name '{TEST_FREQUENCY_NAME}' already exists" in response.text


def test_get_all_frequencies(client):
    data = {"name": TEST_FREQUENCY_NAME, "description": TEST_FREQUENCY_DESCRIPTION}

    num_test_objects = 10
    for i in range(num_test_objects):
        data["name"] = data["name"] + f"-{i+1}"
        response = client.post("/frequencies/", json.dumps(data))
        assert response.status_code == 200

    response = client.get("/frequencies")
    assert response.status_code == 200
    assert len(list(response.json())) == num_test_objects


def test_retreive_frequency_by_id(client):
    data = {"name": TEST_FREQUENCY_NAME, "description": TEST_FREQUENCY_DESCRIPTION}

    response = client.post("/frequencies/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/frequencies/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_FREQUENCY_NAME
    assert response.json()["description"] == TEST_FREQUENCY_DESCRIPTION
    assert response.json()["last_updated_date"] is not None
    assert response.json()["created_date"] is not None
    assert response.json()["created_date"] == response.json()["last_updated_date"]


def test_retreive_frequency_by_id_not_found(client):
    response = client.get("/frequencies/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Frequency with id 1 does not exist"


def test_update_frequency(client):
    data = {"name": TEST_FREQUENCY_NAME, "description": TEST_FREQUENCY_DESCRIPTION}

    response = client.post("/frequencies/", json.dumps(data))
    assert response.status_code == 200

    # Sleep for 1 second to ensure that the updated date would not still
    # equal the created date
    time.sleep(1)

    modification_data = {"name": TEST_MODIFIED_FREQUENCY_NAME}
    response = client.put("/frequencies/1", json.dumps(modification_data))
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated frequency."

    response = client.get("/frequencies/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_FREQUENCY_NAME
    assert response.json()["description"] == TEST_FREQUENCY_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]

    my_saved_last_updated_date = response.json()["last_updated_date"]

    time.sleep(1)
    modification_data = {"description": TEST_MODIFIED_FREQUENCY_DESCRIPTION}
    response = client.put("/frequencies/1", json.dumps(modification_data))
    print(f"Returned: {response.text}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated frequency."

    response = client.get("/frequencies/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_FREQUENCY_NAME
    assert response.json()["description"] == TEST_MODIFIED_FREQUENCY_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]
    assert my_saved_last_updated_date < response.json()["last_updated_date"]


def test_update_frequency_to_duplicate_raises_409(client):
    data = {"name": TEST_FREQUENCY_NAME, "description": TEST_FREQUENCY_DESCRIPTION}
    data2 = {"name": "Dog", "description": TEST_FREQUENCY_DESCRIPTION}

    response = client.post("/frequencies/", json.dumps(data))
    assert response.status_code == 200

    response = client.post("/frequencies/", json.dumps(data2))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.put("/frequencies/1", json.dumps(data2))
    assert response.status_code == 409
    assert f"Frequency with name 'Dog' already exists" in response.text


def test_delete_frequency(client):
    data = {"name": TEST_FREQUENCY_NAME, "description": TEST_FREQUENCY_DESCRIPTION}

    response = client.post("/frequencies/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/frequencies/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_FREQUENCY_NAME
    assert response.json()["description"] == TEST_FREQUENCY_DESCRIPTION

    response = client.delete("/frequencies/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted frequency."

    response = client.get("/frequencies/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Frequency with id 1 does not exist"
