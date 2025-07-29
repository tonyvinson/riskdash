import logging
from datetime import datetime
from typing import Dict, List
import os

from fastapi import UploadFile, status, Depends
from sqlalchemy import func
from sqlalchemy.orm.session import Session
from sqlalchemy.orm import joinedload

from fedrisk_api.db.models import Tenant, User, UserInvitation, Role, SystemRole
from fedrisk_api.schema.user import UpdateUserProfile, UpdateUserRole, DisplayUser
from fedrisk_api.utils.utils import ordering_query

from fedrisk_api.db.util.encrypt_pii_utils import decrypt_user_fields, encrypt_user_by_id

from fedrisk_api.s3 import S3Service

LOGGER = logging.getLogger(__name__)

LINK_EXPIRE_TIME_AFTER_VERIFY_IN_MIN = 30


def get_all_users(
    db: Session,
    user: Dict[str, str],
    q: str,
    sort_by: str,
    filter_by: str,
    filter_value: str,
):
    db_user = db.query(User).filter(User.id == user["user_id"]).first()

    if db_user.is_superuser:
        queryset = db.query(User)
    else:
        queryset = db.query(User).filter(User.tenant_id == user["tenant_id"])

    if filter_by:
        if filter_by in ("email",):
            queryset = queryset.filter(
                func.lower(getattr(User, filter_by)).contains(filter_value.lower())
            )
        else:
            queryset = queryset.filter(func.lower(getattr(User, filter_by)) == filter_value.lower())

    if sort_by:
        queryset = ordering_query(query=queryset, model=User.__tablename__, order=sort_by)

    if q:
        queryset = queryset.filter(
            func.lower(User.email).contains(func.lower(q)),
        )

    return queryset  # 👈 Return the query object, not .all()


def get_user_by_id(db: Session, id: int, tenant_id: int):
    user = db.query(User).filter(User.id == id).first()
    LOGGER.info(user)

    if not user:
        return None

    user = decrypt_user_fields(user)  # decrypt once only

    s3_service = S3Service()

    if isinstance(user, dict):
        user_dict = user
    else:
        user_model = DisplayUser.from_orm(user)
        user_dict = user_model.dict()

    profile_pic = user_dict.get("profile_picture")
    user_folder = user_dict.get("s3_bucket")
    tenant = user_dict.get("tenant")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    LOGGER.info(tenant)
    tenant_bucket = tenant.s3_bucket

    system_role = db.query(Role).filter(Role.id == user_dict.get("system_role")).first()
    user_dict["system_role_name"] = system_role.name

    if profile_pic:
        file_key = f"{user_folder}{profile_pic}"
        try:
            user_dict["profile_picture_url"] = s3_service.get_profile_picture_image_url(
                86400, tenant, file_key
            )
        except Exception as e:
            LOGGER.warning(f"Failed to generate presigned URL: {e}")
            user_dict["profile_picture_url"] = ""

        try:
            tag_response = s3_service.get_object_tags(tenant_bucket, file_key)
            user_dict["profile_picture_tags"] = tag_response.get(
                "TagSet", [{"Value": "Not Scanned"}]
            )[0]["Value"]
        except Exception as e:
            LOGGER.warning(f"Failed to fetch object tags: {e}")
            user_dict["profile_picture_tags"] = "Not Scanned"
    else:
        user_dict["profile_picture_url"] = ""
        user_dict["profile_picture_tags"] = "Not Scanned"

    return DisplayUser(**user_dict)


def get_tenant_user_roles(db: Session, tenant_id: str):
    users = (
        db.query(User)
        .join(SystemRole, User.id == SystemRole.user_id)
        .filter(User.tenant_id == tenant_id)
        .all()
    )
    return users


def get_user_by_email(db: Session, email: str, tenant_id: int):
    user = db.query(User).filter(User.tenant_id == tenant_id, User.email == email).first()
    return DisplayUser(**decrypt_user_fields(user))


def deactivate_user(id: int, user: Dict[str, str], db: Session):
    LOGGER.info(f"user = {user}")
    user = db.query(User).filter(User.id == user["user_id"]).first()
    existing_user = db.query(User).filter(User.id == id)
    # if user.is_superuser:
    # if user is system administrator
    if user.system_role == 4:
        existing_user = db.query(User).filter(User.id == id)
    # elif user.is_tenant_admin:
    # if user is billing administrator
    elif user.system_role == 6:
        existing_user = db.query(User).filter(User.id == id, User.tenant_id == user.tenant_id)
    # else:
    # return False

    existing_user.update({"is_active": False})
    db.commit()
    return True


