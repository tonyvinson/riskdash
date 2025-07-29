import json
import logging
from typing import List
from datetime import datetime, timedelta
import boto3
from botocore.exceptions import ClientError

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status

# from fastapi.exceptions import HTTPException
from jose import jwt
from sqlalchemy.exc import DataError, ProgrammingError
from sqlalchemy.orm import Session, load_only, joinedload
from starlette.status import HTTP_401_UNAUTHORIZED

from config.config import Settings
from fedrisk_api.db import user as db_user
from fedrisk_api.db import role as db_role
from fedrisk_api.db.database import get_db
from fedrisk_api.db.models import User, Tenant, Role
from fedrisk_api.s3 import S3Service, get_profile_s3_key
from fedrisk_api.dynamodb import DynamoDBService
from fedrisk_api.schema.user import (
    CredentialRequestFormCIUser,
    CredentialRequestForm,
    # CredentialResponseForm,
    DisplayUser,
    UpdateUserPassword,
    UpdateUserProfile,
    UpdateUserRole,
    ForgotPassword,
    ConfirmForgotPassword,
    # GetMFACode,
    # UseMFACode,
    # VerifyMFACode,
    MfaChallengeRequest,
    ResendConfirmationCodeRequestForm,
    TmpUserPasswordMfa,
    EmailTempPassword,
    UpdateSystemRole,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.cognito import CognitoIdentityProviderWrapper
from fedrisk_api.utils.utils import PaginateResponse, pagination, filter_by_tenant

from fedrisk_api.db.util.encrypt_pii_utils import decrypt_user_fields

from fedrisk_api.utils.email_util import send_temp_password

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])


# Read all users
@router.get("/", response_model=PaginateResponse[DisplayUser])
def get_all_users(
    q: str = None,
    offset: int = 0,
    limit: int = 10,
    filter_by: str = None,
    filter_value: str = None,
    sort_by: str = "email",
    db: Session = Depends(get_db),
    user: str = Depends(custom_auth),
    # cognito_client=Depends(cognito_client),
):
    try:
        LOGGER.info(f"custom auth {custom_auth}")
        queryset = db_user.get_all_users(
            db=db,
            user=user,
            q=q,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_value=filter_value,
            # cognito_client=cognito_client,
        )
        result = pagination(query=queryset, limit=limit, offset=offset)
        result["items"] = [decrypt_user_fields(u) for u in result["items"]]
        return result

    except DataError:
        LOGGER.exception("Get User Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Please provide correct filter_value"
        )
    except ProgrammingError:
        LOGGER.exception("Get User Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Please provide correct order field value"
        )
    except AttributeError:
        LOGGER.exception("Get User Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct filter_by field value",
        )


# Read user
@router.get("/{id}/", response_model=DisplayUser)
def get_user_by_id(id: int, db: Session = Depends(get_db), user: str = Depends(custom_auth)):
    # tenant_id = user["tenant_id"]

    user = db.query(User).options(joinedload(User.system_roles)).filter(User.id == id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id '{id}' does not exist"
        )

    return user


# Read users and roles
@router.get("/tenant/roles/")
def get_tenant_user_roles(db: Session = Depends(get_db), user: str = Depends(custom_auth)):
    users = db_user.get_tenant_user_roles(db, user["tenant_id"])
    if not users:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Users do not exist")

    return users


@router.put("/{id}/update_profile")
def update_user_profile_by_id(
    id: int,
    request: UpdateUserProfile,
    db: Session = Depends(get_db),
    user: str = Depends(custom_auth),
):
    try:
        response = db_user.update_user_profile_by_id(
            id=id, request=request, user_id=user["user_id"], db=db
        )
        LOGGER.info(f"user update response {response}")
        LOGGER.info(f"update user request {request}")
        cognito_client = CognitoIdentityProviderWrapper()
        phone_number = "+" + request.phone_no
        cognito_response = cognito_client.update_user_attributes(
            request.last_name, request.first_name, phone_number, user["cognito_token"]
        )
        LOGGER.info(f"cognito update response {cognito_response}")
        return response

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User with specified id does not exists"
        )
    # return {"detail": "Successfully updated profile"}


