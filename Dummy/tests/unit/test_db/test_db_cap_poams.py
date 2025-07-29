import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from fedrisk_api.db.models import CapPoam, User, Project, CapPoamHistory, UserWatching
from fedrisk_api.schema.cap_poam import CreateCapPoam, UpdateCapPoam
from fedrisk_api.utils.email_util import send_watch_email
from fedrisk_api.utils.sms_util import publish_notification
from fedrisk_api.db.cap_poam import (
    create_cap_poam,
    manage_notifications,
    manage_stakeholders,
    notify_user,
    delete_cap_poam,
    update_cap_poam,
)


@pytest.fixture
def mock_db():
    # Mock the DB session
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def mock_user():
    # Mock a user for testing
    return User(id=1, email="test@example.com", phone_no="1234567890")


@pytest.fixture
def mock_user_watching():
    # Mock a user for testing
    return UserWatching(user_id=1, project_cap_poams=True)


@pytest.fixture
def mock_project():
    # Mock a project for testing
    return Project(id=1, tenant_id=1)


@pytest.mark.asyncio
async def test_create_cap_poam(mock_db, mock_user, mock_project):
    # Arrange: Mock the necessary methods
    cap_poam_data = CreateCapPoam(
        project_id=mock_project.id,
        name="Test Cap Poam",
        owner_id=mock_user.id,
        description="Test description",
    )

    mock_db.query.return_value.filter_by.return_value.first.return_value = mock_project
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()

    # Act: Call the function to create a CapPoam
    result = await create_cap_poam(
        mock_db, cap_poam_data, tenant_id=mock_project.tenant_id, user_id=mock_user.id
    )

    # Assert: Check the function behavior
    assert result.name == "Test Cap Poam"
    mock_db.add.assert_called()
    mock_db.commit.assert_called()

    # Check if notification was added for the owner
    # mock_db.add.assert_any_call(
    #     CapPoamHistory(
    #         cap_poam_id=result.id,
    #         author_id=mock_user.id,
    #         history=f"Created new cap poam {result.name}"
    #     )
    # )

    # Check the send email function was called
    # with patch('fedrisk_api.utils.email_util.send_watch_email') as mock_email:
    #     await manage_notifications(mock_db, [mock_user], "New cap poam created", "/link", 1, result.id)
    #     mock_email.assert_called_with(
    #         {"subject": "New cap poam created", "email": mock_user.email, "message": "New cap poam created Link: /link"}
    #     )


@pytest.mark.asyncio
async def test_update_cap_poam(mock_db, mock_user, mock_project, mock_user_watching):
    # Arrange: Mock existing Cap Poam and the updated data
    existing_cap_poam = CapPoam(
        id=1,
        name="Old Cap Poam",
        description="Old description",
        due_date="2024-12-31",
        status="open",
        criticality_rating=3,
        owner_id=mock_user.id,
        project_id=mock_project.id,
    )

    updated_data = UpdateCapPoam(
        name="Updated Cap Poam",
        description="Updated description",
        due_date="2025-01-01",
        status="In Progress",
        criticality_rating="Low",
        owner_id=mock_user.id,
        stakeholder_ids=[mock_user.id],
        project_control_ids=[1, 2],
        project_id=mock_project.id,
    )

    # Mock the DB query to return the existing Cap Poam
    mock_db.query.return_value.filter.return_value.first.return_value = existing_cap_poam
    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()

    # Act: Call the update_cap_poam function
    result = await update_cap_poam(
        db=mock_db,
        id=existing_cap_poam.id,
        cap_poam=updated_data,
        tenant_id=mock_project.tenant_id,
        user_id=mock_user.id,
    )

    # Assert: Check that the Cap Poam was updated
    # assert result.name == "Updated Cap Poam"
    # mock_db.add.assert_called()  # Check if CapPoamHistory was added
    # mock_db.commit.assert_called()

    # Assert that history entries were logged
    history_entry = mock_db.add.call_args_list[0][0][0]  # Get the first call to add
    # assert isinstance(history_entry, CapPoamHistory)
    # assert history_entry.history == "Updated name"

    # # Assert that the stakeholder management function was called
    # mock_db.query.assert_called_with(UserWatching)

    # Assert email notification was sent
    # with patch('fedrisk_api.utils.email_util.send_watch_email') as mock_email:
    #     message = "Updated name"
    #     link = f"/projects/{mock_project.id}/cap_poams/{existing_cap_poam.id}"
    #     users_watching = [mock_user_watching]  # Assuming mock_user is watching
    #     await manage_notifications(mock_db, users_watching, message, link, mock_project.id, existing_cap_poam.id)
    # mock_email.assert_called_once_with({
    #     "subject": message,
    #     "email": mock_user.email,
    #     "message": f"{message} Link: {link}"
    # })


# @pytest.mark.asyncio
# async def test_manage_stakeholders(mock_db, mock_user, mock_project):
#     # Mock stakeholder management functionality
#     stakeholder_ids = [mock_user.id]
#     cap_poam = CapPoam(
#         id=1, name="Test Cap Poam", project_id=mock_project.id, owner_id=mock_user.id
#     )
#     mock_db.query.return_value.filter.return_value.all.return_value = [mock_user]

#     # Act: Call function to manage stakeholders
#     await manage_stakeholders(mock_db, stakeholder_ids, cap_poam, mock_project, "/link")

#     # Assert: Ensure stakeholder has been added and notification sent
#     mock_db.add.assert_called()
#     mock_db.commit.assert_called()


# @pytest.mark.asyncio
# async def test_notify_user(mock_user):
#     # Test the notify user function for email and SMS
#     with patch("fedrisk_api.utils.email_util.send_watch_email") as mock_email, patch(
#         "fedrisk_api.utils.sms_util.publish_notification"
#     ) as mock_sms:

#         await notify_user(mock_user, "Test Message", "/test-link", None)

#         # # Assert email was sent
#         # mock_email.assert_called_once_with({
#         #     "subject": "Test Message",
#         #     "email": mock_user.email,
#         #     "message": "Test Message Link: /test-link"
#         # })

#         # # Assert SMS was sent
#         # mock_sms.assert_called_once_with({
#         #     "phone_no": mock_user.phone_no,
#         #     "message": "Test Message Link: /test-link"
#         # })


@pytest.mark.asyncio
async def test_delete_cap_poam(mock_db, mock_user, mock_project):
    # Arrange: Mock delete functionality
    cap_poam_id = 1
    mock_db.query.return_value.filter.return_value.first.return_value = CapPoam(
        id=cap_poam_id, project_id=mock_project.id
    )
    mock_db.query.return_value.filter.return_value.delete.return_value = None
    mock_db.commit = MagicMock()

    # Act: Call delete
    result = await delete_cap_poam(mock_db, cap_poam_id, mock_project.tenant_id)

    # Assert: Check that the cap poam was deleted
    assert result is True
    mock_db.commit.assert_called()
