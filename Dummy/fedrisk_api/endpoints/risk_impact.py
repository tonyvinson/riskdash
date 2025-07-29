import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import risk_impact as db_risk_impact
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.risk_impact import CreateRiskImpact, DisplayRiskImpact, UpdateRiskImpact
from fedrisk_api.utils.permissions import (
    create_riskimpact_permission,
    delete_riskimpact_permission,
    update_riskimpact_permission,
    view_riskimpact_permission,
)

router = APIRouter(prefix="/risk_impacts", tags=["risk_impacts"])
LOGGER = logging.getLogger(__name__)

# Create risk_impact
@router.post(
    "/", response_model=DisplayRiskImpact, dependencies=[Depends(create_riskimpact_permission)]
)
def create_risk_impact(request: CreateRiskImpact, db: Session = Depends(get_db)):
    try:
        return db_risk_impact.create_risk_impact(db, request)
    except IntegrityError as ie:
        LOGGER.exception("Create Risk Impact Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Impact with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all risk_impacts
@router.get(
    "/", response_model=List[DisplayRiskImpact], dependencies=[Depends(view_riskimpact_permission)]
)
def get_all_risk_impacts(db: Session = Depends(get_db)):
    return db_risk_impact.get_all_risk_impacts(db)


# Read one risk_impact
@router.get(
    "/{id}", response_model=DisplayRiskImpact, dependencies=[Depends(view_riskimpact_permission)]
)
def get_risk_impact_by_id(id: int, db: Session = Depends(get_db)):
    risk_impact = db_risk_impact.get_risk_impact(db=db, id=id)
    if not risk_impact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskImpact with id {id} does not exist",
        )

    return risk_impact


# Update risk_impact
@router.put("/{id}", dependencies=[Depends(update_riskimpact_permission)])
def update_risk_impact_by_id(id: int, request: UpdateRiskImpact, db: Session = Depends(get_db)):
    try:
        db_status = db_risk_impact.update_risk_impact(db=db, id=id, risk_impact=request)
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RiskImpact with id {id} does not exist",
            )

        return {"detail": "Successfully updated risk_impact."}
    except IntegrityError as ie:
        LOGGER.exception("Update Risk Category Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Impact with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete risk_impact
@router.delete("/{id}", dependencies=[Depends(delete_riskimpact_permission)])
def delete_risk_impact_by_id(id: int, db: Session = Depends(get_db)):
    db_status = db_risk_impact.delete_risk_impact(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskImpact with id {id} does not exist",
        )

    return {"detail": "Successfully deleted risk_impact."}
