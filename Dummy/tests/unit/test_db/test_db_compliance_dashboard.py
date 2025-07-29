import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.compliance_dashboard import (
    get_compliance_dashboard_metrics,
    get_compliance_dashboard_metrics_cap_poam,
)  # Adjust the import as needed

# from fedrisk_api.db.models import AuditTest, Control, Framework

# from fedrisk_api.db.dashboard import get_framework, get_project


@pytest.fixture
def db():
    return MagicMock(spec=Session)


@pytest.fixture
def user():
    return {"user_id": 1}


@pytest.fixture
def project():
    return MagicMock(id=1, name="Test Project")


@pytest.fixture
def framework():
    return MagicMock(id=1, name="Test Framework", tenant_id=1)


@pytest.fixture
def mock_get_project():
    #     return {"return_value": {"id":1, "name":"Test Project"}}
    query = MagicMock()
    query.filter.return_value = query  # Simulate filter chain
    return query


@pytest.fixture
def mock_get_framework():
    #     return {"return_value": {"id":1, "name":"Test Framework", "tenant_id":1}}
    query = MagicMock()
    query.filter.return_value = query  # Simulate filter chain
    return query


@pytest.fixture
def audit_tests():
    return [
        MagicMock(due_date="2024-01-15", status="open", control_id=1, project_id=1),
        MagicMock(due_date="2024-02-15", status="closed", control_id=1, project_id=1),
    ]


@pytest.fixture
def cap_poams():
    return [
        MagicMock(due_date="2024-01-15", status="In Progress", project_id=1),
        MagicMock(due_date="2024-02-15", status="Completed", project_id=1),
    ]


@pytest.mark.asyncio
# @patch("fedrisk_api.db.dashboard.get_project")
# @patch("fedrisk_api.db.dashboard.get_framework")
async def test_get_compliance_dashboard_metrics(
    db, user, project, framework, audit_tests, mock_get_project, mock_get_framework
):
    # Mock project retrieval
    mock_get_project.return_value = project
    # Mock framework retrieval
    mock_get_framework.return_value = framework

    # Mock total count query
    db.query.return_value.join.return_value.filter.return_value.distinct.return_value.count.return_value = len(
        audit_tests
    )

    # Mock monthly count query
    db.query.return_value.select_from.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = [
        {"month": "January", "count": 1},
        {"month": "February", "count": 1},
    ]

    # Mock status count query
    db.query.return_value.select_from.return_value.join.return_value.filter.return_value.group_by.return_value = [
        MagicMock(name="AuditTest", status="open", count=1),
        MagicMock(name="AuditTest", status="closed", count=1),
    ]

    # Call the function
    result = get_compliance_dashboard_metrics(db, project_id=1, framework_id=1, user=user)

    # Assertions
    # assert result["project_id"] == project.id
    # assert result["project_name"] == project.name
    # assert result["framework_id"] == framework.id
    # assert result["framework_name"] == framework.name
    # assert result["total"] == len(audit_tests)
    # assert len(result["monthly"]) == 2  # Should have entries for January and February
    # assert len(result["status"]) == len(set(["open", "closed"]))  # Should have entries for all statuses


@pytest.mark.asyncio
# @patch("fedrisk_api.db.dashboard.get_project")
# @patch("fedrisk_api.db.dashboard.get_framework")
async def test_get_compliance_dashboard_metrics_no_project(db, user, mock_get_project):
    # Mock project retrieval to return None
    mock_get_project.return_value = None

    # Call the function
    result = get_compliance_dashboard_metrics(db, project_id=1, framework_id=1, user=user)

    # Assertions
    # assert result == {
    #     "project_id": -1,
    #     "project_name": "",
    #     "framework_id": -1,
    #     "framework_name": "",
    #     "total": 0,
    #     "monthly": [],
    #     "status": [],
    # }


@pytest.mark.asyncio
# @patch("fedrisk_api.db.dashboard.get_project")
# @patch("fedrisk_api.db.dashboard.get_framework")
async def test_get_compliance_dashboard_metrics_no_framework(
    db, user, project, mock_get_project, mock_get_framework
):
    # Mock project retrieval
    mock_get_project.return_value = project
    # Mock framework retrieval to return None
    mock_get_framework.return_value = None

    # Call the function
    result = get_compliance_dashboard_metrics(db, project_id=1, framework_id=99, user=user)

    # Assertions
    # assert result == {
    #     "project_id": -1,
    #     "project_name": "",
    #     "framework_id": -1,
    #     "framework_name": "",
    #     "total": 0,
    #     "monthly": [],
    #     "status": [],
    # }


@pytest.mark.asyncio
# @patch("fedrisk_api.db.dashboard.get_project")
# @patch("fedrisk_api.db.dashboard.get_framework")
async def test_get_compliance_dashboard_metrics_cap_poam(
    db, user, project, cap_poams, mock_get_project
):
    # Mock project retrieval
    mock_get_project.return_value = project

    # Mock total count query
    db.query.return_value.join.return_value.filter.return_value.distinct.return_value.count.return_value = len(
        cap_poams
    )

    # Mock monthly count query
    db.query.return_value.select_from.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = [
        {"month": "January", "count": 1},
        {"month": "February", "count": 1},
    ]

    # Mock status count query
    db.query.return_value.select_from.return_value.join.return_value.filter.return_value.group_by.return_value = [
        MagicMock(name="CAPPOAM1", status="In Progress", count=1),
        MagicMock(name="CAPPOAM2", status="Completed", count=1),
    ]

    # Call the function
    result = get_compliance_dashboard_metrics_cap_poam(db, project_id=1, user=user)
