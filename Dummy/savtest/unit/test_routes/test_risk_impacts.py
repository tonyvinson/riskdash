import json
import time

TEST_RISK_IMPACT_NAME = "First RiskImpact"
TEST_RISK_IMPACT_DESCRIPTION = "Risk Impact for Testing"
TEST_MODIFIED_RISK_IMPACT_NAME = "Modified -" + TEST_RISK_IMPACT_NAME
TEST_MODIFIED_RISK_IMPACT_DESCRIPTION = "Modified -" + TEST_RISK_IMPACT_DESCRIPTION


def test_create_risk_impact(client):
    data = {"name": TEST_RISK_IMPACT_NAME, "description": TEST_RISK_IMPACT_DESCRIPTION}

    response = client.post("/risk_impacts/", json.dumps(data))
    assert response.status_code == 200


def test_create_duplicate_risk_impact_raises_409(client):
    data = {"name": TEST_RISK_IMPACT_NAME, "description": TEST_RISK_IMPACT_DESCRIPTION}

    response = client.post("/risk_impacts/", json.dumps(data))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.post("/risk_impacts/", json.dumps(data))
    assert response.status_code == 409
    assert f"Risk Impact with name '{TEST_RISK_IMPACT_NAME}' already exists" in response.text


def test_get_all_risk_impacts(client):
    data = {"name": TEST_RISK_IMPACT_NAME, "description": TEST_RISK_IMPACT_DESCRIPTION}

    num_test_objects = 10
    for i in range(num_test_objects):
        data["name"] = data["name"] + f"-{i+1}"
        response = client.post("/risk_impacts/", json.dumps(data))
        assert response.status_code == 200

    response = client.get("/risk_impacts")
    assert response.status_code == 200
    assert len(list(response.json())) == num_test_objects


def test_retreive_risk_impact_by_id(client):
    data = {"name": TEST_RISK_IMPACT_NAME, "description": TEST_RISK_IMPACT_DESCRIPTION}

    response = client.post("/risk_impacts/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/risk_impacts/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_RISK_IMPACT_NAME
    assert response.json()["description"] == TEST_RISK_IMPACT_DESCRIPTION
    assert response.json()["last_updated_date"] is not None
    assert response.json()["created_date"] is not None
    assert response.json()["created_date"] == response.json()["last_updated_date"]


def test_retreive_risk_impact_by_id_not_found(client):
    response = client.get("/risk_impacts/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "RiskImpact with id 1 does not exist"


def test_update_risk_impact(client):
    data = {"name": TEST_RISK_IMPACT_NAME, "description": TEST_RISK_IMPACT_DESCRIPTION}

    response = client.post("/risk_impacts/", json.dumps(data))
    assert response.status_code == 200

    # Sleep for 1 second to ensure that the updated date would not still
    # equal the created date
    time.sleep(1)

    modification_data = {"name": TEST_MODIFIED_RISK_IMPACT_NAME}
    response = client.put("/risk_impacts/1", json.dumps(modification_data))
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated risk_impact."

    response = client.get("/risk_impacts/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_RISK_IMPACT_NAME
    assert response.json()["description"] == TEST_RISK_IMPACT_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]

    my_saved_last_updated_date = response.json()["last_updated_date"]

    time.sleep(1)
    modification_data = {"description": TEST_MODIFIED_RISK_IMPACT_DESCRIPTION}
    response = client.put("/risk_impacts/1", json.dumps(modification_data))
    print(f"Returned: {response.text}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated risk_impact."

    response = client.get("/risk_impacts/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_RISK_IMPACT_NAME
    assert response.json()["description"] == TEST_MODIFIED_RISK_IMPACT_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]
    assert my_saved_last_updated_date < response.json()["last_updated_date"]


def test_update_risk_impact_to_duplicate_raises_409(client):
    data = {"name": TEST_RISK_IMPACT_NAME, "description": TEST_RISK_IMPACT_DESCRIPTION}
    data2 = {"name": "Dog", "description": TEST_RISK_IMPACT_DESCRIPTION}

    response = client.post("/risk_impacts/", json.dumps(data))
    assert response.status_code == 200

    response = client.post("/risk_impacts/", json.dumps(data2))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.put("/risk_impacts/1", json.dumps(data2))
    assert response.status_code == 409
    assert f"Risk Impact with name 'Dog' already exists" in response.text


def test_delete_risk_impact(client):
    data = {"name": TEST_RISK_IMPACT_NAME, "description": TEST_RISK_IMPACT_DESCRIPTION}

    response = client.post("/risk_impacts/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/risk_impacts/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_RISK_IMPACT_NAME
    assert response.json()["description"] == TEST_RISK_IMPACT_DESCRIPTION

    response = client.delete("/risk_impacts/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted risk_impact."

    response = client.get("/risk_impacts/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "RiskImpact with id 1 does not exist"
