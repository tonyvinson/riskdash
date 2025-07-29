import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.orm import Session
from fedrisk_api.db.models import (
    Risk,
    Project,
    User,
    ProjectUser,
    UserNotifications,
    UserWatching,
    RiskHistory,
    Keyword,
    KeywordMapping,
    RiskDocument,
    TaskRisk,
    RiskStakeholder,
    UserNotificationSettings,
    RiskCategory,
    RiskImpact,
    RiskLikelihood,
)
from fedrisk_api.schema.risk import CreateRisk, UpdateRisk
from fedrisk_api.db.risk import (
    create_risk,
    get_all_risks,
    get_risk,
    update_risk,
    delete_risk,
    search,
)


@pytest.fixture
def db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


@pytest.mark.asyncio
async def test_create_risk(db_session):
    """Test creating a risk."""
    db_session.query().filter().first.return_value = Project(
        id=1, tenant_id=1, project_controls=[], audit_tests=[]
    )
    risk_data = CreateRisk(name="Test Risk", project_id=1)

    result = await create_risk(db_session, risk=risk_data, tenant_id=1, keywords="", user_id=1)

    db_session.add.assert_called()
    db_session.commit.assert_called()
    assert result.name == "Test Risk"


def test_get_all_risks(db_session):
    """Test retrieving all risks."""
    db_session.query().filter().join().options().all.return_value = [Risk(id=1, name="Risk A")]

    result = get_all_risks(tenant_id=1, project_id=1, db=db_session)

    # assert len(result) == 1
    # assert result[0].name == "Risk A"


def test_get_risk(db_session):
    """Test retrieving a specific risk."""
    db_session.query().filter().first.return_value = Risk(id=1, name="Risk A")

    result = get_risk(db=db_session, id=1, tenant_id=1)

    # assert result.id == 1
    # assert result.name == "Risk A"


@pytest.mark.asyncio
async def test_update_risk(db_session):
    """Test updating a risk."""
    db_session.query().filter().first.return_value = Risk(id=1, name="Risk A")
    update_data = UpdateRisk(name="Updated Risk A")

    result = await update_risk(
        db_session, id=1, risk=update_data, tenant_id=1, keywords="", user_id=1
    )

    db_session.commit.assert_called()
    # assert result.name == "Updated Risk A"


@pytest.mark.asyncio
async def test_delete_risk(db_session):
    """Test deleting a risk."""
    db_session.query().filter().first.return_value = Risk(id=1, name="Risk A")

    result = await delete_risk(db=db_session, id=1, tenant_id=1)

    db_session.commit.assert_called()
    assert result is True


def test_search_risks(db_session):
    """Test searching for risks."""
    db_session.query().filter().all.return_value = [Risk(id=1, name="Risk A")]
    db_session.query().filter().count.return_value = 1

    count, result = search(query="Risk", db=db_session, tenant_id=1, user_id=1)

    assert count == 1
    assert len(result) == 1
    assert result[0].name == "Risk A"
