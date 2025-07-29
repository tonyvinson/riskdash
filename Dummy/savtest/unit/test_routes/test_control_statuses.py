import json
import time

TEST_CONTROL_STATUS_NAME = "First ControlStatus"
TEST_CONTROL_STATUS_DESCRIPTION = "Control Status for Testing"
TEST_MODIFIED_CONTROL_STATUS_NAME = "Modified -" + TEST_CONTROL_STATUS_NAME
TEST_MODIFIED_CONTROL_STATUS_DESCRIPTION = "Modified -" + TEST_CONTROL_STATUS_DESCRIPTION


def test_create_control_status(client):
    data = {"name": TEST_CONTROL_STATUS_NAME, "description": TEST_CONTROL_STATUS_DESCRIPTION}

    response = client.post("/control_statuses/", json.dumps(data))
    assert response.status_code == 200


def test_create_duplicate_control_status_raises_409(client):
    data = {"name": TEST_CONTROL_STATUS_NAME, "description": TEST_CONTROL_STATUS_DESCRIPTION}

    response = client.post("/control_statuses/", json.dumps(data))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.post("/control_statuses/", json.dumps(data))
    assert response.status_code == 409
    assert f"Control Status with name '{TEST_CONTROL_STATUS_NAME}' already exists" in response.text


def test_get_all_control_statuses(client):
    data = {"name": TEST_CONTROL_STATUS_NAME, "description": TEST_CONTROL_STATUS_DESCRIPTION}

    num_test_objects = 10
    for i in range(num_test_objects):
        data["name"] = data["name"] + f"-{i+1}"
        response = client.post("/control_statuses/", json.dumps(data))
        assert response.status_code == 200

    response = client.get("/control_statuses")
    assert response.status_code == 200
    assert len(list(response.json())) == num_test_objects


def test_retreive_control_status_by_id(client):
    data = {"name": TEST_CONTROL_STATUS_NAME, "description": TEST_CONTROL_STATUS_DESCRIPTION}

    response = client.post("/control_statuses/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/control_statuses/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_CONTROL_STATUS_NAME
    assert response.json()["description"] == TEST_CONTROL_STATUS_DESCRIPTION
    assert response.json()["last_updated_date"] is not None
    assert response.json()["created_date"] is not None
    assert response.json()["created_date"] == response.json()["last_updated_date"]


def test_retreive_control_status_by_id_not_found(client):
    response = client.get("/control_statuses/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "ControlStatus with id 1 does not exist"


def test_update_control_status(client):
    data = {"name": TEST_CONTROL_STATUS_NAME, "description": TEST_CONTROL_STATUS_DESCRIPTION}

    response = client.post("/control_statuses/", json.dumps(data))
    assert response.status_code == 200

    # Sleep for 1 second to ensure that the updated date would not still
    # equal the created date
    time.sleep(1)

    modification_data = {"name": TEST_MODIFIED_CONTROL_STATUS_NAME}
    response = client.put("/control_statuses/1", json.dumps(modification_data))
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated control_status."

    response = client.get("/control_statuses/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_CONTROL_STATUS_NAME
    assert response.json()["description"] == TEST_CONTROL_STATUS_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]

    my_saved_last_updated_date = response.json()["last_updated_date"]

    time.sleep(1)
    modification_data = {"description": TEST_MODIFIED_CONTROL_STATUS_DESCRIPTION}
    response = client.put("/control_statuses/1", json.dumps(modification_data))
    print(f"Returned: {response.text}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated control_status."

    response = client.get("/control_statuses/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_CONTROL_STATUS_NAME
    assert response.json()["description"] == TEST_MODIFIED_CONTROL_STATUS_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]
    assert my_saved_last_updated_date < response.json()["last_updated_date"]


def test_update_control_status_to_duplicate_raises_409(client):
    data = {"name": TEST_CONTROL_STATUS_NAME, "description": TEST_CONTROL_STATUS_DESCRIPTION}
    data2 = {"name": "Dog", "description": TEST_CONTROL_STATUS_DESCRIPTION}

    response = client.post("/control_statuses/", json.dumps(data))
    assert response.status_code == 200

    response = client.post("/control_statuses/", json.dumps(data2))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.put("/control_statuses/1", json.dumps(data2))
    assert response.status_code == 409
    assert f"Control Status with name 'Dog' already exists" in response.text


def test_delete_control_status(client):
    data = {"name": TEST_CONTROL_STATUS_NAME, "description": TEST_CONTROL_STATUS_DESCRIPTION}

    response = client.post("/control_statuses/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/control_statuses/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_CONTROL_STATUS_NAME
    assert response.json()["description"] == TEST_CONTROL_STATUS_DESCRIPTION

    response = client.delete("/control_statuses/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted control_status."

    response = client.get("/control_statuses/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "ControlStatus with id 1 does not exist"
