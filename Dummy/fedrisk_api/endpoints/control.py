import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import control as db_control
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.control import (
    CreateControl,
    CreateBatchControlsFrameworkVersion,
    DisplayControl,
    UpdateControl,
)
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    create_control_permission,
    delete_control_permission,
    update_control_permission,
    view_control_permission,
)
from fedrisk_api.utils.utils import (
    PaginateResponse,
    # delete_documents_for_fedrisk_object,
    pagination,
)

router = APIRouter(prefix="/controls", tags=["controls"])
LOGGER = logging.getLogger(__name__)

# Create control
@router.post("/", response_model=DisplayControl, dependencies=[Depends(create_control_permission)])
async def create_control(
    request: CreateControl,
    keywords: str = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        response = await db_control.create_control(db, request, keywords, user["tenant_id"])
        return response
    except IntegrityError as ie:
        LOGGER.exception("Create Control Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Control with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Add endpoint that allows batch upload of controls to a framework version
@router.put(
    "/add_controls/{framework_version_id}",
)
def add_batch_controls_by_project_id(
    framework_version_id: int,
    controls: CreateBatchControlsFrameworkVersion,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    updated_framework_version = db_control.add_batch_controls_to_framework_version(
        db=db, framework_version_id=framework_version_id, controls=controls
    )
    return updated_framework_version


# Read all controls
@router.get(
    "/",
    response_model=PaginateResponse[DisplayControl],
    dependencies=[Depends(view_control_permission)],
)
def get_all_controls(
    project_id: int = None,
    q: str = None,
    filter_by: str = None,
    filter_value: str = None,
    sort_by: str = "name",
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_control.get_all_controls(
            db, user["tenant_id"], project_id, q, filter_by, filter_value, sort_by
        )
        return pagination(query=queryset, limit=limit, offset=offset)
    except DataError:
        LOGGER.exception("Get Control Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Please provide correct filter_value"
        )
    except ProgrammingError:
        LOGGER.exception("Get Control Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Please provide correct order field value"
        )
    except AttributeError:
        LOGGER.exception("Get Control Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct filter_by field value",
        )


# Read one control
@router.get("/{id}", response_model=DisplayControl, dependencies=[Depends(view_control_permission)])
def get_control_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    control = db_control.get_control(db=db, id=id, tenant_id=user["tenant_id"])
    if not control:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control with id {id} does not exist",
        )

    return control


# Update control
@router.put("/{id}", dependencies=[Depends(update_control_permission)])
async def update_control_by_id(
    id: int,
    request: UpdateControl,
    keywords: str = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        db_status = await db_control.update_control(
            db=db, id=id, control=request, keywords=keywords, tenant_id=user["tenant_id"]
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Control with id {id} does not exist",
            )

        return {"detail": "Successfully updated control."}
    except IntegrityError as ie:
        LOGGER.exception("Update Control Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Control with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete control
@router.delete("/{id}", dependencies=[Depends(delete_control_permission)])
def delete_control_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    # try:
    #     delete_documents_for_fedrisk_object(
    #         db=db, fedrisk_object_id=id, fedrisk_object_type="control"
    #     )
    # except Exception:
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail="Error while deleting associated documents",
    #     )

    db_status = db_control.delete_control(db=db, id=id, tenant_id=user["tenant_id"])
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Control with id {id} does not exist",
        )

    return {"detail": "Successfully deleted control."}
