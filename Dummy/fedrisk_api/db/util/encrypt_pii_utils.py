import boto3
import binascii
from fedrisk_api.db.models import User  # update import to your actual User model path
from sqlalchemy.orm.session import Session as SessionLocal
import os

# AWS KMS setup
kms_client = boto3.client("kms")
KMS_KEY_ID = os.getenv("AWS_KMS_KEY_ID")  # Replace with your actual AWS KMS Key ID


def encrypt_value(value: str) -> str:
    if not value:
        return value
    response = kms_client.encrypt(
        KeyId=KMS_KEY_ID,
        Plaintext=value.encode("utf-8"),
    )
    return response["CiphertextBlob"].hex()


def decrypt_value(encrypted_hex: str) -> str:
    if not encrypted_hex:
        return encrypted_hex
    try:
        binary_blob = bytes.fromhex(encrypted_hex)
        response = kms_client.decrypt(CiphertextBlob=binary_blob)
        return response["Plaintext"].decode("utf-8")
    except (binascii.Error, kms_client.exceptions.InvalidCiphertextException) as e:
        print(f"Error decrypting value: {e}")
        return encrypted_hex


def encrypt_user_data(db: SessionLocal):
    users = db.query(User).all()
    for user in users:

        if user.first_name and not user.first_name.startswith("ENC::"):
            user.first_name = f"ENC::{encrypt_value(user.first_name)}"
        if user.last_name and not user.last_name.startswith("ENC::"):
            user.last_name = f"ENC::{encrypt_value(user.last_name)}"
        if user.phone_no and not user.phone_no.startswith("ENC::"):
            user.phone_no = f"ENC::{encrypt_value(user.phone_no)}"
        # Add more fields as needed...

    db.commit()
    print("User data encrypted and saved.")


def decrypt_user_data(db: SessionLocal):
    users = db.query(User).all()
    for user in users:

        if user.first_name and user.first_name.startswith("ENC::"):
            encrypted_part = user.first_name[5:]
            user.first_name = decrypt_value(encrypted_part)

        if user.last_name and user.last_name.startswith("ENC::"):
            encrypted_part = user.last_name[5:]
            user.last_name = decrypt_value(encrypted_part)

        if user.phone_no and user.phone_no.startswith("ENC::"):
            encrypted_part = user.phone_no[5:]
            user.phone_no = decrypt_value(encrypted_part)

    db.commit()
    print("User data decrypted and saved.")


def encrypt_user_by_id(db: SessionLocal, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        print(f"User with ID {user_id} not found.")
        return

    if user.first_name and not user.first_name.startswith("ENC::"):
        user.first_name = f"ENC::{encrypt_value(user.first_name)}"
    if user.last_name and not user.last_name.startswith("ENC::"):
        user.last_name = f"ENC::{encrypt_value(user.last_name)}"
    if user.phone_no and not user.phone_no.startswith("ENC::"):
        user.phone_no = f"ENC::{encrypt_value(user.phone_no)}"

    db.commit()
    print(f"User {user_id} encrypted.")


def decrypt_user_by_id(db: SessionLocal, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        print(f"User with ID {user_id} not found.")
        return

    if user.first_name and user.first_name.startswith("ENC::"):
        encrypted_part = user.first_name[5:]
        user.first_name = decrypt_value(encrypted_part)
    if user.last_name and user.last_name.startswith("ENC::"):
        encrypted_part = user.last_name[5:]
        user.last_name = decrypt_value(encrypted_part)
    if user.phone_no and user.phone_no.startswith("ENC::"):
        encrypted_part = user.phone_no[5:]
        user.phone_no = decrypt_value(encrypted_part)

    db.commit()
    print(f"User {user_id} decrypted.")


def get_decrypted_user_display_by_id(db: SessionLocal, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        print(f"User with ID {user_id} not found.")
        return None

    decrypted_user = {
        "id": user.id,
        "email": user.email,
        "first_name": (
            decrypt_value(user.first_name[5:])
            if user.first_name and user.first_name.startswith("ENC::")
            else user.first_name
        ),
        "last_name": (
            decrypt_value(user.last_name[5:])
            if user.last_name and user.last_name.startswith("ENC::")
            else user.last_name
        ),
        "phone_no": (
            decrypt_value(user.phone_no[5:])
            if user.phone_no and user.phone_no.startswith("ENC::")
            else user.phone_no
        ),
    }

    print(decrypted_user)

    return decrypted_user


def decrypt_user_fields(user_obj):
    if not user_obj:
        return None

    def maybe_decrypt(value):
        return decrypt_value(value[5:]) if value and value.startswith("ENC::") else value

    return {
        "id": user_obj.id,
        "email": user_obj.email,
        "first_name": maybe_decrypt(user_obj.first_name),
        "last_name": maybe_decrypt(user_obj.last_name),
        "phone_no": maybe_decrypt(user_obj.phone_no),
        "tenant_id": user_obj.tenant_id,
        "is_superuser": user_obj.is_superuser,
        "is_tenant_admin": user_obj.is_tenant_admin,
        "is_email_verified": user_obj.is_email_verified,
        "is_active": user_obj.is_active,
        "status": user_obj.status,
        "system_role": user_obj.system_role,
        "s3_bucket": user_obj.s3_bucket,
        "profile_picture": user_obj.profile_picture,
    }
