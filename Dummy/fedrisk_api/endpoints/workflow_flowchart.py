import logging

from typing import List, Callable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import workflow_flowchart as db_workflow_flowchart
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.workflow_flowchart import (
    CreateWorkflowFlowchart,
    DisplayWorkflowFlowchart,
    UpdateWorkflowFlowchart,
    CreateWorkflowProjectTemplate,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_workflow_flowchart_permission,
    delete_workflow_flowchart_permission,
    update_workflow_flowchart_permission,
    view_workflow_flowchart_permission,
)

from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

from fedrisk_api.db.util.import_workflow_tasks import (
    safe_import_spreadsheet as safe_import_spreadsheet_util,
    import_workflow_flowchart_from_excel as import_workflow_flowchart_from_excel_util,
)


LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/workflow_flowchart", tags=["workflow_flowchart"])


@router.post(
    "/",
    response_model=DisplayWorkflowFlowchart,
    dependencies=[Depends(create_workflow_flowchart_permission)],
)
async def create_workflow_flowchart(
    request: CreateWorkflowFlowchart, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        workflow_flowchart = await db_workflow_flowchart.create_workflow_flowchart(
            workflow_flowchart=request, db=db, user_id=user["user_id"]
        )
    except IntegrityError as ie:
        LOGGER.exception("Create WorkflowFlowchart Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return workflow_flowchart


@router.get(
    "/project/{project_id}",
    response_model=List[DisplayWorkflowFlowchart],
    dependencies=[Depends(view_workflow_flowchart_permission)],
)
def get_all_workflow_flowcharts_by_project(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_workflow_flowchart.get_all_workflow_flowcharts_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplayWorkflowFlowchart,
    dependencies=[Depends(view_workflow_flowchart_permission)],
)
def get_workflow_flowchart_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_workflow_flowchart.get_workflow_flowchart_by_id(db=db, workflow_flowchart_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow Flowchart with specified id does not exist",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_workflow_flowchart_permission)])
async def update_workflow_flowchart_by_id(
    request: UpdateWorkflowFlowchart,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = await db_workflow_flowchart.update_workflow_flowchart_by_id(
            workflow_flowchart=request,
            db=db,
            workflow_flowchart_id=id,
            tenant_id=user["tenant_id"],
            user_id=user["user_id"],
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow Flowchart with specified id does not exist",
            )
        return {"detail": "Successfully updated Workflow Flowchart."}
    except IntegrityError as ie:
        LOGGER.exception("Get Workflow Flowchart Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_workflow_flowchart_permission)])
def delete_workflow_flowchart_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_workflow_flowchart.delete_workflow_flowchart_by_id(
        db=db, workflow_flowchart_id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workflow Flowchart with specified id does not exist",
        )
    return {"detail": "Successfully deleted Workflow Flowchart."}


@router.post(
    "/project_template",
    response_model=DisplayWorkflowFlowchart,
    dependencies=[Depends(create_workflow_flowchart_permission)],
)
async def create_workflow_flowchart_for_project_from_template(
    request: CreateWorkflowProjectTemplate, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        workflow_flowchart = (
            await db_workflow_flowchart.create_workflow_flowchart_for_project_from_template(
                workflow_flowchart=request,
                db=db,
                user_id=user["user_id"],
                tenant_id=user["tenant_id"],
            )
        )
    except IntegrityError as ie:
        LOGGER.exception(
            "Create WorkflowFlowchart for Project from template Error. Invalid request"
        )
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return workflow_flowchart


# Create import framework
@router.put(
    "/import/{project_id}",
    # response_model=DisplayImportFramework,
    # dependencies=[Depends(create_import_framework_permission)],
)
async def create_import_workflow(
    project_id: int,
    fileobject: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        suffix = Path(fileobject.filename).suffix
        with NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(fileobject.file, tmp)
            tmp_path = Path(tmp.name)
        fileobject.file.close()
        if safe_import_spreadsheet_util(tmp_path) is True:
            new_workflow_flowchart = import_workflow_flowchart_from_excel_util(
                tmp_path, db, user["user_id"], user["tenant_id"], project_id
            )
        tmp_path.unlink()  # Delete the temp file
        return new_workflow_flowchart
    except Exception as e:
        LOGGER.exception("Import Workflow Error - Invalid Request")
        raise HTTPException(
            status_code=400, detail="Unable to Import Workflow Due to connection error"
        )
