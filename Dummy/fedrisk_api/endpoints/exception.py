import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


# from fedrisk_api.db.models import User

from fedrisk_api.db import exception as db_exception
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.exception import (
    CreateException,
    DisplayException,
    UpdateException,
    CreateExceptionReview,
    DisplayExceptionReview,
    UpdateExceptionReview,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_exception_permission,
    delete_exception_permission,
    update_exception_permission,
    view_exception_permission,
)
from fedrisk_api.utils.utils import delete_documents_for_fedrisk_object

router = APIRouter(prefix="/exceptions", tags=["exceptions"])
LOGGER = logging.getLogger(__name__)

# Create exception
@router.post(
    "/", response_model=DisplayException, dependencies=[Depends(create_exception_permission)]
)
async def create_exception(
    request: CreateException,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        db_status_or_object = {}
        db_status_or_object = await db_exception.create_exception(
            db, request, keywords, user["tenant_id"], user["user_id"]
        )
        if db_status_or_object == -1:
            project_control_id = request.project_control_id
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project Control with id '{project_control_id}' does not exist",
            )
        return db_status_or_object

    except IntegrityError as ie:
        LOGGER.exception("Create Exception Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"An Exception already exists for the target Project Control"
        if "foreign key" in detail_message:
            detail_message = f"Owner with Id '{request.owner_id}' does not exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all exceptions
@router.get(
    "/", response_model=List[DisplayException], dependencies=[Depends(view_exception_permission)]
)
def get_all_exceptions(
    project_id: int = None, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    return db_exception.get_all_exceptions(db, user["tenant_id"], project_id, user["user_id"])


# Read one exception
@router.get(
    "/{id}", response_model=DisplayException, dependencies=[Depends(view_exception_permission)]
)
def get_exception_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    exception = db_exception.get_exception(
        db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not exception:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception with id {id} does not exist",
        )

    return exception


# Update exception
@router.put("/{id}", dependencies=[Depends(update_exception_permission)])
async def update_exception_by_id(
    id: int,
    request: UpdateException,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        db_status = await db_exception.update_exception(
            db=db,
            id=id,
            exception=request,
            keywords=keywords,
            tenant_id=user["tenant_id"],
            user_id=user["user_id"],
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exception with id {id} does not exist",
            )

        return db_status
    except IntegrityError as ie:
        LOGGER.exception("Update Exception Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Exception with name '{request.name}' already exists"
        if "foreign key" in detail_message:
            detail_message = f"Owner with Id '{request.owner_id}' does not exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete exception
@router.delete("/{id}", dependencies=[Depends(delete_exception_permission)])
def delete_exception_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):

    try:
        delete_documents_for_fedrisk_object(
            db=db, fedrisk_object_id=id, fedrisk_object_type="exception"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error while deleting associated documents",
        )

    db_status = db_exception.delete_exception(db=db, id=id, tenant_id=user["tenant_id"])
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception with id {id} does not exist",
        )

    return {"detail": "Successfully deleted exception."}


# Create exception_review
@router.post(
    "/exception_review",
    response_model=DisplayExceptionReview,
    dependencies=[Depends(create_exception_permission)],
)
async def create_exception_review(
    request: CreateExceptionReview,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_exception.create_exception_review(db, request)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not create exception_review for exception id {request.exception_id}",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Exception Review Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# Read one exception_review
@router.get("/exception_review/{id}", response_model=DisplayExceptionReview)
def get_exception_review_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    exception_review = db_exception.get_exception_review(
        db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not exception_review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception Review with id {id} does not exist",
        )

    return exception_review


# Get all exception_review with exception id
@router.get("/exception_review/all/{exception_id}", response_model=List[DisplayExceptionReview])
def get_exception_review_by_exception_id(
    exception_id: int,
    # limit: int = 10,
    # offset: int = 0,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    exception_reviews = db_exception.get_exception_review_by_exception_id(
        db=db, exception_id=exception_id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not exception_reviews:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception Reviews with exception id {id} do not exist",
        )
    # return pagination(query=exception_reviews, limit=limit, offset=offset)
    return exception_reviews


# Delete exception_review
@router.delete("/exception_review/{id}", dependencies=[Depends(delete_exception_permission)])
async def delete_exception_review_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_exception.delete_exception_review(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception Review with id {id} does not exist",
        )
    return {"detail": "Successfully deleted exception_review."}


# Create exception_review on schedule
@router.post(
    "/exception_review/automated",
    dependencies=[Depends(create_exception_permission)],
)
async def create_exception_review_automated(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_exception.create_exception_review_reoccurring(db)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not create exception_reviews",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Exception Review Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# Update exception_review
@router.put(
    "/exception_review/{id}",
    dependencies=[Depends(update_exception_permission)],
)
async def update_exception_review_by_id(
    id: int,
    request: UpdateExceptionReview,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        db_status = await db_exception.update_exception_review(
            db=db,
            id=id,
            exception_review=request,
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Exception Review with id {id} does not exist",
            )
        return db_status
    except IntegrityError as ie:
        LOGGER.exception("Update Exception Review Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
