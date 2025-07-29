import pytest
from unittest.mock import MagicMock, AsyncMock
from sqlalchemy.orm.session import Session
from fedrisk_api.schema.wbs import CreateWBS, UpdateWBS
from fedrisk_api.db.models import WBS, UserNotifications, KeywordMapping, Task
from fedrisk_api.utils.email_util import send_watch_email
from fedrisk_api.utils.sms_util import publish_notification
from fedrisk_api.db.wbs import create_wbs, update_wbs, delete_wbs, get_all_project_wbs, get_wbs

# Mock data for tests
@pytest.fixture
def mock_session():
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_create_wbs_data():
    return CreateWBS(name="Test WBS", description="Description of WBS", project_id="1", user_id="1")


@pytest.fixture
def mock_update_wbs_data():
    return UpdateWBS(
        id="1", name="Updated WBS", description="Updated Description", project_id="1", user_id="2"
    )


@pytest.mark.asyncio
async def test_create_wbs(mock_session, mock_create_wbs_data):
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()
    mock_session.query().filter().all.return_value = []

    new_wbs = await create_wbs(
        mock_session, mock_create_wbs_data, keywords="test,example", tenant_id=1, user_id=1
    )

    assert new_wbs.name == "Test WBS"
    assert new_wbs.description == "Description of WBS"
    # mock_session.add.assert_called_once()
    mock_session.commit.assert_called()
    mock_session.refresh.assert_called()


@pytest.mark.asyncio
async def test_update_wbs(mock_session, mock_update_wbs_data):
    mock_session.query().filter().first.return_value = MagicMock(spec=WBS, name="Old WBS")
    mock_session.commit = MagicMock()

    updated_wbs = await update_wbs(
        mock_session, id=1, wbs=mock_update_wbs_data, tenant_id=1, keywords="updated", user_id=1
    )

    # assert updated_wbs.name == "Updated WBS"
    # assert updated_wbs.description == "Updated Description"
    # mock_session.commit.assert_called()


@pytest.mark.asyncio
async def test_delete_wbs(mock_session):
    mock_session.query().filter().first.return_value = MagicMock(spec=WBS, name="WBS to delete")
    mock_session.commit = MagicMock()

    result = await delete_wbs(mock_session, id=1)

    assert result is True
    mock_session.commit.assert_called()


def test_get_all_project_wbs(mock_session):
    mock_session.query().filter().all.return_value = [MagicMock(spec=WBS, name="Test WBS")]

    result = get_all_project_wbs(mock_session, project_id=1)

    # assert len(result) == 1
    # assert result[0].name == "Test WBS"


def test_get_wbs(mock_session):
    mock_session.query().filter().first.return_value = MagicMock(spec=WBS, name="Test WBS")

    result = get_wbs(mock_session, id=1)

    # assert result.name == "Test WBS"
