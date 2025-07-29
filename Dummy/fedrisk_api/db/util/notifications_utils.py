import logging
import os

from fedrisk_api.db.models import (
    User,
    UserNotifications,
    UserNotificationSettings,
)

from fedrisk_api.utils.email_util import send_watch_email
from fedrisk_api.utils.email_util import send_assigned_to_email
from fedrisk_api.utils.sms_util import publish_notification

LOGGER = logging.getLogger(__name__)

frontend_server_url = os.getenv("FRONTEND_SERVER_URL", "")

# Notification Functions
async def notify_user(user, message, link, settings):
    """Send notification emails and/or SMS to user if enabled in settings."""
    full_link = frontend_server_url + link
    LOGGER.info(f"link {full_link}")
    if settings is not None:
        if settings.assigned_email and user.email:
            await send_watch_email(
                {"subject": message, "email": user.email, "message": f"{message} Link: {full_link}"}
            )
        if settings.assigned_sms and user.phone_no:
            await publish_notification(
                {"phone_no": user.phone_no, "message": f"{message} Link: {full_link}"}
            )
    if settings is None:
        await send_watch_email(
            {"subject": message, "email": user.email, "message": f"{message} Link: {full_link}"}
        )


async def add_notification(db, user_id, data_type, data_id, path, message, project_id):
    """Add a notification entry in the database."""
    LOGGER.info("adding a notification")
    notification = UserNotifications(
        user_id=user_id,
        notification_data_type=data_type,
        notification_data_id=data_id,
        notification_data_path=path,
        notification_message=message,
        project_id=project_id,
    )
    db.add(notification)
    db.commit()


async def manage_notifications(db, users_watching, data_type, message, link, project_id, id):
    """Batch notification handler for multiple users."""
    for userwatch in users_watching:
        try:
            # Add a notification for the user
            await add_notification(db, userwatch.user_id, data_type, id, link, message, project_id)

            # Query the user's notification settings and user info in parallel if possible.
            # If your ORM supports asynchronous queries, consider using them.
            user_notification_settings = (
                db.query(UserNotificationSettings).filter_by(user_id=userwatch.user_id).first()
            )
            user = db.query(User).filter_by(id=userwatch.user_id).first()

            # Notify the user based on their settings
            await notify_user(user, message, link, user_notification_settings)
        except Exception as e:
            # Log error for this user and continue with next user
            # Use your logging framework if available
            print(f"Error managing notifications for user {userwatch.user_id}: {e}")


async def send_assigned_email(subject: str, email: str, message: str):
    payload = {
        "subject": subject,
        "email": email,
        "message": message,
    }
    await send_assigned_to_email(payload)


async def send_sms(phone_no: str, message: str):
    payload = {
        "phone_no": phone_no,
        "message": message,
    }
    await publish_notification(payload)
