import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm.session import Session

from sqlalchemy.exc import IntegrityError

from typing import List

from fedrisk_api.db import role as db_role
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.role import (
    DisplayPermissions,
    DisplayRoles,
    CreatePermissionRole,
    PermissionRoleUpdate,
)
from fedrisk_api.utils.permissions import view_permission_permission, view_role_permission
from fedrisk_api.utils.authentication import custom_auth

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=DisplayRoles, dependencies=[Depends(view_role_permission)])
def get_all_roles(
    db: Session = Depends(get_db),
    offset: int = 0,
    limit: int = 10,
    name: str = None,
    order: str = "-created_date",
):
    roles, total = db_role.get_all_roles(db=db, offset=offset, limit=limit, order=order, name=name)
    return DisplayRoles(items=roles, total=total)


@router.get(
    "/permissions/by_category",
    # response_model=List[DisplayRole],
    dependencies=[Depends(view_role_permission)],
)
def get_all_roles(db: Session = Depends(get_db), category: str = None, user=Depends(custom_auth)):
    roles_perms_categories = db_role.get_all_roles_permissions_by_category(
        db=db, category=category, tenant_id=user["tenant_id"]
    )
    return roles_perms_categories


@router.get(
    "/{id}/permissions",
    response_model=DisplayPermissions,
    dependencies=[Depends(view_permission_permission)],
)
def get_permissions_of_role(
    id: int,
    db: Session = Depends(get_db),
    offset: int = 0,
    limit: int = 10,
    name: str = None,
    order: str = "-created_date",
):
    permissions, total = db_role.get_permissions_of_role(
        db=db, id=id, offset=offset, limit=limit, order=order, name=name
    )
    if permissions is False:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Role with id '{id}' does not exist",
        )

    return DisplayPermissions(items=permissions, total=total)


@router.get(
    "/permissions",
    response_model=DisplayPermissions,
    dependencies=[Depends(view_permission_permission)],
)
def get_all_permissions(
    db: Session = Depends(get_db),
    offset: int = 0,
    limit: int = 10,
    name: str = None,
    order: str = "-created_date",
):
    permissions, total = db_role.get_all_permissions(
        db=db, offset=offset, limit=limit, order=order, name=name
    )
    return DisplayPermissions(items=permissions, total=total)


# POST a new permission for a role
@router.post("/", dependencies=[Depends(view_permission_permission)])
async def create_permission_for_role(
    request: CreatePermissionRole,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_role.create_permission_for_system_role(db, request, user["tenant_id"])

        if not result:
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Permission couldn't be added to role",
                )

        return result

    except IntegrityError as ie:
        LOGGER.exception("Create Permission for Role Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.post("/permissions/update", dependencies=[Depends(view_permission_permission)])
def update_permissions_for_roles(
    updates: List[PermissionRoleUpdate],
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    """
    Bulk update of permission-role mappings for a tenant.
    Each item in the list is either created or updated depending on existence.
    """
    updated = []

    try:
        for item in updates:
            updated_entry = db_role.create_permission_for_system_role(
                db=db, request=item, tenant_id=user["tenant_id"]
            )
            updated.append(updated_entry.id)

        return {"updated": updated}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/name",
    # response_model=List[DisplayRole],
    dependencies=[Depends(view_role_permission)],
)
def get_all_roles_by_name(db: Session = Depends(get_db), user=Depends(custom_auth)):
    roles = db_role.get_all_roles_by_name(db=db)
    return roles
