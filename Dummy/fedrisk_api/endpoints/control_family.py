import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import control_family as db_control_family
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.control_family import (
    CreateControlFamily,
    DisplayControlFamily,
    UpdateControlFamily,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_controlfamily_permission,
    delete_controlfamily_permission,
    update_controlfamily_permission,
    view_controlfamily_permission,
)
from fedrisk_api.utils.utils import PaginateResponse, pagination

router = APIRouter(prefix="/control_families", tags=["control_families"])
LOGGER = logging.getLogger(__name__)

# Create control_family
@router.post(
    "/",
    response_model=DisplayControlFamily,
    dependencies=[Depends(create_controlfamily_permission)],
)
def create_control_family(
    request: CreateControlFamily, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        return db_control_family.create_control_family(db, request, tenant_id=user["tenant_id"])
    except IntegrityError as ie:
        LOGGER.exception("Create Control Family Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Control Family with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all control_families
@router.get(
    "/",
    response_model=PaginateResponse[DisplayControlFamily],
    dependencies=[Depends(view_controlfamily_permission)],
)
def get_all_control_families(
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
        queryset = db_control_family.get_all_control_families(
            q=q,
            filter_by=filter_by,
            filter_value=filter_value,
            sort_by=sort_by,
            tenant_id=user["tenant_id"],
            db=db,
        )
        return pagination(query=queryset, limit=limit, offset=offset)
    except DataError as e:
        LOGGER.exception(f"Get Control Family Error - Invalid request")

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
        LOGGER.exception(f"Get Control Family Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct sort_by field value",
        )
    except AttributeError as e:
        LOGGER.exception(f"Get Control Family Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct filter_by field value",
        )


# Read one control_family
@router.get(
    "/{id}",
    response_model=DisplayControlFamily,
    dependencies=[Depends(view_controlfamily_permission)],
)
def get_control_family_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    control_family = db_control_family.get_control_family(db=db, id=id, tenant_id=user["tenant_id"])
    if not control_family:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ControlFamily with id {id} does not exist",
        )

    return control_family


# Update control_family
@router.put("/{id}", dependencies=[Depends(update_controlfamily_permission)])
def update_control_family_by_id(
    id: int, request: UpdateControlFamily, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        db_status = db_control_family.update_control_family(
            db=db, id=id, control_family=request, tenant_id=user["tenant_id"]
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"ControlFamily with id {id} does not exist",
            )

        return {"detail": "Successfully updated control_family."}
    except IntegrityError as ie:
        LOGGER.exception("Update Control Family Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Control Family with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete control_family
@router.delete("/{id}", dependencies=[Depends(delete_controlfamily_permission)])
def delete_control_family_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_control_family.delete_control_family(db=db, id=id, tenant_id=user["tenant_id"])
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ControlFamily with id {id} does not exist",
        )

    return {"detail": "Successfully deleted control_family."}
