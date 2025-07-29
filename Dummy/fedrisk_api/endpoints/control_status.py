import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError, DataError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import control_status as db_control_status
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.control_status import (
    CreateControlStatus,
    DisplayControlStatus,
    UpdateControlStatus,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_controlstatus_permission,
    delete_controlstatus_permission,
    update_controlstatus_permission,
    view_controlstatus_permission,
)

from fedrisk_api.utils.utils import PaginateResponse, pagination

router = APIRouter(prefix="/control_statuses", tags=["control_statuses"])
LOGGER = logging.getLogger(__name__)

# Create control_status
@router.post(
    "/",
    response_model=DisplayControlStatus,
    dependencies=[Depends(create_controlstatus_permission)],
)
def create_control_status(
    request: CreateControlStatus, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        return db_control_status.create_control_status(db, request)
    except IntegrityError as ie:
        LOGGER.exception("Create Control Status Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Control Status with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all control_statuses
@router.get(
    "/",
    response_model=PaginateResponse[DisplayControlStatus],
    dependencies=[Depends(view_controlstatus_permission)],
)
def get_all_control_statuses(
    q: str = None,
    # filter_by: str = None,
    # filter_value: str = None,
    sort_by: str = "-created_date",
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    # try:
    queryset = db_control_status.get_all_control_statuses(
        q=q,
        # filter_by=filter_by,
        # filter_value=filter_value,
        sort_by=sort_by,
        tenant_id=user["tenant_id"],
        db=db,
    )
    return pagination(query=queryset, limit=limit, offset=offset)
    # except DataError as e:
    #     LOGGER.exception(f"Get Control Status Error - Invalid request")

    #     if "LIMIT must not be negative" in str(e):
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail="LIMIT must not be negative",
    #         )
    #     elif "OFFSET must not be negative" in str(e):
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND,
    #             detail="OFFSET must not be negative",
    #         )
    #     else:
    #         raise HTTPException(
    #             status_code=status.HTTP_404_NOT_FOUND, detail="Please provide correct filter_value"
    #         )
    # except ProgrammingError as e:
    #     LOGGER.exception(f"Get Control Class Error - Invalid request")
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Please provide correct sort_by field value",
    #     )
    # except AttributeError as e:
    #     LOGGER.exception(f"Get Control Class Error - Invalid request")
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="Please provide correct filter_by field value",
    #     )


# Read one control_status
@router.get(
    "/{id}",
    response_model=DisplayControlStatus,
    dependencies=[Depends(view_controlstatus_permission)],
)
def get_control_status_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    control_status = db_control_status.get_control_status(db=db, id=id)
    if not control_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ControlStatus with id {id} does not exist",
        )

    return control_status


# Update control_status
@router.put("/{id}", dependencies=[Depends(update_controlstatus_permission)])
def update_control_status_by_id(
    id: int, request: UpdateControlStatus, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        db_status = db_control_status.update_control_status(db=db, id=id, control_status=request)
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ControlStatus with id {id} does not exist",
            )

        return {"detail": "Successfully updated control_status."}
    except IntegrityError as ie:
        LOGGER.exception("Update Control Family Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Control Status with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete control_status
@router.delete("/{id}", dependencies=[Depends(delete_controlstatus_permission)])
def delete_control_status_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_control_status.delete_control_status(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ControlStatus with id {id} does not exist",
        )

    return {"detail": "Successfully deleted control_status."}
