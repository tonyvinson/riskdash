from sqlalchemy import func
from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import Permission, PermissionRole, Role
from fedrisk_api.utils.utils import ordering_query

from fedrisk_api.schema.role import CreatePermissionRole


def get_all_roles(db: Session, offset: int, limit: int, order: str, name: str):
    name = name.strip() if name else None
    if name:
        lowercase_name = name.lower()
        filtered_query = db.query(Role).filter(func.lower(Role.name).contains(lowercase_name))
    else:
        filtered_query = db.query(Role)

    ordered_query = ordering_query(query=filtered_query, order=order)
    result = ordered_query.limit(limit).offset(offset).all()
    return result, filtered_query.count()


def get_all_roles_permissions_by_category(db: Session, category: str, tenant_id: int):
    all_permissions = db.query(Permission).filter(Permission.category == category).all()
    permission_map = {perm.perm_key: perm for perm in all_permissions}

    role_permission_links = (
        db.query(PermissionRole.role_id, PermissionRole.permission_id, PermissionRole.enabled)
        .filter(PermissionRole.tenant_id == tenant_id)
        .all()
    )

    from collections import defaultdict

    role_permissions = defaultdict(dict)
    for role_id, perm_id, enabled in role_permission_links:
        role_permissions[role_id][perm_id] = enabled

    roles = db.query(Role).all()

    output = []
    for role in roles:
        permissions_for_role = {}
        for perm_key, perm in permission_map.items():
            is_enabled = role_permissions.get(role.id, {}).get(perm.id, False)
            permissions_for_role[perm_key] = {
                "enabled": is_enabled,
                "permission_id": perm.id,
                "name": perm.name,
            }

        output.append(
            {"role_id": role.id, "role_name": role.name, "permissions": permissions_for_role}
        )

    return output


def get_permissions_of_role(db: Session, id: int, offset: int, limit: int, order: str, name: str):
    role = db.query(db.query(Role).filter(Role.id == id).exists()).scalar()
    if not role:
        return False, 0

    name = name.strip() if name else None
    if name:
        lowercase_name = name.lower()
        filtered_query = (
            db.query(Permission)
            .select_from(Permission)
            .join(PermissionRole)
            .filter(
                PermissionRole.role_id == id, func.lower(Permission.name).contains(lowercase_name)
            )
        )
    else:
        filtered_query = (
            db.query(Permission)
            .select_from(Permission)
            .join(PermissionRole)
            .filter(PermissionRole.role_id == id)
        )

    ordered_query = ordering_query(query=filtered_query, order=order)
    result = ordered_query.limit(limit).offset(offset).all()
    return result, filtered_query.count()


def get_all_permissions(db: Session, offset: int, limit: int, order: str, name: str):
    name = name.strip() if name else None
    if name:
        lowercase_name = name.lower()
        filtered_query = db.query(Permission).filter(
            func.lower(Permission.name).contains(lowercase_name)
        )
    else:
        filtered_query = db.query(Permission)

    ordered_query = ordering_query(query=filtered_query, order=order)
    result = ordered_query.limit(limit).offset(offset).all()
    return result, filtered_query.count()


def get_name_of_role(db: Session, id: int):
    return db.query(Role).filter(Role.id == id).all()


def get_all_roles_by_name(db: Session):
    return db.query(Role).all()


def create_permission_for_system_role(db: Session, request: CreatePermissionRole, tenant_id: int):
    """
    Create or update a PermissionRole for a system role on a tenant.
    """
    existing = (
        db.query(PermissionRole)
        .filter_by(
            tenant_id=tenant_id, role_id=request.role_id, permission_id=request.permission_id
        )
        .first()
    )

    if existing:
        existing.enabled = request.enabled
        db.commit()
        db.refresh(existing)
        return existing

    new_perm = PermissionRole(
        tenant_id=tenant_id,
        role_id=request.role_id,
        permission_id=request.permission_id,
        enabled=request.enabled,
    )
    db.add(new_perm)
    db.commit()
    db.refresh(new_perm)
    return new_perm
