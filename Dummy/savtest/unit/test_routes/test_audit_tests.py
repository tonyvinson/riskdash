import json
import time

from fedrisk_api.db.project import create_project

TEST_AUDIT_TEST_NAME = "First AuditTest"
TEST_AUDIT_TEST_DESCRIPTION = "AuditTest for Testing"
TEST_MODIFIED_AUDIT_TEST_NAME = "Modified -" + TEST_AUDIT_TEST_NAME
TEST_MODIFIED_AUDIT_TEST_DESCRIPTION = "Modified -" + TEST_AUDIT_TEST_DESCRIPTION

TEST_PROJECT_NAME = "First Project"
TEST_PROJECT_DESCRIPTION = "First Project Description"


def create_project(client):
    # We need to create a project . . .
    project_data = {"name": TEST_PROJECT_NAME, "description": TEST_PROJECT_DESCRIPTION}
    response = client.post("/projects/", json.dumps(project_data))
    print(response.text)
    assert response.status_code == 200


def test_create_audit_test(client):
    create_project(client)

    data = {
        "name": TEST_AUDIT_TEST_NAME,
        "description": TEST_AUDIT_TEST_DESCRIPTION,
        "project_id": 1,
    }
    print("about to post create_audit_test...")
    response = client.post("/audit_tests/", json.dumps(data))
    print(response.text)
    print(data)
    assert response.status_code == 200


def test_create_duplicate_audit_test_raises_409(client):
    create_project(client)

    data = {
        "name": TEST_AUDIT_TEST_NAME,
        "description": TEST_AUDIT_TEST_DESCRIPTION,
        "project_id": 1,
    }

    response = client.post("/audit_tests/", json.dumps(data))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.post("/audit_tests/", json.dumps(data))
    assert response.status_code == 409
    assert f"AuditTest with name '{TEST_AUDIT_TEST_NAME}' already exists" in response.text


def test_get_all_audit_tests(client):
    create_project(client)

    data = {
        "name": TEST_AUDIT_TEST_NAME,
        "description": TEST_AUDIT_TEST_DESCRIPTION,
        "project_id": 1,
    }

    num_test_objects = 10
    for i in range(num_test_objects):
        data["name"] = data["name"] + f"-{i+1}"
        response = client.post("/audit_tests/", json.dumps(data))
        assert response.status_code == 200

    response = client.get("/audit_tests")
    assert response.status_code == 200
    assert len(list(response.json())) == num_test_objects


def test_retreive_audit_test_by_id(client):
    create_project(client)

    data = {
        "name": TEST_AUDIT_TEST_NAME,
        "description": TEST_AUDIT_TEST_DESCRIPTION,
        "project_id": 1,
    }

    response = client.post("/audit_tests/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/audit_tests/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_AUDIT_TEST_NAME
    assert response.json()["description"] == TEST_AUDIT_TEST_DESCRIPTION
    assert response.json()["last_updated_date"] is not None
    assert response.json()["created_date"] is not None
    assert response.json()["created_date"] == response.json()["last_updated_date"]
    assert response.json()["project"]["id"] == "1"


def test_retreive_audit_test_by_id_not_found(client):
    create_project(client)

    response = client.get("/audit_tests/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "AuditTest with id 1 does not exist"


def test_update_audit_test(client):
    create_project(client)

    data = {
        "name": TEST_AUDIT_TEST_NAME,
        "description": TEST_AUDIT_TEST_DESCRIPTION,
        "project_id": 1,
    }

    response = client.post("/audit_tests/", json.dumps(data))
    assert response.status_code == 200

    # Sleep for 1 second to ensure that the updated date would not still
    # equal the created date
    time.sleep(1)

    modification_data = {"name": TEST_MODIFIED_AUDIT_TEST_NAME}
    response = client.put("/audit_tests/1", json.dumps(modification_data))
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated audit_test."

    response = client.get("/audit_tests/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_AUDIT_TEST_NAME
    assert response.json()["description"] == TEST_AUDIT_TEST_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]

    my_saved_last_updated_date = response.json()["last_updated_date"]

    time.sleep(1)
    modification_data = {"description": TEST_MODIFIED_AUDIT_TEST_DESCRIPTION}
    response = client.put("/audit_tests/1", json.dumps(modification_data))
    print(f"Returned: {response.text}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated audit_test."

    response = client.get("/audit_tests/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_AUDIT_TEST_NAME
    assert response.json()["description"] == TEST_MODIFIED_AUDIT_TEST_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]
    assert my_saved_last_updated_date < response.json()["last_updated_date"]


def test_update_audit_test_to_duplicate_raises_409(client):
    create_project(client)

    data = {
        "name": TEST_AUDIT_TEST_NAME,
        "description": TEST_AUDIT_TEST_DESCRIPTION,
        "project_id": 1,
    }
    data2 = {"name": "Dog", "description": TEST_AUDIT_TEST_DESCRIPTION, "project_id": 1}

    response = client.post("/audit_tests/", json.dumps(data))
    assert response.status_code == 200

    response = client.post("/audit_tests/", json.dumps(data2))
    assert response.status_code == 200

    # Now attempt to create an audit_test with the exact same name - should return status_code 409
    response = client.put("/audit_tests/1", json.dumps(data2))
    assert response.status_code == 409
    assert f"AuditTest with name 'Dog' already exists" in response.text


def test_delete_audit_test(client):
    create_project(client)

    data = {
        "name": TEST_AUDIT_TEST_NAME,
        "description": TEST_AUDIT_TEST_DESCRIPTION,
        "project_id": 1,
    }

    response = client.post("/audit_tests/", json.dumps(data))
    assert response.status_code == 200

    response = client.get("/audit_tests/1")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_AUDIT_TEST_NAME
    assert response.json()["description"] == TEST_AUDIT_TEST_DESCRIPTION

    response = client.delete("/audit_tests/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted audit_test."

    response = client.get("/audit_tests/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "AuditTest with id 1 does not exist"
