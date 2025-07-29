import json
import time

TEST_CONTROL_FAMILY_NAME = "First ControlFamily"
TEST_CONTROL_FAMILY_DESCRIPTION = "Control Family for Testing"
TEST_MODIFIED_CONTROL_FAMILY_NAME = "Modified -" + TEST_CONTROL_FAMILY_NAME
TEST_MODIFIED_CONTROL_FAMILY_DESCRIPTION = "Modified -" + TEST_CONTROL_FAMILY_DESCRIPTION


def test_create_control_family(client):
    data = {"name": TEST_CONTROL_FAMILY_NAME, "description": TEST_CONTROL_FAMILY_DESCRIPTION}

    response = client.post("/control_families/", json.dumps(data))
    assert response.status_code == 200


def test_create_duplicate_control_family_raises_409(client):
    data = {"name": TEST_CONTROL_FAMILY_NAME, "description": TEST_CONTROL_FAMILY_DESCRIPTION}

    response = client.post("/control_families/", json.dumps(data))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.post("/control_families/", json.dumps(data))
    assert response.status_code == 409
    assert f"Control Family with name '{TEST_CONTROL_FAMILY_NAME}' already exists" in response.text


def test_get_all_control_families(client):
    data = {"name": TEST_CONTROL_FAMILY_NAME, "description": TEST_CONTROL_FAMILY_DESCRIPTION}

    num_test_objects = 10
    for i in range(num_test_objects):
        data["name"] = data["name"] + f"-{i+1}"
        response = client.post("/control_families/", json.dumps(data))
        assert response.status_code == 200

    response = client.get("/control_families")
    assert response.status_code == 200
    assert len(list(response.json())) == num_test_objects


def test_retreive_control_family_by_id(client):
    data = {"name": TEST_CONTROL_FAMILY_NAME, "description": TEST_CONTROL_FAMILY_DESCRIPTION}

    response = client.post("/control_families/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/control_families/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_CONTROL_FAMILY_NAME
    assert response.json()["description"] == TEST_CONTROL_FAMILY_DESCRIPTION
    assert response.json()["last_updated_date"] is not None
    assert response.json()["created_date"] is not None
    assert response.json()["created_date"] == response.json()["last_updated_date"]


def test_retreive_control_family_by_id_not_found(client):
    response = client.get("/control_families/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "ControlFamily with id 1 does not exist"


def test_update_control_family(client):
    data = {"name": TEST_CONTROL_FAMILY_NAME, "description": TEST_CONTROL_FAMILY_DESCRIPTION}

    response = client.post("/control_families/", json.dumps(data))
    assert response.status_code == 200

    # Sleep for 1 second to ensure that the updated date would not still
    # equal the created date
    time.sleep(1)

    modification_data = {"name": TEST_MODIFIED_CONTROL_FAMILY_NAME}
    response = client.put("/control_families/1", json.dumps(modification_data))
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated control_family."

    response = client.get("/control_families/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_CONTROL_FAMILY_NAME
    assert response.json()["description"] == TEST_CONTROL_FAMILY_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]

    my_saved_last_updated_date = response.json()["last_updated_date"]

    time.sleep(1)
    modification_data = {"description": TEST_MODIFIED_CONTROL_FAMILY_DESCRIPTION}
    response = client.put("/control_families/1", json.dumps(modification_data))
    print(f"Returned: {response.text}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated control_family."

    response = client.get("/control_families/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_CONTROL_FAMILY_NAME
    assert response.json()["description"] == TEST_MODIFIED_CONTROL_FAMILY_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]
    assert my_saved_last_updated_date < response.json()["last_updated_date"]


def test_update_control_family_to_duplicate_raises_409(client):
    data = {"name": TEST_CONTROL_FAMILY_NAME, "description": TEST_CONTROL_FAMILY_DESCRIPTION}
    data2 = {"name": "Dog", "description": TEST_CONTROL_FAMILY_DESCRIPTION}

    response = client.post("/control_families/", json.dumps(data))
    assert response.status_code == 200

    response = client.post("/control_families/", json.dumps(data2))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.put("/control_families/1", json.dumps(data2))
    assert response.status_code == 409
    assert f"Control Family with name 'Dog' already exists" in response.text


def test_delete_control_family(client):
    data = {"name": TEST_CONTROL_FAMILY_NAME, "description": TEST_CONTROL_FAMILY_DESCRIPTION}

    response = client.post("/control_families/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/control_families/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_CONTROL_FAMILY_NAME
    assert response.json()["description"] == TEST_CONTROL_FAMILY_DESCRIPTION

    response = client.delete("/control_families/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted control_family."

    response = client.get("/control_families/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "ControlFamily with id 1 does not exist"
