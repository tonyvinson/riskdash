import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from unittest.mock import MagicMock, patch

from main import app  # Assuming this is where the FastAPI app is created
from fedrisk_api.schema.project_group import CreateProjectGroup, UpdateProjectGroup
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_project_group_permission,
    delete_project_group_permission,
    update_project_group_permission,
    view_project_group_permission,
)

client = TestClient(app)

# Mock user and permissions dependencies
@pytest.fixture
def mock_user():
    return {"user_id": 1, "tenant_id": 1}


def mock_permission():
    return True


# Apply mocks globally for dependencies
@pytest.fixture(autouse=True)
def setup_dependencies():
    app.dependency_overrides[custom_auth] = lambda: {"user_id": 1, "tenant_id": 1}
    app.dependency_overrides[create_project_group_permission] = mock_permission
    app.dependency_overrides[view_project_group_permission] = mock_permission
    app.dependency_overrides[update_project_group_permission] = mock_permission
    app.dependency_overrides[delete_project_group_permission] = mock_permission
    yield
    app.dependency_overrides = {}


# Test creating a project group
def test_create_project_group(mock_user):
    with patch("fedrisk_api.db.project_group.create_project_group") as mock_create:
        mock_create.return_value = {
            "id": 1,
            "name": "Test Group",
            "description": "A test project group",
        }

        response = client.post(
            "/project_groups/", json={"name": "Test Group", "description": "A test project group"}
        )

        assert response.status_code == 200
        assert response.json()["name"] == "Test Group"
        assert response.json()["description"] == "A test project group"


# Test error during creation (duplicate name)
def test_create_project_group_duplicate(mock_user):
    with patch("fedrisk_api.db.project_group.create_project_group") as mock_create:
        mock_create.side_effect = IntegrityError("Duplicate entry", {}, None)

        response = client.post(
            "/project_groups/",
            json={"name": "Duplicate Group", "description": "A test project group"},
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


# Test fetching all project groups
def test_get_all_project_groups(mock_user):
    with patch("fedrisk_api.db.project_group.get_project_group") as mock_get:
        mock_get.return_value = [
            {"id": 1, "name": "Group 1", "description": "Test Group 1"},
            {"id": 2, "name": "Group 2", "description": "Test Group 2"},
        ]

        response = client.get("/project_groups/")

        assert response.status_code == 200
        assert len(response.json()["items"]) == 2


# Test fetching a project group by ID
def test_get_project_group_by_id(mock_user):
    with patch("fedrisk_api.db.project_group.get_project_group_by_id") as mock_get:
        mock_get.return_value = {"id": 1, "name": "Test Group", "description": "A test group"}

        response = client.get("/project_groups/1")

        assert response.status_code == 200
        assert response.json()["name"] == "Test Group"


# Test updating a project group by ID
def test_update_project_group_by_id(mock_user):
    with patch("fedrisk_api.db.project_group.update_project_group_by_id") as mock_update:
        mock_update.return_value = {
            "id": 1,
            "name": "Updated Group",
            "description": "Updated description",
        }

        response = client.put(
            "/project_groups/1",
            json={"name": "Updated Group", "description": "Updated description"},
        )

        assert response.status_code == 200
        assert response.json()["detail"] == "Successfully updated project group."


# Test deleting a project group by ID
def test_delete_project_group_by_id(mock_user):
    with patch("fedrisk_api.db.project_group.delete_project_group_by_id") as mock_delete:
        mock_delete.return_value = True

        response = client.delete("/project_groups/1")

        assert response.status_code == 200
        assert response.json()["detail"] == "Successfully deleted project group."


# Test deleting a non-existent project group
def test_delete_nonexistent_project_group(mock_user):
    with patch("fedrisk_api.db.project_group.delete_project_group_by_id") as mock_delete:
        mock_delete.return_value = False

        response = client.delete("/project_groups/999")

        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"]
