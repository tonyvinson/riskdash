import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.models import RiskImpact
from fedrisk_api.schema.risk_impact import CreateRiskImpact, UpdateRiskImpact
from fedrisk_api.db.risk_impact import (
    create_risk_impact,
    get_all_risk_impacts,
    get_risk_impact,
    update_risk_impact,
    delete_risk_impact,
)


@pytest.fixture
def db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


def test_create_risk_impact(db_session):
    """Test creating a risk impact."""
    risk_impact_data = CreateRiskImpact(name="High Impact", description="Description")
    db_session.add = MagicMock()
    db_session.commit = MagicMock()
    db_session.refresh = MagicMock()

    result = create_risk_impact(db_session, risk_impact_data)

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(result)
    assert result.name == "High Impact"


def test_get_all_risk_impacts(db_session):
    """Test getting all risk impacts."""
    db_session.query().all.return_value = [RiskImpact(id=1, name="Low Impact")]

    result = get_all_risk_impacts(db_session)

    assert len(result) == 1
    assert result[0].name == "Low Impact"


def test_get_risk_impact(db_session):
    """Test getting a specific risk impact."""
    db_session.query().filter().first.return_value = RiskImpact(id=1, name="Medium Impact")

    result = get_risk_impact(db_session, id=1)

    assert result is not None
    assert result.name == "Medium Impact"


def test_update_risk_impact(db_session):
    """Test updating a risk impact."""
    db_session.query().filter().first.return_value = RiskImpact(id=1, name="Low Impact")
    risk_impact_data = UpdateRiskImpact(name="Updated Low Impact")

    result = update_risk_impact(db_session, id=1, risk_impact=risk_impact_data)

    db_session.commit.assert_called_once()
    assert result == 1


def test_update_risk_impact_not_found(db_session):
    """Test updating a non-existent risk impact."""
    db_session.query().filter().first.return_value = None
    risk_impact_data = UpdateRiskImpact(name="Non-Existent Impact")

    result = update_risk_impact(db_session, id=2, risk_impact=risk_impact_data)

    assert result == 0


def test_delete_risk_impact(db_session):
    """Test deleting a risk impact."""
    db_session.query().filter().first.return_value = RiskImpact(id=1, name="Critical Impact")

    result = delete_risk_impact(db_session, id=1)

    db_session.commit.assert_called_once()
    assert result == 1


def test_delete_risk_impact_not_found(db_session):
    """Test deleting a non-existent risk impact."""
    db_session.query().filter().first.return_value = None

    result = delete_risk_impact(db_session, id=2)

    assert result == 0
