import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import risk_likelihood as db_risk_likelihood
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.risk_likelihood import (
    CreateRiskLikelihood,
    DisplayRiskLikelihood,
    UpdateRiskLikelihood,
)
from fedrisk_api.utils.permissions import (
    create_risklikelihood_permission,
    delete_risklikelihood_permission,
    update_risklikelihood_permission,
    view_risklikelihood_permission,
)

router = APIRouter(prefix="/risk_likelihoods", tags=["risk_likelihoods"])
LOGGER = logging.getLogger(__name__)

# Create risk_likelihood
@router.post(
    "/",
    response_model=DisplayRiskLikelihood,
    dependencies=[Depends(create_risklikelihood_permission)],
)
def create_risk_likelihood(request: CreateRiskLikelihood, db: Session = Depends(get_db)):
    try:
        return db_risk_likelihood.create_risk_likelihood(db, request)
    except IntegrityError as ie:
        LOGGER.exception("Create Risk Likelihood Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Likelihood with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all risk_likelihoods
@router.get(
    "/",
    response_model=List[DisplayRiskLikelihood],
    dependencies=[Depends(view_risklikelihood_permission)],
)
def get_all_risk_likelihoods(db: Session = Depends(get_db)):
    return db_risk_likelihood.get_all_risk_likelihoods(db)


# Read one risk_likelihood
@router.get(
    "/{id}",
    response_model=DisplayRiskLikelihood,
    dependencies=[Depends(view_risklikelihood_permission)],
)
def get_risk_likelihood_by_id(id: int, db: Session = Depends(get_db)):
    risk_likelihood = db_risk_likelihood.get_risk_likelihood(db=db, id=id)
    if not risk_likelihood:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskLikelihood with id {id} does not exist",
        )

    return risk_likelihood


# Update risk_likelihood
@router.put("/{id}", dependencies=[Depends(update_risklikelihood_permission)])
def update_risk_likelihood_by_id(
    id: int, request: UpdateRiskLikelihood, db: Session = Depends(get_db)
):
    try:
        db_status = db_risk_likelihood.update_risk_likelihood(db=db, id=id, risk_likelihood=request)
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RiskLikelihood with id {id} does not exist",
            )

        return {"detail": "Successfully updated risk_likelihood."}
    except IntegrityError as ie:
        LOGGER.exception("Update Risk Likelihood Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Likelihood with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete risk_likelihood
@router.delete("/{id}", dependencies=[Depends(delete_risklikelihood_permission)])
def delete_risk_likelihood_by_id(id: int, db: Session = Depends(get_db)):
    db_status = db_risk_likelihood.delete_risk_likelihood(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskLikelihood with id {id} does not exist",
        )

    return {"detail": "Successfully deleted risk_likelihood."}
