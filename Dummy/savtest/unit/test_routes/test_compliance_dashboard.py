import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from sqlalchemy.orm import Session
from fastapi import FastAPI  # Assuming your FastAPI app is in the main.py file

# Assuming `DisplayComplianceMetrics` is the expected response model.
from fedrisk_api.schema.compliance_dashboard import DisplayComplianceMetrics

from config.config import Settings

settings = Settings()

app = FastAPI(title=settings.PROJECT_TITLE, version=settings.PROJECT_VERSION)

client = TestClient(app)

# Sample data for successful response
mock_compliance_metrics = {
    "project_id": 1,
    "project_name": "Project A",
    "framework_id": 2,
    "framework_name": "Framework B",
    "total": 15,
    "monthly": [{"name": "January", "count": 2}, {"name": "February", "count": 3}],
    "status": [{"name": "open", "count": 5}, {"name": "closed", "count": 10}],
}

# Test 1: Successful retrieval of compliance metrics
@patch("fedrisk_api.db.compliance_dashboard.get_compliance_dashboard_metrics")
@patch("fedrisk_api.utils.authentication.custom_auth")
def test_get_compliance_matrics_success(mock_auth, mock_get_metrics):
    # Mocking the authentication and dashboard metrics function
    mock_auth.return_value = {"id": 1, "is_authenticated": True}
    mock_get_metrics.return_value = mock_compliance_metrics

    response = client.get("/dashboards/compliance/metrics?project_id=1&framework_id=2")

    # Check the status code
    assert response.status_code == 200
    assert response.json() == mock_compliance_metrics


# Test 2: Permission denied (mock permission check failure)
@patch("fedrisk_api.db.compliance_dashboard.get_compliance_dashboard_metrics")
@patch("fedrisk_api.utils.authentication.custom_auth")
@patch("fedrisk_api.utils.permissions.view_compliance_dashboard")
def test_get_compliance_matrics_permission_denied(mock_permissions, mock_auth, mock_get_metrics):
    # Simulating permission failure
    mock_permissions.side_effect = Exception("Permission denied")
    mock_auth.return_value = {"id": 1, "is_authenticated": True}

    response = client.get("/dashboards/compliance/metrics?project_id=1&framework_id=2")

    # Check that the response code is 403 (forbidden)
    assert response.status_code == 403


# Test 3: Missing project_id or framework_id
@patch("fedrisk_api.db.compliance_dashboard.get_compliance_dashboard_metrics")
@patch("fedrisk_api.utils.authentication.custom_auth")
def test_get_compliance_matrics_missing_params(mock_auth, mock_get_metrics):
    mock_auth.return_value = {"id": 1, "is_authenticated": True}

    # Test without project_id and framework_id
    response = client.get("/dashboards/compliance/metrics")

    # Check if default behavior works (depending on your function's implementation)
    assert response.status_code == 200
    # Optionally: assert specific response if these are required params.


# Test 4: Invalid project or framework (mocking a failure)
@patch("fedrisk_api.db.compliance_dashboard.get_compliance_dashboard_metrics")
@patch("fedrisk_api.utils.authentication.custom_auth")
def test_get_compliance_matrics_invalid_project(mock_auth, mock_get_metrics):
    # Simulate a scenario where the project or framework is not found
    mock_auth.return_value = {"id": 1, "is_authenticated": True}
    mock_get_metrics.return_value = {
        "project_id": -1,
        "project_name": "",
        "framework_id": -1,
        "framework_name": "",
        "total": 0,
        "monthly": [],
        "status": [],
    }

    response = client.get("/dashboards/compliance/metrics?project_id=9999&framework_id=9999")

    assert response.status_code == 200
    assert response.json() == {
        "project_id": -1,
        "project_name": "",
        "framework_id": -1,
        "framework_name": "",
        "total": 0,
        "monthly": [],
        "status": [],
    }
