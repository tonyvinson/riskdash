import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import framework as db_framework
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.framework import (
    CreateFramework,
    DisplayFrameworkTenant,
    DisplayFramework,
    UpdateFramework,
    CreateFrameworkTenant,
    UpdateFrameworkTenant,
)
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    create_framework_permission,
    delete_framework_permission,
    update_framework_permission,
    view_framework_permission,
)
from fedrisk_api.utils.utils import PaginateResponse, pagination

router = APIRouter(prefix="/frameworks", tags=["frameworks"])
LOGGER = logging.getLogger(__name__)

# Create framework
@router.post(
    "/", response_model=DisplayFramework, dependencies=[Depends(create_framework_permission)]
)
def create_framework(
    request: CreateFramework,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        response = db_framework.create_framework(db, request, user["tenant_id"], keywords)
        return response
    except IntegrityError as ie:
        LOGGER.exception("Create Framework Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Framework with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Create framework mapping to tenant
@router.post(
    "/map",
    response_model=DisplayFrameworkTenant,
    dependencies=[Depends(create_framework_permission)],
)
def create_framework_map_to_tenant(
    request: CreateFrameworkTenant,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        response = db_framework.create_framework_map_tenant(db, request)
        return response
    except IntegrityError as ie:
        LOGGER.exception("Create Framework Tenant mapping Error - Invalid Request")
        return str(ie)


# Update framework mapping to tenant
@router.put(
    "/map",
    response_model=DisplayFrameworkTenant,
    dependencies=[Depends(create_framework_permission)],
)
def update_framework_map_to_tenant(
    request: UpdateFrameworkTenant,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        response = db_framework.update_framework_map_tenant(db, request)
        return response
    except IntegrityError as ie:
        LOGGER.exception("Update Framework Tenant mapping Error - Invalid Request")
        return str(ie)


# Read all frameworks
@router.get(
    "/",
    response_model=PaginateResponse[DisplayFramework],
    dependencies=[Depends(view_framework_permission)],
)
def get_all_frameworks(
    project_id: int = None,
    # q: str = None,
    # filter_by: str = None,
    # filter_value: str = None,
    # sort_by: str = "name",
    is_global: bool = None,
    is_enabled: bool = None,
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    LOGGER.warning(
        f"Getting all Frameworks for user {user['user_id']} - Tenant: {user['tenant_id']}"
    )
    try:
        queryset = db_framework.get_all_frameworks(
            db, user["tenant_id"], project_id, is_global, is_enabled
        )
        return pagination(query=queryset, limit=limit, offset=offset)
    except DataError:
        LOGGER.exception("Get Framework Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Please provide correct filter_value"
        )
    except ProgrammingError:
        LOGGER.exception("Get Framework Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Please provide correct order field value"
        )
    except AttributeError:
        LOGGER.exception("Get Framework Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct filter_by field value",
        )


# Read one framework
@router.get(
    "/{id}", response_model=DisplayFramework, dependencies=[Depends(view_framework_permission)]
)
def get_framework_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    framework = db_framework.get_framework(db=db, id=id, tenant_id=user["tenant_id"])
    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Framework with id {id} does not exist",
        )

    return framework


# Update framework
@router.put("/{id}", dependencies=[Depends(update_framework_permission)])
def update_framework_by_id(
    id: int,
    request: UpdateFramework,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        db_status = db_framework.update_framework(
            db=db, id=id, framework=request, tenant_id=user["tenant_id"], keywords=keywords
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Framework with id {id} does not exist",
            )
        return {"detail": "Successfully updated framework."}
    except IntegrityError as ie:
        LOGGER.exception("Update Framework Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Framework with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete framework
@router.delete("/{id}", dependencies=[Depends(delete_framework_permission)])
def delete_framework_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_framework.delete_framework(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Framework with id {id} does not exist",
        )
    return {"detail": "Successfully deleted framework."}
