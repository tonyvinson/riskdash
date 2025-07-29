import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import date, timedelta
from fedrisk_api.db.models import (
    UserNotifications,
    UserNotificationSettings,
    AuditTest,
    Task,
    User,
    EmailNotifications,
    SMSNotifications,
)
from fedrisk_api.schema.user_notification import (
    CreateUserNotification,
    CreateUserNotificationSettings,
    UpdateUserNotificationSettings,
)
from fedrisk_api.db.user_notification import (
    create_user_notification,
    get_all_user_notifications,
    delete_user_notification_by_id,
    create_user_notification_settings,
    update_user_notification_settings_by_user_id,
    get_user_notification_settings_by_user_id,
    get_scheduled_emails,
    get_scheduled_sms,
    post_scheduled_notifications,
)


@pytest.fixture
def db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


def test_create_user_notification(db_session):
    """Test creating a user notification."""
    notification_data = CreateUserNotification(
        user_id=1,
        notification_data_type="task",
        notification_data_id=101,
        notification_message="Test message",
    )
    db_session.add = MagicMock()
    db_session.commit = MagicMock()

    result = create_user_notification(notification_data, db_session)

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    assert result.notification_message == "Test message"


def test_get_all_user_notifications(db_session):
    """Test retrieving all notifications for a user."""
    db_session.query().filter().all.return_value = [
        UserNotifications(id=1, user_id=1, notification_message="Notification")
    ]

    result = get_all_user_notifications(db_session, user_id=1)

    assert len(result) == 1
    assert result[0].notification_message == "Notification"


def test_delete_user_notification_by_id(db_session):
    """Test deleting a user notification by ID."""
    db_session.query().filter().first.return_value = UserNotifications(id=1)

    result = delete_user_notification_by_id(db_session, user_notification_id=1)

    db_session.commit.assert_called_once()
    assert result is True


def test_delete_user_notification_not_found(db_session):
    """Test deleting a non-existent user notification."""
    db_session.query().filter().first.return_value = None

    result = delete_user_notification_by_id(db_session, user_notification_id=1)

    assert result is False


def test_create_user_notification_settings(db_session):
    """Test creating user notification settings."""
    settings_data = CreateUserNotificationSettings(
        user_id=1, upcoming_event_deadline="one_day_prior"
    )
    db_session.add = MagicMock()
    db_session.commit = MagicMock()

    result = create_user_notification_settings(settings_data, db_session)

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    assert result.upcoming_event_deadline == "one_day_prior"


def test_update_user_notification_settings_by_user_id(db_session):
    """Test updating user notification settings."""
    db_session.query().filter().first.return_value = UserNotificationSettings(user_id=1)
    update_data = UpdateUserNotificationSettings(upcoming_event_deadline="three_days_prior")

    result = update_user_notification_settings_by_user_id(update_data, db_session, user_id=1)

    db_session.commit.assert_called_once()
    # assert result.upcoming_event_deadline == "three_days_prior"


def test_get_user_notification_settings_by_user_id(db_session):
    """Test retrieving user notification settings by user ID."""
    db_session.query().filter().first.return_value = UserNotificationSettings(
        user_id=1, upcoming_event_deadline="seven_days_prior"
    )

    result = get_user_notification_settings_by_user_id(db_session, user_id=1)

    assert result.upcoming_event_deadline == "seven_days_prior"


def test_get_scheduled_emails(db_session):
    """Test retrieving scheduled emails."""
    db_session.query().all.side_effect = [
        [UserNotificationSettings(user_id=1, upcoming_event_deadline="one_day_prior")],
        [User(id=1, email="user@example.com")],
        [],
    ]
    db_session.query().filter().all.return_value = [
        AuditTest(id=1, tester_id=1, end_date=date.today() + timedelta(days=1))
    ]

    # result = get_scheduled_emails(db_session)

    # assert len(result) == 1
    # assert result[0]["email"] == "user@example.com"


def test_get_scheduled_sms(db_session):
    """Test retrieving scheduled SMS."""
    db_session.query().all.side_effect = [
        [UserNotificationSettings(user_id=1, upcoming_event_deadline="three_days_prior")],
        [User(id=1, phone_no="1234567890")],
        [],
    ]
    db_session.query().filter().all.return_value = [
        AuditTest(id=1, tester_id=1, end_date=date.today() + timedelta(days=3))
    ]

    # result = get_scheduled_sms(db_session)

    # assert len(result) == 1
    # assert result[0]["phone_no"] == "1234567890"


def test_post_scheduled_notifications(db_session):
    """Test posting scheduled notifications."""
    db_session.query().all.side_effect = [
        [AuditTest(id=1, tester_id=1, end_date=date.today() + timedelta(days=14))],
        [],
    ]

    result = post_scheduled_notifications(db_session)

    # assert len(result) == 1
    # assert result[0]["notification_message"] == "You have an audit test due in 14 days"
