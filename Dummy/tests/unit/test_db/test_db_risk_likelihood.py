import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.models import RiskLikelihood
from fedrisk_api.schema.risk_likelihood import CreateRiskLikelihood, UpdateRiskLikelihood
from fedrisk_api.db.risk_likelihood import (
    create_risk_likelihood,
    get_all_risk_likelihoods,
    get_risk_likelihood,
    update_risk_likelihood,
    delete_risk_likelihood,
)


@pytest.fixture
def db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


def test_create_risk_likelihood(db_session):
    """Test creating a risk likelihood."""
    risk_likelihood_data = CreateRiskLikelihood(name="Very Likely", description="Description")
    db_session.add = MagicMock()
    db_session.commit = MagicMock()
    db_session.refresh = MagicMock()

    result = create_risk_likelihood(db_session, risk_likelihood_data)

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(result)
    assert result.name == "Very Likely"


def test_get_all_risk_likelihoods(db_session):
    """Test getting all risk likelihoods."""
    db_session.query().all.return_value = [RiskLikelihood(id=1, name="Unlikely")]

    result = get_all_risk_likelihoods(db_session)

    assert len(result) == 1
    assert result[0].name == "Unlikely"


def test_get_risk_likelihood(db_session):
    """Test getting a specific risk likelihood."""
    db_session.query().filter().first.return_value = RiskLikelihood(id=1, name="Likely")

    result = get_risk_likelihood(db_session, id=1)

    assert result is not None
    assert result.name == "Likely"


def test_update_risk_likelihood(db_session):
    """Test updating a risk likelihood."""
    db_session.query().filter().first.return_value = RiskLikelihood(id=1, name="Unlikely")
    risk_likelihood_data = UpdateRiskLikelihood(name="Updated Unlikely")

    result = update_risk_likelihood(db_session, id=1, risk_likelihood=risk_likelihood_data)

    db_session.commit.assert_called_once()
    assert result == 1


def test_update_risk_likelihood_not_found(db_session):
    """Test updating a non-existent risk likelihood."""
    db_session.query().filter().first.return_value = None
    risk_likelihood_data = UpdateRiskLikelihood(name="Non-Existent Likelihood")

    result = update_risk_likelihood(db_session, id=2, risk_likelihood=risk_likelihood_data)

    assert result == 0


def test_delete_risk_likelihood(db_session):
    """Test deleting a risk likelihood."""
    db_session.query().filter().first.return_value = RiskLikelihood(
        id=1, name="Critical Likelihood"
    )

    result = delete_risk_likelihood(db_session, id=1)

    db_session.commit.assert_called_once()
    assert result == 1


def test_delete_risk_likelihood_not_found(db_session):
    """Test deleting a non-existent risk likelihood."""
    db_session.query().filter().first.return_value = None

    result = delete_risk_likelihood(db_session, id=2)

    assert result == 0