@router.put("/{id}/update_profile_picture")
async def update_profile_picture(
    id: int, profile_picture: UploadFile, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    allowedFiles = {
        "image/jpg",
        "image/jpeg",
        "image/png",
        "image/gif",
        "image/tiff",
        "image/bmp",
        "video/webm",
    }
    s3_service = S3Service()
    dynamodb_service = DynamoDBService()

    if profile_picture.content_type not in allowedFiles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Image format not allowed"
        )

    # get s3 bucket for tenant
    tenant = db.query(Tenant).filter(Tenant.id == user["tenant_id"]).first()

    user_obj = db.query(User).filter(User.id == id).first()

    # delete previous picture
    if user_obj.profile_picture is not None and user_obj.profile_picture != "":
        file_key = f"{user_obj.s3_bucket}{user_obj.profile_picture}"
        try:
            size = 0
            scan_result = ""
            # LOGGER.info(f"file_key {file_key}")
            try:
                response = s3_service.get_object_tags(tenant.s3_bucket, file_key)
                # Extract tags from the response
                tags = response.get("TagSet", [])
                if tags:
                    # print("Tags for the object:")
                    for tag in tags:
                        # print(f"Key: {tag['Key']}, Value: {tag['Value']}")
                        if tag["Key"] == "ScanResult":
                            scan_result = tag["Value"]
                else:
                    print("No tags found for the object.")
                try:
                    response_contents = await s3_service.list_objects(tenant.s3_bucket)
                    # LOGGER.info(response_contents)
                    for page in response_contents:
                        if "Contents" in page:
                            for obj in page["Contents"]:
                                # print(f"object {obj}")
                                # print(f"Key: {obj['Key']}, Size: {obj['Size']} bytes")
                                if obj["Key"] == file_key:
                                    size = obj["Size"]
                        else:
                            print("No objects found on this page.")
                    # size = object['ContentLength']
                    sort_key = (
                        '{"bucket": "'
                        + tenant.s3_bucket
                        + '", "size": "'
                        + str(size)
                        + '", "scan_result": "'
                        + scan_result
                        + '"}'
                    )
                    LOGGER.info(f"sort key {sort_key}")
                    # Delete DynamoDB reference
                    await dynamodb_service.delete_item_by_partition_key(file_key, sort_key)
                    try:
                        await s3_service.delete_fileobj(bucket=tenant.s3_bucket, key=file_key)
                    except Exception:
                        LOGGER.exception("Could not delete user profile picture")
                        raise AssertionError("Could not delete user profile picture")
                except Exception:
                    LOGGER.exception("Could not list objects for s3 bucket")
                    raise AssertionError("Could not list objects for s3 bucket")
            except Exception:
                LOGGER.exception("Could not find object with tags")
                raise AssertionError("Could not find object with tags")
        except Exception:
            LOGGER.exception("Unable to delete previous profile picture")
            raise AssertionError("Unable to delete previous profile picture")

    filename = profile_picture.filename
    new_filename = (
        str(uuid.uuid4())
        + (datetime.utcnow().strftime("-%Y-%m-%d-%I-%M-%S"))
        + "."
        + filename.split(".")[1]
    )

    # compressed_image = await compress_image(profile_picture, max_size_mb=20, quality=20)

    response = db_user.update_profile_picture(user_id=id, profile_picture=new_filename, db=db)

    if not response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Upload profile picture error"
        )

    try:
        # if not compressed_image:
        new_file_key = f"{user_obj.s3_bucket}{new_filename}"
        uploaded_successfully = await s3_service.upload_fileobj(
            bucket=tenant.s3_bucket,
            key=new_file_key,
            fileobject=profile_picture.file._file,
        )

        if uploaded_successfully:
            # Get object tags
            response = s3_service.get_object_tags(tenant.s3_bucket, new_file_key)
            # Extract tags from the response
            tags = response.get("TagSet", [])
            if tags:
                print("Tags for the object:")
                for tag in tags:
                    print(f"Key: {tag['Key']}, Value: {tag['Value']}")
            else:
                print("No tags found for the object.")
            return {"status": "Successfully updated profile picture"}
        # else:
        #     # append jpeg extension
        #     # file_key_with_jpeg = new_filename.split(".")[0] + ".jpeg"
        #     new_file_key = f"{user_obj.s3_bucket}{new_filename}"
        #     uploaded_successfully = await s3_service.upload_fileobj(
        #         bucket=tenant.s3_bucket,
        #         key=new_file_key,
        #         fileobject=compressed_image,
        #     )

        #     if uploaded_successfully:
        #         return {"status": "Successfully updated profile picture"}

    except AssertionError as assertion_error:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(assertion_error),
        )

    except Exception:
        LOGGER.exception("S3 Upload profile picture  Error - Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unable to upload profile Due to connection error",
        )

    LOGGER.error("S3 Upload profile picture   Error - Invalid Request")
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to upload in S3")


