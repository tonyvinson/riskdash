import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from main import app  # Import the FastAPI app
from fedrisk_api.schema.summary_dashboard import (
    DisplayGovernance,
    FinalCompilanceDisplay,
    FinalDisplayRiskItems,
    FinalDisplayTask,
)

from fedrisk_api.db.database import get_db
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    view_compliance_permission,
    view_governanceprojects_permission,
    view_projecttasks_permission,
    view_riskitems_permission,
)

client = TestClient(app)


@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides = {
        get_db: lambda: MagicMock(spec=Session),
        custom_auth: lambda: {"user_id": 1, "tenant_id": 1},
        view_governanceprojects_permission: lambda: True,
        view_compliance_permission: lambda: True,
        view_riskitems_permission: lambda: True,
        view_projecttasks_permission: lambda: True,
    }
    yield
    app.dependency_overrides = {}


# Sample data creation functions
def sample_project(id, name="Project"):
    return {
        "id": id,
        "name": name,
        "project_controls": [],
        "risks": [],
        "audit_tests": [],
    }


# Governance projects endpoint test
def test_get_governance_projects():
    projects = [sample_project(1), sample_project(2, "Project B")]
    with patch("fedrisk_api.db.summary_dashboard.get_governance_projects", return_value=projects):
        response = client.get("/summary_dashboards/governance/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["name"] == "Project"


# Risk items endpoint test
def test_get_risk_items():
    projects = [
        {
            "id": 1,
            "name": "Project A",
            "project_controls": [],
            "risks": [{"risk_score": {"name": "5"}}],
        },
        {
            "id": 2,
            "name": "Project B",
            "project_controls": [],
            "risks": [{"risk_score": {"name": "3"}}],
        },
    ]
    with patch("fedrisk_api.db.summary_dashboard.get_risk_items", return_value=projects):
        response = client.get("/summary_dashboards/risk_items/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][0]["risk_score"] == 5  # Average risk score for this project


# Compliance endpoint test
def test_get_compliance():
    projects = [sample_project(1), sample_project(2, "Project B")]
    with patch("fedrisk_api.db.summary_dashboard.get_compliance", return_value=projects):
        response = client.get("/summary_dashboards/compliance/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][1]["name"] == "Project B"


# Project tasks endpoint test
def test_get_project_tasks():
    projects = [sample_project(1), sample_project(2, "Project B")]
    with patch("fedrisk_api.db.summary_dashboard.get_projects_tasks", return_value=projects):
        response = client.get("/summary_dashboards/tasks/")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["items"][1]["name"] == "Project B"


# Summary chart data by project endpoint test
def test_get_summary_chart_data_by_project():
    project_id = 1
    chart_data = {"data": "sample_chart_data"}
    with patch(
        "fedrisk_api.db.summary_dashboard.get_summary_chart_data_by_project",
        return_value=chart_data,
    ):
        response = client.get(f"/summary_dashboards/{project_id}")
        assert response.status_code == 200
        data = response.json()
        assert data == chart_data


# Test for a non-existent project ID in the summary chart data
def test_get_summary_chart_data_by_nonexistent_project():
    project_id = 999
    with patch(
        "fedrisk_api.db.summary_dashboard.get_summary_chart_data_by_project", return_value=None
    ):
        response = client.get(f"/summary_dashboards/{project_id}")
        assert response.status_code == 404
        assert response.json()["detail"] == f"Project with {project_id} do not exist"
