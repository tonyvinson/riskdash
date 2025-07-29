import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import wbs as db_wbs
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.wbs import CreateWBS, DisplayWBS, UpdateWBS
from fedrisk_api.utils.authentication import custom_auth

# from fedrisk_api.utils.permissions import (
#     create_wbs_permission,
#     delete_wbs_permission,
#     update_wbs_permission,
#     view_wbs_permission,
# )

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/wbs", tags=["wbs"])

# Create wbs
@router.post(
    "/",
    response_model=DisplayWBS,
    # dependencies=[Depends(create_wbs_permission)]
)
async def create_wbs(
    request: CreateWBS,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    result = await db_wbs.create_wbs(
        db, request, keywords, int(user["tenant_id"]), int(user["user_id"])
    )
    if not result:
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the wbs",
            )

    return result


# Read all wbs for a project
@router.get(
    "/project/{project_id}",
    response_model=[],
    # dependencies=[Depends(view_wbs_permission)]
)
def get_all_project_wbs(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    result = db_wbs.get_all_project_wbs(db, project_id)
    if not result:
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No WBS were found for this project.",
            )

    return result


# Read one wbs
@router.get("/{id}", response_model=DisplayWBS)
def get_wbs_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    wbs = db_wbs.get_wbs(db, id)
    if not wbs:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WBS with id {id} does not exist",
        )

    return wbs


# Update wbs
@router.put(
    "/{id}"
    # response_model=UpdateWBS
    # dependencies=[Depends(update_risk_permission)]
)
async def update_wbs_by_id(
    id: int,
    request: UpdateWBS,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    db_status = await db_wbs.update_wbs(
        db=db,
        id=id,
        wbs=request,
        tenant_id=user["tenant_id"],
        keywords=keywords,
        user_id=user["user_id"],
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WBS with id {id} does not exist",
        )

    return db_status


# Delete wbs
@router.delete(
    "/{id}",
    # dependencies=[Depends(delete_risk_permission)]
)
async def delete_wbs_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):

    db_status = await db_wbs.delete_wbs(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WBS with id {id} does not exist",
        )
    return {"detail": "Successfully deleted wbs."}
