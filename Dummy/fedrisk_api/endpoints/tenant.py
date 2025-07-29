import json
import logging
import requests
import os
from itertools import chain

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import EmailStr
from sqlalchemy.orm import Session

from config.config import Settings
from fedrisk_api.db import tenant as db_tenant
from fedrisk_api.db.database import get_db
from fedrisk_api.db.models import Tenant, User
from fedrisk_api.schema.tenant import (
    Emails,
    TenantUserDetails,
    UserDetails,
    UserInvite,
    TenantResend,
    TenantConfirm,
    CaptchaToken,
)
from fedrisk_api.schema.user import CredentialResponseForm
from fedrisk_api.service.email_service import EmailService
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.cognito import cognito_client
from fedrisk_api.utils.email_util import (
    send_invitation_email,
    # send_otp_email,
    send_signup_success_email,
)
from fedrisk_api.utils.permissions import (
    send_invitation_tenant_permission,
    # view_subscription_permission,
)
from fedrisk_api.utils.utils import (
    # expire_tenant_registration_otp,
    expire_token,
    # generate_otp,
    get_contained_email_addresses_that_are_unverified,
    get_contained_email_addresses_that_are_verified,
    get_contained_email_addresses_that_need_invitation,
    get_custom_jwt_token,
    get_invitation_link,
    get_number_of_active_users_for_tenant,
    get_number_of_pending_user_for_tenant,
    verify_signup_credential,
    # verify_tenant_registration_otp,
    # verify_tenant_registration_otp_email,
)

router = APIRouter(prefix="/tenants", tags=["tenants"])
LOGGER = logging.getLogger(__name__)


@router.post("/user_invite", dependencies=[Depends(send_invitation_tenant_permission)])
async def user_invite(
    request: UserInvite, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()
    LOGGER.info(f"tenant = {tenant}")
    tenant_active_user_count = get_number_of_active_users_for_tenant(
        db=db, tenant_id=user["tenant_id"]
    )
    tenant_pending_user_count = get_number_of_pending_user_for_tenant(
        db=db, tenant_id=user["tenant_id"]
    )
    max_allowed_user_count = tenant.user_licence - 1
    tenant_user_count = tenant_active_user_count + tenant_pending_user_count

    if tenant_user_count > max_allowed_user_count:
        LOGGER.exception("Tenant License User Count Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant maximum user limit exceed"
        )

    invitation_object = db_tenant.create_user_invite(
        email=request.email, db=db, tenant_id=tenant.id, role=request.system_role
    )
    invitation_email_data = []

    invitation_email_data.append(
        {
            "email": invitation_object.email,
            "link": get_invitation_link(invitation_object.email, tenant.name, tenant.id),
        }
    )
    try:
        # email_service = EmailService(config=Settings())
        await send_invitation_email(user_email_data=invitation_email_data)
        return {"details": "Invitation sent Successfully"}
    except Exception:
        LOGGER.exception("Send Invitation Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error while sending invitation"
        )


@router.post("/user_invitation", dependencies=[Depends(send_invitation_tenant_permission)])
async def user_invitation(
    request: Request, emails: Emails, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    emails = emails.dict().pop("emails")
    tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()
    LOGGER.info(f"tenant = {tenant}")

    email_addresses_that_need_invitation = get_contained_email_addresses_that_need_invitation(
        db=db, email_addresses=emails
    )
    tenant_active_user_count = get_number_of_active_users_for_tenant(db=db, tenant_id=tenant.id)
    tenant_pending_user_count = get_number_of_pending_user_for_tenant(db=db, tenant_id=tenant.id)
    non_verified_email_addresses = get_contained_email_addresses_that_are_unverified(
        db=db, email_addresses=emails
    )
    verified_email_addresses = get_contained_email_addresses_that_are_verified(
        db=db, email_addresses=emails
    )

    if len(verified_email_addresses) > 0:
        LOGGER.error("Received request to send user invitation to already verified user")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already registered with other organization",
        )

    # TODO:
    # Horrible naming here - this is the number of users in the tenant, not the number of users in the invitation
    # Will read much better when the attribute on tenant is renamed to allowed_user_licenses
    # ALSO!!! should reverse the direction for better readability
    # if tenant_active_user_count + len(email_addresses_that_need_invitation) > tenant.allowed_user_licenses:

    max_allowed_user_count = tenant.user_licence
    tenant_user_count = tenant_active_user_count + tenant_pending_user_count

    if tenant_user_count + len(email_addresses_that_need_invitation) > max_allowed_user_count:
        LOGGER.exception("Tenant License User Count Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant maximum user limit exceed"
        )

    invitation_objects = db_tenant.create_user_invitation(
        emails=email_addresses_that_need_invitation, db=db, tenant_id=tenant.id
    )

    unverified_invitation_objects = []
    for email in non_verified_email_addresses:
        invitation = db_tenant.resend_invitation_mail(email=email, db=db, tenant_id=tenant.id)
        unverified_invitation_objects.append(invitation)

    invitation_email_data = []
    for invitation in chain(invitation_objects, unverified_invitation_objects):
        invitation_email_data.append(
            {"email": invitation.email, "link": get_invitation_link(invitation.token)}
        )
    try:
        # email_service = EmailService(config=Settings())
        await send_invitation_email(user_email_data=invitation_email_data)
        return {"details": "Invitation sent Successfully"}
    except Exception:
        LOGGER.exception("Send Invitation Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error while sending invitation"
        )


@router.post("/resend_invite_email", dependencies=[Depends(send_invitation_tenant_permission)])
async def resend_invitation_mail(
    request: Request, email: str, db: Session = Depends(get_db), user=Depends(custom_auth)
):

    LOGGER.info(f"user logged in = {user}")

    user_object = (
        db.query(User)
        .filter(User.email == email)
        .filter(User.tenant_id == user["tenant_id"])
        .first()
    )

    LOGGER.info(f"user object = {user_object}")

    if not user_object:
        LOGGER.error(f"RESEND_INVITATION_EMAIL_USER_DOESNOT_EXIST - {email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cant sent invitation to this user, please try send invitation",
        )

    if user_object.is_email_verified:
        LOGGER.error("User already verified")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified")

    invitation_objects = db_tenant.resend_invitation_mail(
        email=email, db=db, tenant_id=user["tenant_id"]
    )
    invitation = [
        {
            "email": invitation_objects.email,
            "link": get_invitation_link(invitation_objects.token),
        }
    ]
    try:
        email_service = EmailService(config=Settings())
        await send_invitation_email(email_service=email_service, user_email_data=invitation)
        return {"details": "Invitation sent Successfully"}
    except Exception:
        LOGGER.exception("Resend Invite email error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error while sending invite email"
        )


@router.get("/user_invitation/verify/{token}")
def verify_invitation(token: str, db: Session = Depends(get_db)):
    invitation = db_tenant.verify_invitation(token=token, db=db)

    if not invitation:
        LOGGER.error(f"Token expired : {token}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Link Expired")

    response = {"token": token, "email": invitation.email}
    return response


@router.post("/user_invitation/signup")
def setup_user_account(request: UserDetails, db: Session = Depends(get_db)):
    try:
        response, message = verify_signup_credential(request=request, db=db)
        if response:
            # cognito_client = CognitoIdentityProviderWrapper()
            # response = cognito_client.sign_up_user(
            #     user_email=request.email, password=request.password
            # )
            db_tenant.update_user(request, db)
            expire_token(request.dict()["token"], db)
            return {"details": "Signup Successfully"}
    except json.decoder.JSONDecodeError:
        LOGGER.exception("Token is invalid")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token is invalid")
    except Exception as e:
        LOGGER.exception("Error while creating cognito user")
        if "UsernameExistsException" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with same email address already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error while creating cognito user"
        )
    LOGGER.error(message)
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=message)


