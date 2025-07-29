import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import risk_category as db_risk_category
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.risk_category import (
    CreateRiskCategory,
    DisplayRiskCategory,
    UpdateRiskCategory,
)
from fedrisk_api.utils.permissions import (
    create_riskcategory_permission,
    delete_riskcategory_permission,
    update_riskcategory_permission,
    view_riskcategory_permission,
)
from fedrisk_api.utils.authentication import custom_auth

router = APIRouter(prefix="/risk_categories", tags=["risk_categories"])
LOGGER = logging.getLogger(__name__)

# Create risk_category
@router.post(
    "/", response_model=DisplayRiskCategory, dependencies=[Depends(create_riskcategory_permission)]
)
def create_risk_category(
    request: CreateRiskCategory, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        return db_risk_category.create_risk_category(db, request, user["tenant_id"])
    except IntegrityError as ie:
        LOGGER.exception("Create Risk Category Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        # if "duplicate" in detail_message or "UNIQUE" in detail_message:
        #     detail_message = f"Risk Category with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all risk_categories
@router.get(
    "/",
    response_model=List[DisplayRiskCategory],
    dependencies=[Depends(view_riskcategory_permission)],
)
def get_all_risk_categories(db: Session = Depends(get_db), user=Depends(custom_auth)):
    return db_risk_category.get_all_risk_categories(db, user["tenant_id"])


# Read one risk_category
@router.get(
    "/{id}",
    response_model=DisplayRiskCategory,
    dependencies=[Depends(view_riskcategory_permission)],
)
def get_risk_category_by_id(id: int, db: Session = Depends(get_db)):
    risk_category = db_risk_category.get_risk_category(db=db, id=id)
    if not risk_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskCategory with id {id} does not exist",
        )

    return risk_category


# Update risk_category
@router.put("/{id}", dependencies=[Depends(update_riskcategory_permission)])
def update_risk_category_by_id(id: int, request: UpdateRiskCategory, db: Session = Depends(get_db)):
    try:
        db_status = db_risk_category.update_risk_category(db=db, id=id, risk_category=request)
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RiskCategory with id {id} does not exist",
            )

        return {"detail": "Successfully updated risk_category."}
    except IntegrityError as ie:
        LOGGER.exception("Update Risk Category Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Category with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete risk_category
@router.delete("/{id}", dependencies=[Depends(delete_riskcategory_permission)])
def delete_risk_category_by_id(id: int, db: Session = Depends(get_db)):
    db_status = db_risk_category.delete_risk_category(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskCategory with id {id} does not exist",
        )

    return {"detail": "Successfully deleted risk_category."}
