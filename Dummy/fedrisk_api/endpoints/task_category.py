import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import task_category as db_task_category
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.task_category import (
    CreateTaskCategory,
    DisplayTaskCategory,
    UpdateTaskCategory,
)
from fedrisk_api.utils.permissions import (
    create_taskcategory_permission,
    delete_taskcategory_permission,
    update_taskcategory_permission,
    view_taskcategory_permission,
)

from fedrisk_api.utils.authentication import custom_auth

router = APIRouter(prefix="/task_category", tags=["task_category"])
LOGGER = logging.getLogger(__name__)

# Create task_category
@router.post(
    "/", response_model=DisplayTaskCategory, dependencies=[Depends(create_taskcategory_permission)]
)
def create_task_category(
    request: CreateTaskCategory, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        return db_task_category.create_task_category(db, request, user["tenant_id"])
    except IntegrityError as ie:
        LOGGER.exception("Create Risk Category Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Category with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all task_category
@router.get(
    "/",
    response_model=List[DisplayTaskCategory],
    dependencies=[Depends(view_taskcategory_permission)],
)
def get_all_task_category(db: Session = Depends(get_db), user=Depends(custom_auth)):
    return db_task_category.get_all_task_categories(db, user["tenant_id"])


# Read one task_category
@router.get(
    "/{id}",
    response_model=DisplayTaskCategory,
    dependencies=[Depends(view_taskcategory_permission)],
)
def get_task_category_by_id(id: int, db: Session = Depends(get_db)):
    task_category = db_task_category.get_task_category(db=db, id=id)
    if not task_category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskCategory with id {id} does not exist",
        )

    return task_category


# Update task_category
@router.put("/{id}", dependencies=[Depends(update_taskcategory_permission)])
def update_task_category_by_id(id: int, request: UpdateTaskCategory, db: Session = Depends(get_db)):
    try:
        db_status = db_task_category.update_task_category(db=db, id=id, task_category=request)
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"RiskCategory with id {id} does not exist",
            )

        return {"detail": "Successfully updated task_category."}
    except IntegrityError as ie:
        LOGGER.exception("Update Risk Category Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk Category with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete task_category
@router.delete("/{id}", dependencies=[Depends(delete_taskcategory_permission)])
def delete_task_category_by_id(id: int, db: Session = Depends(get_db)):
    db_status = db_task_category.delete_task_category(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"RiskCategory with id {id} does not exist",
        )

    return {"detail": "Successfully deleted task_category."}
