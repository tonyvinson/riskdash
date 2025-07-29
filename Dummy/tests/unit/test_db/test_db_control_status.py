import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from fedrisk_api.db.control_status import (
    create_control_status,
    get_all_control_statuses,
    get_control_status,
    update_control_status,
    delete_control_status,
)
from fedrisk_api.db.models import ControlStatus
from fedrisk_api.schema.control_status import CreateControlStatus, UpdateControlStatus


@pytest.fixture
def db_session():
    """Mocked database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_control_status():
    """Mock ControlStatus instance."""
    return ControlStatus(id=1, name="Test Status", description="Test Description", tenant_id=100)


@pytest.fixture
def create_control_status_data():
    """Mock CreateControlStatus data."""
    return CreateControlStatus(name="New Status", description="A new control status")


@pytest.fixture
def update_control_status_data():
    """Mock UpdateControlStatus data."""
    return UpdateControlStatus(name="Updated Status", description="An updated control status")


def test_create_control_status(db_session, create_control_status_data):
    """Test creating a new control status."""
    new_status = create_control_status(db=db_session, control_status=create_control_status_data)

    assert new_status is not None
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(new_status)


def test_get_all_control_statuses(db_session, mock_control_status):
    """Test retrieving all control statuses with searching and sorting."""
    db_session.query().filter().all.return_value = [mock_control_status]
    control_statuses = get_all_control_statuses(
        q="status",
        db=db_session,
        tenant_id=100,
        sort_by="name",
    )

    assert control_statuses is not None
    # assert len(control_statuses.all()) > 0
    db_session.query().filter.assert_called()


def test_get_control_status(db_session, mock_control_status):
    """Test retrieving a single control status by ID."""
    db_session.query().filter().first.return_value = mock_control_status

    control_status = get_control_status(db=db_session, id=1)

    assert control_status is not None
    assert control_status.id == mock_control_status.id
    db_session.query().filter().first.assert_called_once()


def test_update_control_status(db_session, mock_control_status, update_control_status_data):
    """Test updating an existing control status."""
    db_session.query().filter().first.return_value = mock_control_status

    result = update_control_status(db=db_session, id=1, control_status=update_control_status_data)

    assert result is True
    db_session.commit.assert_called_once()
    db_session.query().filter().update.assert_called_once()


def test_update_control_status_not_found(db_session, update_control_status_data):
    """Test updating a non-existent control status returns False."""
    db_session.query().filter().first.return_value = None

    result = update_control_status(db=db_session, id=1, control_status=update_control_status_data)

    assert result is False
    db_session.commit.assert_not_called()


def test_delete_control_status(db_session, mock_control_status):
    """Test deleting an existing control status."""
    db_session.query().filter().first.return_value = mock_control_status

    result = delete_control_status(db=db_session, id=1)

    assert result is True
    db_session.commit.assert_called_once()
    db_session.query().filter().delete.assert_called_once()


def test_delete_control_status_not_found(db_session):
    """Test deleting a non-existent control status returns False."""
    db_session.query().filter().first.return_value = None

    result = delete_control_status(db=db_session, id=1)

    assert result is False
    db_session.commit.assert_not_called()
