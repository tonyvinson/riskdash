import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import task_status as db_task_status
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.task_status import (
    CreateTaskStatus,
    DisplayTaskStatus,
    UpdateTaskStatus,
)
from fedrisk_api.utils.permissions import (
    create_taskstatus_permission,
    delete_taskstatus_permission,
    update_taskstatus_permission,
    view_taskstatus_permission,
)

from fedrisk_api.utils.authentication import custom_auth

router = APIRouter(prefix="/task_status", tags=["task_status"])
LOGGER = logging.getLogger(__name__)

# Create task_status
@router.post(
    "/", response_model=DisplayTaskStatus, dependencies=[Depends(create_taskstatus_permission)]
)
def create_task_status(
    request: CreateTaskStatus, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        return db_task_status.create_task_status(db, request, user["tenant_id"])
    except IntegrityError as ie:
        LOGGER.exception("Create Task Status Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")


# Read all task_status
@router.get(
    "/",
    response_model=List[DisplayTaskStatus],
    dependencies=[Depends(view_taskstatus_permission)],
)
def get_all_task_status(db: Session = Depends(get_db), user=Depends(custom_auth)):
    return db_task_status.get_all_task_statuses(db, user["tenant_id"])


# Read one task_status
@router.get(
    "/{id}",
    response_model=DisplayTaskStatus,
    dependencies=[Depends(view_taskstatus_permission)],
)
def get_task_status_by_id(id: int, db: Session = Depends(get_db)):
    task_status = db_task_status.get_task_status(db=db, id=id)
    if not task_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task Status with id {id} does not exist",
        )

    return task_status


# Update task_status
@router.put("/{id}", dependencies=[Depends(update_taskstatus_permission)])
def update_task_status_by_id(id: int, request: UpdateTaskStatus, db: Session = Depends(get_db)):
    try:
        db_status = db_task_status.update_task_status(db=db, id=id, task_status=request)
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task Status with id {id} does not exist",
            )

        return {"detail": "Successfully updated task_status."}
    except IntegrityError as ie:
        LOGGER.exception("Update Task Status Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Task Status with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete task_status
@router.delete("/{id}", dependencies=[Depends(delete_taskstatus_permission)])
def delete_task_status_by_id(id: int, db: Session = Depends(get_db)):
    db_status = db_task_status.delete_task_status(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task Status with id {id} does not exist",
        )

    return {"detail": "Successfully deleted task status."}
