import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.models import RiskScore
from fedrisk_api.schema.risk_score import CreateRiskScore, UpdateRiskScore
from fedrisk_api.db.risk_score import (
    create_risk_score,
    get_all_risk_scores,
    get_risk_score,
    update_risk_score,
    delete_risk_score,
)


@pytest.fixture
def db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


def test_create_risk_score(db_session):
    """Test creating a risk score."""
    risk_score_data = CreateRiskScore(name="High Score", description="Description")
    db_session.add = MagicMock()
    db_session.commit = MagicMock()
    db_session.refresh = MagicMock()

    result = create_risk_score(db_session, risk_score_data)

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(result)
    assert result.name == "High Score"


def test_get_all_risk_scores(db_session):
    """Test getting all risk scores."""
    db_session.query().all.return_value = [RiskScore(id=1, name="Medium Score")]

    result = get_all_risk_scores(db_session)

    assert len(result) == 1
    assert result[0].name == "Medium Score"


def test_get_risk_score(db_session):
    """Test getting a specific risk score."""
    db_session.query().filter().first.return_value = RiskScore(id=1, name="Low Score")

    result = get_risk_score(db_session, id=1)

    assert result is not None
    assert result.name == "Low Score"


def test_update_risk_score(db_session):
    """Test updating a risk score."""
    db_session.query().filter().first.return_value = RiskScore(id=1, name="Low Score")
    risk_score_data = UpdateRiskScore(name="Updated Low Score")

    result = update_risk_score(db_session, id=1, risk_score=risk_score_data)

    db_session.commit.assert_called_once()
    assert result == 1


def test_update_risk_score_not_found(db_session):
    """Test updating a non-existent risk score."""
    db_session.query().filter().first.return_value = None
    risk_score_data = UpdateRiskScore(name="Non-Existent Score")

    result = update_risk_score(db_session, id=2, risk_score=risk_score_data)

    assert result == 0


def test_delete_risk_score(db_session):
    """Test deleting a risk score."""
    db_session.query().filter().first.return_value = RiskScore(id=1, name="Critical Score")

    result = delete_risk_score(db_session, id=1)

    db_session.commit.assert_called_once()
    assert result == 1


def test_delete_risk_score_not_found(db_session):
    """Test deleting a non-existent risk score."""
    db_session.query().filter().first.return_value = None

    result = delete_risk_score(db_session, id=2)

    assert result == 0
