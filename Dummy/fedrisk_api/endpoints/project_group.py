import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import project_group as db_project_group
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.project_group import (
    CreateProjectGroup,
    DisplayProjectGroup,
    UpdateProjectGroup,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_project_group_permission,
    delete_project_group_permission,
    update_project_group_permission,
    view_project_group_permission,
)
from fedrisk_api.utils.utils import PaginateResponse, pagination

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/project_groups", tags=["project_groups"])


@router.post(
    "/", response_model=DisplayProjectGroup, dependencies=[Depends(create_project_group_permission)]
)
def create_project_group(
    request: CreateProjectGroup, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        project_group = db_project_group.create_project_group(
            project_group=request, db=db, tenant_id=user["tenant_id"]
        )
    except IntegrityError as ie:
        LOGGER.exception("Create Project Group Error. Invalid request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Project Group with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)
    return project_group


@router.get(
    "/",
    response_model=List[DisplayProjectGroup],
    dependencies=[Depends(view_project_group_permission)],
)
def get_all_project_groups(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_project_group.get_project_group(
        db=db,
        tenant_id=user["tenant_id"],
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplayProjectGroup,
    dependencies=[Depends(view_project_group_permission)],
)
def get_project_group_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_project_group.get_project_group_by_id(db=db, project_group_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project Group with specified id does not exists",
        )
    return queryset


@router.get(
    "/{id}/projects",
    dependencies=[Depends(view_project_group_permission)],
)
def get_project_group_projects_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_project_group.get_projects_by_group_id(
        db=db, tenant_id=user["tenant_id"], project_group_id=id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project Group with specified id does not exists",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_project_group_permission)])
def update_project_group_by_id(
    request: UpdateProjectGroup, id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        queryset = db_project_group.update_project_group_by_id(
            project_group=request, db=db, project_group_id=id, tenant_id=user["tenant_id"]
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project Group with specified id does not exist",
            )
        return {"detail": "Successfully updated project Group."}
    except IntegrityError as ie:
        LOGGER.exception("Get Project_Group Error - Invalid request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Project Group with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_project_group_permission)])
def delete_project_group_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_project_group.delete_project_group_by_id(
        db=db, tenant_id=user["tenant_id"], project_group_id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project Group with specified id does not exist",
        )
    return {"detail": "Successfully deleted project Group."}
