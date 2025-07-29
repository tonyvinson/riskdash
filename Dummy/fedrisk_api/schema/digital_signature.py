from pydantic import BaseModel, root_validator
from datetime import datetime

from fedrisk_api.schema.user import DisplayUser

from fedrisk_api.s3 import S3Service

import logging

LOGGER = logging.getLogger(__name__)


# Digital Signature Model


class CreateApprovalDigitalSignature(BaseModel):
    approval_id: int = None
    digital_signature_id: int = None


class CreateDigitalSignature(BaseModel):
    filename: str = None
    user_id: int = None
    checksum: str = None


class DisplayDigitalSignature(BaseModel):
    id: int
    filename: str = None
    user_id: int = None
    created_date: datetime = None
    image_url: str = None
    user: DisplayUser = None
    checksum: str = None

    class Config:
        orm_mode = True

    @root_validator(pre=False)
    def set_image_url(cls, values):
        expire_time = 86400
        s3_service = S3Service()

        sig_pic = values.get("filename")
        user = values.get("user")

        if not user or not sig_pic:
            LOGGER.warning("Missing user or filename in DisplayDigitalSignature validator")
            values["image_url"] = ""
            return values

        user_folder = getattr(user, "s3_bucket", None)
        tenant = getattr(user, "tenant", None)
        if not user_folder or not tenant:
            LOGGER.warning(f"Missing user_folder or tenant: folder={user_folder}, tenant={tenant}")
            values["image_url"] = ""
            return values

        try:
            file_key = f"{user_folder}{sig_pic}"
            url = s3_service.get_digital_signature_image_url(expire_time, tenant, file_key)
            LOGGER.info(f"Generated presigned URL: {url}")
            values["image_url"] = url
        except Exception as e:
            LOGGER.error(f"Error generating presigned URL: {e}")
            values["image_url"] = ""

        return values