@router.put("/{id}/remove_profile_picture")
async def remove_profile_picture(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    if id != user["user_id"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with specified id does not matched with logged in user",
        )
    user = db.query(User).filter(User.id == user["user_id"]).first()
    current_profile_picture = user.profile_picture
    removed_status = db_user.remove_profile_picture(user_id=id, db=db)
    file_key = f"{user.s3_bucket}{current_profile_picture}"

    if removed_status and current_profile_picture:
        try:
            s3_service = S3Service()
            await s3_service.delete_fileobj(bucket=user.s3_bucket, key=file_key)
        except Exception:
            LOGGER.exception("S3 delete profile picture Error")

    if not status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Upload profile picture error"
        )
    return {"status": "Successfully removed profile picture"}


@router.post("/{id}/activate_user")
def activate_user(id: int, db: Session = Depends(get_db), user: str = Depends(custom_auth)):
    db_status, db_status_code, message = db_user.activate_user(id=id, user=user, db=db)
    if db_status:
        return {"detail": message}

    LOGGER.error(message)
    raise HTTPException(
        status_code=db_status_code,
        detail=message,
    )


# deactivate user
@router.delete("/{id}")
def deactivate_user(id: int, db: Session = Depends(get_db), user: str = Depends(custom_auth)):
    response = db_user.deactivate_user(id=id, user=user, db=db)
    if response:
        return {"detail": "Successfully deactivated User"}

    LOGGER.error("User does not exist")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="User with specified id does not exists"
    )


@router.post("/{id}/make_system_admin")
def make_user_tenant_admin(
    id: int, db: Session = Depends(get_db), user: str = Depends(custom_auth)
):
    response = db_user.make_user_tenant_admin(id=id, user=user, db=db)
    if response:
        return {"detail": "Successfully created user as admin"}

    LOGGER.error("User does not exist")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="User with specified id does not exists"
    )


# user log in no mfa - ci users only
@router.post(
    "/get-token",  # response_model=CredentialResponseForm#
)
async def get_token(
    request: Request, form_data: CredentialRequestFormCIUser, db: Session = Depends(get_db)
):
    """
    Authenticate CI user process by providing the username and password.
    This api will return a session token which can be used with subsequent endpoints.
    """
    client = CognitoIdentityProviderWrapper()
    try:
        # result = client.authenticate_user(form_data.email.lower(), form_data.password)
        result = await client.authenticate_user(form_data.username.lower(), form_data.password)
        token = jwt.encode(
            {
                "user_id": 0,
                "email": "cicd@riskuity.com",
                "tenant_id": 1,
                "cognito_token": result["AccessToken"],
                "cognito_refresh_token": result["RefreshToken"],
                "exp": datetime.utcnow() + timedelta(days=1),
            },
            Settings().FEDRISK_JWT_SECRET_KEY,
            algorithm="HS256",
        )
        return {
            "access_token": token,
            "token_type": "bearer",
            "status": "SUCCESS",
        }

    except Exception as e:
        LOGGER.exception(
            f"Unable to authenticate user,"
            f"url : {request.url}, "
            f"username : {form_data.username}, "
        )
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(e))


# get user custom token
@router.post(
    "/get-auth-token",  # response_model=CredentialResponseForm#
)
def get_auth_token(
    request: Request, form_data: CredentialRequestForm, db: Session = Depends(get_db)
):
    """
    Authenticate user by providing the email and password.
    This api will return a session token which we can use with MFA.
    """
    client = CognitoIdentityProviderWrapper()
    try:
        # result = client.authenticate_user(form_data.email.lower(), form_data.password)
        result = client.start_sign_in(form_data.email.lower(), form_data.password)
    except Exception as e:
        LOGGER.exception(
            f"Unable to authenticate user," f"url : {request.url}, " f"email : {form_data.email}, "
        )
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(e))

    LOGGER.info(f"result {result}")

    return result


