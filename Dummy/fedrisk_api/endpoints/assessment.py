import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import assessment as db_assessment
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.assessment import (
    DisplayAssessment,
    UpdateAssessment,
    DisplayAssessmentInstance,
    CreateAssessmentInstance,
    UpdateAssessmentInstance,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    update_assessment_permission,
    view_assessment_permission,
    create_assessment_permission,
    delete_assessment_permission,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])
LOGGER = logging.getLogger(__name__)

# Create assessment
# Note: Assessments are not created explicitly . . .
# @router.post("/", response_model=DisplayAssessment)
# def create_assessment(request: CreateAssessment, db: Session = Depends(get_db)):
#     try:
#         return db_assessment.create_assessment(db, request)
#     except IntegrityError as ie:
#         detail_message = str(ie)
#         print(f"\n\nDetail Message: {detail_message} . . .")
#         if "duplicate" in detail_message or "UNIQUE" in detail_message:
#             detail_message = f"Assessment with name '{request.name}' already exists"
#         raise HTTPException(status_code=409, detail=detail_message)


# Read all assessments
@router.get(
    "/",
    response_model=List[DisplayAssessment],  # dependencies=[Depends(view_assessment_permission)]
)
def get_all_assessments(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    project_id: str = None,
):
    return db_assessment.get_all_assessments(db, user["tenant_id"], project_id)


# Read one assessment
@router.get(
    "/{id}",
    response_model=DisplayAssessment,  # dependencies=[Depends(view_assessment_permission)]
)
def get_assessment_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    assessment = db_assessment.get_assessment(db=db, id=id, tenant_id=user["tenant_id"])
    if not assessment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment with id {id} does not exist",
        )

    return assessment


# Update assessment
@router.put("/{id}", dependencies=[Depends(update_assessment_permission)])
async def update_assessment_by_id(
    id: int,
    request: UpdateAssessment,
    keywords: str = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        db_status = await db_assessment.update_assessment(
            db=db,
            id=id,
            keywords=keywords,
            assessment=request,
            tenant_id=user["tenant_id"],
            user_id=user["user_id"],
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment with id {id} does not exist",
            )
        return db_status
    except IntegrityError as ie:
        LOGGER.exception("Update Assessment Error - Invalid request.")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Assessment with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Note: Assessments are tightly coupled to ProjectControls
#       and do not exist without the corresponding project control
#       and vice versa.  It makes no sense to allow explicit delete of
#       an Assessment.
# Delete assessment
# @router.delete("/{id}")
# def delete_assessment_by_id(id: int, db: Session = Depends(get_db)):
#     db_status = db_assessment.delete_assessment(db=db, id=id)
#     if not db_status:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"Assessment with id {id} does not exist",
#         )

#     return {"detail": "Successfully deleted assessment."}

# Create assessment_instance
@router.post(
    "/instance",
    response_model=DisplayAssessmentInstance,
    dependencies=[Depends(create_assessment_permission)],
)
async def create_assessment_instance(
    request: CreateAssessmentInstance,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_assessment.create_assessment_instance(db, request)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not create assessment_instance for assessment id {request.assessment_id}",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Assessment Instance Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# Read one assessment_instance
@router.get(
    "/instance/{id}",
    response_model=DisplayAssessmentInstance,
    dependencies=[Depends(view_assessment_permission)],
)
def get_assessment_instance_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    assessment_instance = db_assessment.get_assessment_instance(
        db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not assessment_instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment Instance with id {id} does not exist",
        )

    return assessment_instance


# Get all assessment_instance with assessment id
@router.get(
    "/instance/all/{assessment_id}",
    dependencies=[
        Depends(view_assessment_permission)
    ],  # , response_model=PaginateResponse[DisplayAssessmentInstance]
)
def get_assessment_instance_by_assessment_id(
    assessment_id: int,
    # limit: int = 10,
    # offset: int = 0,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    assessment_instances = db_assessment.get_assessment_instance_by_assessment_id(
        db=db, assessment_id=assessment_id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not assessment_instances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment Instances with assessment id {assessment_id} do not exist",
        )
    # return pagination(query=assessment_instances, limit=limit, offset=offset)
    return assessment_instances


# Delete assessment_instance
@router.delete("/instance/{id}", dependencies=[Depends(delete_assessment_permission)])
async def delete_assessment_instance_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_assessment.delete_assessment_instance(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment Instance with id {id} does not exist",
        )
    return {"detail": "Successfully deleted assessment_instance."}


# Create assessment_instance on schedule
@router.post(
    "/instance/automated",
    dependencies=[Depends(create_assessment_permission)],
)
async def create_assessment_instance_automated(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_assessment.create_assessment_instance_reoccurring(db)
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Could not create assessment_instances",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Assessment Instance Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# Update assessment_instance
@router.put(
    "/instance/{id}",
    # response_model=DisplayAssessmentInstance,
    dependencies=[Depends(update_assessment_permission)],
)
async def update_assessment_instance_by_id(
    id: int,
    request: UpdateAssessmentInstance,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        db_status = await db_assessment.update_assessment_instance(
            db=db,
            id=id,
            assessment_instance=request,
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment Instance with id {id} does not exist",
            )
        return db_status
    except IntegrityError as ie:
        LOGGER.exception("Update Assessment Instance Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
