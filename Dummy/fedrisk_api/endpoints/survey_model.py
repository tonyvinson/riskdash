import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import survey_model as db_survey_model
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.survey_model import (
    CreateSurveyModel,
    DisplaySurveyModel,
    UpdateSurveyModel,
    CreateSurveyProjectTemplate,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_survey_model_permission,
    delete_survey_model_permission,
    update_survey_model_permission,
    view_survey_model_permission,
)

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/survey_model", tags=["survey_model"])


@router.post(
    "/",
    response_model=DisplaySurveyModel,
    dependencies=[Depends(create_survey_model_permission)],
)
def create_survey_model(
    request: CreateSurveyModel, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        survey_model = db_survey_model.create_survey_model(survey_model=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Survey Model Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return survey_model


@router.get(
    "/{project_id}/all",
    response_model=List[DisplaySurveyModel],
    dependencies=[Depends(view_survey_model_permission)],
)
def get_all_survey_models(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_survey_model.get_all_survey_models_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplaySurveyModel,
    dependencies=[Depends(view_survey_model_permission)],
)
def get_survey_model_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_survey_model.get_survey_model_by_id(db=db, survey_model_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey Model with specified id does not exist",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_survey_model_permission)])
def update_survey_model_by_id(
    request: UpdateSurveyModel,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_survey_model.update_survey_model_by_id(
            survey_model=request, db=db, survey_model_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey Model with specified id does not exist",
            )
        return {"detail": "Successfully updated Survey Model."}
    except IntegrityError as ie:
        LOGGER.exception("Get Survey Model Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_survey_model_permission)])
def delete_survey_model_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_survey_model.delete_survey_model_by_id(db=db, survey_model_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey Model with specified id does not exist",
        )
    return {"detail": "Successfully deleted Survey Model."}


@router.post(
    "/project_template",
    response_model=DisplaySurveyModel,
    dependencies=[Depends(create_survey_model_permission)],
)
async def create_survey_for_project_from_template(
    request: CreateSurveyProjectTemplate, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        workflow_flowchart = await db_survey_model.create_survey_for_project_from_template(
            survey_template=request,
            db=db,
            user_id=user["user_id"],
            tenant_id=user["tenant_id"],
        )
    except IntegrityError as ie:
        LOGGER.exception("Create Survey for Project from template Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return workflow_flowchart
