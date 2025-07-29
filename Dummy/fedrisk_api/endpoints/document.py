import logging

from datetime import datetime
from typing import List
import uuid

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from fastapi.responses import StreamingResponse
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import document as db_document
from fedrisk_api.db.database import get_db
from fedrisk_api.s3 import S3Service
from fedrisk_api.schema.document import CreateDocument, DisplayDocument, UpdateDocument
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    create_document_permission,
    delete_document_permission,
    download_document_permission,
    update_document_permission,
    view_document_permission,
)

from fedrisk_api.db.models import Tenant

router = APIRouter(prefix="/s3", tags=["upload_documents"])

# s3_config = S3Config(AWS_DEFAULT_REGION="us-east-1")

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Object of S3Service Class
s3_service = None
try:
    s3_service = S3Service()
except Exception as e:
    LOGGER.warning("S3 Service Error - %s", e)


# Create document
@router.post("/", dependencies=[Depends(create_document_permission)])
async def create_document(
    fileobject: UploadFile = File(...),
    db: Session = Depends(get_db),
    title: str = None,
    description: str = None,
    fedrisk_object_type: str = None,
    fedrisk_object_id: int = None,
    owner_id: int = None,
    version: str = None,
    user=Depends(custom_auth),
    keywords: str = None,
    project_id: int = None,
):
    my_file_key = None
    filename = fileobject.filename
    new_filename = (
        filename.split(".")[0]
        + (datetime.utcnow().strftime("_%Y_%m_%d-%I:%M:%S"))
        + "."
        + str(uuid.uuid4())
        + "."
        + filename.split(".")[1]
    )
    file_content_type = fileobject.content_type
    data = fileobject.file._file  # Converting tempfile.SpooledTemporaryFile to io.BytesIO
    try:
        document = CreateDocument(
            name=new_filename,
            description=description,
            project_id=project_id,
            title=title,
            fedrisk_object_type=fedrisk_object_type,
            fedrisk_object_id=fedrisk_object_id,
            owner_id=owner_id,
            version=version,
            keywords=keywords,
        )

        new_document = await db_document.create_document(
            db,
            document,
            fedrisk_object_type,
            fedrisk_object_id,
            file_content_type,
            user["tenant_id"],
            keywords,
            user["user_id"],
            project_id,
        )

        if not new_document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"tenant id {user['tenant_id']} cannot create this document",
            )

        my_file_key = f"documents/{new_document.id}-{new_document.name}"
    except IntegrityError as ie:
        LOGGER.exception("Create Document Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message:
            detail_message = f"Document with name '{new_filename}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)

    try:
        # get s3 bucket for tenant
        tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()
        uploaded_file = await s3_service.upload_fileobj(
            bucket=tenant.s3_bucket, key=my_file_key, fileobject=data
        )
        if uploaded_file:
            return new_document  # response added
        else:
            raise HTTPException(status_code=400, detail="Failed to upload in S3")
    except ClientError:
        LOGGER.exception("S3 Upload Document  Error - Invalid Request")
        raise HTTPException(
            status_code=400, detail="Unable to Create Document Due to connection error"
        )


# Read all documents
@router.get(
    "/", response_model=List[DisplayDocument], dependencies=[Depends(view_document_permission)]
)
def get_all_documents(db: Session = Depends(get_db), user=Depends(custom_auth)):
    return db_document.get_all_documents(db, user["tenant_id"], user_id=user["user_id"])


# Read one document
@router.get("/{id}", response_model=DisplayDocument)
def get_document_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    document = db_document.get_document(
        db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {id} does not exist",
        )

    return document


# Update document
@router.put(
    "/{id}", response_model=DisplayDocument, dependencies=[Depends(update_document_permission)]
)
async def update_document_by_id(
    fileobject: UploadFile = File(...),
    db: Session = Depends(get_db),
    project_id: int = None,
    title: str = None,
    description: str = None,
    fedrisk_object_type: str = None,
    fedrisk_object_id: int = None,
    owner_id: int = None,
    version: str = None,
    user=Depends(custom_auth),
    id: int = None,
    keywords: str = None,
):
    my_file_key = None
    filename = fileobject.filename
    new_filename = (
        filename.split(".")[0]
        + (datetime.utcnow().strftime("_%Y_%m_%d-%I:%M:%S"))
        + "."
        + str(uuid.uuid4())
        + "."
        + filename.split(".")[1]
    )
    file_content_type = fileobject.content_type
    data = fileobject.file._file  # Converting tempfile.SpooledTemporaryFile to io.BytesIO
    try:
        document = UpdateDocument(
            # id=id,
            name=new_filename,
            description=description,
            project_id=project_id,
            title=title,
            owner_id=owner_id,
            version=version,
        )

        db_status = await db_document.update_document(
            db=db,
            id=id,
            file_content_type=file_content_type,
            document=document,
            tenant_id=user["tenant_id"],
            keywords=keywords,
            fedrisk_object_type=fedrisk_object_type,
            fedrisk_object_id=fedrisk_object_id,
            user_id=user["user_id"],
        )

        LOGGER.info(f"db_status {db_status}")

        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"tenant id {user['tenant_id']} does not have document id {id}",
            )

        my_file_key = f"documents/{id}-{new_filename}"
    except IntegrityError as ie:
        LOGGER.exception("Update Document Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message:
            detail_message = f"Document with name '{new_filename}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)

    try:
        # get s3 bucket for tenant
        tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()
        uploaded_file = await s3_service.upload_fileobj(
            bucket=tenant.s3_bucket, key=my_file_key, fileobject=data
        )
        if uploaded_file:
            return db_status  # response added
        else:
            raise HTTPException(status_code=400, detail="Failed to upload in S3")
    except ClientError:
        LOGGER.exception("S3 Upload Document  Error - Invalid Request")
        raise HTTPException(
            status_code=400, detail="Unable to Create Document Due to connection error"
        )


# Delete document
@router.delete("/{id}", dependencies=[Depends(delete_document_permission)])
async def delete_document_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    document = db_document.get_document(
        db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {id} does not exist",
        )

    my_file_key = f"documents/{document.id}-{document.name}"
    try:
        # get s3 bucket for tenant
        tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()
        await s3_service.delete_fileobj(bucket=tenant.s3_bucket, key=my_file_key)
    except ClientError:
        LOGGER.exception("Delete Document Error - Invalid Request")
        raise HTTPException(status_code=400, detail="Failed to delete document")
    db_status = await db_document.delete_document(db=db, id=id, tenant_id=user["tenant_id"])
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {id} does not exist",
        )
    return {"detail": "Successfully deleted document."}


@router.get("/download/{id}", dependencies=[Depends(download_document_permission)])
async def download_file(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    LOGGER.info(f"Download File - about to get document: {id} from database . . .")
    document = db_document.get_document(
        db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id {id} does not exist",
        )

    my_file_key = f"documents/{id}-{document.name}"

    async def s3_stream(chunk_size: int = 4096):
        try:
            # get s3 bucket for tenant
            tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()
            # s3_obj = boto3_s3_client.get_object(Bucket=BUCKET_NAME, Key=my_file_key)
            s3_obj = await s3_service.get_file_object(bucket=tenant.s3_bucket, key=my_file_key)

            stream = s3_obj["Body"]
            chunk = stream.read(chunk_size)
            while chunk:
                yield chunk
                chunk = stream.read(chunk_size)
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise HTTPException(status_code=404, detail="Item not found")
            else:
                raise e

    return StreamingResponse(
        s3_stream(),
        media_type=document.file_content_type,
        headers={"Content-Disposition": f"attachment;filename={document.name}"},
    )
