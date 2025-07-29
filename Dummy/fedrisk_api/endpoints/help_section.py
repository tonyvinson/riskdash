import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import help_section as db_help_section
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.help_section import (
    CreateHelpSection,
    DisplayHelpSection,
    UpdateHelpSection,
)
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    create_help_section_permission,
    delete_help_section_permission,
    update_help_section_permission,
    view_help_section_permission,
)

# from fedrisk_api.utils.utils import PaginateResponse, pagination

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/help_sections", tags=["help_sections"])


@router.post(
    "/", response_model=DisplayHelpSection, dependencies=[Depends(create_help_section_permission)]
)
def create_help_section(
    request: CreateHelpSection, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        help_section = db_help_section.create_help_section(help_section=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Help Section Error. Invalid request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Help Section with title '{request.title}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)
    return help_section


@router.get(
    "/",
    response_model=List[DisplayHelpSection],
    dependencies=[Depends(view_help_section_permission)],
)
def get_all_help_sections(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_help_section.get_help_sections(
        db=db,
        # tenant_id=user["tenant_id"],
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplayHelpSection,
    dependencies=[Depends(view_help_section_permission)],
)
def get_help_section_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_help_section.get_help_section_by_id(db=db, help_section_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help Section with specified id does not exists",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_help_section_permission)])
def update_help_section_by_id(
    request: UpdateHelpSection, id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        queryset = db_help_section.update_help_section_by_id(
            help_section=request, db=db, help_section_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Help Section with specified id does not exists",
            )
        return {"detail": "Successfully updated Help Section."}
    except IntegrityError as ie:
        LOGGER.exception("Get Help Section Error - Invalid request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Help Section with title '{request.title}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_help_section_permission)])
def delete_help_section_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_help_section.delete_help_section_by_id(db=db, help_section_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Help Section with specified id does not exists",
        )
    return {"detail": "Successfully deleted Help Section."}
