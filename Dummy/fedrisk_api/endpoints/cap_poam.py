import logging
from typing import List
import pandas as pd
from io import BytesIO

from fastapi.responses import StreamingResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import cap_poam as db_cap_poam
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.cap_poam import CreateCapPoam, DisplayCapPoam, UpdateCapPoam
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    create_cappoam_permission,
    delete_cappoam_permission,
    update_cappoam_permission,
    view_cappoam_permission,
)

# from fedrisk_api.utils.utils import (
#     PaginateResponse,
#     pagination,
# )

router = APIRouter(prefix="/cap_poams", tags=["cap_poams"])
LOGGER = logging.getLogger(__name__)

# Create cap_poam
@router.post("/", response_model=DisplayCapPoam, dependencies=[Depends(create_cappoam_permission)])
async def create_cap_poam(
    request: CreateCapPoam,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_cap_poam.create_cap_poam(db, request, user["tenant_id"], user["user_id"])
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"tenant with specified id does not have project id {request.project_id}",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create CAP/POAM Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"CapPoam with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Get cap_poams by project id
@router.get(
    "/project/{project_id}",
    response_model=List[DisplayCapPoam],
    dependencies=[Depends(view_cappoam_permission)],
)
def get_cap_poam_by_id(project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    cap_poams = db_cap_poam.get_cap_poams_by_project_id(
        db=db, tenant_id=user["tenant_id"], project_id=project_id, user_id=user["user_id"]
    )
    if not cap_poams:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CapPoams with project id {project_id} do not exist",
        )

    return cap_poams


# Read one cap_poam
@router.get("/{id}", response_model=DisplayCapPoam)
def get_cap_poam_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    cap_poam = db_cap_poam.get_cap_poam(
        db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not cap_poam:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CapPoam with id {id} does not exist",
        )

    return cap_poam


# Update cap_poam
@router.put(
    "/{id}", response_model=DisplayCapPoam, dependencies=[Depends(update_cappoam_permission)]
)
async def update_cap_poam_by_id(
    id: int,
    request: UpdateCapPoam,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        db_status = await db_cap_poam.update_cap_poam(
            db=db,
            id=id,
            cap_poam=request,
            tenant_id=user["tenant_id"],
            user_id=user["user_id"],
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CapPoam with id {id} does not exist",
            )
        return db_status
    except IntegrityError as ie:
        LOGGER.exception("Update CAP/POAM Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"CapPoam with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete cap_poam
@router.delete("/{id}", dependencies=[Depends(delete_cappoam_permission)])
async def delete_cap_poam_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = await db_cap_poam.delete_cap_poam(db=db, id=id, tenant_id=user["tenant_id"])
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CapPoam with id {id} does not exist",
        )
    return {"detail": "Successfully deleted cap_poam."}


@router.get("/data/{project_id}")
def get_cap_poam_data_by_project_id(
    project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    # get data for export
    cap_export_data = db_cap_poam.get_cap_poams_data_for_spreadsheet_by_project_id(
        db=db, tenant_id=user["tenant_id"], project_id=project_id, user_id=user["user_id"]
    )

    return cap_export_data
