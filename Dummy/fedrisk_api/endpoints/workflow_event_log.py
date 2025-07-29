import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import workflow_event_log as db_workflow_event_log
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.workflow_event_log import (
    CreateWorkflowEventLog,
    DisplayWorkflowEventLog,
    UpdateWorkflowEventLog,
)
from fedrisk_api.utils.authentication import custom_auth

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/workflow_event_log", tags=["workflow_event_log"])


@router.post(
    "/",
    response_model=DisplayWorkflowEventLog,
)
def create_workflow_event_log(
    request: CreateWorkflowEventLog, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        workflow_event_log = db_workflow_event_log.create_workflow_event_log(
            workflow_event_log=request, db=db
        )
    except IntegrityError as ie:
        LOGGER.exception("Create WorkflowEventLog Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return workflow_event_log


@router.get(
    "/workflow_event/{id}",
    response_model=List[DisplayWorkflowEventLog],
)
def get_all_workflow_event_logs(
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_workflow_event_log.get_all_workflow_event_logs_by_workflow_event_id(
        workflow_event_id=id,
        db=db,
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplayWorkflowEventLog,
)
def get_workflow_event_log_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_workflow_event_log.get_workflow_event_log_by_id(db=db, workflow_event_log_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow Event Log with specified id does not exist",
        )
    return queryset


@router.put("/{id}")
def update_workflow_event_log_by_id(
    request: UpdateWorkflowEventLog,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_workflow_event_log.update_workflow_event_log_by_id(
            workflow_event_log=request, db=db, workflow_event_log_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow Event Log with specified id does not exist",
            )
        return {"detail": "Successfully updated Workflow Event Log."}
    except IntegrityError as ie:
        LOGGER.exception("Get Workflow Event Log Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}")
def delete_workflow_event_log_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_workflow_event_log.delete_workflow_event_log_by_id(
        db=db, workflow_event_log_id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow Event Log with specified id does not exist",
        )
    return {"detail": "Successfully deleted Workflow Event Log."}
