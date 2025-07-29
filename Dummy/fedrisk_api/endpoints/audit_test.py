import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import audit_test as db_audit_test
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.audit_test import (
    CreateAuditTest,
    DisplayAuditTest,
    UpdateAuditTest,
    CreateAuditTestInstance,
    DisplayAuditTestInstance,
    UpdateAuditTestInstance,
)
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    create_audittest_permission,
    delete_audittest_permission,
    update_audittest_permission,
    view_audittest_permission,
)
from fedrisk_api.utils.utils import (
    PaginateResponse,
    delete_documents_for_fedrisk_object,
    pagination,
)

router = APIRouter(prefix="/audit_tests", tags=["audit_tests"])
LOGGER = logging.getLogger(__name__)

# Create audit_test
@router.post(
    "/", response_model=DisplayAuditTest, dependencies=[Depends(create_audittest_permission)]
)
async def create_audit_test(
    request: CreateAuditTest,
    keywords: str = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_audit_test.create_audit_test(
            db, keywords, request, user["tenant_id"], user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"tenant with specified id does not have project id {request.project_id}",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Test Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"AuditTest with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all audit_tests
@router.get(
    "/",
    response_model=PaginateResponse[DisplayAuditTest],
    dependencies=[Depends(view_audittest_permission)],
)
def get_all_audit_tests(
    project_id: int = None,
    framework_id: int = None,
    q: str = None,
    filter_by: str = None,
    filter_value: str = None,
    sort_by: str = "-created_date",
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_audit_test.get_all_audit_tests(
            db,
            user["tenant_id"],
            user["user_id"],
            project_id,
            framework_id,
            q,
            filter_by,
            filter_value,
            sort_by,
        )
        return pagination(query=queryset, limit=limit, offset=offset)
    except DataError as e:
        LOGGER.exception("Get Audit Test Error - Invalid request")

        if "LIMIT must not be negative" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LIMIT must not be negative",
            )
        elif "OFFSET must not be negative" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OFFSET must not be negative",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Please provide correct filter_value"
            )
    except ProgrammingError:
        LOGGER.exception("Get Audit Test Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct sort_by field value",
        )
    except AttributeError:
        LOGGER.exception("Get Audit Test Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct filter_by field value",
        )


# Read one audit_test
@router.get("/{id}", response_model=DisplayAuditTest)
def get_audit_test_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    audit_test = db_audit_test.get_audit_test(
        db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not audit_test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AuditTest with id {id} does not exist",
        )

    return audit_test


# Update audit_test
@router.put(
    "/{id}", response_model=DisplayAuditTest, dependencies=[Depends(update_audittest_permission)]
)
async def update_audit_test_by_id(
    id: int,
    request: UpdateAuditTest,
    keywords: str = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        db_status = await db_audit_test.update_audit_test(
            db=db,
            id=id,
            keywords=keywords,
            audit_test=request,
            tenant_id=user["tenant_id"],
            user_id=user["user_id"],
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AuditTest with id {id} does not exist",
            )
        return db_status
    except IntegrityError as ie:
        LOGGER.exception("Update Audit Test Error - Invalid Request")
        detail_message = str(ie)
        # if "duplicate" in detail_message or "UNIQUE" in detail_message:
        #     detail_message = f"AuditTest with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete audit_test
@router.delete("/{id}", dependencies=[Depends(delete_audittest_permission)])
async def delete_audit_test_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        delete_documents_for_fedrisk_object(
            db=db, fedrisk_object_id=id, fedrisk_object_type="audit_test"
        )

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while deleting associated documents",
        )
    db_status = await db_audit_test.delete_audit_test(db=db, id=id, tenant_id=user["tenant_id"])
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AuditTest with id {id} does not exist",
        )
    return {"detail": "Successfully deleted audit_test."}


# Create audit_test_instance
@router.post(
    "/instance",
    response_model=DisplayAuditTestInstance,
    dependencies=[Depends(create_audittest_permission)],
)
async def create_audit_test_instance(
    request: CreateAuditTestInstance,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_audit_test.create_audit_test_instance(db, request)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not create audit_test_instance for audit test id {request.audit_test_id}",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Test Instance Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# Read one audit_test_instance
@router.get("/instance/{id}", response_model=DisplayAuditTestInstance)
def get_audit_test_instance_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    audit_test_instance = db_audit_test.get_audit_test_instance(
        db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not audit_test_instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AuditTest Instance with id {id} does not exist",
        )

    return audit_test_instance


# Get all audit_test_instance with audit_test id
@router.get(
    "/instance/all/{audit_test_id}"  # , response_model=PaginateResponse[DisplayAuditTestInstance]
)
def get_audit_test_instance_by_audit_test_id(
    audit_test_id: int,
    # limit: int = 10,
    # offset: int = 0,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    audit_test_instances = db_audit_test.get_audit_test_instance_by_audit_test_id(
        db=db, audit_test_id=audit_test_id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not audit_test_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AuditTest Instances with audit test id {audit_test_id} do not exist",
        )
    # return pagination(query=audit_test_instances, limit=limit, offset=offset)
    return audit_test_instances


# Delete audit_test_instance
@router.delete("/instance/{id}", dependencies=[Depends(delete_audittest_permission)])
async def delete_audit_test_instance_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_audit_test.delete_audit_test_instance(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit Test Instance with id {id} does not exist",
        )
    return {"detail": "Successfully deleted audit_test_instance."}


# Create audit_test_instance on schedule
@router.post(
    "/instance/automated",
    dependencies=[Depends(create_audittest_permission)],
)
async def create_audit_test_instance_automated(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_audit_test.create_audit_test_instance_reoccurring(db)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not create audit_test_instances",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Test Instance Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# Update audit_test_instance
@router.put(
    "/instance/{id}",
    # response_model=DisplayAuditTestInstance,
    dependencies=[Depends(update_audittest_permission)],
)
async def update_audit_test_instance_by_id(
    id: int,
    request: UpdateAuditTestInstance,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        db_status = await db_audit_test.update_audit_test_instance(
            db=db,
            id=id,
            audit_test_instance=request,
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AuditTestInstance with id {id} does not exist",
            )
        return db_status
    except IntegrityError as ie:
        LOGGER.exception("Update Audit Test Instance Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
