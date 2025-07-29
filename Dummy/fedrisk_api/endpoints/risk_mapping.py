import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import risk_mapping as db_risk_mapping
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.risk_mapping import CreateRiskMapping, DisplayRiskMapping, UpdateRiskMapping
from fedrisk_api.utils.permissions import (
    create_riskmapping_permission,
    delete_riskmapping_permission,
    update_riskmapping_permission,
    view_riskmapping_permission,
)

router = APIRouter(prefix="/risk_mappings", tags=["risk_mappings"])
LOGGER = logging.getLogger(__name__)

# Create risk_mapping
@router.post(
    "/", response_model=DisplayRiskMapping, dependencies=[Depends(create_riskmapping_permission)]
)
def create_risk_mapping(request: CreateRiskMapping, db: Session = Depends(get_db)):
    try:
        return db_risk_mapping.create_risk_mapping(db, request)
    except IntegrityError as ie:
        LOGGER.exception("Create Risk Mapping Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Mapping with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all risk_mappings
@router.get(
    "/",
    response_model=List[DisplayRiskMapping],
    dependencies=[Depends(view_riskmapping_permission)],
)
def get_all_risk_mappings(db: Session = Depends(get_db)):
    return db_risk_mapping.get_all_risk_mappings(db)


# Read one risk_mapping
@router.get(
    "/{id}", response_model=DisplayRiskMapping, dependencies=[Depends(view_riskmapping_permission)]
)
def get_risk_mapping_by_id(id: int, db: Session = Depends(get_db)):
    risk_mapping = db_risk_mapping.get_risk_mapping(db=db, id=id)
    if not risk_mapping:
        LOGGER.exception("Update Risk Mapping Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskMapping with id {id} does not exist",
        )

    return risk_mapping


# Update risk_mapping
@router.put("/{id}", dependencies=[Depends(update_riskmapping_permission)])
def update_risk_mapping_by_id(id: int, request: UpdateRiskMapping, db: Session = Depends(get_db)):
    try:
        db_status = db_risk_mapping.update_risk_mapping(db=db, id=id, risk_mapping=request)
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RiskMapping with id {id} does not exist",
            )

        return {"detail": "Successfully updated risk_mapping."}
    except IntegrityError as ie:
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Mapping with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete risk_mapping
@router.delete("/{id}", dependencies=[Depends(delete_riskmapping_permission)])
def delete_risk_mapping_by_id(id: int, db: Session = Depends(get_db)):
    db_status = db_risk_mapping.delete_risk_mapping(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskMapping with id {id} does not exist",
        )

    return {"detail": "Successfully deleted risk_mapping."}
