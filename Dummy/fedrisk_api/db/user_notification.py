import logging

from sqlalchemy.orm import Session

from fedrisk_api.db.models import (
    Approval,
    ApprovalStakeholder,
    ApprovalWorkflow,
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

from datetime import date, timedelta

# from fedrisk_api.utils.utils import filter_by_tenant

LOGGER = logging.getLogger(__name__)

# User Notifications
def create_user_notification(user_notification: CreateUserNotification, db: Session):
    notification = UserNotifications(**user_notification.dict())
    db.add(notification)
    db.commit()
    return notification


def get_all_user_notifications(db: Session, user_id: int):
    queryset = db.query(UserNotifications).filter(UserNotifications.user_id == user_id).all()
    return queryset


def delete_user_notification_by_id(db: Session, user_notification_id: int):
    user_notification = (
        db.query(UserNotifications).filter(UserNotifications.id == user_notification_id).first()
    )

    if not user_notification:
        return False

    db.delete(user_notification)
    db.commit()
    return True


# User Notifications Settings
def create_user_notification_settings(
    user_notification_settings: CreateUserNotificationSettings, db: Session
):
    notification_settings = UserNotificationSettings(**user_notification_settings.dict())
    db.add(notification_settings)
    db.commit()
    return notification_settings


def update_user_notification_settings_by_user_id(
    user_notification_settings: UpdateUserNotificationSettings, db: Session, user_id: int
):
    queryset = db.query(UserNotificationSettings).filter(
        UserNotificationSettings.user_id == user_id
    )

    if not queryset.first():
        return False

    queryset.update(user_notification_settings.dict(exclude_unset=True))
    db.commit()
    return queryset.first()


def get_user_notification_settings_by_user_id(db: Session, user_id: int):
    queryset = (
        db.query(UserNotificationSettings)
        .filter(UserNotificationSettings.user_id == user_id)
        .first()
    )
    return queryset


# Returns all scheduled emails
def get_scheduled_emails(db: Session):
    today = date.today()
    emails = []
    users = db.query(UserNotificationSettings).all()
    for user in users:
        days_prior = 0
        if user.upcoming_event_deadline == "one_day_prior":
            days_prior = 1
        if user.upcoming_event_deadline == "three_days_prior":
            days_prior = 3
        if user.upcoming_event_deadline == "seven_days_prior":
            days_prior = 7
        if user.upcoming_event_deadline == "fifteen_days_prior":
            days_prior = 15
        if user.upcoming_event_deadline == "thirty_days_prior":
            days_prior = 30
        if user.upcoming_event_deadline == "sixty_days_prior":
            days_prior = 60
        if user.upcoming_event_deadline == "ninety_days_prior":
            days_prior = 90
        audit_tests = db.query(AuditTest).filter(AuditTest.tester_id == user.user_id).all()
        for audit in audit_tests:
            if audit.end_date - timedelta(days=days_prior) == today:
                user_email = db.query(User).filter(User.id == user.user_id).first()
                message = (
                    f"An audit test {audit.name} you are assigned to is due in {days_prior} days"
                )
                # check if email has already been sent
                email_sent = (
                    db.query(EmailNotifications)
                    .filter(EmailNotifications.user_id == user.user_id)
                    .filter(EmailNotifications.message == message)
                )
                if not email_sent.first():
                    # add an email
                    email = {
                        "email": user_email.email,
                        "message": message,
                    }
                    emails.append(email)
                    email_notification = {
                        "user_id": user.user_id,
                        "email": user_email.email,
                        "message": message,
                    }
                    new_notification = EmailNotifications(**email_notification)
                    db.add(new_notification)
                    db.commit()
        tasks = db.query(Task).filter(Task.assigned_to == user.user_id).all()
        for task in tasks:
            if task.due_date - timedelta(days=days_prior) == today:
                user_email = db.query(User).filter(User.id == user.user_id).first()
                message = f"A task {task.name} you are assigned to is due in {days_prior} days"
                # check if email has already been sent
                email_sent = (
                    db.query(EmailNotifications)
                    .filter(EmailNotifications.user_id == user.user_id)
                    .filter(EmailNotifications.message == message)
                )
                if not email_sent.first():
                    # add an email
                    email = {
                        "email": user_email.email,
                        "message": message,
                    }
                    emails.append(email)
                    email_notification = {
                        "user_id": user.user_id,
                        "email": user_email.email,
                        "message": message,
                    }
                    new_notification = EmailNotifications(**email_notification)
                    db.add(new_notification)
                    db.commit()
                tasks = db.query(Task).filter(Task.assigned_to == user.user_id).all()
        approval_workflows = (
            db.query(ApprovalWorkflow).filter(ApprovalWorkflow.owner_id == user.user_id).all()
        )
        for apwf in approval_workflows:
            if apwf.due_date - timedelta(days=days_prior) == today:
                user_email = db.query(User).filter(User.id == user.user_id).first()
                message = f"An approval workflow {apwf.name} you own is due in {days_prior} days"
                # check if email has already been sent
                email_sent = (
                    db.query(EmailNotifications)
                    .filter(EmailNotifications.user_id == user.user_id)
                    .filter(EmailNotifications.message == message)
                )
                if not email_sent.first():
                    # add an email
                    email = {
                        "email": user_email.email,
                        "message": message,
                    }
                    emails.append(email)
                    email_notification = {
                        "user_id": user.user_id,
                        "email": user_email.email,
                        "message": message,
                    }
                    new_notification = EmailNotifications(**email_notification)
                    db.add(new_notification)
                    db.commit()
        approvals = (
            db.query(ApprovalWorkflow)
            .join(Approval, Approval.approval_workflow_id == ApprovalWorkflow.id)
            .filter(Approval.user_id == user.user_id)
            .all()
        )
        for ap in approvals:
            if ap.due_date - timedelta(days=days_prior) == today:
                user_email = db.query(User).filter(User.id == user.user_id).first()
                message = f"An approval workflow {ap.name} you own is due in {days_prior} days"
                # check if email has already been sent
                email_sent = (
                    db.query(EmailNotifications)
                    .filter(EmailNotifications.user_id == user.user_id)
                    .filter(EmailNotifications.message == message)
                )
                if not email_sent.first():
                    # add an email
                    email = {
                        "email": user_email.email,
                        "message": message,
                    }
                    emails.append(email)
                    email_notification = {
                        "user_id": user.user_id,
                        "email": user_email.email,
                        "message": message,
                    }
                    new_notification = EmailNotifications(**email_notification)
                    db.add(new_notification)
                    db.commit()
        stakeholders = (
            db.query(ApprovalWorkflow)
            .join(
                ApprovalStakeholder, ApprovalStakeholder.approval_workflow_id == ApprovalWorkflow.id
            )
            .filter(ApprovalStakeholder.user_id == user.user_id)
            .all()
        )
        for apst in stakeholders:
            if apst.due_date - timedelta(days=days_prior) == today:
                user_email = db.query(User).filter(User.id == user.user_id).first()
                message = f"An approval workflow {apst.name} you own is due in {days_prior} days"
                # check if email has already been sent
                email_sent = (
                    db.query(EmailNotifications)
                    .filter(EmailNotifications.user_id == user.user_id)
                    .filter(EmailNotifications.message == message)
                )
                if not email_sent.first():
                    # add an email
                    email = {
                        "email": user_email.email,
                        "message": message,
                    }
                    emails.append(email)
                    email_notification = {
                        "user_id": user.user_id,
                        "email": user_email.email,
                        "message": message,
                    }
                    new_notification = EmailNotifications(**email_notification)
                    db.add(new_notification)
                    db.commit()
    return emails


# Returns all scheduled sms
def get_scheduled_sms(db: Session):
    today = date.today()
    sms = []
    users = db.query(UserNotificationSettings).all()
    for user in users:
        days_prior = 0
        if user.upcoming_event_deadline == "one_day_prior":
            days_prior = 1
        if user.upcoming_event_deadline == "three_days_prior":
            days_prior = 3
        if user.upcoming_event_deadline == "seven_days_prior":
            days_prior = 7
        if user.upcoming_event_deadline == "fifteen_days_prior":
            days_prior = 15
        if user.upcoming_event_deadline == "thirty_days_prior":
            days_prior = 30
        if user.upcoming_event_deadline == "sixty_days_prior":
            days_prior = 60
        if user.upcoming_event_deadline == "ninety_days_prior":
            days_prior = 90
        audit_tests = db.query(AuditTest).filter(AuditTest.tester_id == user.user_id).all()
        for audit in audit_tests:
            LOGGER.info(f"days prior = {days_prior}")
            if audit.end_date - timedelta(days=days_prior) == today:
                LOGGER.info(
                    f"An audit test {audit.name} you are assigned to is due in {days_prior} days"
                )
                user_phone = db.query(User).filter(User.id == user.user_id).first()
                message = (
                    f"An audit test {audit.name} you are assigned to is due in {days_prior} days"
                )
                # check if email has already been sent
                sms_sent = (
                    db.query(SMSNotifications)
                    .filter(SMSNotifications.user_id == user.user_id)
                    .filter(SMSNotifications.message == message)
                )
                if not sms_sent.first():
                    # add an email
                    sms_msg = {
                        "phone_no": user_phone.phone_no,
                        "message": message,
                    }
                    sms.append(sms_msg)
                    sms_notification = {
                        "user_id": user.user_id,
                        "phone_no": user_phone.phone_no,
                        "message": message,
                    }
                    new_notification = SMSNotifications(**sms_notification)
                    db.add(new_notification)
                    db.commit()
        tasks = db.query(Task).filter(Task.assigned_to == user.user_id).all()
        for task in tasks:
            if task.due_date - timedelta(days=days_prior) == today:
                LOGGER.info(f"A task {task.name} you are assigned to is due in {days_prior} days")
                user_phone = db.query(User).filter(User.id == user.user_id).first()
                message = f"A task {task.name} you are assigned to is due in {days_prior} days"
                # check if email has already been sent
                sms_sent = (
                    db.query(SMSNotifications)
                    .filter(SMSNotifications.user_id == user.user_id)
                    .filter(SMSNotifications.message == message)
                )
                if not sms_sent.first():
                    # add an email
                    sms_msg = {
                        "phone_no": user_phone.phone_no,
                        "message": message,
                    }
                    sms.append(sms_msg)
                    sms_notification = {
                        "user_id": user.user_id,
                        "phone_no": user_phone.phone_no,
                        "message": message,
                    }
                    new_notification = SMSNotifications(**sms_notification)
                    db.add(new_notification)
                    db.commit()
        apwfs = db.query(ApprovalWorkflow).filter(ApprovalWorkflow.owner_id == user.user_id).all()
        for apwf in apwfs:
            if apwf.due_date - timedelta(days=days_prior) == today:
                LOGGER.info(f"An approval workflow {apwf.name} you own is due in {days_prior} days")
                user_phone = db.query(User).filter(User.id == user.user_id).first()
                message = f"An approval workflow {apwf.name} you own is due in {days_prior} days"
                # check if email has already been sent
                sms_sent = (
                    db.query(SMSNotifications)
                    .filter(SMSNotifications.user_id == user.user_id)
                    .filter(SMSNotifications.message == message)
                )
                if not sms_sent.first():
                    # add an email
                    sms_msg = {
                        "phone_no": user_phone.phone_no,
                        "message": message,
                    }
                    sms.append(sms_msg)
                    sms_notification = {
                        "user_id": user.user_id,
                        "phone_no": user_phone.phone_no,
                        "message": message,
                    }
                    new_notification = SMSNotifications(**sms_notification)
                    db.add(new_notification)
                    db.commit()
        approvals = (
            db.query(ApprovalWorkflow)
            .join(Approval, ApprovalWorkflow.id == Approval.approval_workflow_id)
            .filter(Approval.user_id == user.user_id)
            .all()
        )
        for ap in approvals:
            if ap.due_date - timedelta(days=days_prior) == today:
                LOGGER.info(
                    f"An approval workflow {ap.name} you are an approver on is due in {days_prior} days"
                )
                user_phone = db.query(User).filter(User.id == user.user_id).first()
                message = f"An approval workflow {ap.name} you are an approver on is due in {days_prior} days"
                # check if email has already been sent
                sms_sent = (
                    db.query(SMSNotifications)
                    .filter(SMSNotifications.user_id == user.user_id)
                    .filter(SMSNotifications.message == message)
                )
                if not sms_sent.first():
                    # add an email
                    sms_msg = {
                        "phone_no": user_phone.phone_no,
                        "message": message,
                    }
                    sms.append(sms_msg)
                    sms_notification = {
                        "user_id": user.user_id,
                        "phone_no": user_phone.phone_no,
                        "message": message,
                    }
                    new_notification = SMSNotifications(**sms_notification)
                    db.add(new_notification)
                    db.commit()
        stakeholders = (
            db.query(ApprovalWorkflow)
            .join(
                ApprovalStakeholder, ApprovalWorkflow.id == ApprovalStakeholder.approval_workflow_id
            )
            .filter(ApprovalStakeholder.user_id == user.user_id)
            .all()
        )
        for ap in stakeholders:
            if ap.due_date - timedelta(days=days_prior) == today:
                LOGGER.info(
                    f"An approval workflow {ap.name} you are a stakeholder on is due in {days_prior} days"
                )
                user_phone = db.query(User).filter(User.id == user.user_id).first()
                message = f"An approval workflow {ap.name} you are a stakeholder on is due in {days_prior} days"
                # check if email has already been sent
                sms_sent = (
                    db.query(SMSNotifications)
                    .filter(SMSNotifications.user_id == user.user_id)
                    .filter(SMSNotifications.message == message)
                )
                if not sms_sent.first():
                    # add an email
                    sms_msg = {
                        "phone_no": user_phone.phone_no,
                        "message": message,
                    }
                    sms.append(sms_msg)
                    sms_notification = {
                        "user_id": user.user_id,
                        "phone_no": user_phone.phone_no,
                        "message": message,
                    }
                    new_notification = SMSNotifications(**sms_notification)
                    db.add(new_notification)
                    db.commit()
    return sms


# Posts all scheduled notifications
def post_scheduled_notifications(db: Session):
    today = date.today()
    notifications = []
    # audit tests
    audits = db.query(AuditTest).filter(AuditTest.end_date.isnot(None)).all()
    for audit in audits:
        if audit.end_date - timedelta(days=14) == today:
            message = "You have an audit test due in 14 days"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == audit.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": audit.tester_id,
                    "notification_data_type": "audit_tests",
                    "notification_data_id": audit.id,
                    "notification_data_path": f"/projects/{audit.project_id}/audit_tests/{audit.id}",
                    "notification_message": message,
                    "project_id": audit.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if audit.end_date - timedelta(days=7) == today:
            message = "You have an audit test due in 7 days"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == audit.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": audit.tester_id,
                    "notification_data_type": "audit_tests",
                    "notification_data_id": audit.id,
                    "notification_data_path": f"/projects/{audit.project_id}/audit_tests/{audit.id}",
                    "notification_message": f"You have an audit test due in 7 days",
                    "project_id": audit.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if audit.end_date - timedelta(days=1) == today:
            message = "You have an audit test due in 1 day"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == audit.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": audit.tester_id,
                    "notification_data_type": "audit_tests",
                    "notification_data_id": audit.id,
                    "notification_data_path": f"/projects/{audit.project_id}/audit_tests/{audit.id}",
                    "notification_message": f"You have an audit test due in 1 day",
                    "project_id": audit.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if audit.end_date + timedelta(days=1) == today:
            message = "Your audit test is 1 day overdue"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == audit.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": audit.tester_id,
                    "notification_data_type": "audit_tests",
                    "notification_data_id": audit.id,
                    "notification_data_path": f"/projects/{audit.project_id}/audit_tests/{audit.id}",
                    "notification_message": f"Your audit test is 1 day overdue",
                    "project_id": audit.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if audit.end_date + timedelta(days=7) == today:
            message = "Your audit test is 7 days overdue"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == audit.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": audit.tester_id,
                    "notification_data_type": "audit_tests",
                    "notification_data_id": audit.id,
                    "notification_data_path": f"/projects/{audit.project_id}/audit_tests/{audit.id}",
                    "notification_message": f"Your audit test is 7 days overdue",
                    "project_id": audit.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if audit.end_date + timedelta(days=14) == today:
            message = "Your audit test is 14 days overdue"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == audit.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": audit.tester_id,
                    "notification_data_type": "audit_tests",
                    "notification_data_id": audit.id,
                    "notification_data_path": f"/projects/{audit.project_id}/audit_tests/{audit.id}",
                    "notification_message": f"Your audit test is 14 days overdue",
                    "project_id": audit.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
    # Task notifications
    tasks = db.query(Task).filter(Task.due_date.isnot(None)).all()
    for task in tasks:
        if task.due_date - timedelta(days=14) == today:
            message = "You have a task due in 14 days"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == task.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that task is due in 14 days
                notification = {
                    "user_id": task.assigned_to,
                    "notification_data_type": "tasks",
                    "notification_data_id": task.id,
                    "notification_data_path": f"/projects/{task.project_id}/tasks/{task.id}",
                    "notification_message": message,
                    "project_id": task.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if task.due_date - timedelta(days=7) == today:
            message = "You have a task due in 7 days"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == task.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that task is due in 7 days
                notification = {
                    "user_id": task.assigned_to,
                    "notification_data_type": "tasks",
                    "notification_data_id": task.id,
                    "notification_data_path": f"/projects/{task.project_id}/tasks/{task.id}",
                    "notification_message": message,
                    "project_id": task.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if task.due_date - timedelta(days=1) == today:
            message = "You have a task due in 1 day"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == task.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 1 day
                notification = {
                    "user_id": task.assigned_to,
                    "notification_data_type": "tasks",
                    "notification_data_id": task.id,
                    "notification_data_path": f"/projects/{task.project_id}/tasks/{task.id}",
                    "notification_message": "You have a task due in 1 day",
                    "project_id": task.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if task.due_date + timedelta(days=1) == today:
            # post notification that task is overdue by 1 day
            message = "Your task is 1 day overdue"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == task.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": task.assigned_to,
                    "notification_data_type": "tasks",
                    "notification_data_id": task.id,
                    "notification_data_path": f"/projects/{task.project_id}/tasks/{task.id}",
                    "notification_message": message,
                    "project_id": task.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if task.due_date + timedelta(days=7) == today:
            message = "Your task is 7 days overdue"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == task.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": task.assigned_to,
                    "notification_data_type": "tasks",
                    "notification_data_id": task.id,
                    "notification_data_path": f"/projects/{task.project_id}/tasks/{task.id}",
                    "notification_message": message,
                    "project_id": task.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if task.due_date + timedelta(days=14) == today:
            message = "Your task is 14 days overdue"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == task.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": task.assigned_to,
                    "notification_data_type": "tasks",
                    "notification_data_id": task.id,
                    "notification_data_path": f"/projects/{task.project_id}/tasks/{task.id}",
                    "notification_message": message,
                    "project_id": task.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)

    # approval workflows
    approval_workflows = (
        db.query(ApprovalWorkflow).filter(ApprovalWorkflow.due_date.isnot(None)).all()
    )
    for app_wf in approval_workflows:
        if app_wf.due_date - timedelta(days=14) == today:
            message = "You have an approval workflow due in 14 days"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == app_wf.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": app_wf.owner_id,
                    "notification_data_type": "approval_workflows",
                    "notification_data_id": app_wf.id,
                    "notification_data_path": f"/approval_workflows/{app_wf.id}",
                    "notification_message": message,
                    "project_id": None,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if app_wf.due_date - timedelta(days=7) == today:
            message = "You have an approval workflow due in 7 days"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == app_wf.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": app_wf.owner_id,
                    "notification_data_type": "approval_workflows",
                    "notification_data_id": app_wf.id,
                    "notification_data_path": f"/approval_workflows/{app_wf.id}",
                    "notification_message": message,
                    "project_id": None,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)
        if app_wf.due_date - timedelta(days=1) == today:
            message = "You have an approval workflow due in 1 day"
            # see if notification already exists
            exists = (
                db.query(UserNotifications)
                .filter(UserNotifications.notification_data_id == app_wf.id)
                .filter(UserNotifications.notification_message == message)
            )
            if not exists.first():
                # post notification that audit test is due in 14 days
                notification = {
                    "user_id": app_wf.owner_id,
                    "notification_data_type": "approval_workflows",
                    "notification_data_id": app_wf.id,
                    "notification_data_path": f"/approval_workflows/{app_wf.id}",
                    "notification_message": message,
                    "project_id": None,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
                notifications.append(notification)

    return notifications
