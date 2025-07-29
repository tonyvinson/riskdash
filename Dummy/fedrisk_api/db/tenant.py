import logging
from secrets import token_urlsafe

from sqlalchemy import func
from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import (
    Tenant,
    # TenantRegisterOTP,
    User,
    UserInvitation,
)
from fedrisk_api.schema.tenant import TenantUserDetails, UserDetails

# from fedrisk_api.db.util.data_creation_utils import (
#     create_tenant_s3_bucket,
#     create_tenant_user_folder_s3,
# )

# from fedrisk_api.db.util.data_creation_utils import (
#     create_tenant_user_folder_s3
# )

LOGGER = logging.getLogger(__name__)


def create_user_invitation(emails, db: Session, tenant_id: int):
    # uninvited_users = []
    invitation_object = []
    index = 0
    for email in emails:
        user = User(email=email, tenant_id=tenant_id)
        db.add(user)
        db.commit()
        db.refresh(user)
        # uninvited_users.append(user)

        invitation = UserInvitation(
            email=email, token=token_urlsafe(96), tenant_id=tenant_id, user_id=user.id
        )
        invitation_object.append(invitation)
        index = index + 1

    # db.add_all(uninvited_users)
    db.add_all(invitation_object)
    db.commit()
    db.flush()
    return invitation_object


def create_user_invite(email, db: Session, tenant_id: int, role):
    from fedrisk_api.db.util.data_creation_utils import create_tenant_user_folder_s3

    user = User(email=email, tenant_id=tenant_id, system_role=role)
    db.add(user)
    db.commit()
    db.refresh(user)

    create_tenant_user_folder_s3(db, user.id, tenant_id)

    invitation = UserInvitation(
        email=email, token=token_urlsafe(96), tenant_id=tenant_id, user_id=user.id
    )
    db.add(invitation)
    db.commit()
    db.flush()
    return invitation


def verify_invitation(token, db: Session):
    invitation = (
        db.query(UserInvitation)
        .filter(UserInvitation.token == token)
        .filter(UserInvitation.is_expired is False)
    )
    invitation_object = invitation.first()
    if not invitation_object:
        return False

    return invitation_object


def resend_invitation_mail(email: str, db: Session, tenant_id: int):
    user_object = db.query(User).filter(User.email == email).first()
    user_invitation = db.query(UserInvitation).filter(UserInvitation.email == email)

    user_invitation.update({"is_expired": True})
    new_invitation = UserInvitation(
        email=email,
        token=token_urlsafe(96),
        is_used=False,
        is_expired=False,
        tenant_id=tenant_id,
        user_id=user_object.id,
    )

    db.add(new_invitation)
    db.commit()
    db.flush()

    return new_invitation


def update_user(response: UserDetails, db: Session):
    response = response.dict(exclude_unset=True)

    email = response.pop("email")
    first_name = response.pop("first_name")
    last_name = response.pop("last_name")
    phone_no = response.pop("phone_no")

    user = db.query(User).filter(User.email == email)

    user_update_data = {
        "first_name": first_name,
        "last_name": last_name,
        "phone_no": phone_no,
        "is_active": True,
        "is_email_verified": True,
    }

    user.update(user_update_data)
    db.commit()
    return True


def check_unique_email(email: str, db: Session):
    return db.query(User).filter(func.lower(User.email) == email.lower()).first()


# def get_signup_otp(email: str, otp: str, db: Session):
#     existing_otp = db.query(TenantRegisterOTP).filter(TenantRegisterOTP.email == email)
#     if existing_otp.first():
#         existing_otp.update({"is_expired": True})
#     otp_object = TenantRegisterOTP(code=otp, email=email, is_expired=False)
#     db.add(otp_object)
#     db.commit()
#     return otp


def tenant_signup(request: TenantUserDetails, db: Session):
    tenant_user = {
        "first_name": request.first_name,
        "last_name": request.last_name,
        "email": request.email,
        "is_tenant_admin": True,
        "is_active": True,
        "is_email_verified": True,
        "system_role": 4,
    }

    tenant_info = {
        "name": request.organization,
        "is_active": False,
        "user_licence": 0,
    }

    tenant = Tenant(**tenant_info)
    db.add(tenant)
    db.flush()

    tenant_user.update({"tenant_id": tenant.id})
    tenant_user = User(**tenant_user)

    db.add_all([tenant, tenant_user])
    db.commit()
    from fedrisk_api.db.util.data_creation_utils import create_tenant_s3_bucket

    create_tenant_s3_bucket(db, tenant.id)
    from fedrisk_api.db.util.data_creation_utils import create_tenant_user_folder_s3

    create_tenant_user_folder_s3(db, tenant_user.id, tenant.id)

    # from fedrisk_api.db.util.data_creation_utils import create_tenant_s3_lambda_trigger

    # updated_tenant = db.query(Tenant).filter(Tenant.id == tenant.id).first()

    # create_tenant_s3_lambda_trigger("FedriskClamAVS3ScanTag", updated_tenant.s3_bucket)

    return {"tenant": tenant, "user": tenant_user}


def tenant_user_signup(request: TenantUserDetails, db: Session):
    existing_user = db.query(User).filter(User.email == request.email)
    if not existing_user.first():
        return False
    # update user with details
    existing_user.update({"first_name": request.first_name})
    existing_user.update({"last_name": request.last_name})
    existing_user.update({"is_email_verified": True})

    db.commit()

    return {existing_user.first()}


def update_tenant_customer(customer_id: str, tenant_id: str, db: Session):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id)

    if not tenant.first():
        return False

    tenant.update({"customer_id": customer_id})
    db.commit()
    return True


def update_tenant_user_licenses(user_licence: int, tenant_id: str, db: Session):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id)

    if not tenant.first():
        return False

    tenant.update({"user_licence": user_licence})
    db.commit()
    return True


def get_tenant_by_id(tenant_id: int, db: Session):
    return db.query(Tenant).filter(Tenant.id == tenant_id).first()


def get_active_member_count(tenant_id, db):
    return db.query(User).filter(User.is_active is True).filter(User.tenant_id == tenant_id).count()


def get_user_invites(tenant_id: int, db: Session):
    return db.query(UserInvitation).filter(UserInvitation.tenant_id == tenant_id).all()


def update_tenant_webhook_api_key(tenant_id: int, webhook_api_key: str, db: Session):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id)

    if not tenant.first():
        return False

    tenant.update({"webhook_api_key": webhook_api_key})
    db.commit()
    return True
