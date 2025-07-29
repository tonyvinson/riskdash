import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import survey_template as db_survey_template
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.survey_template import (
    CreateSurveyTemplate,
    DisplaySurveyTemplate,
    UpdateSurveyTemplate,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_survey_template_permission,
    delete_survey_template_permission,
    update_survey_template_permission,
    view_survey_template_permission,
)

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/survey_template", tags=["survey_template"])


@router.post(
    "/",
    response_model=DisplaySurveyTemplate,
    dependencies=[Depends(create_survey_template_permission)],
)
def create_survey_template(
    request: CreateSurveyTemplate, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        survey_template = db_survey_template.create_survey_template(
            survey_template=request, db=db, tenant_id=user["tenant_id"]
        )
    except IntegrityError as ie:
        LOGGER.exception("Create Survey Template Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return survey_template


@router.get(
    "/all",
    response_model=List[DisplaySurveyTemplate],
    dependencies=[Depends(view_survey_template_permission)],
)
def get_all_survey_templates(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_survey_template.get_all_survey_templates_by_tenant_id(
        db=db,
        tenant_id=user["tenant_id"],
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplaySurveyTemplate,
    dependencies=[Depends(view_survey_template_permission)],
)
def get_survey_template_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_survey_template.get_survey_template_by_id(db=db, survey_template_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey Template with specified id does not exist",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_survey_template_permission)])
def update_survey_template_by_id(
    request: UpdateSurveyTemplate,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_survey_template.update_survey_template_by_id(
            survey_template=request, db=db, survey_template_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Survey Template with specified id does not exist",
            )
        return {"detail": "Successfully updated Survey Template."}
    except IntegrityError as ie:
        LOGGER.exception("Get Survey Template Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_survey_template_permission)])
def delete_survey_template_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_survey_template.delete_survey_template_by_id(db=db, survey_template_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Survey Template with specified id does not exist",
        )
    return {"detail": "Successfully deleted Survey Template."}
