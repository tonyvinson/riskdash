import logging

import boto3
from aiobotocore.session import get_session

from config.config import Settings

from sqlalchemy.orm import Session

from fedrisk_api.db.models import User

from botocore.exceptions import ClientError

from botocore.client import Config

LOGGER = logging.getLogger(__name__)

"""
For Asynchronous Events
"""
PROFILE_FOLDER = "profile"

BUCKET_NAME = "fedriskapi-documents-bucket"


def get_profile_s3_key(profile_picture_name: str):
    return f"{profile_picture_name}"


class S3Service:
    def __init__(self, *args, **kwargs):
        conf = Settings()
        LOGGER.debug(f"Creating S3Service with '{conf}' . . .")
        self.aws_access_key_id = conf.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = conf.AWS_SECRET_ACCESS_KEY
        self.region = conf.AWS_DEFAULT_REGION
        self.session = boto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        self.s3 = self.session.resource("s3")
        self.s3_resource = self.session.resource("s3")
        self.s3_client = boto3.client(
            "s3",
            region_name=self.region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            config=Config(signature_version="s3v4"),  # <-- explicitly set Signature Version 4
        )

    async def upload_fileobj(self, fileobject, bucket, key):
        session = get_session()
        LOGGER.info(f"aws acess key {self.aws_access_key_id}")
        async with session.create_client(
            "s3",
            region_name=self.region,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_access_key_id=self.aws_access_key_id,
        ) as client:
            file_upload_response = await client.put_object(Bucket=bucket, Key=key, Body=fileobject)

            if file_upload_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                LOGGER.info(
                    f"File uploaded path : https://{bucket}.s3.{self.region}.amazonaws.com/{key}"
                )
                return True
        return False

    async def delete_fileobj(self, bucket, key):
        session = get_session()
        async with session.create_client(
            "s3",
            region_name=self.region,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_access_key_id=self.aws_access_key_id,
        ) as client:
            file_delete_response = await client.delete_object(Bucket=bucket, Key=key)
            if file_delete_response["ResponseMetadata"]["HTTPStatusCode"] == 200:
                LOGGER.info(
                    f"File deleted path : https://{bucket}.s3.{self.region}.amazonaws.com/{key}"
                )
                return True
        return False

    async def list_buckets(self):
        """[List existing buckets]
        Returns:
            [dict]: [List of buckets]
        """
        buckets = []
        for bucket in self.s3_resource.buckets.all():
            buckets.append(bucket.name)
        return buckets

    async def create_bucket(self, bucket_name: str):
        """Create an S3 bucket in a specified region
        If a region is not specified, the bucket is created in the S3 default
        region (us-east-1).
        Args:
            bucket_name (str): [Bucket name to create bucket in s3]
        :param bucket_name: Bucket to create
        :param region: String region to create bucket in, e.g., 'us-west-2'
        :return: True if bucket created, else False
        """
        # Create bucket
        # s3_resource = self.session.resource("s3")
        try:
            if self.region is None:
                self.s3_resource.create_bucket(Bucket=bucket_name)
            else:
                location = {"LocationConstraint": self.region}

                self.s3_resource.create_bucket(
                    Bucket=bucket_name, CreateBucketConfiguration=location
                )

        except Exception:
            LOGGER.exception("Error while creating S3 Bucket")
            return False
        return True

    async def list_objects(self, bucket_name, prefix: str = None):
        """[List objects in Bucket]
        Args:
            bucket_name ([str]): [Name of Bucket]
            prefix (str, optional): [Prefix parameter used to filter the paginated results by prefix server-side before sending them to the client]. Defaults to None.
        Returns:
            [Iterator]: [PageIterator]
        """

        operation_parameters = {"Bucket": bucket_name}

        if prefix:
            operation_parameters = operation_parameters["Prefix"] = prefix

        paginator = self.s3_client.get_paginator("list_objects")

        page_iterator = paginator.paginate(**operation_parameters)

        return page_iterator

    def get_profile_picture_image_url(self, expire_time, tenant, s3_key):
        # my_array = list(values.values())
        LOGGER.info(s3_key)
        # s3_key = f"{my_array[5]}{profile_picture_name}"
        return self.s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": tenant.s3_bucket, "Key": s3_key},
            ExpiresIn=expire_time,
        )

    def get_digital_signature_image_url(self, expire_time, tenant, s3_key):
        LOGGER.info(f"Generating presigned URL with bucket={tenant.s3_bucket}, key={s3_key}")

        # my_array = list(values.values())
        LOGGER.info(s3_key)
        # s3_key = f"{my_array[5]}{profile_picture_name}"
        return self.s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": tenant.s3_bucket, "Key": s3_key},
            ExpiresIn=expire_time,
        )

    # async def get_file_object(self, bucket, key):
    #     return self.s3_client.get_object(Bucket=bucket, Key=key)

    # def get_object_tags(self, bucket_name, key):
    #     results = self.s3_client.get_object_tagging(Bucket=bucket_name, Key=key)
    #     return results

    def list_keys(self, bucket, prefix=""):
        """List all keys in the given S3 bucket under the specified prefix."""
        try:
            paginator = self.s3.get_paginator("list_objects_v2")
            keys = []
            for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
                contents = page.get("Contents", [])
                for obj in contents:
                    keys.append(obj["Key"])
            return keys
        except ClientError as e:
            LOGGER.error(f"Failed to list keys in bucket {bucket}: {e}")
            return []

    def key_exists(self, bucket: str, key: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=bucket, Key=key)  # ✅ use client not resource
            return True
        except self.s3_client.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            raise

    def get_object_tags(self, bucket, key):
        """Get tags from a given S3 object."""
        try:
            return self.s3_client.get_object_tagging(Bucket=bucket, Key=key)
        except ClientError as e:
            LOGGER.error(f"Failed to get tags for key {key}: {e}")
            return {"TagSet": []}

    async def get_file_object(self, bucket, key):
        """Fetch object from S3 for processing."""
        try:
            return self.s3_client.get_object(Bucket=bucket, Key=key)
        except ClientError as e:
            LOGGER.error(f"Failed to fetch S3 file {key} from bucket {bucket}: {e}")
            raise
