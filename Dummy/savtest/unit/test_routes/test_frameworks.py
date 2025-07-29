import json
import time

TEST_FRAMEWORK_NAME = "First Framework"
TEST_FRAMEWORK_DESCRIPTION = "Framework for Testing"
TEST_MODIFIED_FRAMEWORK_NAME = "Modified -" + TEST_FRAMEWORK_NAME
TEST_MODIFIED_FRAMEWORK_DESCRIPTION = "Modified -" + TEST_FRAMEWORK_DESCRIPTION


def test_create_framework(client):
    data = {"name": TEST_FRAMEWORK_NAME, "description": TEST_FRAMEWORK_DESCRIPTION}

    response = client.post("/frameworks/", json.dumps(data))
    assert response.status_code == 200


def test_create_duplicate_framework_raises_409(client):
    data = {"name": TEST_FRAMEWORK_NAME, "description": TEST_FRAMEWORK_DESCRIPTION}

    response = client.post("/frameworks/", json.dumps(data))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.post("/frameworks/", json.dumps(data))
    assert response.status_code == 409
    assert f"Framework with name '{TEST_FRAMEWORK_NAME}' already exists" in response.text


def test_get_all_frameworks(client):
    data = {"name": TEST_FRAMEWORK_NAME, "description": TEST_FRAMEWORK_DESCRIPTION}

    num_test_objects = 10
    for i in range(num_test_objects):
        data["name"] = data["name"] + f"-{i+1}"
        response = client.post("/frameworks/", json.dumps(data))
        assert response.status_code == 200

    response = client.get("/frameworks")
    assert response.status_code == 200
    assert len(list(response.json())) == num_test_objects


def test_retreive_framework_by_id(client):
    data = {"name": TEST_FRAMEWORK_NAME, "description": TEST_FRAMEWORK_DESCRIPTION}

    response = client.post("/frameworks/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/frameworks/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_FRAMEWORK_NAME
    assert response.json()["description"] == TEST_FRAMEWORK_DESCRIPTION
    assert response.json()["last_updated_date"] is not None
    assert response.json()["created_date"] is not None
    assert response.json()["created_date"] == response.json()["last_updated_date"]


def test_retreive_framework_by_id_not_found(client):
    response = client.get("/frameworks/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Framework with id 1 does not exist"


def test_update_framework(client):
    data = {"name": TEST_FRAMEWORK_NAME, "description": TEST_FRAMEWORK_DESCRIPTION}

    response = client.post("/frameworks/", json.dumps(data))
    assert response.status_code == 200

    # Sleep for 1 second to ensure that the updated date would not still
    # equal the created date
    time.sleep(1)

    modification_data = {"name": TEST_MODIFIED_FRAMEWORK_NAME}
    response = client.put("/frameworks/1", json.dumps(modification_data))
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated framework."

    response = client.get("/frameworks/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_FRAMEWORK_NAME
    assert response.json()["description"] == TEST_FRAMEWORK_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]

    my_saved_last_updated_date = response.json()["last_updated_date"]

    time.sleep(1)
    modification_data = {"description": TEST_MODIFIED_FRAMEWORK_DESCRIPTION}
    response = client.put("/frameworks/1", json.dumps(modification_data))
    print(f"Returned: {response.text}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated framework."

    response = client.get("/frameworks/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_FRAMEWORK_NAME
    assert response.json()["description"] == TEST_MODIFIED_FRAMEWORK_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]
    assert my_saved_last_updated_date < response.json()["last_updated_date"]


def test_update_framework_to_duplicate_raises_409(client):
    data = {"name": TEST_FRAMEWORK_NAME, "description": TEST_FRAMEWORK_DESCRIPTION}
    data2 = {"name": "Dog", "description": TEST_FRAMEWORK_DESCRIPTION}

    response = client.post("/frameworks/", json.dumps(data))
    assert response.status_code == 200

    response = client.post("/frameworks/", json.dumps(data2))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.put("/frameworks/1", json.dumps(data2))
    assert response.status_code == 409
    assert f"Framework with name 'Dog' already exists" in response.text


def test_delete_framework(client):
    data = {"name": TEST_FRAMEWORK_NAME, "description": TEST_FRAMEWORK_DESCRIPTION}

    response = client.post("/frameworks/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/frameworks/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_FRAMEWORK_NAME
    assert response.json()["description"] == TEST_FRAMEWORK_DESCRIPTION

    response = client.delete("/frameworks/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted framework."

    response = client.get("/frameworks/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Framework with id 1 does not exist"
