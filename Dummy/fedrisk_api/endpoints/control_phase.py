import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import control_phase as db_control_phase
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.control_phase import (
    CreateControlPhase,
    DisplayControlPhase,
    UpdateControlPhase,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_controlphase_permission,
    delete_controlphase_permission,
    update_controlphase_permission,
    view_controlphase_permission,
)
from fedrisk_api.utils.utils import PaginateResponse, pagination

router = APIRouter(prefix="/control_phases", tags=["control_phases"])
LOGGER = logging.getLogger(__name__)

# Create control_phase
@router.post(
    "/", response_model=DisplayControlPhase, dependencies=[Depends(create_controlphase_permission)]
)
def create_control_phase(
    request: CreateControlPhase, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        return db_control_phase.create_control_phase(db, request, tenant_id=user["tenant_id"])
    except IntegrityError as ie:
        LOGGER.exception("Create Control Phase Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Control Phase with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all control_phases
@router.get(
    "/",
    response_model=PaginateResponse[DisplayControlPhase],
    dependencies=[Depends(view_controlphase_permission)],
)
def get_all_control_phases(
    q: str = None,
    filter_by: str = None,
    filter_value: str = None,
    sort_by: str = "-created_date",
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_control_phase.get_all_control_phases(
            q=q,
            filter_by=filter_by,
            filter_value=filter_value,
            sort_by=sort_by,
            tenant_id=user["tenant_id"],
            db=db,
        )
        return pagination(query=queryset, limit=limit, offset=offset)
    except DataError as e:
        LOGGER.exception(f"Get Control Phase Error - Invalid request")

        if "LIMIT must not be negative" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LIMIT must not be negative",
            )
        elif "OFFSET must not be negative" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OFFSET must not be negative",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Please provide correct filter_value"
            )
    except ProgrammingError as e:
        LOGGER.exception(f"Get Control Phase Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct sort_by field value",
        )
    except AttributeError as e:
        LOGGER.exception(f"Get Control Phase Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct filter_by field value",
        )


# Read one control_phase
@router.get(
    "/{id}",
    response_model=DisplayControlPhase,
    dependencies=[Depends(view_controlphase_permission)],
)
def get_control_phase_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    control_phase = db_control_phase.get_control_phase(db=db, id=id, tenant_id=user["tenant_id"])
    if not control_phase:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ControlPhase with id {id} does not exist",
        )

    return control_phase


# Update control_phase
@router.put("/{id}", dependencies=[Depends(update_controlphase_permission)])
def update_control_phase_by_id(
    id: int, request: UpdateControlPhase, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        db_status = db_control_phase.update_control_phase(
            db=db, id=id, control_phase=request, tenant_id=user["tenant_id"]
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ControlPhase with id {id} does not exist",
            )

        return {"detail": "Successfully updated control_phase."}
    except IntegrityError as ie:
        LOGGER.exception("Update Control Phase Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Control Phase with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete control_phase
@router.delete("/{id}", dependencies=[Depends(delete_controlphase_permission)])
def delete_control_phase_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_control_phase.delete_control_phase(db=db, id=id, tenant_id=user["tenant_id"])
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ControlPhase with id {id} does not exist",
        )

    return {"detail": "Successfully deleted control_phase."}
