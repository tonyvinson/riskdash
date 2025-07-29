import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from main import app  # Replace `your_module` with the actual module name

# from your_module.routers.dashboard import (
#     get_project_framework_metrics,
#     get_all_project_control,
#     get_all_project_exception,
#     get_all_project_assessments,
#     get_mit_percentage,
#     get_class_names_percentage,
#     get_class_family_percentage,
#     get_class_phase_percentage,
#     get_class_status_percentage,
# )

client = TestClient(app)


@pytest.fixture
def mock_session():
    session = MagicMock(spec=Session)
    return session


def test_get_project_framework_metrics(mock_session):
    mock_session.query().filter().first.return_value = MagicMock()
    mock_session.query().filter().all.return_value = [MagicMock()]
    mock_session.query().distinct().subquery.return_value = MagicMock()

    response = client.get(
        "/dashboards/governance/metrics/", params={"project_id": 1, "framework_id": 1}
    )
    assert response.status_code == 200
    assert "project_id" in response.json()


def test_get_all_project_control(mock_session):
    mock_session.query().filter().first.return_value = MagicMock()
    response = client.get(
        "/dashboards/governance/controls/",
        params={"project_id": 1, "framework_id": 1, "limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_get_all_project_exception(mock_session):
    mock_session.query().filter().first.return_value = MagicMock()
    response = client.get(
        "/dashboards/governance/exceptions/",
        params={"project_id": 1, "framework_id": 1, "limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_get_all_project_assessments(mock_session):
    mock_session.query().filter().first.return_value = MagicMock()
    response = client.get(
        "/dashboards/governance/assessments/",
        params={"project_id": 1, "framework_id": 1, "limit": 10, "offset": 0},
    )
    assert response.status_code == 200
    assert isinstance(response.json()["items"], list)


def test_get_mit_percentage(mock_session):
    mock_session.query().filter().all.return_value = [
        MagicMock(mitigation_percentage=50, control=MagicMock(name="Control 1"))
    ]
    response = client.get(
        "/dashboards/governance/project_controls/mit-percentage/", params={"project_id": 1}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "x" in response.json()[0] and "y" in response.json()[0]


def test_get_class_names_percentage(mock_session):
    mock_session.query().filter().all.return_value = [
        MagicMock(mitigation_percentage=50, control_class_id=1)
    ]
    response = client.get(
        "/dashboards/governance/project_controls/class-names-percentage/", params={"project_id": 1}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "x" in response.json()[0] and "y" in response.json()[0]


def test_get_class_family_percentage(mock_session):
    mock_session.query().filter().all.return_value = [
        MagicMock(mitigation_percentage=50, control_family_id=1)
    ]
    response = client.get(
        "/dashboards/governance/project_controls/class-family-percentage/", params={"project_id": 1}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "x" in response.json()[0] and "y" in response.json()[0]


def test_get_class_phase_percentage(mock_session):
    mock_session.query().filter().all.return_value = [
        MagicMock(mitigation_percentage=50, control_phase_id=1)
    ]
    response = client.get(
        "/dashboards/governance/project_controls/class-phase-percentage/", params={"project_id": 1}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "x" in response.json()[0] and "y" in response.json()[0]


def test_get_class_status_percentage(mock_session):
    mock_session.query().filter().all.return_value = [
        MagicMock(mitigation_percentage=50, control_status_id=1)
    ]
    response = client.get(
        "/dashboards/governance/project_controls/class-status-percentage/", params={"project_id": 1}
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    assert "x" in response.json()[0] and "y" in response.json()[0]
