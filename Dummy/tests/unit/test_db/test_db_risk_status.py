import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.models import RiskStatus
from fedrisk_api.schema.risk_status import CreateRiskStatus, UpdateRiskStatus
from fedrisk_api.db.risk_status import (
    create_risk_status,
    get_all_risk_statuses,
    get_risk_status,
    update_risk_status,
    delete_risk_status,
)


@pytest.fixture
def db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


def test_create_risk_status(db_session):
    """Test creating a risk status."""
    risk_status_data = CreateRiskStatus(name="Active", description="Description")
    db_session.add = MagicMock()
    db_session.commit = MagicMock()
    db_session.refresh = MagicMock()

    result = create_risk_status(db_session, risk_status_data)

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(result)
    assert result.name == "Active"


def test_get_all_risk_statuses(db_session):
    """Test getting all risk statuses."""
    db_session.query().all.return_value = [RiskStatus(id=1, name="Inactive")]

    result = get_all_risk_statuses(db_session)

    assert len(result) == 1
    assert result[0].name == "Inactive"


def test_get_risk_status(db_session):
    """Test getting a specific risk status."""
    db_session.query().filter().first.return_value = RiskStatus(id=1, name="Pending")

    result = get_risk_status(db_session, id=1)

    assert result is not None
    assert result.name == "Pending"


def test_update_risk_status(db_session):
    """Test updating a risk status."""
    db_session.query().filter().first.return_value = RiskStatus(id=1, name="Draft")
    risk_status_data = UpdateRiskStatus(name="Published")

    result = update_risk_status(db_session, id=1, risk_status=risk_status_data)

    db_session.commit.assert_called_once()
    assert result == 1


def test_update_risk_status_not_found(db_session):
    """Test updating a non-existent risk status."""
    db_session.query().filter().first.return_value = None
    risk_status_data = UpdateRiskStatus(name="Non-Existent Status")

    result = update_risk_status(db_session, id=2, risk_status=risk_status_data)

    assert result == 0


def test_delete_risk_status(db_session):
    """Test deleting a risk status."""
    db_session.query().filter().first.return_value = RiskStatus(id=1, name="Archived")

    result = delete_risk_status(db_session, id=1)

    db_session.commit.assert_called_once()
    assert result == 1


def test_delete_risk_status_not_found(db_session):
    """Test deleting a non-existent risk status."""
    db_session.query().filter().first.return_value = None

    result = delete_risk_status(db_session, id=2)

    assert result == 0
