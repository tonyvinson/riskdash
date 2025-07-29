import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import survey_response as db_survey_response
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.survey_response import (
    CreateSurveyResponse,
    DisplaySurveyResponse,
    UpdateSurveyResponse,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_survey_response_permission,
    delete_survey_response_permission,
    update_survey_response_permission,
    view_survey_response_permission,
)

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/survey_response", tags=["survey_response"])


@router.post(
    "/",
    response_model=DisplaySurveyResponse,
    dependencies=[Depends(create_survey_response_permission)],
)
def create_survey_response(
    request: CreateSurveyResponse, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        survey_response = db_survey_response.create_survey_response(survey_response=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Survey Response Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return survey_response


@router.get(
    "/{survey_model_id}/survey/all",
    # response_model=List[DisplaySurveyResponse],
    dependencies=[Depends(view_survey_response_permission)],
)
def get_all_survey_responses_by_survey(
    survey_model_id: int,
    test: bool = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_survey_response.get_all_survey_responses_by_survey_id(
        db=db,
        survey_model_id=survey_model_id,
        test=test,
    )
    return queryset


@router.get(
    "/{user_id}/user/all",
    response_model=List[DisplaySurveyResponse],
    dependencies=[Depends(view_survey_response_permission)],
)
def get_all_survey_responses_by_user(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_survey_response.get_all_survey_responses_by_user_id(
        db=db,
        user_id=user_id,
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplaySurveyResponse,
    dependencies=[Depends(view_survey_response_permission)],
)
def get_survey_response_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_survey_response.get_survey_response_by_id(db=db, survey_response_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey Response with specified id does not exist",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_survey_response_permission)])
def update_survey_response_by_id(
    request: UpdateSurveyResponse,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_survey_response.update_survey_response_by_id(
            survey_response=request, db=db, survey_response_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey Response with specified id does not exist",
            )
        return {"detail": "Successfully updated Survey Response."}
    except IntegrityError as ie:
        LOGGER.exception("Get Survey Response Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_survey_response_permission)])
def delete_survey_response_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_survey_response.delete_survey_response_by_id(db=db, survey_response_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey Response with specified id does not exist",
        )
    return {"detail": "Successfully deleted Survey Response."}
