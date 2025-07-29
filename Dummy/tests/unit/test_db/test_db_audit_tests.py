import pytest
from sqlalchemy.orm import Session
from unittest.mock import AsyncMock, MagicMock
from fedrisk_api.db.models import AuditTest, Project, User, UserWatching, UserNotifications
from fedrisk_api.schema.audit_test import CreateAuditTest, UpdateAuditTest
from fedrisk_api.db.audit_test import (
    create_audit_test,
    update_audit_test,
    delete_audit_test,
    get_audit_test,
    get_all_audit_tests,
)

# Mock database session
@pytest.fixture
def db_session():
    session = AsyncMock(spec=Session)
    return session


# Test creating an audit test
# @pytest.mark.asyncio
# async def test_create_audit_test(db_session, mocker):
#     tenant_id, user_id = 1, 1
#     project_id = 1
#     create_audit_data = CreateAuditTest(
#         name="Test Audit",
#         description="Audit test description",
#         project_id=project_id,
#         tester_id=user_id,
#     )
#     # Mock project retrieval
#     project_mock = Project(id=project_id, tenant_id=tenant_id)
#     mocker.patch("fedrisk_api.db.models.Project", return_value=project_mock)

#     # Mock user with a valid email
#     user_mock = MagicMock()
#     user_mock.email = "test@example.com"  # Explicitly set to a string
#     mocker.patch("fedrisk_api.db.models.User.query.filter_by().first", return_value=user_mock)

#     # Mock the notification functions to prevent actual calls
#     mocker.patch("fedrisk_api.utils.email_util.send_watch_email", new_callable=AsyncMock)
#     mocker.patch("fedrisk_api.utils.sms_util.publish_notification", new_callable=AsyncMock)


#     # Act
#     result = await create_audit_test(db=db_session, keywords="keyword1,keyword2", audit_test=create_audit_data, tenant_id=tenant_id, user_id=user_id)

#     # Assert
#     assert result is not None
#     assert result.name == "Test Audit"
#     assert db_session.commit.called

# Test updating an audit test with history and notifications
@pytest.mark.asyncio
async def test_update_audit_test(db_session, mocker):
    # Arrange
    tenant_id, user_id, audit_test_id = 1, 1, 1
    update_data = UpdateAuditTest(
        name="Updated Audit Test",
        description="Updated description",
    )

    # Mock audit test and project
    db_session.query(AuditTest).filter_by.return_value.first.return_value = AuditTest(
        id=audit_test_id, name="Old Name", project_id=1
    )

    # Mock notification functions
    mocker.patch("fedrisk_api.utils.email_util.send_watch_email", new_callable=AsyncMock)
    mocker.patch("fedrisk_api.utils.sms_util.publish_notification", new_callable=AsyncMock)

    # Act
    result = await update_audit_test(
        db=db_session,
        id=audit_test_id,
        keywords="new_keyword",
        audit_test=update_data,
        tenant_id=tenant_id,
        user_id=user_id,
    )

    # # Assert
    # assert result is not None
    # assert result.name == "Updated Audit Test"
    # assert db_session.commit.called


# Test deleting an audit test
@pytest.mark.asyncio
async def test_delete_audit_test(db_session, mocker):
    # Arrange
    tenant_id, audit_test_id = 1, 1

    # Mock audit test and related data
    db_session.query(AuditTest).filter_by.return_value.first.return_value = AuditTest(
        id=audit_test_id
    )

    # Act
    result = await delete_audit_test(db=db_session, id=audit_test_id, tenant_id=tenant_id)

    # Assert
    assert result is True
    assert db_session.commit.called


# Test retrieving a single audit test
def test_get_audit_test(db_session, mocker):
    # Arrange
    tenant_id, user_id, audit_test_id = 1, 1, 1

    # Mock data retrieval
    db_session.query(AuditTest).filter_by.return_value.first.return_value = AuditTest(
        id=audit_test_id
    )

    # Act
    result = get_audit_test(db=db_session, id=audit_test_id, tenant_id=tenant_id, user_id=user_id)

    # # Assert
    # assert result is not None
    # assert result.id == audit_test_id


# Test retrieving all audit tests with filters
def test_get_all_audit_tests(db_session, mocker):
    # Arrange
    tenant_id, user_id = 1, 1
    project_id, framework_id = 1, 1
    filter_by, filter_value, sort_by = "status", "active", "name"

    # Mock data retrieval
    db_session.query(AuditTest).all.return_value = [AuditTest(id=1), AuditTest(id=2)]

    # Act
    result = get_all_audit_tests(
        db=db_session,
        tenant_id=tenant_id,
        user_id=user_id,
        project_id=project_id,
        framework_id=framework_id,
        q=None,
        filter_by=filter_by,
        filter_value=filter_value,
        sort_by=sort_by,
    )

    # Assert


#  assert len(result) == 2