@router.post("/check_unique_email")
def check_unique_email(email: EmailStr, db: Session = Depends(get_db)):
    email = db_tenant.check_unique_email(email, db)
    if not email:
        return {"status": True}
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="email already exists")


# @router.get("/get-tenant-registration-otp")
# async def send_signup_otp(email: str, db: Session = Depends(get_db)):
#     is_verified = verify_tenant_registration_otp_email(email, db)

#     if is_verified:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail="Email already verified"
#         )

#     otp = generate_otp()
#     otp = db_tenant.get_signup_otp(email, otp, db)
#     try:
#         # email_service = EmailService(config=Settings())
#         await send_otp_email(user_otp_data={"otp": otp, "email": email})
#         return {"details": "otp sent Successfully"}
#     except Exception:
#         LOGGER.exception("Send OTP email error - Invalid Request")
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail="Error while sending otp email"
#         )


@router.post("/register", response_model=CredentialResponseForm)
async def tenant_signup(
    request: TenantUserDetails,
    db: Session = Depends(get_db),
    cognito_client=Depends(cognito_client),
):
    # otp_status = verify_tenant_registration_otp(request.otp, request.email, db)
    # if not otp_status:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP is invalid")

    try:
        cognito_client.sign_up_user(
            user_email=request.email,
            password=request.password,
            phone_number=f"+{request.phone_no}",
            first_name=request.first_name,
            last_name=request.last_name,
        )
        tenant_info = db_tenant.tenant_signup(request=request, db=db)
        # expire_tenant_registration_otp(request.otp, request.email, db)
    except Exception as e:
        LOGGER.exception("Error while creating cognito user")
        if "UsernameExistsException" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with same username already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error while creating cognito user"
        )

    # email_service = EmailService(config=Settings())
    name = f"{request.first_name} {request.last_name}"
    await send_signup_success_email(user_signup_data={"name": name, "email": request.email})
    cognito_initial_auth = cognito_client.authenticate_user(
        user_email=request.email, password=request.password
    )
    cognito_user = cognito_client.get_user(access_token=cognito_initial_auth["AccessToken"])
    cognito_token = cognito_initial_auth["AccessToken"]
    tenant_id = tenant_info["tenant"].id
    user_id = tenant_info["user"].id
    jwt_token = get_custom_jwt_token(
        email=request.email, user_id=user_id, tenant_id=tenant_id, cognito_token=cognito_token
    )
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": tenant_info["user"],
        "client_id": cognito_client.client_id,
        "cognito_user": cognito_user.get("Username"),
    }


