import logging

from sqlalchemy.orm import Session

from fedrisk_api.db.models import DigitalSignature, ApprovalDigitalSignature, User, Tenant
from fedrisk_api.schema.digital_signature import (
    CreateDigitalSignature,
    CreateApprovalDigitalSignature,
)

from fedrisk_api.s3 import S3Service
from fedrisk_api.dynamodb import DynamoDBService


LOGGER = logging.getLogger(__name__)


# digital_signature
async def create_digital_signature(db: Session, digital_signature: CreateDigitalSignature):
    my_new_digital_signature_dict = digital_signature.dict()
    new_digital_signature = DigitalSignature(**my_new_digital_signature_dict)
    db.add(new_digital_signature)
    db.commit()
    return new_digital_signature


async def create_approval_digital_signature(
    db: Session, approval_digital_signature: CreateApprovalDigitalSignature
):
    my_new_approval_digital_signature_dict = approval_digital_signature.dict()
    new_approval_digital_signature = ApprovalDigitalSignature(
        **my_new_approval_digital_signature_dict
    )
    db.add(new_approval_digital_signature)
    db.commit()
    return new_approval_digital_signature


def get_all_digital_signatures_by_approval_id(
    db: Session,
    approval_id: int,
):
    digital_signatures = (
        db.query(DigitalSignature)
        .join(ApprovalDigitalSignature)
        .filter(ApprovalDigitalSignature.approval_id == approval_id)
        .all()
    )

    return digital_signatures


def get_all_digital_signatures_by_user_id(
    db: Session,
    user_id: int,
):
    digital_signatures = (
        db.query(DigitalSignature).filter(DigitalSignature.user_id == user_id).all()
    )

    return digital_signatures


def get_digital_signature_by_id(db: Session, digital_signature_id: int):
    queryset = (
        db.query(DigitalSignature).filter(DigitalSignature.id == digital_signature_id).first()
    )
    return queryset


async def delete_digital_signature_by_id(db: Session, digital_signature_id: int):
    s3_service = S3Service()
    dynamodb_service = DynamoDBService()
    digital_signature = (
        db.query(DigitalSignature).filter(DigitalSignature.id == digital_signature_id).first()
    )

    LOGGER.info(digital_signature)

    if not digital_signature:
        return False

    # delete previous picture
    if digital_signature.filename is not None:
        user = db.query(User).filter(User.id == digital_signature.user_id).first()
        tenant = db.query(Tenant).filter(Tenant.id == user.tenant_id).first()
        file_key = f"{user.s3_bucket}{digital_signature.filename}"
        try:
            size = 0
            scan_result = ""
            LOGGER.info(f"file_key {file_key}")
            try:
                response = s3_service.get_object_tags(tenant.s3_bucket, file_key)
                LOGGER.info(response)
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
                                if obj["Key"] == file_key:
                                    size = obj["Size"]
                        else:
                            print("No objects found on this page.")
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
                        LOGGER.exception("Could not delete user digital signature")
                        raise AssertionError("Could not delete user digital signature")
                except Exception:
                    LOGGER.exception("Could not list objects for s3 bucket")
                    raise AssertionError("Could not list objects for s3 bucket")
            except Exception:
                LOGGER.exception("Could not find object with tags")
                raise AssertionError("Could not find object with tags")
        except Exception:
            LOGGER.exception("Unable to delete previous user digital signature")
            raise AssertionError("Unable to delete previous user digital signature")

    # delete all assocations
    db.query(ApprovalDigitalSignature).filter(
        ApprovalDigitalSignature.digital_signature_id == digital_signature_id
    ).delete()
    db.delete(digital_signature)
    db.commit()
    return True


def delete_approval_digital_signature_by_id(db: Session, digital_signature_id: int):
    approval_digital_signature = (
        db.query(ApprovalDigitalSignature)
        .filter(ApprovalDigitalSignature.digital_signature_id == digital_signature_id)
        .first()
    )

    if not approval_digital_signature:
        return False

    db.delete(approval_digital_signature)
    db.commit()
    return True
