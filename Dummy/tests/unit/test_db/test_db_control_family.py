import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from fedrisk_api.db.control_family import (
    create_control_family,
    get_all_control_families,
    get_control_family,
    update_control_family,
    delete_control_family,
)
from fedrisk_api.db.models import ControlFamily
from fedrisk_api.schema.control_family import CreateControlFamily, UpdateControlFamily


@pytest.fixture
def db_session():
    """Mocked database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_control_family():
    """Mock ControlFamily instance."""
    return ControlFamily(id=1, name="Test Family", description="Test Description", tenant_id=100)


@pytest.fixture
def create_control_family_data():
    """Mock CreateControlFamily data."""
    return CreateControlFamily(name="New Family", description="A new control family")


@pytest.fixture
def update_control_family_data():
    """Mock UpdateControlFamily data."""
    return UpdateControlFamily(name="Updated Family", description="An updated control family")


def test_create_control_family(db_session, create_control_family_data):
    """Test creating a new control family."""
    new_family = create_control_family(
        db=db_session, control_family=create_control_family_data, tenant_id=100
    )

    assert new_family is not None
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(new_family)


def test_get_all_control_families(db_session, mock_control_family):
    """Test retrieving all control families with filtering, searching, and sorting."""
    db_session.query().filter().all.return_value = [mock_control_family]
    control_families = get_all_control_families(
        q="family",
        db=db_session,
        tenant_id=100,
        filter_by="name",
        filter_value="Test",
        sort_by="name",
    )

    assert control_families is not None
    # assert len(control_families.all()) > 0
    db_session.query().filter.assert_called()


def test_get_control_family(db_session, mock_control_family):
    """Test retrieving a single control family by ID."""
    db_session.query().filter().filter().first.return_value = mock_control_family

    control_family = get_control_family(db=db_session, id=1, tenant_id=100)

    assert control_family is not None
    assert control_family.id == mock_control_family.id
    db_session.query().filter().filter().first.assert_called_once()


def test_update_control_family(db_session, mock_control_family, update_control_family_data):
    """Test updating an existing control family."""
    db_session.query().filter().filter().first.return_value = mock_control_family

    result = update_control_family(
        db=db_session, id=1, control_family=update_control_family_data, tenant_id=100
    )

    assert result is True
    db_session.commit.assert_called_once()
    db_session.query().filter().filter().update.assert_called_once()


def test_update_control_family_not_found(db_session, update_control_family_data):
    """Test updating a non-existent control family returns False."""
    db_session.query().filter().filter().first.return_value = None

    result = update_control_family(
        db=db_session, id=1, control_family=update_control_family_data, tenant_id=100
    )

    assert result is False
    db_session.commit.assert_not_called()


def test_delete_control_family(db_session, mock_control_family):
    """Test deleting an existing control family."""
    db_session.query().filter().filter().first.return_value = mock_control_family

    result = delete_control_family(db=db_session, id=1, tenant_id=100)

    assert result is True
    db_session.commit.assert_called_once()
    db_session.query().filter().filter().delete.assert_called_once()


def test_delete_control_family_not_found(db_session):
    """Test deleting a non-existent control family returns False."""
    db_session.query().filter().filter().first.return_value = None

    result = delete_control_family(db=db_session, id=1, tenant_id=100)

    assert result is False
    db_session.commit.assert_not_called()
