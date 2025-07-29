import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import risk_status as db_risk_status
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.risk_status import CreateRiskStatus, DisplayRiskStatus, UpdateRiskStatus
from fedrisk_api.utils.permissions import (
    create_riskstatus_permission,
    delete_riskstatus_permission,
    update_riskstatus_permission,
    view_riskstatus_permission,
)

router = APIRouter(prefix="/risk_statuses", tags=["risk_statuses"])
LOGGER = logging.getLogger(__name__)

# Create risk_status
@router.post(
    "/", response_model=DisplayRiskStatus, dependencies=[Depends(create_riskstatus_permission)]
)
def create_risk_status(request: CreateRiskStatus, db: Session = Depends(get_db)):
    try:
        return db_risk_status.create_risk_status(db, request)
    except IntegrityError as ie:
        LOGGER.exception("Create Risk Status Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Status with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all risk_statuses
@router.get(
    "/", response_model=List[DisplayRiskStatus], dependencies=[Depends(view_riskstatus_permission)]
)
def get_all_risk_statuses(db: Session = Depends(get_db)):
    return db_risk_status.get_all_risk_statuses(db)


# Read one risk_status
@router.get(
    "/{id}", response_model=DisplayRiskStatus, dependencies=[Depends(view_riskstatus_permission)]
)
def get_risk_status_by_id(id: int, db: Session = Depends(get_db)):
    risk_status = db_risk_status.get_risk_status(db=db, id=id)
    if not risk_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskStatus with id {id} does not exist",
        )

    return risk_status


# Update risk_status
@router.put("/{id}", dependencies=[Depends(update_riskstatus_permission)])
def update_risk_status_by_id(id: int, request: UpdateRiskStatus, db: Session = Depends(get_db)):
    try:
        db_status = db_risk_status.update_risk_status(db=db, id=id, risk_status=request)
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RiskStatus with id {id} does not exist",
            )

        return {"detail": "Successfully updated risk_status."}
    except IntegrityError as ie:
        LOGGER.exception("Update Risk Status Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Status with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete risk_status
@router.delete("/{id}", dependencies=[Depends(delete_riskstatus_permission)])
def delete_risk_status_by_id(id: int, db: Session = Depends(get_db)):
    db_status = db_risk_status.delete_risk_status(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskStatus with id {id} does not exist",
        )

    return {"detail": "Successfully deleted risk_status."}
