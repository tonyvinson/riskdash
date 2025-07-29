import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.models import RiskMapping
from fedrisk_api.schema.risk_mapping import CreateRiskMapping, UpdateRiskMapping
from fedrisk_api.db.risk_mapping import (
    create_risk_mapping,
    get_all_risk_mappings,
    get_risk_mapping,
    update_risk_mapping,
    delete_risk_mapping,
)


@pytest.fixture
def db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


def test_create_risk_mapping(db_session):
    """Test creating a risk mapping."""
    risk_mapping_data = CreateRiskMapping(name="Mapping A", description="Description")
    db_session.add = MagicMock()
    db_session.commit = MagicMock()
    db_session.refresh = MagicMock()

    result = create_risk_mapping(db_session, risk_mapping_data)

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(result)
    assert result.name == "Mapping A"


def test_get_all_risk_mappings(db_session):
    """Test getting all risk mappings."""
    db_session.query().all.return_value = [RiskMapping(id=1, name="Mapping A")]

    result = get_all_risk_mappings(db_session)

    assert len(result) == 1
    assert result[0].name == "Mapping A"


def test_get_risk_mapping(db_session):
    """Test getting a specific risk mapping."""
    db_session.query().filter().first.return_value = RiskMapping(id=1, name="Mapping B")

    result = get_risk_mapping(db_session, id=1)

    assert result is not None
    assert result.name == "Mapping B"


def test_update_risk_mapping(db_session):
    """Test updating a risk mapping."""
    db_session.query().filter().first.return_value = RiskMapping(id=1, name="Mapping A")
    risk_mapping_data = UpdateRiskMapping(name="Updated Mapping A")

    result = update_risk_mapping(db_session, id=1, risk_mapping=risk_mapping_data)

    db_session.commit.assert_called_once()
    assert result == 1


def test_update_risk_mapping_not_found(db_session):
    """Test updating a non-existent risk mapping."""
    db_session.query().filter().first.return_value = None
    risk_mapping_data = UpdateRiskMapping(name="Non-Existent Mapping")

    result = update_risk_mapping(db_session, id=2, risk_mapping=risk_mapping_data)

    assert result == 0


def test_delete_risk_mapping(db_session):
    """Test deleting a risk mapping."""
    db_session.query().filter().first.return_value = RiskMapping(id=1, name="Mapping C")

    result = delete_risk_mapping(db_session, id=1)

    db_session.commit.assert_called_once()
    assert result == 1


def test_delete_risk_mapping_not_found(db_session):
    """Test deleting a non-existent risk mapping."""
    db_session.query().filter().first.return_value = None

    result = delete_risk_mapping(db_session, id=2)

    assert result == 0
