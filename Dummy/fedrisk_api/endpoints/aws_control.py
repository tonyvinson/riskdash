import logging

from typing import List
from datetime import datetime
import pandas as pd
from io import BytesIO

# import clamd

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File

from fedrisk_api.db import aws_control as db_aws_control
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.aws_control import (
    CreateAWSControl,
    DisplayAWSControl,
    UpdateAWSControl,
    DisplayImportAWSControl,
    CreateImportAWSControl,
)

from fedrisk_api.s3 import S3Service

from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_aws_control_permission,
    delete_aws_control_permission,
    update_aws_control_permission,
    view_aws_control_permission,
)

from fedrisk_api.db.models import Tenant

# from fedrisk_api.db.util.import_aws_controls import (
#     load_aws_control_data_from_dataframe as load_aws_control_data_from_dataframe_util,
# )

AWS_S3_BUCKET = "fedriskapi-aws-controls-bucket"

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/aws_controls", tags=["aws_controls"])


@router.post(
    "/", response_model=DisplayAWSControl, dependencies=[Depends(create_aws_control_permission)]
)
def create_aws_control(
    request: CreateAWSControl, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        aws_control = db_aws_control.create_aws_control(
            aws_control=request, db=db, tenant_id=user["tenant_id"]
        )
    except IntegrityError as ie:
        LOGGER.exception("Create AWS Control Error. Invalid request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"AWS Control with id '{request.aws_id}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)
    return aws_control


@router.get(
    "/",
    response_model=List[DisplayAWSControl],
    dependencies=[Depends(view_aws_control_permission)],
)
def get_all_aws_controls(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_aws_control.get_aws_control(db=db, tenant_id=user["tenant_id"])
    return queryset


@router.get(
    "/{id}",
    response_model=DisplayAWSControl,
    dependencies=[Depends(view_aws_control_permission)],
)
def get_aws_control_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_aws_control.get_aws_control_by_id(db=db, aws_control_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AWS Control with specified id does not exists",
        )
    return queryset


@router.get(
    "/project_control_id/{project_control_id}",
    dependencies=[Depends(view_aws_control_permission)],
)
def get_aws_controls_by_project_control(
    project_control_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_aws_control.get_aws_controls_by_project_control_id(
        db=db, project_control_id=project_control_id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AWS Control with specified project control id does not exist",
        )
    return queryset


@router.get(
    "/project_id/{project_id}",
    dependencies=[Depends(view_aws_control_permission)],
)
def get_aws_controls_by_project(
    project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_aws_control.get_aws_controls_by_project_id(db=db, project_id=project_id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AWS Control with specified project id does not exist",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_aws_control_permission)])
def update_aws_control_by_id(
    request: UpdateAWSControl, id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        queryset = db_aws_control.update_aws_control_by_id(
            aws_control=request, db=db, aws_control_id=id, tenant_id=user["tenant_id"]
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="AWS Control with specified id does not exists",
            )
        return {"detail": "Successfully updated AWS Control."}
    except IntegrityError as ie:
        LOGGER.exception("Get AWS Control Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_aws_control_permission)])
def delete_aws_control_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_aws_control.delete_aws_control_by_id(db=db, aws_control_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AWS Control with sepcified id does not exists",
        )
    return {"detail": "Successfully deleted AWS Control."}


# Create import aws control
@router.put(
    "/import-aws-controls/{project_id}",
    response_model=DisplayImportAWSControl,
    # dependencies=[Depends(create_aws_control)],
)
async def create_import_aws_controls(
    project_id: int,
    fileobject: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    s3_service = S3Service()
    my_file_key = None
    filename = fileobject.filename
    new_filename = (
        filename.split(".")[0].replace(" ", "_")
        + (datetime.utcnow().strftime("_%Y_%m_%d-%I:%M:%S"))
        + "."
        + filename.split(".")[1]
    )
    file_content_type = fileobject.content_type
    data = fileobject.file._file  # Converting tempfile.SpooledTemporaryFile to io.BytesIO
    # contents = fileobject.file.read()
    # datacsv = BytesIO(contents)
    try:
        importawscontrol = CreateImportAWSControl(name=new_filename, project_id=project_id)

        new_importawscontrol = db_aws_control.create_import_aws_control(
            db, importawscontrol, file_content_type, user["tenant_id"]
        )

        if not new_importawscontrol:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"tenant id {user['tenant_id']} does not have...",
            )

        my_file_key = f"awscontrols/{new_importawscontrol.id}-{new_importawscontrol.name}"
    except IntegrityError as ie:
        LOGGER.exception("Import AWS Controls Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message:
            detail_message = f"AWS Control import with name '{new_filename}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)

    try:
        # get s3 bucket for tenant
        tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()
        uploads3 = await s3_service.upload_fileobj(
            bucket=tenant.s3_bucket, key=my_file_key, fileobject=data
        )
        if uploads3:
            # import file data using util
            # my_data_frame = pd.read_csv(datacsv)
            # aws_control_num = load_aws_control_data_from_dataframe_util(my_data_frame, project_id)
            # LOGGER.info(f"Successfully loaded {aws_control_num[0]} aws controls.")
            # LOGGER.info(
            #     f"Successfully loaded {aws_control_num[1]} aws control to project control mappings."
            # )
            return new_importawscontrol  # response added
        else:
            raise HTTPException(status_code=400, detail="Failed to upload in S3")
    except Exception as e:
        LOGGER.exception("S3 Upload Document  Error - Invalid Request")
        raise HTTPException(
            status_code=400, detail="Unable to Import AWS Controls Due to connection error"
        )


@router.put(
    "/aws_control_imports/",
    dependencies=[Depends(view_aws_control_permission)],
)
async def get_aws_controls_imports_by_tenant(
    db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = await db_aws_control.get_aws_controls_import(db=db, tenant_id=user["tenant_id"])
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="AWS Control Imports do not exist",
        )
    return queryset
