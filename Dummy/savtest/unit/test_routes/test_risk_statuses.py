import json
import time

TEST_RISK_STATUS_NAME = "First RiskStatus"
TEST_RISK_STATUS_DESCRIPTION = "Risk Status for Testing"
TEST_MODIFIED_RISK_STATUS_NAME = "Modified -" + TEST_RISK_STATUS_NAME
TEST_MODIFIED_RISK_STATUS_DESCRIPTION = "Modified -" + TEST_RISK_STATUS_DESCRIPTION


def test_create_risk_status(client):
    data = {"name": TEST_RISK_STATUS_NAME, "description": TEST_RISK_STATUS_DESCRIPTION}

    response = client.post("/risk_statuses/", json.dumps(data))
    assert response.status_code == 200


def test_create_duplicate_risk_status_raises_409(client):
    data = {"name": TEST_RISK_STATUS_NAME, "description": TEST_RISK_STATUS_DESCRIPTION}

    response = client.post("/risk_statuses/", json.dumps(data))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.post("/risk_statuses/", json.dumps(data))
    assert response.status_code == 409
    assert f"Risk Status with name '{TEST_RISK_STATUS_NAME}' already exists" in response.text


def test_get_all_risk_statuses(client):
    data = {"name": TEST_RISK_STATUS_NAME, "description": TEST_RISK_STATUS_DESCRIPTION}

    num_test_objects = 10
    for i in range(num_test_objects):
        data["name"] = data["name"] + f"-{i+1}"
        response = client.post("/risk_statuses/", json.dumps(data))
        assert response.status_code == 200

    response = client.get("/risk_statuses")
    assert response.status_code == 200
    assert len(list(response.json())) == num_test_objects


def test_retreive_risk_status_by_id(client):
    data = {"name": TEST_RISK_STATUS_NAME, "description": TEST_RISK_STATUS_DESCRIPTION}

    response = client.post("/risk_statuses/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/risk_statuses/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_RISK_STATUS_NAME
    assert response.json()["description"] == TEST_RISK_STATUS_DESCRIPTION
    assert response.json()["last_updated_date"] is not None
    assert response.json()["created_date"] is not None
    assert response.json()["created_date"] == response.json()["last_updated_date"]


def test_retreive_risk_status_by_id_not_found(client):
    response = client.get("/risk_statuses/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "RiskStatus with id 1 does not exist"


def test_update_risk_status(client):
    data = {"name": TEST_RISK_STATUS_NAME, "description": TEST_RISK_STATUS_DESCRIPTION}

    response = client.post("/risk_statuses/", json.dumps(data))
    assert response.status_code == 200

    # Sleep for 1 second to ensure that the updated date would not still
    # equal the created date
    time.sleep(1)

    modification_data = {"name": TEST_MODIFIED_RISK_STATUS_NAME}
    response = client.put("/risk_statuses/1", json.dumps(modification_data))
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated risk_status."

    response = client.get("/risk_statuses/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_RISK_STATUS_NAME
    assert response.json()["description"] == TEST_RISK_STATUS_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]

    my_saved_last_updated_date = response.json()["last_updated_date"]

    time.sleep(1)
    modification_data = {"description": TEST_MODIFIED_RISK_STATUS_DESCRIPTION}
    response = client.put("/risk_statuses/1", json.dumps(modification_data))
    print(f"Returned: {response.text}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated risk_status."

    response = client.get("/risk_statuses/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_RISK_STATUS_NAME
    assert response.json()["description"] == TEST_MODIFIED_RISK_STATUS_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]
    assert my_saved_last_updated_date < response.json()["last_updated_date"]


def test_update_risk_status_to_duplicate_raises_409(client):
    data = {"name": TEST_RISK_STATUS_NAME, "description": TEST_RISK_STATUS_DESCRIPTION}
    data2 = {"name": "Dog", "description": TEST_RISK_STATUS_DESCRIPTION}

    response = client.post("/risk_statuses/", json.dumps(data))
    assert response.status_code == 200

    response = client.post("/risk_statuses/", json.dumps(data2))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.put("/risk_statuses/1", json.dumps(data2))
    assert response.status_code == 409
    assert f"Risk Status with name 'Dog' already exists" in response.text


def test_delete_risk_status(client):
    data = {"name": TEST_RISK_STATUS_NAME, "description": TEST_RISK_STATUS_DESCRIPTION}

    response = client.post("/risk_statuses/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/risk_statuses/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_RISK_STATUS_NAME
    assert response.json()["description"] == TEST_RISK_STATUS_DESCRIPTION

    response = client.delete("/risk_statuses/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted risk_status."

    response = client.get("/risk_statuses/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "RiskStatus with id 1 does not exist"
