import logging
import math
import random
import string
from datetime import datetime, timedelta
from typing import Generic, List, TypeVar

from fastapi import HTTPException, status
from jose import jwt
from pydantic import BaseModel
from pydantic.generics import GenericModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from config.config import Settings
from fedrisk_api.db.models import (
    AuditTest,
    Control,
    Document,
    Exception,
    Project,
    ProjectUser,
    Risk,
    Role,
    Tenant,
    # TenantRegisterOTP,
    User,
    UserInvitation,
    WBS,
)
from fedrisk_api.s3 import BUCKET_NAME, S3Service

from fedrisk_api.db.util.encrypt_pii_utils import decrypt_user_fields

ResponseType = TypeVar("ResponseType", bound=BaseModel)
LOGGER = logging.getLogger(__name__)
LINK_EXPIRE_TIME_AFTER_VERIFY_IN_MIN = 20


class PaginateResponse(GenericModel, Generic[ResponseType]):
    items: List[ResponseType] = []
    total: int = 0
    offset: int
    limit: int

    class Config:
        orm_mode = True


def pagination(query, offset, limit):
    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def get_cognito_token(request):
    try:
        cognito_token = request.headers["authorization"].split(" ")[1]
    except Exception as e:
        LOGGER.exception("Get Cognito Token Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return cognito_token


def filter_by_tenant(db, model, tenant_id):
    return db.query(model).filter(model.tenant_id == tenant_id)


def ordering_query(query, order, model=None):
    order_by_field = order.strip() if order else None

    if order_by_field and order_by_field[0] == "-":
        order_type = "desc"
        order_by_field_name = order_by_field[1:]
    else:
        order_type = "asc"
        order_by_field_name = order_by_field

    # is_valid_attribute = getattr(model, order_by_field_name, None)

    # if not is_valid_attribute:
    #     return query
    if model:
        order_by_field_name = f"{model}_{order_by_field_name}"
    return query.order_by(text(f"{order_by_field_name} {order_type}"))


def filtering_query(query, model=None, **kwargs):
    for attr_name, attr_value in kwargs.items():
        if attr_value is None:
            continue

        if model:
            attr_name = f"{model}_{attr_name}"

        if isinstance(attr_value, bool):
            query = query.filter(text(f"{attr_name} is {attr_value}"))
        elif isinstance(attr_value, int):
            query = query.filter(text(f"{attr_name} == {attr_value}"))
        else:
            query = query.filter(text(f"{attr_name} like '%{attr_value}%'"))

    return query


def verify_add_user_to_project(db, id, project_users, tenant_id):
    new_added_user = []
    existing_project = filter_by_tenant(db, Project, tenant_id).filter(Project.id == id).first()
    if not existing_project:
        return False, status.HTTP_404_NOT_FOUND, "Project with specified id does not exists"

    user_list = [user.user_id for user in project_users.users]

    db_users = (
        db.query(User.id).filter(User.tenant_id == tenant_id).filter(User.id.in_(user_list)).all()
    )
    roles = db.query(Role.id).all()

    existing_users = db.query(ProjectUser.user_id).filter(ProjectUser.project_id == id).all()

    for project_user in project_users.users:
        if (project_user.user_id,) not in db_users:
            return (
                False,
                status.HTTP_404_NOT_FOUND,
                f"User with id '{project_user.user_id}' does not exist",
            )

        if (project_user.role_id,) not in roles:
            return (
                False,
                status.HTTP_404_NOT_FOUND,
                f"Role with id '{project_user.role_id}' does not exist",
            )

        if project_user.user_id in new_added_user:
            return (
                False,
                status.HTTP_404_NOT_FOUND,
                f"Role with id '{project_user.role_id}' does not exist",
            )

        is_project_user_already_exists = (project_user.user_id,) in existing_users

        if is_project_user_already_exists:
            return (
                False,
                status.HTTP_400_BAD_REQUEST,
                "User with specified id already exists in project with specified id",
            )

        new_added_user.append(project_user.user_id)

    return True, status.HTTP_200_OK, ""


def get_contained_email_addresses_that_need_invitation(db, email_addresses):
    users_in_db = db.query(User.email).filter(User.email.in_(email_addresses)).all()
    email_addresses_that_need_invitation = set(email_addresses) - {
        user.email for user in users_in_db
    }

    return email_addresses_that_need_invitation


def get_contained_email_addresses_that_are_unverified(db, email_addresses):
    users_in_db = (
        db.query(User.email)
        .filter(User.email.in_(email_addresses))
        .filter(User.is_email_verified is False)
        .all()
    )
    return {user.email for user in users_in_db}


def get_contained_email_addresses_that_are_verified(db, email_addresses):
    users_in_db = (
        db.query(User.email)
        .filter(User.email.in_(email_addresses))
        .filter(User.is_email_verified is True)
        .all()
    )
    return {user.email for user in users_in_db}


def get_invitation_link(email, tenant, tenant_id):
    settings = Settings()
    return f"{settings.FRONTEND_SERVER_URL}/register-user/email={email}&tenant={tenant}&tenant_id={tenant_id}"


def get_number_of_active_users_for_tenant(db, tenant_id):
    number_of_active_users = (
        db.query(User).filter(User.tenant_id == tenant_id).filter(User.is_active is True).count()
    )
    return number_of_active_users


def verify_signup_credential(request, db):
    request = request.dict(exclude_unset=True)
    invitation = db.query(UserInvitation).filter(
        UserInvitation.token == request["token"],
        UserInvitation.is_expired is False,
    )

    if not invitation.first():
        return False, "Operation not permitted"

    activated_user = db.query(User).filter(
        User.email == request.email, User.is_email_verified is True
    )

    if activated_user.first():
        return False, "User is already registered with other organization"

    return True, "Link Active"


def expire_token(token, db):
    user_invitation = db.query(UserInvitation).filter(UserInvitation.token == token)
    user_invitation.update({"is_expired": True})
    db.commit()


def get_risk_mapping_metrics():
    risk_mapping_metrics = {
        "low": [
            "possible__insignificant",
            "unlikely__insignificant",
            "very_unlikely__insignificant",
            "very_unlikely__minor",
        ],
        "low_medium": [
            "very_likely__insignificant",
            "likely__insignificant",
            "likely__minor",
            "possible__minor",
            "unlikely__minor",
            "unlikely__moderate",
            "very_unlikely__moderate",
        ],
        "medium": [
            "very_likely__minor",
            "likely__moderate",
            "possible__moderate",
            "unlikely__major",
            "very_unlikely__major",
            "very_unlikely__extreme",
        ],
        "medium_high": [
            "very_likely__moderate",
            "likely__major",
            "possible__major",
            "possible__extreme",
            "Unlikely__extreme",
        ],
        "high": ["very_likely__major", "very_likely__extreme", "likely__extreme"],
    }

    return risk_mapping_metrics.copy()


def get_risk_mapping_order():
    risk_mapping_order = {
        "low": 0,
        "low_medium": 1,
        "medium": 2,
        "medium_high": 3,
        "high": 4,
    }
    return risk_mapping_order.copy()


def filter_by_user_project_role(db, model, user_id, tenant_id):
    user = db.query(User).filter(User.id == user_id).first()
    return db.query(model)
    # if user.is_superuser:
    # return db.query(model)
    # elif user.is_tenant_admin:
    # return db.query(model).filter(model.tenant_id == tenant_id)
    # else:
    # return (
    # db.query(model)
    # .join(ProjectUser, ProjectUser.project_id == model.project_id)
    # .filter(ProjectUser.user_id == user_id)
    # )


def verify_add_user_to_multiple_project(db, project_users, tenant_id):
    new_added_user = []
    LOGGER.info(f"id = {id}, project_users = {project_users}, tenant_id = {tenant_id}")
    project_ids = {project_user.project_id for project_user in project_users.users}
    user_ids = {project_user.user_id for project_user in project_users.users}

    existing_project = (
        filter_by_tenant(db, Project, tenant_id).filter(Project.id.in_(project_ids)).all()
    )
    LOGGER.info(f"Existing project = {existing_project}")

    for project_user in project_users.users:
        for project in existing_project:
            if project_user.project_id == project.id:
                break
        else:
            LOGGER.error(f"Project with id {project_user.project_id} does not exists")
            return False, status.HTTP_404_NOT_FOUND, "Project with specified id does not exists"

    db_users = (
        db.query(User.id).filter(User.tenant_id == tenant_id).filter(User.id.in_(user_ids)).all()
    )
    roles = db.query(Role.id).all()
    existing_users = (
        db.query(ProjectUser.user_id, ProjectUser.project_id)
        .filter(ProjectUser.project_id.in_(project_ids))
        .all()
    )

    for project_user in project_users.users:
        if (project_user.user_id,) not in db_users:
            LOGGER.error(f"User with id {project_user.user_id} does not exists")
            return (
                False,
                status.HTTP_404_NOT_FOUND,
                f"User with id '{project_user.user_id}' does not exist",
            )

        if (project_user.role_id,) not in roles:
            LOGGER.error(f"Role with id {project_user.user_id} does not exists")
            return (
                False,
                status.HTTP_404_NOT_FOUND,
                f"Role with id '{project_user.role_id}' does not exist",
            )

        is_project_user_already_exists = (
            project_user.user_id,
            project_user.project_id,
        ) in existing_users

        is_project_user_duplicate_in_request = (
            project_user.user_id,
            project_user.project_id,
        ) in new_added_user

        if is_project_user_already_exists:
            LOGGER.error(
                f"User with id {project_user.user_id} already exists in project with id {project_user.project_id}"
            )
            return (
                False,
                status.HTTP_400_BAD_REQUEST,
                f"User with id {project_user.user_id} already exists in project with id {project_user.project_id}",
            )

        if is_project_user_duplicate_in_request:
            LOGGER.error(
                f"User with id {project_user.user_id} already exists in request with project id {project_user.project_id}"
            )
            return (
                False,
                status.HTTP_400_BAD_REQUEST,
                "User with specified id already exists in request with specified project id",
            )

        new_added_user.append((project_user.user_id, project_user.project_id))

    return True, status.HTTP_200_OK, ""


def get_modify_objects(documents, db):
    control_ids = []
    audit_test_ids = []
    exception_ids = []
    risk_ids = []
    project_ids = []

    # for document in documents:
    #     if document.fedrisk_object_type == "control":
    #         control_ids.append(int(document.fedrisk_object_id))
    #     elif document.fedrisk_object_type == "audit_test":
    #         audit_test_ids.append(document.fedrisk_object_id)
    #     elif document.fedrisk_object_type == "risk":
    #         risk_ids.append(document.fedrisk_object_id)
    #     elif document.fedrisk_object_type == "exception":
    #         exception_ids.append(document.fedrisk_object_id)
    #     elif document.fedrisk_object_type == "project":
    #         project_ids.append(document.fedrisk_object_id)

    controls = {obj.id: obj for obj in db.query(Control).filter(Control.id.in_(control_ids)).all()}
    audit_tests = {
        obj.id: obj for obj in db.query(AuditTest).filter(AuditTest.id.in_(audit_test_ids)).all()
    }
    exceptions = {
        obj.id: obj for obj in db.query(Exception).filter(Exception.id.in_(exception_ids)).all()
    }
    risks = {obj.id: obj for obj in db.query(Risk).filter(Risk.id.in_(risk_ids)).all()}

    projects = {obj.id: obj for obj in db.query(Project).filter(Project.id.in_(project_ids)).all()}

    document_entities = {
        "control": controls,
        "audit_test": audit_tests,
        "risk": risks,
        "exception": exceptions,
        "project": projects,
    }

    # for document in documents:
    #     try:
    #         document_associated_entity = document_entities.get(document.fedrisk_object_type)
    #         response = {
    #             "fedrisk_object_type_name": document_associated_entity.get(
    #                 document.fedrisk_object_id
    #             ).name
    #         }
    #     except KeyError:
    #         response = {"fedrisk_object_type_name": None}
    #     except AttributeError:
    #         response = {"fedrisk_object_type_name": None}
    #     setattr(document, "fedrisk_object_type_object", response)

    return documents


async def delete_documents_for_fedrisk_object(
    db: Session, fedrisk_object_id: int, fedrisk_object_type: str
):
    """
    Delete all documents for a fedrisk object
    """
    documents = db.query(Document).filter(
        Document.fedrisk_object_type == fedrisk_object_type,
        Document.fedrisk_object_id == fedrisk_object_id,
    )
    try:
        s3_service = S3Service()
        for document in documents.all():
            try:
                my_file_key = f"{document.id}-{document.name}"
                await s3_service.delete_fileobj(bucket=BUCKET_NAME, key=my_file_key)
            except Exception as delete_exception:
                error_message = (
                    f"Unexpected Exception attempting to delete S3 file object: '{my_file_key}' "
                    f"for document with Id: '{document.id} "
                    f"while deleting {fedrisk_object_type} with Id: '{fedrisk_object_id}"
                )
                raise Exception(error_message) from delete_exception

        documents.delete()
        db.commit()
    except Exception:
        db.rollback()
        LOGGER.exception("Unexpected Exception Attempting to Delete Documents for Fedrisk Object")
        raise


def get_custom_jwt_token(email, user_id, tenant_id, cognito_token):
    secret_key = Settings().FEDRISK_JWT_SECRET_KEY
    exp_time = datetime.utcnow() + timedelta(days=1)
    user_token = jwt.encode(
        {
            "username": email,
            "email": email,
            "user_id": user_id,
            "tenant_id": tenant_id,
            "cognito_token": cognito_token,
            "exp": exp_time,
        },
        secret_key,
        algorithm="HS256",
    )
    return user_token


# def generate_otp():
#     string_num = string.digits
#     string_alpha = string.ascii_uppercase

#     OTP = ""
#     for i in range(3):
#         OTP += string_num[math.floor(random.random() * len(string_num))]

#     for i in range(3):
#         OTP += string_alpha[math.floor(random.random() * len(string_alpha))]

#     OTP = "".join(random.sample(OTP, len(OTP)))

#     return OTP


# def verify_tenant_registration_otp(otp, email, db):
#     email_otp = (
#         db.query(TenantRegisterOTP)
#         .filter(TenantRegisterOTP.email == email, TenantRegisterOTP.is_expired is False)
#         .first()
#     )

#     if not email_otp:
#         return False

#     if email_otp.code == otp:
#         return True

#     return False


# def expire_tenant_registration_otp(otp, email, db):
#     email_otp = db.query(TenantRegisterOTP).filter(
#         TenantRegisterOTP.email == email, TenantRegisterOTP.is_expired is False
#     )
#     email_otp.update({"is_expired": True})
#     db.commit()
#     return True


# def verify_tenant_registration_otp_email(email, db):
#     user = db.query(User).filter(User.email == email).first()
#     return user is not None


def get_tenant_customer_data(tenant_id, user_id, db):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    user_decrypt = decrypt_user_fields(user)
    data = {
        "first_name": user_decrypt["first_name"],
        "last_name": user_decrypt["last_name"],
        "email": user.email,
        "organization": tenant.name,
        "tenant_id": tenant.id,
    }
    return data


def convert_unix_time_to_postgres_timestamp(unix_timestamp):
    return datetime.fromtimestamp(unix_timestamp).strftime("%Y-%m-%d %H:%M:%S")


def get_subscription_email_data(subscription_data, email):
    return {
        "start_date": subscription_data["start_datetime"],
        "end_date": subscription_data["end_datetime"],
        "free_users": subscription_data["free_member"],
        "additional_users": subscription_data["additional_member"],
        "frequency": subscription_data["frequency"],
        "email": email,
    }


def get_number_of_pending_user_for_tenant(db, tenant_id):
    number_of_pending_users = (
        db.query(User)
        .filter(User.tenant_id == tenant_id)
        .filter(User.is_email_verified is False)
        .count()
    )
    return number_of_pending_users


if __name__ == "__main__":
    print(get_risk_mapping_order())
    delete_documents_for_fedrisk_object(None, None, None)
