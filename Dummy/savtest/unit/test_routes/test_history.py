from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from fastapi.testclient import TestClient
from main import app  # Adjust path to your FastAPI app
from fedrisk_api.db.database import get_db

client = TestClient(app)

# Dependency override for testing
@pytest.fixture
def override_get_db():
    return Mock()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def test_client():
    yield client


# Test: Get Assessment History by ID
def test_get_assessment_history_by_id(test_client):
    response = test_client.get("/history/assessments/1")  # Assume ID 1 exists for testing
    assert response.status_code == 200
    data = response.json()
    assert "assessment_id" in data  # Replace with actual schema keys


# Test: Get All Assessment History by Project ID
def test_get_all_assessment_history_by_project_id(test_client):
    response = test_client.get("/history/assessments/project/1")  # Assume Project ID 1 exists
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "assessment_id" in data[0]  # Replace with actual schema keys


# Test: Get Document History by ID
def test_get_document_history_by_id(test_client):
    response = test_client.get("/history/documents/1")  # Assume ID 1 exists
    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data  # Replace with actual schema keys


# Test: Get All Document History by Project ID
def test_get_all_document_history_by_project_id(test_client):
    response = test_client.get("/history/documents/project/1")  # Assume Project ID 1 exists
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "document_id" in data[0]  # Replace with actual schema keys


# Test: Get Project Control History by ID
def test_get_project_control_history_by_id(test_client):
    response = test_client.get("/history/project_controls/1")  # Assume ID 1 exists
    assert response.status_code == 200
    data = response.json()
    assert "project_control_id" in data  # Replace with actual schema keys


# Test: Get All Project Control History by Project ID
def test_get_all_project_control_history_by_project_id(test_client):
    response = test_client.get("/history/project_controls/project/1")  # Assume Project ID 1 exists
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "project_control_id" in data[0]  # Replace with actual schema keys


# Test: Get Project History by ID
def test_get_project_history_by_id(test_client):
    response = test_client.get("/history/projects/1")  # Assume ID 1 exists
    assert response.status_code == 200
    data = response.json()
    assert "project_id" in data  # Replace with actual schema keys


# Test: Get All Project History by Project ID
def test_get_all_project_history_by_project_id(test_client):
    response = test_client.get("/history/projects/project/1")  # Assume Project ID 1 exists
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "project_id" in data[0]  # Replace with actual schema keys


# Test: Get User Watching by Project ID
def test_get_user_watching_by_project_id(test_client):
    response = test_client.get("/history/user_watching/1")  # Assume Project ID 1 exists
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# Test: Get All User Watching by User ID
def test_get_all_user_watching_by_user_id(test_client):
    response = test_client.get("/history/user_watching/all/1")  # Assume User ID 1 exists
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# Test: Update User Watching by Project ID
def test_update_user_watching_by_project_id(test_client):
    update_data = {"project_assessments": True, "project_audit_tests": False}  # Modify as needed
    response = test_client.put("/history/user_watching/project/1", json=update_data)
    assert response.status_code == 200
    data = response.json()
    assert "project_assessments" in data
    assert data["project_assessments"] == True
