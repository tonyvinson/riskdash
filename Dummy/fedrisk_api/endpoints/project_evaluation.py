import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import project_evaluation as db_project_evaluation
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.project_evaluation import (
    CreateProjectEvaluation,
    DisplayProjectEvaluation,
    UpdateProjectEvaluation,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_projectevaluation_permission,
    delete_projectevaluation_permission,
    update_projectevaluation_permission,
    view_projectevaluation_permission,
)

router = APIRouter(prefix="/project_evaluations", tags=["project_evaluations"])
LOGGER = logging.getLogger(__name__)

# Create project_evaluation
@router.post(
    "/",
    response_model=DisplayProjectEvaluation,
    dependencies=[Depends(create_projectevaluation_permission)],
)
async def create_project_evaluation(
    request: CreateProjectEvaluation,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        result = await db_project_evaluation.create_project_evaluation(
            db, request, user["tenant_id"], keywords, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"tenant with specified id does not have project id {request.project_id}",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Project Evaluation Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"ProjectEvaluation with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# # Read all project_evaluations
@router.get(
    "/",
    response_model=List[DisplayProjectEvaluation],
    dependencies=[Depends(view_projectevaluation_permission)],
)
def get_all_project_evaluations(db: Session = Depends(get_db), user=Depends(custom_auth)):
    return db_project_evaluation.get_all_project_evaluations(db, user["tenant_id"], user["user_id"])


# Read one project_evaluation
@router.get(
    "/{id}",
    response_model=DisplayProjectEvaluation,
)
def get_project_evaluation_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    project_evaluation = db_project_evaluation.get_project_evaluation(
        db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not project_evaluation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ProjectEvaluation with id {id} does not exist",
        )

    return project_evaluation


# Update project_evaluation
@router.put("/{id}", dependencies=[Depends(update_projectevaluation_permission)])
async def update_project_evaluation_by_id(
    id: int,
    request: UpdateProjectEvaluation,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        db_status = await db_project_evaluation.update_project_evaluation(
            db=db,
            id=id,
            project_evaluation=request,
            tenant_id=user["tenant_id"],
            keywords=keywords,
            user_id=user["user_id"],
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ProjectEvaluation with id {id} does not exist",
            )

        return db_status
    except IntegrityError as ie:
        LOGGER.exception("Update Project Evaluation Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"ProjectEvaluation with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete project_evaluation
@router.delete("/{id}", dependencies=[Depends(delete_projectevaluation_permission)])
async def delete_project_evaluation_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_project_evaluation.delete_project_evaluation(
        db=db, id=id, tenant_id=user["tenant_id"]
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ProjectEvaluation with id {id} does not exist",
        )

    return {"detail": "Successfully deleted project_evaluation."}
