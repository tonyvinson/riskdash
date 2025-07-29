from datetime import datetime
from typing import List

from pydantic import BaseModel, constr, validator

from fedrisk_api.s3 import S3Service

import logging

LOGGER = logging.getLogger(__name__)


class DisplayRole(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplaySubscription(BaseModel):
    frequency: str = None
    start_datetime: datetime
    end_datetime: datetime
    is_active: bool

    class Config:
        orm_mode = True


class DisplayTenant(BaseModel):
    id: int = None
    name: str = None
    s3_bucket: str = None

    class Config:
        orm_mode = True


class DisplayUser(BaseModel):
    id: str
    email: str
    first_name: str = None
    last_name: str = None
    phone_no: str = None
    s3_bucket: str = None
    tenant_id: str = None
    is_superuser: bool
    is_tenant_admin: bool
    is_email_verified: bool = None
    is_active: bool
    status: str = None
    profile_picture: str = None
    profile_picture_url: str = None
    profile_picture_tags: str = None
    system_role: str = None
    system_role_name: str = None
    tenant: DisplayTenant = None
    # project_roles: List[DisplayRole] = None
    system_roles: List[DisplayRole] = None

    class Config:
        orm_mode = True
        extra = "allow"


class DisplayUsers(BaseModel):
    items: List[DisplayUser] = []
    total: int

    class Config:
        orm_mode = True
        extra = "allow"


class CredentialRequestForm(BaseModel):
    email: constr(strip_whitespace=True)
    password: str


class ResendConfirmationCodeRequestForm(BaseModel):
    username: constr(strip_whitespace=True)


class CredentialResponseForm(BaseModel):
    access_token: str
    token_type: str
    user: DisplayUser
    client_id: str = None
    cognito_user: str = None


class CredentialRequestFormCIUser(BaseModel):
    username: constr(strip_whitespace=True)
    password: str


class UpdateUserProfile(BaseModel):
    first_name: str = None
    last_name: str = None
    phone_no: str = None
    system_role: str = None


class UpdateUserPassword(BaseModel):
    current_password: str
    new_password: constr(min_length=8)
    confirm_password: constr(min_length=8)
    access_token: str

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if "new_password" in values and v != values["new_password"]:
            raise ValueError("passwords do not match")
        return v


class EmailTempPassword(BaseModel):
    email: str


class TmpUserPasswordMfa(BaseModel):
    username: str
    session: str
    mfa_code: str
    challenge_name: str
    new_password: constr(min_length=8)


class UpdateUserRole(BaseModel):
    system_role: str = None


class UpdateSystemRole(BaseModel):
    role_id: int
    user_id: int
    enabled: bool


class ForgotPassword(BaseModel):
    email: str


class ConfirmForgotPassword(BaseModel):
    email: str
    confirmation_code: str
    password: str


class UseMFACode(BaseModel):
    username: str
    session_token: str
    mfa_code: str
    # email: str
    # password: str


class VerifyMFACode(BaseModel):
    session_token: str
    mfa_code: str


class GetMFACode(BaseModel):
    session_token: str


class MfaChallengeRequest(BaseModel):
    username: str
    session: str
    mfa_code: str
    email: str
    challenge_type: str  # Either "SOFTWARE_TOKEN_MFA" or "SMS_MFA" or "EMAIL_OTP"
