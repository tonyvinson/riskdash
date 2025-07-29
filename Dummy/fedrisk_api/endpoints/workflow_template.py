import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import workflow_template as db_workflow_template
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.workflow_template import (
    CreateWorkflowTemplate,
    DisplayWorkflowTemplate,
    UpdateWorkflowTemplate,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_workflow_template_permission,
    delete_workflow_template_permission,
    update_workflow_template_permission,
    view_workflow_template_permission,
)

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/workflow_template", tags=["workflow_template"])


@router.post(
    "/",
    response_model=DisplayWorkflowTemplate,
    dependencies=[Depends(create_workflow_template_permission)],
)
def create_workflow_template(
    request: CreateWorkflowTemplate, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        workflow_template = db_workflow_template.create_workflow_template(
            workflow_template=request, db=db, tenant_id=user["tenant_id"]
        )
    except IntegrityError as ie:
        LOGGER.exception("Create WorkflowTemplate Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return workflow_template


@router.get(
    "/all",
    response_model=List[DisplayWorkflowTemplate],
    dependencies=[Depends(view_workflow_template_permission)],
)
def get_all_workflow_templates(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_workflow_template.get_all_workflow_templates_by_tenant_id(
        db=db,
        tenant_id=user["tenant_id"],
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplayWorkflowTemplate,
    dependencies=[Depends(view_workflow_template_permission)],
)
def get_workflow_template_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_workflow_template.get_workflow_template_by_id(db=db, workflow_template_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow Template with specified id does not exist",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_workflow_template_permission)])
def update_workflow_template_by_id(
    request: UpdateWorkflowTemplate,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_workflow_template.update_workflow_template_by_id(
            workflow_template=request, db=db, workflow_template_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow Template with specified id does not exist",
            )
        return {"detail": "Successfully updated Workflow Template."}
    except IntegrityError as ie:
        LOGGER.exception("Get Workflow Template Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_workflow_template_permission)])
def delete_workflow_template_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_workflow_template.delete_workflow_template_by_id(db=db, workflow_template_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow Template with specified id does not exist",
        )
    return {"detail": "Successfully deleted Workflow Template."}
