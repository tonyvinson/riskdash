import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import user_notification as db_user_notification
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.user_notification import (
    CreateUserNotification,
    DisplayUserNotification,
    CreateUserNotificationSettings,
    UpdateUserNotificationSettings,
    # DisplayUserNotificationSettings,
)
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.utils import PaginateResponse, pagination

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/user_notifications", tags=["user_notifications"])

# User Notifications
@router.post(
    "/",
    # response_model=DisplayUserNotification,
)
def create_user_notification(
    request: CreateUserNotification, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    user_notification = db_user_notification.create_user_notification(
        user_notification=request, db=db
    )
    return user_notification


@router.get(
    "/",
    response_model=List[DisplayUserNotification],
)
def get_all_user_notifications(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_user_notification.get_all_user_notifications(
        db=db,
        user_id=user["user_id"],
    )
    return queryset


@router.delete("/{id}")
def delete_user_notification_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_user_notification.delete_user_notification_by_id(db=db, user_notification_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User Notification with specified id does not exists",
        )
    return {"detail": "Successfully deleted user Notification."}


# User Notification Settings


@router.post(
    "/settings/",
    # response_model=DisplayUserNotificationSettings,
)
def create_user_notification_settings(
    request: CreateUserNotificationSettings,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    user_notif_settings = db_user_notification.create_user_notification_settings(
        user_notification_settings=request, db=db
    )
    return user_notif_settings


@router.get(
    "/settings/{user_id}",
    # response_model=DisplayUserNotificationSettings,
)
def get_user_notification_settings_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_user_notification.get_user_notification_settings_by_user_id(
        db=db,
        user_id=user_id,
    )
    return queryset


@router.put("/settings/update/{user_id}")
def update_user_notification_settings_by_user_id(
    request: UpdateUserNotificationSettings,
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_user_notification.update_user_notification_settings_by_user_id(
        user_notification_settings=request, db=db, user_id=user_id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User with specified id does not exists",
        )
    return queryset


# Returns all scheduled emails that should be send out
@router.get("/scheduled-emails")
def get_scheduled_emails(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_user_notification.get_scheduled_emails(db=db)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No emails scheduled",
        )
    return queryset


# Returns all scheduled sms that should be send out
@router.get("/scheduled-sms")
def get_scheduled_sms(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_user_notification.get_scheduled_sms(db=db)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No sms scheduled",
        )
    return queryset


# Posts all scheduled notifications
@router.post("/scheduled-notifications")
def post_scheduled_notifications(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_user_notification.post_scheduled_notifications(db=db)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No notifications scheduled",
        )
    return queryset
