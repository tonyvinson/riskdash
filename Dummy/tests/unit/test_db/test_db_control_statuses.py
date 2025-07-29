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
    return MagicMock(spec=Session)


@pytest.fixture
def create_control_status_data():
    return CreateControlStatus(name="Test Status", description="A test control status", tenant_id=1)


@pytest.fixture
def update_control_status_data():
    return UpdateControlStatus(description="Updated description")


def test_create_control_status(db_session, create_control_status_data):
    created_status = create_control_status(db_session, create_control_status_data)
    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    db_session.refresh.assert_called_once_with(created_status)
    assert created_status == db_session.add.call_args[0][0]


def test_get_all_control_statuses(db_session):
    db_session.query().filter().all.return_value = ["status1", "status2"]
    statuses = get_all_control_statuses(q="test", db=db_session, tenant_id=1, sort_by=None)
    # assert len(statuses) == 2


def test_get_control_status(db_session):
    db_session.query().filter().first.return_value = "test_status"
    status = get_control_status(db_session, id=1)
    assert status == "test_status"


def test_update_control_status(db_session, update_control_status_data):
    db_session.query().filter().first.return_value = True
    updated = update_control_status(db_session, id=1, control_status=update_control_status_data)
    db_session.commit.assert_called_once()
    assert updated

    # Test for non-existent control status
    db_session.query().filter().first.return_value = None
    updated = update_control_status(db_session, id=999, control_status=update_control_status_data)
    assert not updated


def test_delete_control_status(db_session):
    db_session.query().filter().first.return_value = MagicMock()
    deleted = delete_control_status(db_session, id=1)
    db_session.commit.assert_called_once()
    assert deleted

    # Test for non-existent control status
    db_session.query().filter().first.return_value = None
    deleted = delete_control_status(db_session, id=999)
    assert not deleted
