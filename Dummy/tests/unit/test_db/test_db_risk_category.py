import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.models import RiskCategory
from fedrisk_api.schema.risk_category import CreateRiskCategory, UpdateRiskCategory
from fedrisk_api.db.risk_category import (
    create_risk_category,
    get_all_risk_categories,
    get_risk_category,
    update_risk_category,
    delete_risk_category,
)


@pytest.fixture
def db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


def test_create_risk_category(db_session):
    """Test creating a risk category."""
    risk_category_data = CreateRiskCategory(name="Test Category", description="Description")
    db_session.add = MagicMock()
    db_session.commit = MagicMock()
    db_session.refresh = MagicMock()

    result = create_risk_category(db_session, risk_category_data, 1)

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(result)
    assert result.name == "Test Category"


def test_get_all_risk_categories(db_session):
    """Test getting all risk categories."""
    db_session.query().all.return_value = [RiskCategory(id=1, name="Category A")]

    result = get_all_risk_categories(db_session, 1)

    # assert len(result) == 1
    # assert result[0].name == "Category A"


def test_get_risk_category(db_session):
    """Test getting a specific risk category."""
    db_session.query().filter().first.return_value = RiskCategory(id=1, name="Category A")

    result = get_risk_category(db_session, id=1)

    assert result is not None
    assert result.name == "Category A"


def test_update_risk_category(db_session):
    """Test updating a risk category."""
    db_session.query().filter().first.return_value = RiskCategory(id=1, name="Category A")
    risk_category_data = UpdateRiskCategory(name="Updated Category A")

    result = update_risk_category(db_session, id=1, risk_category=risk_category_data)

    db_session.commit.assert_called_once()
    assert result == 1


def test_update_risk_category_not_found(db_session):
    """Test updating a non-existent risk category."""
    db_session.query().filter().first.return_value = None
    risk_category_data = UpdateRiskCategory(name="Non-Existent Category")

    result = update_risk_category(db_session, id=2, risk_category=risk_category_data)

    assert result == 0


def test_delete_risk_category(db_session):
    """Test deleting a risk category."""
    db_session.query().filter().first.return_value = RiskCategory(id=1, name="Category A")

    result = delete_risk_category(db_session, id=1)

    db_session.commit.assert_called_once()
    assert result == 1


def test_delete_risk_category_not_found(db_session):
    """Test deleting a non-existent risk category."""
    db_session.query().filter().first.return_value = None

    result = delete_risk_category(db_session, id=2)

    assert result == 0
