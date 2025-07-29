import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from main import app  # Import your FastAPI app
from fedrisk_api.schema.role import DisplayRoles, DisplayPermissions
from fedrisk_api.db.database import get_db
from fedrisk_api.utils.permissions import view_permission_permission, view_role_permission

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides = {
        get_db: lambda: MagicMock(spec=Session),
        view_role_permission: lambda: True,  # Mock permission dependency
        view_permission_permission: lambda: True,
    }
    yield
    app.dependency_overrides = {}


# Sample data for roles and permissions
def sample_role(id, name="Admin"):
    return {"id": id, "name": name, "created_date": "2023-10-01T00:00:00"}


def sample_permission(id, name="view_users"):
    return {"id": id, "name": name, "created_date": "2023-10-01T00:00:00"}


# Test for retrieving all roles
def test_get_all_roles():
    roles = [sample_role(1), sample_role(2, "User")]
    with patch("fedrisk_api.db.role.get_all_roles", return_value=(roles, len(roles))):
        response = client.get("/roles/")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "Admin"


# Test for retrieving permissions of a role
def test_get_permissions_of_role():
    permissions = [sample_permission(1), sample_permission(2, "edit_users")]
    role_id = 1
    with patch(
        "fedrisk_api.db.role.get_permissions_of_role", return_value=(permissions, len(permissions))
    ):
        response = client.get(f"/roles/{role_id}/permissions")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "view_users"


# Test for invalid role ID for permissions endpoint
def test_get_permissions_of_role_invalid_role():
    role_id = 999
    with patch("fedrisk_api.db.role.get_permissions_of_role", return_value=(False, 0)):
        response = client.get(f"/roles/{role_id}/permissions")
        assert response.status_code == 404
        assert response.json()["detail"] == f"Role with id '{role_id}' does not exist"


# Test for retrieving all permissions
def test_get_all_permissions():
    permissions = [sample_permission(1), sample_permission(2, "edit_users")]
    with patch(
        "fedrisk_api.db.role.get_all_permissions", return_value=(permissions, len(permissions))
    ):
        response = client.get("/roles/permissions")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "view_users"
