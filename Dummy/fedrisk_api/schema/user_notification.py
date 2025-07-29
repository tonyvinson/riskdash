from datetime import datetime

from pydantic import BaseModel

from typing import Optional

from fedrisk_api.db.enums import UpcomingEventDeadline


class DisplayObj(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class CreateUserNotification(BaseModel):
    user_id: int = None
    notification_data_type: str = None
    notification_data_id: str = None
    notification_data_path: str = None
    notification_message: str = None
    project_id: int = None

    class Config:
        orm_mode = True


class DisplayUserNotification(BaseModel):
    id: int = None
    user_id: int = None
    notification_data_type: str = None
    notification_data_id: str = None
    notification_data_path: str = None
    notification_message: str = None
    created: datetime = None
    project_id: int = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class CreateUserNotificationSettings(BaseModel):
    user_id: str = None
    watch_email: bool = None
    watch_sms: bool = None
    assigned_email: bool = None
    assigned_sms: bool = None
    scheduled_email: bool = None
    scheduled_sms: bool = None
    upcoming_event_deadline: Optional[UpcomingEventDeadline]

    class Config:
        orm_mode = True


class DisplayUserNotificationSettings(BaseModel):
    user_id: str = None
    watch_email: bool = None
    watch_sms: bool = None
    assigned_email: bool = None
    assigned_sms: bool = None
    scheduled_email: bool = None
    scheduled_sms: bool = None
    upcoming_event_deadline: UpcomingEventDeadline = None

    class Config:
        orm_mode = True


class UpdateUserNotificationSettings(BaseModel):
    watch_email: bool = None
    watch_sms: bool = None
    assigned_email: bool = None
    assigned_sms: bool = None
    scheduled_email: bool = None
    scheduled_sms: bool = None
    upcoming_event_deadline: Optional[UpcomingEventDeadline]

    class Config:
        orm_mode = True
