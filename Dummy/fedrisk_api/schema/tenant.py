from typing import List

from pydantic import BaseModel, EmailStr, constr, validator


class Emails(BaseModel):
    emails: List[EmailStr]


class UserInvite(BaseModel):
    email: EmailStr
    system_role: int = None


class UserDetails(BaseModel):
    # token: str
    email: EmailStr
    first_name: str = None
    last_name: str = None
    password: constr(min_length=8)
    confirm_password: constr(min_length=8)
    phone_no: str = None
    # system_role: int = None

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if "password" in values and v != values["password"]:
            raise ValueError("passwords do not match")
        return v


class TenantUserDetails(BaseModel):
    # otp: str
    first_name: str
    last_name: str
    organization: str
    email: EmailStr
    password: constr(min_length=8)
    confirm_password: constr(min_length=8)
    phone_no: str = None

    @validator("confirm_password")
    def passwords_match(cls, v, values, **kwargs):
        if "password" in values and v != values["password"]:
            raise ValueError("passwords do not match")
        return v


class TenantResend(BaseModel):
    client_id: str
    username: str


class TenantConfirm(BaseModel):
    client_id: str
    username: str
    confirmation_code: str


class CaptchaToken(BaseModel):
    token: str
