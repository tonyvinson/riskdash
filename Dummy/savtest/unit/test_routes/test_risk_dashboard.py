import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from sqlalchemy.orm import Session

from main import app  # Ensure this imports your FastAPI app
from fedrisk_api.schema.risk_dashboard import DisplayRiskDashboardMetrics
from fedrisk_api.db.database import get_db

client = TestClient(app)

from fedrisk_api.utils.authentication import custom_auth

# Mock user dependency for authentication override
@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides = {
        custom_auth: lambda: {"user_id": 1, "tenant_id": 1},
        get_db: lambda: MagicMock(spec=Session),  # Mock Session
    }
    yield
    app.dependency_overrides = {}


# Helper function for creating a sample risk
def sample_risk(
    id, name, risk_status_id, risk_category_id, risk_score_id, risk_impact_id, current_likelihood_id
):
    return MagicMock(
        id=id,
        name=name,
        risk_status_id=risk_status_id,
        risk_category_id=risk_category_id,
        risk_score_id=risk_score_id,
        risk_impact_id=risk_impact_id,
        current_likelihood_id=current_likelihood_id,
    )


# Test for successful retrieval of risk metrics
def test_get_risk_metrics_success():
    project_id = 1
    mock_project = MagicMock(id=project_id, name="Sample Project")

    with patch("fedrisk_api.db.dashboard.get_project", return_value=mock_project), patch(
        "sqlalchemy.orm.Session.query"
    ) as mock_query:

        mock_query.return_value.filter.return_value.distinct.return_value.all.return_value = [
            sample_risk(1, "Risk 1", 1, 2, 3, 4, 5),
            sample_risk(2, "Risk 2", 1, 2, 3, 4, 5),
        ]

        response = client.get(f"/dashboards/risk/metrics/?project_id={project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == "Sample Project"
        assert data["project_id"] == project_id
        assert isinstance(data["risk_status"], list)
        assert isinstance(data["risk_category"], list)
        assert isinstance(data["risk_score"], list)
        assert isinstance(data["risk_impact"], list)
        assert isinstance(data["risk_likelihood"], list)
        assert isinstance(data["risk_mapping"], list)


# Test for case with missing project
def test_get_risk_metrics_missing_project():
    project_id = 999

    with patch("fedrisk_api.db.dashboard.get_project", return_value=None):
        response = client.get(f"/dashboards/risk/metrics/?project_id={project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == ""
        assert data["project_id"] == -1


# Test for empty risk data
def test_get_risk_metrics_no_risks():
    project_id = 1
    mock_project = MagicMock(id=project_id, name="Sample Project")

    with patch("fedrisk_api.db.dashboard.get_project", return_value=mock_project), patch(
        "sqlalchemy.orm.Session.query"
    ) as mock_query:

        mock_query.return_value.filter.return_value.distinct.return_value.all.return_value = []

        response = client.get(f"/dashboards/risk/metrics/?project_id={project_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["project_name"] == "Sample Project"
        assert data["project_id"] == project_id
        assert data["risk_status"] == []
        assert data["risk_category"] == []
        assert data["risk_score"] == []
        assert data["risk_impact"] == []
        assert data["risk_likelihood"] == []
        assert data["risk_mapping"] == [
            {"name": "Low", "count": 0},
            {"name": "Low-Medium", "count": 0},
            {"name": "Medium", "count": 0},
            {"name": "Medium-High", "count": 0},
            {"name": "High", "count": 0},
        ]


# Test for calculating risk mapping
def test_get_risk_mapping_calculation():
    project_id = 1
    mock_project = MagicMock(id=project_id, name="Sample Project")

    with patch("fedrisk_api.db.dashboard.get_project", return_value=mock_project), patch(
        "sqlalchemy.orm.Session.query"
    ) as mock_query:

        # Mocking sample risks for mapping calculation
        mock_query.return_value.filter.return_value.distinct.return_value.all.return_value = [
            sample_risk(1, "Risk A", 1, 1, 1, 1, 1),
            sample_risk(2, "Risk B", 1, 1, 1, 1, 2),
        ]

        response = client.get(f"/dashboards/risk/metrics/?project_id={project_id}")

        assert response.status_code == 200
        data = response.json()
        # Check if the response includes mapping values
        assert "risk_mapping" in data
        assert any(item["name"] == "Low" for item in data["risk_mapping"])
