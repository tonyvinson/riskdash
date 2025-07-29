import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import cost as db_cost
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.cost import (
    CreateCost,
    DisplayCost,
    UpdateCost,
)
from fedrisk_api.utils.permissions import (
    create_cost_permission,
    delete_cost_permission,
    update_cost_permission,
    view_cost_permission,
)

from fedrisk_api.utils.authentication import custom_auth

router = APIRouter(prefix="/cost", tags=["cost"])
LOGGER = logging.getLogger(__name__)

# Create cost
@router.post("/", response_model=DisplayCost, dependencies=[Depends(create_cost_permission)])
def create_cost(request: CreateCost, db: Session = Depends(get_db), user=Depends(custom_auth)):
    try:
        return db_cost.create_cost(db, request, user["tenant_id"])
    except IntegrityError as ie:
        LOGGER.exception("Create Risk Category Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Category with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all cost
@router.get(
    "/",
    response_model=List[DisplayCost],
    dependencies=[Depends(view_cost_permission)],
)
def get_all_cost(db: Session = Depends(get_db), user=Depends(custom_auth)):
    return db_cost.get_all_costes(db, user["tenant_id"])


# Read one cost
@router.get(
    "/{id}",
    response_model=DisplayCost,
    dependencies=[Depends(view_cost_permission)],
)
def get_cost_by_id(id: int, db: Session = Depends(get_db)):
    cost = db_cost.get_cost(db=db, id=id)
    if not cost:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskCategory with id {id} does not exist",
        )

    return cost


# Update cost
@router.put("/{id}", dependencies=[Depends(update_cost_permission)])
def update_cost_by_id(id: int, request: UpdateCost, db: Session = Depends(get_db)):
    try:
        db_status = db_cost.update_cost(db=db, id=id, cost=request)
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RiskCategory with id {id} does not exist",
            )

        return {"detail": "Successfully updated cost."}
    except IntegrityError as ie:
        LOGGER.exception("Update Risk Category Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Category with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete cost
@router.delete("/{id}", dependencies=[Depends(delete_cost_permission)])
def delete_cost_by_id(id: int, db: Session = Depends(get_db)):
    db_status = db_cost.delete_cost(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskCategory with id {id} does not exist",
        )

    return {"detail": "Successfully deleted cost."}
