import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from unittest.mock import patch

from main import app  # Point this to your FastAPI app
from fedrisk_api.schema.reporting_dashboard import CreateReportingSettings, UpdateReportingSettings
from fedrisk_api.utils.authentication import custom_auth

client = TestClient(app)

# Mock user for dependency override
@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[custom_auth] = lambda: {"user_id": 1, "tenant_id": 1}
    yield
    app.dependency_overrides = {}


# Test case for retrieving risk metrics by category count per month
def test_get_risk_by_category_count_per_month():
    with patch("fedrisk_api.db.reporting_dashboard.get_risk_by_category_count") as mock_get_risk:
        mock_get_risk.return_value = {"data": "Sample risk data"}

        response = client.get("/dashboards/reporting/metrics?project_id=1")

        assert response.status_code == 200
        assert response.json() == {"data": "Sample risk data"}


# Test case for retrieving pivot data for reporting
def test_get_project_data_for_pivot():
    with patch("fedrisk_api.db.reporting_dashboard.get_data_for_pivot") as mock_get_pivot:
        mock_get_pivot.return_value = {"pivot": "Sample pivot data"}

        response = client.get("/dashboards/reporting/pivot")

        assert response.status_code == 200
        assert response.json() == {"pivot": "Sample pivot data"}


# Test case for creating reporting settings
def test_create_reporting_settings():
    with patch("fedrisk_api.db.reporting_dashboard.create_reporting_settings_user") as mock_create:
        mock_create.return_value = {
            "user_id": 1,
            "report_type": "summary",
            "frequency": "weekly",
            "notifications_enabled": True,
        }

        response = client.post(
            "/dashboards/reporting/reporting_settings",
            json={"report_type": "summary", "frequency": "weekly", "notifications_enabled": True},
        )

        assert response.status_code == 200
        assert response.json()["report_type"] == "summary"


# Test case for handling duplicate creation of reporting settings
def test_create_reporting_settings_duplicate():
    with patch("fedrisk_api.db.reporting_dashboard.create_reporting_settings_user") as mock_create:
        mock_create.side_effect = IntegrityError("Duplicate entry", {}, None)

        response = client.post(
            "/dashboards/reporting/reporting_settings",
            json={"report_type": "detailed", "frequency": "daily", "notifications_enabled": False},
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]


# Test case for updating reporting settings
def test_update_reporting_settings():
    with patch("fedrisk_api.db.reporting_dashboard.update_reporting_settings_user") as mock_update:
        mock_update.return_value = {
            "user_id": 1,
            "report_type": "detailed",
            "frequency": "monthly",
            "notifications_enabled": True,
        }

        response = client.put(
            "/dashboards/reporting/reporting_settings",
            json={"report_type": "detailed", "frequency": "monthly", "notifications_enabled": True},
        )

        assert response.status_code == 200
        assert response.json()["report_type"] == "detailed"


# Test case for handling update on a non-existent user reporting setting
def test_update_nonexistent_reporting_settings():
    with patch("fedrisk_api.db.reporting_dashboard.update_reporting_settings_user") as mock_update:
        mock_update.return_value = None

        response = client.put(
            "/dashboards/reporting/reporting_settings",
            json={
                "report_type": "detailed",
                "frequency": "monthly",
                "notifications_enabled": False,
            },
        )

        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"]


# Test case for retrieving user-specific reporting settings
def test_get_reporting_settings():
    with patch("fedrisk_api.db.reporting_dashboard.get_reporting_settings_for_user") as mock_get:
        mock_get.return_value = {
            "user_id": 1,
            "report_type": "summary",
            "frequency": "weekly",
            "notifications_enabled": True,
        }

        response = client.get("/dashboards/reporting/reporting_settings")

        assert response.status_code == 200
        assert response.json()["report_type"] == "summary"


# Test case for deleting a user's reporting settings
def test_delete_reporting_settings():
    with patch(
        "fedrisk_api.db.reporting_dashboard.delete_reporting_settings_by_user_id"
    ) as mock_delete:
        mock_delete.return_value = True

        response = client.delete("/dashboards/reporting/1")

        assert response.status_code == 200
        assert response.json()["detail"] == "Successfully deleted user reporting settings."


# Test case for attempting to delete non-existent reporting settings
def test_delete_nonexistent_reporting_settings():
    with patch(
        "fedrisk_api.db.reporting_dashboard.delete_reporting_settings_by_user_id"
    ) as mock_delete:
        mock_delete.return_value = False

        response = client.delete("/dashboards/reporting/999")

        assert response.status_code == 404
        assert "does not exist" in response.json()["detail"]
