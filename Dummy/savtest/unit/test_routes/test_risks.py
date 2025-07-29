import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError, DataError, ProgrammingError
from unittest.mock import patch

from main import app  # Import your FastAPI app
from fedrisk_api.schema.risk import CreateRisk, UpdateRisk
from fedrisk_api.utils.authentication import custom_auth

client = TestClient(app)

# Mock user for dependency override
@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[custom_auth] = lambda: {"user_id": 1, "tenant_id": 1}
    yield
    app.dependency_overrides = {}


# Test for creating a risk
def test_create_risk():
    with patch("fedrisk_api.db.risk.create_risk") as mock_create_risk:
        mock_create_risk.return_value = {
            "id": 1,
            "name": "Sample Risk",
            "project_id": 1,
            "description": "A test risk",
            "created_by": 1,
            "updated_by": 1,
        }

        response = client.post(
            "/risks/",
            json={
                "name": "Sample Risk",
                "project_id": 1,
                "description": "A test risk",
            },
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Sample Risk"


# Test for handling duplicate risk creation
def test_create_duplicate_risk():
    with patch("fedrisk_api.db.risk.create_risk") as mock_create_risk:
        mock_create_risk.side_effect = IntegrityError("duplicate", {}, None)

        response = client.post(
            "/risks/",
            json={
                "name": "Duplicate Risk",
                "project_id": 1,
                "description": "A duplicate test risk",
            },
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


# Test for retrieving all risks
def test_get_all_risks():
    with patch("fedrisk_api.db.risk.get_all_risks") as mock_get_all_risks:
        mock_get_all_risks.return_value = [
            {
                "id": 1,
                "name": "Sample Risk",
                "project_id": 1,
                "description": "A test risk",
            }
        ]

        response = client.get("/risks/")
        assert response.status_code == 200
        assert response.json()["items"][0]["name"] == "Sample Risk"


# Test for retrieving risks with invalid filter
def test_get_risks_with_invalid_filter():
    with patch("fedrisk_api.db.risk.get_all_risks") as mock_get_all_risks:
        mock_get_all_risks.side_effect = DataError("Invalid filter", {}, None)

        response = client.get("/risks/?filter_by=invalid")
        assert response.status_code == 404
        assert "Please provide correct filter_value" in response.json()["detail"]


# Test for retrieving a single risk by ID
def test_get_risk_by_id():
    with patch("fedrisk_api.db.risk.get_risk") as mock_get_risk:
        mock_get_risk.return_value = {
            "id": 1,
            "name": "Sample Risk",
            "project_id": 1,
            "description": "A test risk",
        }

        response = client.get("/risks/1")
        assert response.status_code == 200
        assert response.json()["name"] == "Sample Risk"


# Test for retrieving non-existent risk
def test_get_nonexistent_risk():
    with patch("fedrisk_api.db.risk.get_risk") as mock_get_risk:
        mock_get_risk.return_value = None

        response = client.get("/risks/999")
        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"]


# Test for updating a risk
def test_update_risk():
    with patch("fedrisk_api.db.risk.update_risk") as mock_update_risk:
        mock_update_risk.return_value = {
            "id": 1,
            "name": "Updated Risk",
            "project_id": 1,
            "description": "An updated test risk",
        }

        response = client.put(
            "/risks/1",
            json={
                "name": "Updated Risk",
                "project_id": 1,
                "description": "An updated test risk",
            },
        )
        assert response.status_code == 200
        assert response.json()["name"] == "Updated Risk"


# Test for updating a non-existent risk
def test_update_nonexistent_risk():
    with patch("fedrisk_api.db.risk.update_risk") as mock_update_risk:
        mock_update_risk.return_value = None

        response = client.put(
            "/risks/999",
            json={
                "name": "Nonexistent Risk",
                "project_id": 1,
                "description": "Trying to update a non-existent risk",
            },
        )
        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"]


# Test for deleting a risk
def test_delete_risk():
    with patch("fedrisk_api.db.risk.delete_risk") as mock_delete_risk:
        mock_delete_risk.return_value = True

        response = client.delete("/risks/1")
        assert response.status_code == 200
        assert response.json()["detail"] == "Successfully deleted risk."


# Test for deleting a non-existent risk
def test_delete_nonexistent_risk():
    with patch("fedrisk_api.db.risk.delete_risk") as mock_delete_risk:
        mock_delete_risk.return_value = False

        response = client.delete("/risks/999")
        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"]