@router.post("/resend-cognito-confirmation-code")
async def resend_cognito_confirmation_code(
    request: TenantResend,
    db: Session = Depends(get_db),
    cognito_client=Depends(cognito_client),
):
    cognito_client.resend_confirmation_code(client_id=request.client_id, username=request.username)
    return True


@router.post("/cognito-confirm-signup")
async def cognito_confirm_signup(
    request: TenantConfirm,
    db: Session = Depends(get_db),
    cognito_client=Depends(cognito_client),
):
    cognito_confirm_signup = cognito_client.confirm_signup(
        client_id=request.client_id,
        username=request.username,
        confirmation_code=request.confirmation_code,
    )
    LOGGER.info(f"cognito_confirm_signup {cognito_confirm_signup}")
    return True


# @router.get(
# "/subscription",
# dependencies=[Depends(view_subscription_permission)],
# )
# def get_current_subscription(db: Session = Depends(get_db), user=Depends(custom_auth)):
# tenant = db_tenant.get_tenant_by_id(user["tenant_id"], db=db)
# if not tenant.subscription:
# raise HTTPException(
# status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant does not have any subscription"
# )

# return db_tenant.get_tenant_subscription(tenant_id=user["tenant_id"], db=db)


# @router.get(
# "/transactions",
# dependencies=[Depends(view_subscription_permission)],
# )
# def get_tenant_transactions(db: Session = Depends(get_db), user=Depends(custom_auth)):
# tenant = db_tenant.get_tenant_by_id(user["tenant_id"], db=db)
# if not tenant.subscription:
# raise HTTPException(
# status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant does not have any subscription"
# )

# return {
# "transaction": db_tenant.get_all_tenant_transaction(tenant_id=user["tenant_id"], db=db),
# }


@router.get(
    "/customer_id",
)
def get_customer_id(db: Session = Depends(get_db), user=Depends(custom_auth)):
    tenant = db_tenant.get_tenant_by_id(user["tenant_id"], db=db)
    return tenant.customer_id


@router.get(
    "/user_invites",
)
def get_user_invites(db: Session = Depends(get_db), user=Depends(custom_auth)):
    invites = db_tenant.get_user_invites(user["tenant_id"], db=db)
    return invites


@router.post("/user/register", response_model=CredentialResponseForm)
async def tenant_user_signup(
    request: UserDetails,
    db: Session = Depends(get_db),
    cognito_client=Depends(cognito_client),
):
    # otp_status = verify_tenant_registration_otp(request.otp, request.email, db)
    # if not otp_status:
    #     raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP is invalid")
    # user_info = []
    try:
        cognito_client.sign_up_user(user_email=request.email, password=request.password)
        db_tenant.tenant_user_signup(request=request, db=db)
        # expire_tenant_registration_otp(request.otp, request.email, db)
    except Exception as e:
        LOGGER.exception("Error while updating user")
        if "UsernameExistsException" in str(e):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User with same username already exists",
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Error while creating cognito user"
        )

    # email_service = EmailService(config=Settings())
    name = f"{request.first_name} {request.last_name}"
    await send_signup_success_email(user_signup_data={"name": name, "email": request.email})
    cognito_initial_auth = cognito_client.authenticate_user(
        user_email=request.email, password=request.password
    )
    cognito_user = cognito_client.get_user(access_token=cognito_initial_auth["AccessToken"])
    cognito_token = cognito_initial_auth["AccessToken"]
    existing_user = db.query(User).filter(User.email == request.email).first()
    LOGGER.info(f"user info {existing_user}")
    tenant_id = existing_user.tenant_id
    user_id = existing_user.id
    jwt_token = get_custom_jwt_token(
        email=request.email, user_id=user_id, tenant_id=tenant_id, cognito_token=cognito_token
    )
    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "user": existing_user,
        "client_id": cognito_client.client_id,
        "cognito_user": cognito_user.get("Username"),
    }


@router.post("/verify_recaptcha")
def verify_recaptcha(request: CaptchaToken):
    site_secret = os.getenv("RECAPTCHA_SECRET_KEY")
    captcha_value = request.token
    api_url = f"https://www.google.com/recaptcha/api/siteverify?secret={site_secret}&response={captcha_value}"
    res = requests.get(api_url).json()
    success = res["success"]
    return {"success": success}


@router.get(
    "/webhook_api_key",
)
def get_webhook_api_key(db: Session = Depends(get_db), user=Depends(custom_auth)):
    tenant = db_tenant.get_tenant_by_id(user["tenant_id"], db=db)
    return tenant.webhook_api_key
