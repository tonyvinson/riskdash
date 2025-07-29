import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import framework_version as db_framework_version
from fedrisk_api.db.database import get_db

from fedrisk_api.schema.framework_version import (
    CreateFrameworkVersion,
    DisplayFrameworkVersion,
    UpdateFrameworkVersion,
)
from fedrisk_api.utils.authentication import custom_auth

from typing import List

from fedrisk_api.utils.permissions import (
    create_framework_version_permission,
    delete_framework_version_permission,
    update_framework_version_permission,
    view_framework_version_permission,
)
from fedrisk_api.utils.utils import PaginateResponse, pagination

router = APIRouter(prefix="/framework_versions", tags=["framework_versions"])
LOGGER = logging.getLogger(__name__)

# Create framework Version
@router.post(
    "/",
    response_model=DisplayFrameworkVersion,
    dependencies=[Depends(create_framework_version_permission)],
)
def create_framework_version(
    request: CreateFrameworkVersion,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        response = db_framework_version.create_framework_version(
            db, request, keywords, tenant_id=user["tenant_id"]
        )
        return response
    except IntegrityError as ie:
        LOGGER.exception("Create Framework  Version Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Framework with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all framework versions
@router.get(
    "/",
    response_model=PaginateResponse[DisplayFrameworkVersion],
    dependencies=[Depends(view_framework_version_permission)],
)
def get_all_framework_versions(
    project_id: int = None,
    framework_id: int = None,
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    LOGGER.warning(
        f"Getting all Frameworks for user {user['user_id']} - Tenant: {user['tenant_id']}"
    )
    try:
        queryset = db_framework_version.get_all_framework_versions(
            db, project_id=project_id, framework_id=framework_id
        )
        return pagination(query=queryset, limit=limit, offset=offset)
    except DataError:
        LOGGER.exception("Get Framework Version Error - Invalid Request")
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


# Read one framework version
@router.get(
    "/{id}",
    response_model=DisplayFrameworkVersion,
    dependencies=[Depends(view_framework_version_permission)],
)
def get_framework_by_version_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    framework_version = db_framework_version.get_framework_version(db=db, id=id)
    if not framework_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Framework with id {id} does not exist",
        )

    return framework_version


# Update framework version
@router.put("/{id}", dependencies=[Depends(update_framework_version_permission)])
def update_framework_version_by_id(
    id: int,
    request: UpdateFrameworkVersion,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        db_status = db_framework_version.update_framework_version(
            db=db, id=id, framework_version=request, tenant_id=user["tenant_id"], keywords=keywords
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Framework version with id {id} does not exist",
            )
        return {"detail": "Successfully updated framework version."}
    except IntegrityError as ie:
        LOGGER.exception("Update Framework Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = (
                f"Framework version with version prefix '{request.version_prefix}' already exists"
            )
            detail_message = (
                f"Framework version with version suffix '{request.version_suffix}' already exists"
            )
        raise HTTPException(status_code=409, detail=detail_message)


# Delete framework version
@router.delete("/{id}", dependencies=[Depends(delete_framework_version_permission)])
def delete_framework_version_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_framework_version.delete_framework_version(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Framework version with id {id} does not exist",
        )
    return {"detail": "Successfully deleted framework version."}
