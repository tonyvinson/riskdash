import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import workflow_template_event as db_workflow_template_event
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.workflow_template_event import (
    CreateWorkflowTemplateEvent,
    DisplayWorkflowTemplateEvent,
    UpdateWorkflowTemplateEvent,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_workflow_template_event_permission,
    delete_workflow_template_event_permission,
    update_workflow_template_event_permission,
    view_workflow_template_event_permission,
)

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/workflow_template_event", tags=["workflow_template_event"])


@router.post(
    "/",
    response_model=DisplayWorkflowTemplateEvent,
    dependencies=[Depends(create_workflow_template_event_permission)],
)
def create_workflow_template_event(
    request: CreateWorkflowTemplateEvent, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        workflow_template_event = db_workflow_template_event.create_workflow_template_event(
            workflow_template_event=request, db=db, tenant_id=user["tenant_id"]
        )
    except IntegrityError as ie:
        LOGGER.exception("Create WorkflowTemplateEvent Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return workflow_template_event


@router.get(
    "/all",
    response_model=List[DisplayWorkflowTemplateEvent],
    dependencies=[Depends(view_workflow_template_event_permission)],
)
def get_all_workflow_template_events(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_workflow_template_event.get_all_workflow_template_events_by_tenant_id(
        db=db,
        tenant_id=user["tenant_id"],
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplayWorkflowTemplateEvent,
    dependencies=[Depends(view_workflow_template_event_permission)],
)
def get_workflow_template_event_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_workflow_template_event.get_workflow_template_event_by_id(
        db=db, workflow_template_event_id=id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow Template Event with specified id does not exist",
        )
    return queryset


@router.get(
    "/workflow_node/{workflow_template_node_id}",
    response_model=List[DisplayWorkflowTemplateEvent],
    dependencies=[Depends(view_workflow_template_event_permission)],
)
def get_workflow_template_event_by_workflow_node_id(
    workflow_template_node_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_workflow_template_event.get_workflow_template_event_by_workflow_template_node_id(
        db=db, workflow_template_node_id=workflow_template_node_id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow Template Event with specified workflow template node id does not exist",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_workflow_template_event_permission)])
def update_workflow_template_event_by_id(
    request: UpdateWorkflowTemplateEvent,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_workflow_template_event.update_workflow_template_event_by_id(
            workflow_template_event=request, db=db, workflow_template_event_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow Template Event with specified id does not exist",
            )
        return {"detail": "Successfully updated Workflow Template Event."}
    except IntegrityError as ie:
        LOGGER.exception("Get Workflow Event Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_workflow_template_event_permission)])
def delete_workflow_template_event_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_workflow_template_event.delete_workflow_template_event_by_id(
        db=db, workflow_template_event_id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow Template Event with specified id does not exist",
        )
    return {"detail": "Successfully deleted Workflow Template Event."}
