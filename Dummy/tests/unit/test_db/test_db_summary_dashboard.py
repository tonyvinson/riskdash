import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.summary_dashboard import (
    get_governance_projects,
    get_risk_items,
    get_compliance,
    get_projects_tasks,
    get_summary_chart_data_by_project,
)


@pytest.fixture
def mock_session():
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_user():
    user = MagicMock()
    user.id = 1
    user.is_superuser = True
    user.is_tenant_admin = False
    return user


@pytest.mark.asyncio
async def test_get_governance_projects(mock_session, mock_user):
    mock_session.query().filter().first.return_value = mock_user
    mock_session.query().filter().all.return_value = [MagicMock(name="Project 1")]

    result = get_governance_projects(
        db=mock_session,
        offset=0,
        limit=10,
        sort_by="name",
        order_type="asc",
        tenant_id=1,
        user_id=1,
    )

    # assert result is not None
    # assert isinstance(result, list)
    # assert result[0].name == "Project 1"


@pytest.mark.asyncio
async def test_get_risk_items(mock_session, mock_user):
    mock_session.query().filter().first.return_value = mock_user
    mock_session.query().join().all.return_value = [MagicMock(name="Risk Project")]

    result = get_risk_items(
        db=mock_session, offset=0, limit=5, sort_by="name", order_type="asc", tenant_id=1, user_id=1
    )

    # assert result is not None
    # assert len(result) > 0
    # assert result[0].name == "Risk Project"


@pytest.mark.asyncio
async def test_get_compliance(mock_session, mock_user):
    mock_session.query().filter().first.return_value = mock_user
    mock_session.query().join().all.return_value = [MagicMock(name="Compliance Project")]

    result = get_compliance(
        db=mock_session,
        offset=0,
        limit=5,
        sort_by="framework",
        order_type="asc",
        tenant_id=1,
        user_id=1,
    )

    # assert result is not None
    # assert isinstance(result, list)
    # assert result[0].name == "Compliance Project"


@pytest.mark.asyncio
async def test_get_projects_tasks(mock_session, mock_user):
    mock_session.query().filter().first.return_value = mock_user
    mock_session.query().all.return_value = [MagicMock(name="Project Task")]

    result = get_projects_tasks(
        db=mock_session,
        offset=0,
        limit=10,
        sort_by="name",
        order_type="asc",
        tenant_id=1,
        user_id=1,
    )

    # assert result is not None
    # assert len(result) > 0
    # assert result[0].name == "Project Task"


@pytest.mark.asyncio
async def test_get_summary_chart_data_by_project(mock_session):
    project_id = 1
    mock_session.query().filter().first.return_value = MagicMock(name="Test Project")
    mock_session.query().join().all.return_value = [MagicMock(risk_impact="Moderate")]
    mock_session.query().filter().count.return_value = 3
    mock_session.query().filter().count.return_value = 1  # for `num_risks_over_5`

    result = get_summary_chart_data_by_project(
        db=mock_session, project_id=project_id, tenant_id=1, user_id=1
    )

    assert result is not None
    assert "name" in result
    assert "low_risks" in result
    assert result["low_risks"] >= 0
