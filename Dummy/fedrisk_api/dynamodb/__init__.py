import logging

import boto3
from aiobotocore.session import get_session

from config.config import Settings

from sqlalchemy.orm import Session

from fedrisk_api.db.models import User
from fedrisk_api.s3 import S3Service

LOGGER = logging.getLogger(__name__)

"""
For Asynchronous Events
"""


class DynamoDBService:
    def __init__(self, *args, **kwargs):
        conf = Settings()
        LOGGER.debug(f"Creating DynamoDBService with '{conf}' . . .")
        self.aws_access_key_id = conf.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = conf.AWS_SECRET_ACCESS_KEY
        self.region = conf.AWS_DEFAULT_REGION
        self.session = boto3.Session(
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )
        # self.dynamodb = self.session.resource("dynamodb")
        self.dynamodb_client = boto3.client(
            "dynamodb",
            region_name=self.region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
        )

    async def delete_item_by_partition_key(self, partition_key_value, sort_key_value):
        LOGGER.info(partition_key_value)
        session = get_session()
        key_value = '"' + partition_key_value + '"'
        partition_key = "key"
        sort_key_name = "upload_data"
        # Initialize the DynamoDB client
        async with session.create_client(
            "dynamodb",
            region_name=self.region,
            aws_secret_access_key=self.aws_secret_access_key,
            aws_access_key_id=self.aws_access_key_id,
        ) as client:
            try:
                # Define the partition key for the item you want to delete
                key = {partition_key: {"S": key_value}, sort_key_name: {"S": sort_key_value}}

                LOGGER.info(f" key is {key}")

                # Delete the item from the DynamoDB table
                response = client.delete_item(TableName="Fedrisk_S3_uploads", Key=key)

                LOGGER.info(f"Item deleted: {response}")
            except Exception as e:
                LOGGER.exception(f"Unable to delete from dynamodb {e}")
