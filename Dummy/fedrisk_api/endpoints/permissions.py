import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fedrisk_api.db.database import get_db
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.db.models import (
    Role,
    PermissionRole,
    Permission,
    User,
    SystemRole,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("/{perm_key}")
def get_extra_permissions(
    perm_key: str,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    # Get all system roles for the user
    system_roles = db.query(SystemRole).filter(SystemRole.user_id == user["user_id"]).all()

    for role in system_roles:
        # Check if the permission exists and is enabled for the role
        permission = (
            db.query(PermissionRole)
            .join(Permission, Permission.id == PermissionRole.permission_id)
            .filter(Permission.perm_key == perm_key)
            .filter(PermissionRole.role_id == role.role_id)
            .filter(PermissionRole.tenant_id == user["tenant_id"])
            .first()
        )

        if permission:
            return permission.enabled is True

    # If no matching permission found for any role
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"This user is not permitted to perform this action",
    )
