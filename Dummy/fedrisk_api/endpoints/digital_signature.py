import logging
from botocore.exceptions import ClientError
from io import BytesIO
import hashlib

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from datetime import datetime

from fastapi.datastructures import UploadFile
from fastapi.param_functions import File

from fedrisk_api.db import digital_signature as db_digital_signature
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.digital_signature import (
    CreateDigitalSignature,
    DisplayDigitalSignature,
    CreateApprovalDigitalSignature,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_digital_signature_permission,
    delete_digital_signature_permission,
    # update_digital_signature_permission,
    view_digital_signature_permission,
)
from fedrisk_api.db.models import User, Tenant, ApprovalDigitalSignature

from fedrisk_api.s3 import S3Service

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/digital_signature", tags=["digital_signature"])

# Object of S3Service Class
s3_service = None
try:
    s3_service = S3Service()
except Exception as e:
    LOGGER.warning("S3 Service Error - %s", e)


@router.post(
    "/",
    response_model=DisplayDigitalSignature,
    dependencies=[Depends(create_digital_signature_permission)],
)
async def create_digital_signature(
    fileobject: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(custom_auth)
):
    new_filename = (
        "dig_sig." + str(user["user_id"]) + "." + (datetime.utcnow().strftime("_%Y_%m_%d-%I:%M:%S"))
    )

    data = fileobject.file._file  # Converting tempfile.SpooledTemporaryFile to io.BytesIO
    # get user s3 folder
    user_s3_folder = db.query(User).filter(User.id == user["user_id"]).first()
    s3_upload_file_key = f"{user_s3_folder.s3_bucket}{new_filename}"
    LOGGER.info(s3_upload_file_key)

    # Read and reset file object for hashing and upload
    file_bytes = await fileobject.read()
    file_hash = hashlib.sha256(file_bytes).hexdigest()

    # Reset stream for upload

    data = BytesIO(file_bytes)

    request = CreateDigitalSignature(
        filename=new_filename, user_id=user["user_id"], checksum=file_hash
    )
    try:
        digital_signature = await db_digital_signature.create_digital_signature(
            digital_signature=request, db=db
        )
        try:
            # get s3 bucket for tenant
            tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()

            uploaded_file = await s3_service.upload_fileobj(
                bucket=tenant.s3_bucket, key=s3_upload_file_key, fileobject=data
            )
            LOGGER.info(uploaded_file)
            if uploaded_file:
                return digital_signature  # response added
            else:
                raise HTTPException(status_code=400, detail="Failed to upload in S3")
        except ClientError:
            LOGGER.exception("S3 Upload Document  Error - Invalid Request")
            raise HTTPException(
                status_code=400, detail="Unable to Create Digital Signature Due to connection error"
            )
    except IntegrityError as ie:
        LOGGER.exception("Create Digital Signature Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.get(
    "/{approval_id}/all",
    response_model=List[DisplayDigitalSignature],
    dependencies=[Depends(view_digital_signature_permission)],
)
def get_all_digital_signatures_for_approval(
    approval_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_digital_signature.get_all_digital_signatures_by_approval_id(
        db=db,
        approval_id=approval_id,
    )
    return queryset


@router.get(
    "/user",
    response_model=List[DisplayDigitalSignature],
    dependencies=[Depends(view_digital_signature_permission)],
)
def get_all_digital_signatures_for_user(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_digital_signature.get_all_digital_signatures_by_user_id(
        db=db,
        user_id=user["user_id"],
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplayDigitalSignature,
    dependencies=[Depends(view_digital_signature_permission)],
)
def get_digital_signature_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_digital_signature.get_digital_signature_by_id(db=db, digital_signature_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Digital Signature with specified id does not exist",
        )
    return queryset


@router.delete(
    "/{id}",
    dependencies=[Depends(delete_digital_signature_permission)],
    status_code=status.HTTP_204_NO_CONTENT,  # 204 is common for successful deletes with no body
)
async def delete_digital_signature_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    # check if digital signature in use
    in_use = db.query(ApprovalDigitalSignature).filter(
        ApprovalDigitalSignature.digital_signature_id == id
    )
    if in_use.first() is not None:
        raise HTTPException(
            status_code=status.HTTP_304_NOT_MODIFIED,
            detail="Digital Signature cannot be deleted as is in use with an approval workflow",
        )
    else:
        success = await db_digital_signature.delete_digital_signature_by_id(
            db=db, digital_signature_id=id
        )
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Digital Signature with specified id does not exist",
            )
        # Return confirmation of deletion
        return {"detail": "Successfully deleted digital signature"}


@router.post(
    "/approval_digital_signature",
    response_model=DisplayDigitalSignature,
    dependencies=[Depends(create_digital_signature_permission)],
)
async def create_approval_digital_signature_assoc(
    request: CreateApprovalDigitalSignature,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        approval_digital_signature = await db_digital_signature.create_approval_digital_signature(
            approval_digital_signature=request,
            db=db,
        )
    except IntegrityError as ie:
        LOGGER.exception("Create Approval Digital Signature Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return approval_digital_signature
