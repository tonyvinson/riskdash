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

from fedrisk_api.db import import_task as db_import_task
from fedrisk_api.db.database import get_db

# from fedrisk_api.db.util.import_task_utils import (
#     remove_data_from_dataframe as remove_data_from_dataframe_util,
# )
from fedrisk_api.s3 import S3Service
from fedrisk_api.schema.import_task import CreateImportTask, DisplayImportTask
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_task_permission,
    delete_task_permission,
    view_task_permission,
)

from fedrisk_api.db.models import Tenant

# AWS_S3_BUCKET = "fedriskapi-tasks-bucket"

router = APIRouter(prefix="/s3", tags=["upload_tasks"])

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/import_tasks", tags=["import_tasks"])

# Create import task
@router.put(
    "/{wbs_id}",
    response_model=DisplayImportTask,
    dependencies=[Depends(create_task_permission)],
)
async def create_import_task(
    fileobject: UploadFile = File(...),
    wbs_id=int,
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
        importtask = CreateImportTask(name=new_filename, wbs_id=wbs_id)

        new_importtask = db_import_task.create_import_task(
            db, importtask, file_content_type, user["tenant_id"]
        )

        if not new_importtask:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"tenant id {user['tenant_id']} does not have...",
            )

        my_file_key = f"tasks/{new_importtask.id}-{new_importtask.name}"
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
            # user_details = db_import_task.get_user_task_import(
            #     db=db, user_id=user["user_id"]
            # )
            # LOGGER.info(f"{user_details}")
            # # import file data using util
            # my_data_frame = pd.read_excel(data)
            # task_control_num = load_data_from_dataframe_util(
            #     my_data_frame, user["tenant_id"], user_details.is_superuser
            # )
            # LOGGER.info(f"Successfully loaded {task_control_num[0]} tasks.")
            # LOGGER.info(f"Successfully loaded {task_control_num[1]} controls.")
            # LOGGER.info(f"Successfully loaded {task_control_num[2]} task_versions.")
            return new_importtask  # response added
        else:
            raise HTTPException(status_code=400, detail="Failed to upload in S3")
    except Exception as e:
        LOGGER.exception("S3 Upload Document  Error - Invalid Request")
        raise HTTPException(
            status_code=400, detail="Unable to Import Framework Due to connection error"
        )


# Read all import tasks
@router.put(
    "/all/{wbs_id}/{project_id}",
    response_model=List[DisplayImportTask],
    dependencies=[Depends(view_task_permission)],
)
async def get_all_import_tasks(
    wbs_id: int, project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    response = await db_import_task.get_all_import_tasks_by_wbs(
        db, user["tenant_id"], wbs_id, user["user_id"], project_id
    )
    return response


# Read one import task
@router.get(
    "/{id}",
    response_model=DisplayImportTask,
    dependencies=[Depends(view_task_permission)],
)
def get_import_task_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    importtask = db_import_task.get_import_task(db=db, id=id, tenant_id=user["tenant_id"])
    if not importtask:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import task with id {id} does not exist",
        )

    return importtask


# # Delete import task
# @router.delete("/{id}", dependencies=[Depends(delete_task_permission)])
# def delete_import_task_by_id(
#     id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
# ):
#     s3_service = S3Service()
#     importtask = db_import_task.get_import_task(
#         db=db, id=id, tenant_id=user["tenant_id"]
#     )
#     if not importtask:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Import task with id {id} does not exist",
#         )
#     my_file_key = f"tasks/{importtask.id}-{importtask.name}"
#     # get s3 file object to delete
#     try:
#         # get s3 bucket for tenant
#         tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()

#         async def read_s3_file_obj():

#             obj = await s3_service.get_file_object(tenant.s3_bucket, my_file_key)
#             dataframe = pd.read_excel(io.BytesIO(obj["Body"].read()))
#             task_control_num = remove_data_from_dataframe_util(dataframe)
#             LOGGER.info(f"Successfully removed {task_control_num[0]} tasks.")
#             LOGGER.info(f"Successfully removed {task_control_num[1]} controls.")

#         asyncio.run(read_s3_file_obj())

#         s3_service.delete_fileobj(tenant.s3_bucket, my_file_key)
#     except Exception as e:
#         LOGGER.exception("Delete import task Error - Invalid Request")
#         raise HTTPException(status_code=400, detail="Failed to delete import task")
#     db_status = db_import_task.delete_import_task(
#         db=db, id=id, tenant_id=user["tenant_id"]
#     )
#     if not db_status:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Document with id {id} does not exist",
#         )
#     return {"detail": "Successfully deleted import task."}


@router.get("/download/{id}", dependencies=[Depends(view_task_permission)])
async def download_import_task_file(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    s3_service = S3Service()
    LOGGER.info(f"Download File - about to get document: {id} from database . . .")
    importtask = db_import_task.get_import_task(db=db, id=id, tenant_id=user["tenant_id"])
    if not importtask:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import task with id {id} does not exist",
        )

    my_file_key = f"tasks/{id}-{importtask.name}"
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
        media_type=importtask.file_content_type,
        headers={"Content-Disposition": f"attachment;filename={importtask.name}"},
    )
