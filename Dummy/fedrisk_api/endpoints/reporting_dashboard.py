from typing import Dict
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# from fedrisk_api.db.compliance_dashboard import get_compliance_dashboard_metrics
from fedrisk_api.db.database import get_db

from sqlalchemy.exc import IntegrityError
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.schema.reporting_dashboard import (
    CreateReportingSettings,
    UpdateReportingSettings,
    DisplayReportingSettings,
)

# from fedrisk_api.utils.permissions import view_compliance_dashboard
from fedrisk_api.db.reporting_dashboard import (
    create_reporting_settings_user,
    update_reporting_settings_user,
    delete_reporting_settings_by_user_id,
    get_risk_by_category_count,
    get_data_for_pivot,
    get_reporting_settings_for_user,
)

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/dashboards/reporting", tags=["dashboards"])


@router.get(
    "/metrics",
    # response_model=DisplayComplianceMetrics,
    # dependencies=[Depends(view_compliance_dashboard)],
)
def get_risk_by_category_count_per_month(
    project_id: int = None,
    year: int = None,
    db: Session = Depends(get_db),
    user: Dict = Depends(custom_auth),
):
    response = get_risk_by_category_count(db=db, project_id=project_id, year=year)
    return response


@router.get(
    "/pivot",
    # response_model=DisplayProject,
    # dependencies=[Depends(view_compliance_dashboard)],
)
def get_project_data_for_pivot(
    db: Session = Depends(get_db),
    user: Dict = Depends(custom_auth),
):
    response = get_data_for_pivot(db=db, tenant_id=user["tenant_id"], user_id=user["user_id"])
    return response


# POST endpoint for reporting settings
@router.post(
    "/reporting_settings",
    response_model=DisplayReportingSettings,  # dependencies=[Depends(create_project_group_permission)]
)
def create_reporting_settings(
    request: CreateReportingSettings, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        reporting_settings = create_reporting_settings_user(settings=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create User Settings Error. Invalid request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Settings with user id {user['user_id']} already exists"
        raise HTTPException(status_code=409, detail=detail_message)
    return reporting_settings


# PUT endpoint for reporting settings
@router.put(
    "/reporting_settings",
    response_model=DisplayReportingSettings,  # dependencies=[Depends(create_project_group_permission)]
)
def create_reporting_settings(
    request: UpdateReportingSettings, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        reporting_settings = update_reporting_settings_user(settings=request, db=db)
        if not reporting_settings:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User with specified id does not exist",
            )
        return reporting_settings
    except IntegrityError as ie:
        LOGGER.exception("Update User Settings Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET endpoint for reporting settings
@router.get(
    "/reporting_settings",
    # response_model=DisplayReportingSettings,
    # dependencies=[Depends(view_compliance_dashboard)],
)
def get_reporting_setttings(
    db: Session = Depends(get_db),
    user: Dict = Depends(custom_auth),
):
    response = get_reporting_settings_for_user(db=db, user_id=user["user_id"])
    return response


# delete reporting settings for user
@router.delete(
    "/{user_id}",
    # dependencies=[Depends(delete_project_group_permission)]
)
def delete_reporting_settings_by_user_id(
    user_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = delete_reporting_settings_by_user_id(db=db, user_id=user_id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User reporting settings with specified id does not exist",
        )
    return {"detail": "Successfully deleted user reporting settings."}