def make_user_tenant_admin(id: int, user: Dict[str, str], db: Session):
    user = db.query(User).filter(User.id == user["user_id"]).first()

    if user.is_superuser:
        existing_user = db.query(User).filter(User.id == id)
    elif user.is_tenant_admin:
        existing_user = db.query(User).filter(User.id == id, User.tenant_id == user.tenant_id)
    else:
        return False

    if not existing_user:
        return False

    if not existing_user.first().is_active or not existing_user.is_email_verified:
        return False

    existing_user.update({"is_tenant_admin": True})
    db.commit()
    return True


def activate_user(id: int, user: Dict[str, str], db: Session):
    user = db.query(User).filter(User.id == user["user_id"]).first()

    # if user.is_superuser:
    # if user is a system administrator
    if user.system_role == 4:
        existing_user = db.query(User).filter(User.id == id)
    # elif user.is_tenant_admin:
    # if user is a billing administrator
    elif user.system_role == 6:
        existing_user = db.query(User).filter(User.id == id, User.tenant_id == user.tenant_id)
    else:
        return False, status.HTTP_400_BAD_REQUEST, "Operation not permitted"

    if not existing_user.first():
        return False, status.HTTP_404_NOT_FOUND, "User with specified id does not exists"

    tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()

    no_tenat_users = (
        db.query(User)
        .filter(User.tenant_id == user.tenant_id)
        .filter(User.is_active is True)
        .count()
    )

    if no_tenat_users == tenant.user_licence:
        return False, status.HTTP_400_BAD_REQUEST, "Tenant reached maximum active users"

    existing_user.update({"is_active": True})
    db.commit()
    return True, status.HTTP_200_OK, "Successfully activated User"


def check_unique_username(db: Session, username: str):
    return check_unique_user_email(db, user_email=username)


def check_unique_user_email(db: Session, user_email: str):
    return db.query(User).filter(User.email == user_email.lower()).first()


def update_user_profile_by_id(id: int, request: UpdateUserProfile, user_id: int, db: Session):
    # if user_id != id:
    # return False

    profile_dict = request.dict(exclude_none=True)

    if len(profile_dict) == 0:
        return True

    existing_user = db.query(User).filter(User.id == id)

    if not existing_user.first():
        return False

    existing_user.update(profile_dict)

    db.commit()
    # encrypt_user_by_id(db, id)
    return True


def update_profile_picture(user_id: int, profile_picture: str, db: Session):
    user = db.query(User).filter(User.id == user_id)

    user.update({"profile_picture": profile_picture})

    db.commit()
    return user.first()


def remove_profile_picture(user_id: int, db: Session):
    user = db.query(User).filter(User.id == user_id)

    user.update({"profile_picture": None})
    db.commit()

    return True


def delete_user(user_id: int, db: Session, user):
    db_user = db.query(User).filter(User.id == user["user_id"]).first()
    if db_user.is_superuser:
        existing_user = db.query(User).filter(User.id == user_id)
    elif db_user.is_tenant_admin:
        existing_user = db.query(User).filter(
            User.id == user_id, User.tenant_id == user["tenant_id"]
        )
    else:
        return False, status.HTTP_400_BAD_REQUEST, "Operation not permitted"

    if not existing_user.first():
        return False, status.HTTP_404_NOT_FOUND, "User does not exists"
    if existing_user is not None:
        invitations = db.query(UserInvitation).filter(
            UserInvitation.email == existing_user.first().email
        )
        if invitations is not None:
            invitations.delete(synchronize_session=False)

    existing_user.delete(synchronize_session=False)
    db.commit()

    return True, status.HTTP_200_OK, "User deleted successfully"


def update_bulk_user_system_roles(request, db: Session):
    for r in request:
        # Check if system role already exists for the user
        existing = (
            db.query(SystemRole)
            .filter(SystemRole.role_id == r.role_id)
            .filter(SystemRole.user_id == r.user_id)
            .first()
        )

        if existing:
            existing.enabled = r.enabled
        else:
            new_role = SystemRole(
                user_id=r.user_id,
                role_id=r.role_id,
                enabled=r.enabled,
            )
            db.add(new_role)

    db.commit()
    return True


def deactivate_users(users, db: Session):
    for user in users:
        dbuser = db.query(User).filter(User.id == user.id)
        dbuser.update({"profile_picture": None})
        dbuser.update({"is_active": False})
        db.commit()
    return True, status.HTTP_200_OK, "Users deactivated successfully"