# get user custom token
@router.post(
    "/resend_confirmation_code",  # response_model=CredentialResponseForm#
)
def resend_confirmation_code(
    request: Request, form_data: ResendConfirmationCodeRequestForm, db: Session = Depends(get_db)
):
    """
    Resend the confirmation code to a user.
    """
    client = CognitoIdentityProviderWrapper()
    try:
        # result = client.authenticate_user(form_data.email.lower(), form_data.password)
        result = client.resend_confirmation_code(form_data.username.lower())
    except Exception as e:
        LOGGER.exception(f"Unable to resend code")
        raise HTTPException(status_code=HTTP_401_UNAUTHORIZED, detail=str(e))

    LOGGER.info(f"result {result}")

    return result


@router.post("/respond_to_mfa_challenge")
def respond_to_mfa_challenge(req: MfaChallengeRequest, db: Session = Depends(get_db)):
    client = CognitoIdentityProviderWrapper()

    # if req.challenge_type not in ["SOFTWARE_TOKEN_MFA", "SMS_MFA"]:
    #     raise HTTPException(status_code=400, detail="Unsupported MFA challenge type.")

    try:
        resp = client.respond_to_mfa_challenge(
            user_name=req.username,
            session=req.session,
            mfa_code=req.mfa_code,
            challenge_name=req.challenge_type,
            new_password=None,
        )
        # LOGGER.info(resp)
        auth_result = resp.get("AccessToken")
        if not auth_result:
            raise HTTPException(status_code=401, detail="MFA challenge failed.")
        user = (
            db.query(User)
            .options(joinedload(User.system_roles))
            .filter(User.email == req.email.lower())
            .first()
        )
        # role = db.query(Role).filter(Role.id == user.system_role).first()
        # user.system_role_name = role.name
        # db_user = db.query(User).filter(User.email == req.email.lower()).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        token = jwt.encode(
            {
                "email": user.email,
                "user_id": user.id,
                # "system_role": user.system_role,
                # "system_roles": user.system_roles,
                "is_superuser": user.is_superuser,
                "is_tenant_admin": user.is_tenant_admin,
                "tenant_id": user.tenant_id,
                "cognito_token": resp["AccessToken"],
                "cognito_refresh_token": resp["RefreshToken"],
                "exp": datetime.utcnow() + timedelta(days=1),
            },
            Settings().FEDRISK_JWT_SECRET_KEY,
            algorithm="HS256",
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "status": "SUCCESS",
            "user": {
                "id": user.id,
                "system_role": 1,
                "is_superuser": user.is_superuser,
                "is_tenant_admin": user.is_tenant_admin,
                "is_active": user.is_active,
                "tenant_id": user.tenant_id,
                "email": user.email,
                # "system_roles": user.system_roles,
            },
        }

    except ClientError as e:
        LOGGER.error("MFA challenge failed for %s: %s", req.username, e)
        raise HTTPException(status_code=401, detail="Invalid MFA code or session")


@router.get("/check_unique_username")
def check_unique_username(key: str, username: str, db: Session = Depends(get_db)):
    try:
        user = db_user.check_unique_username(db, username)
    except json.decoder.JSONDecodeError:
        LOGGER.exception("Key is invalid")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Key is invalid")

    # return 200 if user does not exist in db
    if not user:
        return {"status": True}
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists")


@router.put("/{id}/password_mfa")
def password_change(
    id: int,
    request: CredentialRequestForm,
    db: Session = Depends(get_db),
    user: str = Depends(custom_auth),
):
    user = db.query(User).filter(User.id == id).first()

    client = CognitoIdentityProviderWrapper()

    try:
        # client.change_user_password(user.email, request.current_password, request.new_password)
        response = client.verify_password(request.email, request.password)
        return response
    except Exception as e:
        LOGGER.exception("Unable to verify password for MFA for user")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{id}/change_password")
def password_change(
    id: int,
    request: UpdateUserPassword,
    db: Session = Depends(get_db),
    user: str = Depends(custom_auth),
):
    user = db.query(User).filter(User.id == user["user_id"]).first()

    client = CognitoIdentityProviderWrapper()

    try:
        client.admin_update_user_pasword(user.email, request.new_password, request.access_token)
        # client.change_user_password(user.email, request.current_password, request.new_password, request.access_token)
        return {"details": "Successfully changed User password"}
    except Exception as e:
        LOGGER.exception("Unable to change password for user")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/email_temporary_password")
async def email_temp_password(request: EmailTempPassword):
    client = CognitoIdentityProviderWrapper()

    try:
        temp_password_resp = await client.admin_set_temp_user_pasword(email=request.email)
        LOGGER.info(temp_password_resp)

        payload = {
            "subject": "Password Confirmation Code",
            "email": request.email,
            "tmp_password": temp_password_resp["temp_password"],
        }

        await send_temp_password(payload)
        # return {"details": "Successfully sent temporary password"}
        LOGGER.info("Successfully sent temporary password")
        return temp_password_resp["authorization"]

    except Exception as e:
        LOGGER.exception("Unable to send temporary password for user")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/respond_to_temp_pass_challenge")
