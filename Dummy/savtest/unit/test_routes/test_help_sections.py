from unittest.mock import Mock
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from fastapi.testclient import TestClient
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.help_section import CreateHelpSection, UpdateHelpSection
from main import app  # Your FastAPI app entry point

client = TestClient(app)

# Dependency override for testing
@pytest.fixture
def override_get_db():
    return Mock()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def test_client():
    yield client


# Test: Create Help Section
def test_create_help_section(test_client):
    new_help_section = {"title": "New Help Section", "content": "This is a test help section."}
    response = test_client.post("/help_sections/", json=new_help_section)
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Help Section"
    assert data["content"] == "This is a test help section."


# Test: Get All Help Sections
def test_get_all_help_sections(test_client):
    response = test_client.get("/help_sections/")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if data:
        assert "title" in data[0]
        assert "content" in data[0]


# Test: Get Help Section by ID
def test_get_help_section_by_id(test_client):
    response = test_client.get("/help_sections/1")  # Assume ID 1 exists for testing
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "content" in data


# Test: Get Non-existent Help Section by ID
def test_get_non_existent_help_section(test_client):
    response = test_client.get("/help_sections/9999")  # Use an ID that does not exist
    assert response.status_code == 404
    assert response.json()["detail"] == "Help Section with specified id does not exists"


# Test: Update Help Section by ID
def test_update_help_section_by_id(test_client):
    update_data = {"title": "Updated Title", "content": "Updated Content"}
    response = test_client.put("/help_sections/1", json=update_data)  # Assume ID 1 exists
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated Help Section."


# Test: Update Non-existent Help Section by ID
def test_update_non_existent_help_section(test_client):
    update_data = {"title": "Updated Title", "content": "Updated Content"}
    response = test_client.put("/help_sections/9999", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Help Section with specified id does not exists"


# Test: Delete Help Section by ID
def test_delete_help_section_by_id(test_client):
    response = test_client.delete("/help_sections/1")  # Assume ID 1 exists for testing
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted Help Section."


# Test: Delete Non-existent Help Section by ID
def test_delete_non_existent_help_section(test_client):
    response = test_client.delete("/help_sections/9999")  # Use an ID that does not exist
    assert response.status_code == 404
    assert response.json()["detail"] == "Help Section with specified id does not exists"
