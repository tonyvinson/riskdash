import json
import time

TEST_RISK_LIKELIHOOD_NAME = "First RiskLikelihood"
TEST_RISK_LIKELIHOOD_DESCRIPTION = "Risk Likelihood for Testing"
TEST_MODIFIED_RISK_LIKELIHOOD_NAME = "Modified -" + TEST_RISK_LIKELIHOOD_NAME
TEST_MODIFIED_RISK_LIKELIHOOD_DESCRIPTION = "Modified -" + TEST_RISK_LIKELIHOOD_DESCRIPTION


def test_create_risk_likelihood(client):
    data = {"name": TEST_RISK_LIKELIHOOD_NAME, "description": TEST_RISK_LIKELIHOOD_DESCRIPTION}

    response = client.post("/risk_likelihoods/", json.dumps(data))
    assert response.status_code == 200


def test_create_duplicate_risk_likelihood_raises_409(client):
    data = {"name": TEST_RISK_LIKELIHOOD_NAME, "description": TEST_RISK_LIKELIHOOD_DESCRIPTION}

    response = client.post("/risk_likelihoods/", json.dumps(data))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.post("/risk_likelihoods/", json.dumps(data))
    assert response.status_code == 409
    assert (
        f"Risk Likelihood with name '{TEST_RISK_LIKELIHOOD_NAME}' already exists" in response.text
    )


def test_get_all_risk_likelihoods(client):
    data = {"name": TEST_RISK_LIKELIHOOD_NAME, "description": TEST_RISK_LIKELIHOOD_DESCRIPTION}

    num_test_objects = 10
    for i in range(num_test_objects):
        data["name"] = data["name"] + f"-{i+1}"
        response = client.post("/risk_likelihoods/", json.dumps(data))
        assert response.status_code == 200

    response = client.get("/risk_likelihoods")
    assert response.status_code == 200
    assert len(list(response.json())) == num_test_objects


def test_retreive_risk_likelihood_by_id(client):
    data = {"name": TEST_RISK_LIKELIHOOD_NAME, "description": TEST_RISK_LIKELIHOOD_DESCRIPTION}

    response = client.post("/risk_likelihoods/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/risk_likelihoods/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_RISK_LIKELIHOOD_NAME
    assert response.json()["description"] == TEST_RISK_LIKELIHOOD_DESCRIPTION
    assert response.json()["last_updated_date"] is not None
    assert response.json()["created_date"] is not None
    assert response.json()["created_date"] == response.json()["last_updated_date"]


def test_retreive_risk_likelihood_by_id_not_found(client):
    response = client.get("/risk_likelihoods/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "RiskLikelihood with id 1 does not exist"


def test_update_risk_likelihood(client):
    data = {"name": TEST_RISK_LIKELIHOOD_NAME, "description": TEST_RISK_LIKELIHOOD_DESCRIPTION}

    response = client.post("/risk_likelihoods/", json.dumps(data))
    assert response.status_code == 200

    # Sleep for 1 second to ensure that the updated date would not still
    # equal the created date
    time.sleep(1)

    modification_data = {"name": TEST_MODIFIED_RISK_LIKELIHOOD_NAME}
    response = client.put("/risk_likelihoods/1", json.dumps(modification_data))
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated risk_likelihood."

    response = client.get("/risk_likelihoods/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_RISK_LIKELIHOOD_NAME
    assert response.json()["description"] == TEST_RISK_LIKELIHOOD_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]

    my_saved_last_updated_date = response.json()["last_updated_date"]

    time.sleep(1)
    modification_data = {"description": TEST_MODIFIED_RISK_LIKELIHOOD_DESCRIPTION}
    response = client.put("/risk_likelihoods/1", json.dumps(modification_data))
    print(f"Returned: {response.text}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated risk_likelihood."

    response = client.get("/risk_likelihoods/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_RISK_LIKELIHOOD_NAME
    assert response.json()["description"] == TEST_MODIFIED_RISK_LIKELIHOOD_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]
    assert my_saved_last_updated_date < response.json()["last_updated_date"]


def test_update_risk_likelihood_to_duplicate_raises_409(client):
    data = {"name": TEST_RISK_LIKELIHOOD_NAME, "description": TEST_RISK_LIKELIHOOD_DESCRIPTION}
    data2 = {"name": "Dog", "description": TEST_RISK_LIKELIHOOD_DESCRIPTION}

    response = client.post("/risk_likelihoods/", json.dumps(data))
    assert response.status_code == 200

    response = client.post("/risk_likelihoods/", json.dumps(data2))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.put("/risk_likelihoods/1", json.dumps(data2))
    assert response.status_code == 409
    assert f"Risk Likelihood with name 'Dog' already exists" in response.text


def test_delete_risk_likelihood(client):
    data = {"name": TEST_RISK_LIKELIHOOD_NAME, "description": TEST_RISK_LIKELIHOOD_DESCRIPTION}

    response = client.post("/risk_likelihoods/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/risk_likelihoods/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_RISK_LIKELIHOOD_NAME
    assert response.json()["description"] == TEST_RISK_LIKELIHOOD_DESCRIPTION

    response = client.delete("/risk_likelihoods/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted risk_likelihood."

    response = client.get("/risk_likelihoods/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "RiskLikelihood with id 1 does not exist"
