import os
from pathlib import Path

from botocore.config import Config
from pydantic import Field, BaseSettings

# from pydantic_settings import BaseSettings

from fedrisk_api import __version__ as fedrisk_api_version


class Settings(BaseSettings):
    ENVIRONMENT: str = Field("local", env="ENVIRONMENT")
    PROJECT_TITLE: str = "Riskuity API"
    PROJECT_VERSION: str = f"{fedrisk_api_version}"
    RDS_USER: str = Field("fedrisk", env="RDS_USERNAME")
    RDS_PASSWORD: str = Field("fedrisk", env="RDS_PASSWORD")
    RDS_HOST: str = Field("localhost", env="RDS_HOSTNAME")
    RDS_PORT: str = Field("5432", env="RDS_PORT")
    RDS_DB: str = Field("fedrisk", env="RDS_DB_NAME")
    FEDRISK_JWT_SECRET_KEY: str = Field(
        ..., env=["FEDRISK_JWT_SECRET_KEY", "CUSTOM_JWT_TOKEN_SECRET_KEY"]
    )
    FRONTEND_SERVER_URL: str = Field(..., env=["FRONTEND_SERVER_URL", "FE_SERVER_URL"])
    INVITE_LINK_EXPIRE_TIME_IN_DAYS: str = Field(
        "1", env=["INVITE_LINK_EXPIRE_TIME_IN_DAYS", "INVITE_LINK_EXPITE_TIME_IN_DAYS"]
    )
    AWS_ACCESS_KEY_ID: str = Field(..., env="AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: str = Field(..., env="AWS_SECRET_ACCESS_KEY")
    AWS_DEFAULT_REGION: str = Field("us-east-1", env="AWS_DEFAULT_REGION")
    AWS_CONFIG_FILE: str = Field("~/.aws/config", env="AWS_CONFIG_FILE")
    AWS_SHARED_CREDENTIALS_FILE: str = Field(
        "~/.aws/credentials", env="AWS_SHARED_CREDENTIALS_FILE"
    )

    COGNITO_ACCESS_KEY_ID: str = Field(
        ...,
        env=[
            "COGNITO_ACCESS_KEY_ID",
            "AWS_ACCESS_KEY_ID",
        ],
    )
    COGNITO_SECRET_ACCESS_KEY: str = Field(
        ...,
        env=[
            "COGNITO_SECRET_ACCESS_KEY",
            "AWS_SECRET_ACCESS_KEY",
        ],
    )
    COGNITO_WEB_CLIENT_ID: str = Field(..., env="COGNITO_WEB_CLIENT_ID")
    COGNITO_USER_POOL_ID: str = Field(..., env="COGNITO_USER_POOL_ID")

    SMTP_USERNAME: str = Field("", env="SMTP_USERNAME")
    SMTP_PASSWORD: str = Field("", env="SMTP_PASSWORD")
    SMTP_HOST: str = Field("", env="SMTP_HOST")
    SMTP_PORT: str = Field("", env="SMTP_PORT")
    SMTP_SENDER_EMAIL: str = Field("", env="SMTP_SENDER_EMAIL")
    SMTP_SENDER_NAME: str = Field("", env="SMTP_SENDER_NAME")
    NON_PROD_EMAIL_RECEIVER_ADDRESSES: str = Field(
        "richardwolf@gmail.com, test@fedrisk.com, sarah.vardy@longevityconsulting.com",
        env="NON_PROD_EMAIL_RECEIVER_ADDRESSES",
    )

    DISPLAY_SQL_STATEMENTS: bool = Field(False, env="DISPLAY_SQL_STATEMENTS")

    STRIPE_SECRET_KEY: str = Field("", env="STRIPE_SECRET_KEY")
    STRIPE_PUBLIC_KEY: str = Field("", env="STRIPE_PUBLIC_KEY")

    CC_RETRY_COUNT: str = Field("1", env="CC_RETRY_COUNT")

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql://{self.RDS_USER}:{self.RDS_PASSWORD}@{self.RDS_HOST}:{self.RDS_PORT}/{self.RDS_DB}"

    class Config:
        case_sensitive = True
        env_file = ".env"
        env_file_encoding = "utf-8"
