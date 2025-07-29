import json
import time

from fedrisk_api.db.project import get_project

TEST_ASSESSMENT_NAME = "First Assessment"
TEST_ASSESSMENT_DESCRIPTION = "Assessment for Testing"
TEST_MODIFIED_ASSESSMENT_NAME = "Modified -" + TEST_ASSESSMENT_NAME
TEST_MODIFIED_ASSESSMENT_DESCRIPTION = "Modified -" + TEST_ASSESSMENT_DESCRIPTION


def create_project_structure(client, num_controls=1):
    framework_data = {
        "name": "Test Framework",
        "description": "Testing",
    }

    created_framework = client.post("/frameworks/", json.dumps(framework_data))
    created_framework_json = created_framework.json()
    # print(f"Framework: {created_framework_json}")
    control_data = {
        "framework_id": created_framework_json["id"],
        "name": "Test Control",
        "description": "Testing",
    }

    project_data = {"name": "Test Project", "description": "Testing"}

    created_project = client.post("/projects/", json.dumps(project_data))
    created_project_json = created_project.json()
    created_project_id = created_project_json["id"]

    for i in range(num_controls):
        control_data["name"] = control_data["name"] + f"-{i+1}"
        created_control = client.post("/controls/", json.dumps(control_data))
        created_control_json = created_control.json()
        # print(created_control_json)

        # print(created_project_json)

        created_control_id = created_control_json["id"]
        client.put(f"/projects/{created_project_id}/control/{created_control_id}")

    updated_project = client.get(f"/projects/{created_project_id}").json()
    return updated_project


def test_create_assessment(client):
    updated_project = create_project_structure(client)
    print(updated_project)
    response = client.get("/assessments/")
    assert response.status_code == 200
    response_json = response.json()
    print(json.dumps(response_json, indent=3))
    assert len(response_json) == 1


def test_get_all_assessments(client):
    num_test_objects = 1
    updated_project = create_project_structure(client, num_controls=num_test_objects)

    print(f"Project:\n{json.dumps(updated_project, indent=3)}")
    response = client.get("/assessments")
    assert response.status_code == 200
    response_json = response.json()
    print(json.dumps(response_json, indent=3))
    assert len(list(response.json())) == num_test_objects


def test_retrieve_assessment_by_id(client):
    updated_project = create_project_structure(client)
    print(updated_project)

    response = client.get("/assessments/")
    assert response.status_code == 200
    created_assessment = response.json()[0]
    created_assessment_id = created_assessment["id"]
    response = client.get(f"/assessments/{created_assessment_id}")
    assert response.status_code == 200
    assert response.json()["name"] == created_assessment["name"]
    assert response.json()["description"] == created_assessment["description"]
    assert response.json()["last_updated_date"] is not None
    assert response.json()["created_date"] is not None
    assert response.json()["created_date"] == response.json()["last_updated_date"]


def test_retrieve_assessment_by_id_not_found(client):
    response = client.get("/assessments/1")

    assert response.status_code == 404
    assert response.json()["detail"] == "Assessment with id 1 does not exist"


def test_update_assessment(client):
    updated_project = create_project_structure(client)

    response = client.get("/assessments/")
    assert response.status_code == 200
    created_assessment = response.json()[0]
    created_assessment_id = created_assessment["id"]
    response = client.get(f"/assessments/{created_assessment_id}")

    # Sleep for 1 second to ensure that the updated date would not still
    # equal the created date
    time.sleep(1)

    modification_data = {"name": TEST_MODIFIED_ASSESSMENT_NAME}
    response = client.put(f"/assessments/{created_assessment_id}", json.dumps(modification_data))
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated assessment."

    response = client.get(f"/assessments/{created_assessment_id}")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_ASSESSMENT_NAME
    assert response.json()["created_date"] < response.json()["last_updated_date"]

    my_saved_last_updated_date = response.json()["last_updated_date"]

    time.sleep(1)
    modification_data = {"description": TEST_MODIFIED_ASSESSMENT_DESCRIPTION}
    response = client.put(f"/assessments/{created_assessment_id}", json.dumps(modification_data))
    print(f"Returned: {response.text}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated assessment."

    response = client.get(f"/assessments/{created_assessment_id}")
    assert response.status_code == 200
    assert response.json()["name"] == TEST_MODIFIED_ASSESSMENT_NAME
    assert response.json()["description"] == TEST_MODIFIED_ASSESSMENT_DESCRIPTION
    assert response.json()["created_date"] < response.json()["last_updated_date"]
    assert my_saved_last_updated_date < response.json()["last_updated_date"]


def test_update_assessment_to_duplicate_raises_409(client):
    updated_project = create_project_structure(client, num_controls=2)
    print(updated_project)

    response = client.get("/assessments/")
    assert response.status_code == 200
    assessment_list = response.json()

    data = {"name": TEST_ASSESSMENT_NAME, "description": TEST_ASSESSMENT_DESCRIPTION}

    assessment_1_id = assessment_list[0]["id"]
    assessment_2_id = assessment_list[1]["id"]

    response = client.put(f"/assessments/{assessment_1_id}", json.dumps(data))
    assert response.status_code == 200

    # Now attempt to create a control status with the exact same name - should return status_code 409
    response = client.put(f"/assessments/{assessment_2_id}", json.dumps(data))
    assert response.status_code == 409
    assert f"Assessment with name '{TEST_ASSESSMENT_NAME}' already exists" in response.text
