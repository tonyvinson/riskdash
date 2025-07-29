import asyncio
import io
import logging
from datetime import datetime
from typing import List

# import subprocess

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import import_framework as db_import_framework
from fedrisk_api.db.database import get_db

from fedrisk_api.db.util.import_framework_utils import (
    remove_data_from_dataframe as remove_data_from_dataframe_util,
)
from fedrisk_api.s3 import S3Service
from fedrisk_api.schema.import_framework import CreateImportFramework, DisplayImportFramework
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_import_framework_permission,
    delete_import_framework_permission,
    download_import_framework_permission,
    view_import_framework_permission,
)

from fedrisk_api.db.models import Tenant

# AWS_S3_BUCKET = "fedriskapi-frameworks-bucket"

router = APIRouter(prefix="/s3", tags=["upload_frameworks"])

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/import_frameworks", tags=["import_frameworks"])

# Create import framework
@router.put(
    "/",
    response_model=DisplayImportFramework,
    dependencies=[Depends(create_import_framework_permission)],
)
async def create_import_framework(
    fileobject: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):

    # LOGGER.info(f"File is clean")
    s3_service = S3Service()
    my_file_key = None
    filename = fileobject.filename
    new_filename = (
        filename.split(".")[0]
        + (datetime.utcnow().strftime("_%Y_%m_%d-%I:%M:%S"))
        + "."
        + filename.split(".")[1]
    )
    file_content_type = fileobject.content_type
    data = fileobject.file._file  # Converting tempfile.SpooledTemporaryFile to io.BytesIO
    try:
        importframework = CreateImportFramework(name=new_filename)

        new_importframework = db_import_framework.create_import_framework(
            db, importframework, file_content_type, user["tenant_id"]
        )

        if not new_importframework:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"tenant id {user['tenant_id']} does not have...",
            )

        my_file_key = f"frameworks/{new_importframework.id}-{new_importframework.name}"
    except IntegrityError as ie:
        LOGGER.exception("Import Framework Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message:
            detail_message = f"Framework with name '{new_filename}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)

    try:
        # get s3 bucket for tenant
        tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()
        uploads3 = await s3_service.upload_fileobj(
            bucket=tenant.s3_bucket, key=my_file_key, fileobject=data
        )
        if uploads3:
            # # get user is_superuser
            # user_details = db_import_framework.get_user_framework_import(
            #     db=db, user_id=user["user_id"]
            # )
            # LOGGER.info(f"{user_details}")
            # # import file data using util
            # my_data_frame = pd.read_excel(data)
            # framework_control_num = load_data_from_dataframe_util(
            #     my_data_frame, user["tenant_id"], user_details.is_superuser
            # )
            # LOGGER.info(f"Successfully loaded {framework_control_num[0]} frameworks.")
            # LOGGER.info(f"Successfully loaded {framework_control_num[1]} controls.")
            # LOGGER.info(f"Successfully loaded {framework_control_num[2]} framework_versions.")
            return new_importframework  # response added
        else:
            raise HTTPException(status_code=400, detail="Failed to upload in S3")
    except Exception as e:
        LOGGER.exception("S3 Upload Document  Error - Invalid Request")
        raise HTTPException(
            status_code=400, detail="Unable to Import Framework Due to connection error"
        )


# Read all import frameworks
@router.put(
    "/all",
    response_model=List[DisplayImportFramework],
    dependencies=[Depends(view_import_framework_permission)],
)
async def get_all_import_frameworks(db: Session = Depends(get_db), user=Depends(custom_auth)):
    response = await db_import_framework.get_all_import_frameworks(db, user["tenant_id"])
    return response


# Read one import framework
@router.get(
    "/{id}",
    response_model=DisplayImportFramework,
    dependencies=[Depends(view_import_framework_permission)],
)
def get_import_framework_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    importframework = db_import_framework.get_import_framework(
        db=db, id=id, tenant_id=user["tenant_id"]
    )
    if not importframework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import framework with id {id} does not exist",
        )

    return importframework


# Delete import framework
@router.delete("/{id}", dependencies=[Depends(delete_import_framework_permission)])
def delete_import_framework_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    s3_service = S3Service()
    importframework = db_import_framework.get_import_framework(
        db=db, id=id, tenant_id=user["tenant_id"]
    )
    if not importframework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import framework with id {id} does not exist",
        )
    my_file_key = f"frameworks/{importframework.id}-{importframework.name}"
    # get s3 file object to delete
    try:
        # get s3 bucket for tenant
        tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()

        async def read_s3_file_obj():

            obj = await s3_service.get_file_object(tenant.s3_bucket, my_file_key)
            dataframe = pd.read_excel(io.BytesIO(obj["Body"].read()))
            framework_control_num = remove_data_from_dataframe_util(dataframe)
            LOGGER.info(f"Successfully removed {framework_control_num[0]} frameworks.")
            LOGGER.info(f"Successfully removed {framework_control_num[1]} controls.")

        asyncio.run(read_s3_file_obj())

        s3_service.delete_fileobj(tenant.s3_bucket, my_file_key)
    except Exception as e:
        LOGGER.exception("Delete import framework Error - Invalid Request")
        raise HTTPException(status_code=400, detail="Failed to delete import framework")
    db_status = db_import_framework.delete_import_framework(
        db=db, id=id, tenant_id=user["tenant_id"]
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {id} does not exist",
        )
    return {"detail": "Successfully deleted import framework."}


@router.get("/download/{id}", dependencies=[Depends(download_import_framework_permission)])
async def download_import_framework_file(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    s3_service = S3Service()
    LOGGER.info(f"Download File - about to get document: {id} from database . . .")
    importframework = db_import_framework.get_import_framework(
        db=db, id=id, tenant_id=user["tenant_id"]
    )
    if not importframework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import framework with id {id} does not exist",
        )

    my_file_key = f"frameworks/{id}-{importframework.name}"
    # get s3 bucket for tenant
    tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()

    async def s3_stream(chunk_size: int = 4096):
        try:
            s3_obj = await s3_service.get_file_object(bucket=tenant.s3_bucket, key=my_file_key)

            stream = s3_obj["Body"]
            chunk = stream.read(chunk_size)
            while chunk:
                yield chunk
                chunk = stream.read(chunk_size)
        except Exception as e:
            raise e

    return StreamingResponse(
        s3_stream(),
        media_type=importframework.file_content_type,
        headers={"Content-Disposition": f"attachment;filename={importframework.name}"},
    )
