import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import risk_score as db_risk_score
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.risk_score import CreateRiskScore, DisplayRiskScore, UpdateRiskScore
from fedrisk_api.utils.permissions import (
    create_riskscore_permission,
    delete_riskscore_permission,
    update_riskscore_permission,
    view_riskscore_permission,
)

router = APIRouter(prefix="/risk_scores", tags=["risk_scores"])
LOGGER = logging.getLogger(__name__)

# Create risk_score
@router.post(
    "/", response_model=DisplayRiskScore, dependencies=[Depends(create_riskscore_permission)]
)
def create_risk_score(request: CreateRiskScore, db: Session = Depends(get_db)):
    try:
        return db_risk_score.create_risk_score(db, request)
    except IntegrityError as ie:
        LOGGER.exception("Create Risk Score Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Score with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all risk_scores
@router.get(
    "/", response_model=List[DisplayRiskScore], dependencies=[Depends(view_riskscore_permission)]
)
def get_all_risk_scores(db: Session = Depends(get_db)):
    return db_risk_score.get_all_risk_scores(db)


# Read one risk_score
@router.get(
    "/{id}", response_model=DisplayRiskScore, dependencies=[Depends(view_riskscore_permission)]
)
def get_risk_score_by_id(id: int, db: Session = Depends(get_db)):
    risk_score = db_risk_score.get_risk_score(db=db, id=id)
    if not risk_score:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskScore with id {id} does not exist",
        )

    return risk_score


# Update risk_score
@router.put("/{id}", dependencies=[Depends(update_riskscore_permission)])
def update_risk_score_by_id(id: int, request: UpdateRiskScore, db: Session = Depends(get_db)):
    try:
        db_status = db_risk_score.update_risk_score(db=db, id=id, risk_score=request)
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RiskScore with id {id} does not exist",
            )

        return {"detail": "Successfully updated risk_score."}
    except IntegrityError as ie:
        LOGGER.exception("Update Risk Score Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Score with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete risk_score
@router.delete("/{id}", dependencies=[Depends(delete_riskscore_permission)])
def delete_risk_score_by_id(id: int, db: Session = Depends(get_db)):
    db_status = db_risk_score.delete_risk_score(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskScore with id {id} does not exist",
        )

    return {"detail": "Successfully deleted risk_score."}
