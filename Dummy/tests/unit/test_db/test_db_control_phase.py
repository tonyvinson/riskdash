import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from fedrisk_api.db.control_phase import (
    create_control_phase,
    get_all_control_phases,
    get_control_phase,
    update_control_phase,
    delete_control_phase,
)
from fedrisk_api.db.models import ControlPhase
from fedrisk_api.schema.control_phase import CreateControlPhase, UpdateControlPhase


@pytest.fixture
def db_session():
    """Mocked database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_control_phase():
    """Mock ControlPhase instance."""
    return ControlPhase(id=1, name="Test Phase", description="Test Description", tenant_id=100)


@pytest.fixture
def create_control_phase_data():
    """Mock CreateControlPhase data."""
    return CreateControlPhase(name="New Phase", description="A new control phase")


@pytest.fixture
def update_control_phase_data():
    """Mock UpdateControlPhase data."""
    return UpdateControlPhase(name="Updated Phase", description="An updated control phase")


def test_create_control_phase(db_session, create_control_phase_data):
    """Test creating a new control phase."""
    new_phase = create_control_phase(
        db=db_session, control_phase=create_control_phase_data, tenant_id=100
    )

    assert new_phase is not None
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(new_phase)


def test_get_all_control_phases(db_session, mock_control_phase):
    """Test retrieving all control phases with filtering, searching, and sorting."""
    db_session.query().filter().all.return_value = [mock_control_phase]
    control_phases = get_all_control_phases(
        q="phase",
        db=db_session,
        tenant_id=100,
        filter_by="name",
        filter_value="Test",
        sort_by="name",
    )

    assert control_phases is not None
    # assert len(control_phases.all()) > 0
    db_session.query().filter.assert_called()


def test_get_control_phase(db_session, mock_control_phase):
    """Test retrieving a single control phase by ID."""
    db_session.query().filter().filter().first.return_value = mock_control_phase

    control_phase = get_control_phase(db=db_session, id=1, tenant_id=100)

    assert control_phase is not None
    assert control_phase.id == mock_control_phase.id
    db_session.query().filter().filter().first.assert_called_once()


def test_update_control_phase(db_session, mock_control_phase, update_control_phase_data):
    """Test updating an existing control phase."""
    db_session.query().filter().filter().first.return_value = mock_control_phase

    result = update_control_phase(
        db=db_session, id=1, control_phase=update_control_phase_data, tenant_id=100
    )

    assert result is True
    db_session.commit.assert_called_once()
    db_session.query().filter().filter().update.assert_called_once()


def test_update_control_phase_not_found(db_session, update_control_phase_data):
    """Test updating a non-existent control phase returns False."""
    db_session.query().filter().filter().first.return_value = None

    result = update_control_phase(
        db=db_session, id=1, control_phase=update_control_phase_data, tenant_id=100
    )

    assert result is False
    db_session.commit.assert_not_called()


def test_delete_control_phase(db_session, mock_control_phase):
    """Test deleting an existing control phase."""
    db_session.query().filter().filter().first.return_value = mock_control_phase

    result = delete_control_phase(db=db_session, id=1, tenant_id=100)

    assert result is True
    db_session.commit.assert_called_once()
    db_session.query().filter().filter().delete.assert_called_once()


def test_delete_control_phase_not_found(db_session):
    """Test deleting a non-existent control phase returns False."""
    db_session.query().filter().filter().first.return_value = None

    result = delete_control_phase(db=db_session, id=1, tenant_id=100)

    assert result is False
    db_session.commit.assert_not_called()