async def respond_to_temp_pass_challenge(
    request: TmpUserPasswordMfa,
):
    client = CognitoIdentityProviderWrapper()

    try:
        client.respond_to_mfa_challenge(
            user_name=request.username,
            session=request.session,
            mfa_code=request.mfa_code,
            challenge_name=request.challenge_name,
            new_password=request.new_password,
        )

        # return {"details": "Successfully sent temporary password"}
        LOGGER.info("Successfully responded to MFA challenge for updating password")
        return {"message": "Successfully updated password"}

    except Exception as e:
        LOGGER.exception("Unable to update password for user")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/change_password_tmp_password")
def password_change_tmp_password(
    request: UpdateUserPassword,
    db: Session = Depends(get_db),
    user: str = Depends(custom_auth),
):
    # user = db.query(User).filter(User.id == user["user_id"]).first()

    client = CognitoIdentityProviderWrapper()

    try:
        # client.admin_update_user_pasword(user.email, request.new_password, request.access_token)
        client.change_user_password(
            user.email, request.current_password, request.new_password, request.access_token
        )
        return {"details": "Successfully changed User password"}
    except Exception as e:
        LOGGER.exception("Unable to change password for user")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.delete("/{id}/delete")
def delete_user(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    if id == user["user_id"]:
        LOGGER.error("User trying to delete itself")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Tenant admin can not delete itself"
        )
    response, status_code, message = db_user.delete_user(user_id=id, db=db, user=user)

    if not response:
        LOGGER.error("Error while deleting user")
        raise HTTPException(status_code=status_code, detail=message)

    return {"details": message}


@router.get("/get_users_tenant")
def get_users_tenant(db: Session = Depends(get_db), user=Depends(custom_auth)):
    users = filter_by_tenant(db, User, user["tenant_id"]).all()
    decrypted_users = [decrypt_user_fields(u) for u in users]
    return decrypted_users


@router.get("/get_active_users_tenant")
def get_active_users_tenant(db: Session = Depends(get_db), user=Depends(custom_auth)):
    users = (
        filter_by_tenant(db, User, user["tenant_id"])
        .filter(User.is_active == True)
        .options(
            load_only(User.id, User.email, User.first_name, User.last_name)
        )  # Only load needed fields
        .all()
    )
    decrypted_users = [decrypt_user_fields(u) for u in users]
    return decrypted_users


@router.post("/roles/update")
def update_system_roles_bulk(
    request: List[UpdateSystemRole], db: Session = Depends(get_db), user=Depends(custom_auth)
):
    response = db_user.update_bulk_user_system_roles(request=request, db=db)
    if not response:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Could not complete the request"
        )
    return {"detail": "Successfully updated user system roles"}


# @router.post("/roles/update/{id}")
# def update_system_role_by_id(
#     request: UpdateSystemRole, db: Session = Depends(get_db), user=Depends(custom_auth)
# ):
#     response = db_user.update_user_system_role_by_id(
#         request=request, db=db
#     )
#     if not response:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST, detail="Could not complete the request"
#         )
#     return {"detail": "Successfully updated user system roles"}


@router.post("/reset_password")
def user_reset_password(
    request: ForgotPassword,
):

    client = CognitoIdentityProviderWrapper()
    try:
        return client.user_forgot_password(user_email=request.email)
    except Exception as e:
        LOGGER.exception("Unable to reset password for user")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/confirm_reset_password")
def user_confirm_reset_password(
    request: ConfirmForgotPassword,
):

    client = CognitoIdentityProviderWrapper()
    try:
        return client.user_confirm_forgot_password(
            user_email=request.email,
            confirmation_code=request.confirmation_code,
            password=request.password,
        )
    except Exception as e:
        LOGGER.exception("Unable to reset password for user")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/users_tenant/deactivate")
def users_tenant_deactivate(db: Session = Depends(get_db), user=Depends(custom_auth)):
    users = (
        filter_by_tenant(db, User, user["tenant_id"])
        .filter(User.system_role != 5)
        .filter(User.system_role != 6)
        .all()
    )
    return db_user.deactivate_users(users, db)
