import unittest.mock

import pytest

from config.config import Settings
from fedrisk_api.service.email_service import EmailService

TEST_SMTP_HOST = "127.0.0.5"
TEST_SMTP_PORT = "27"
TEST_SENDER = "dog@gmail.com"
TEST_NON_PROD_EMAIL_RECEIVER_ADDRESSES = "cat@gmail.com, horse@gmail.com"
TEST_INTENDED_TO_ADDRESS = "mouse@gmail.com"
TEST_MESSAGE = "This is a test message."
TEST_SUBJECT = "THIS IS THE SUBJECT"
NON_PROD_ENVIRONMENT_NAME = "dev"
PROD_ENVIRONMENT_NAME = "prod"


def mock_send_non_prod(*args, **kwargs):
    print(f"Mock Send Called in simulated Non Prod Environment")
    print(f"Args: {args}")
    print(f"Kwargs: {kwargs}")

    assert args[0] == TEST_SENDER
    assert args[1] == TEST_NON_PROD_EMAIL_RECEIVER_ADDRESSES
    assert "the following recipients would have received this email" in args[2]
    assert f"\t{TEST_INTENDED_TO_ADDRESS}" in args[2]
    assert f"\nSubject: From {NON_PROD_ENVIRONMENT_NAME} Environment: {TEST_SUBJECT}" in args[2]
    return ""


def mock_send_prod(*args, **kwargs):
    print(f"Mock Send Called in simulated Prod Environment")
    print(f"Args: {args}")
    print(f"Kwargs: {kwargs}")

    assert args[0] == TEST_SENDER
    assert args[1] == TEST_INTENDED_TO_ADDRESS
    assert "the following recipients would have received this email" not in args[2]
    assert f"\t{TEST_INTENDED_TO_ADDRESS}" not in args[2]
    assert f"\nSubject: {TEST_SUBJECT}" in args[2]
    return ""


@pytest.fixture
def email_service_non_prod():
    test_settings = Settings()
    test_settings.ENVIRONMENT = NON_PROD_ENVIRONMENT_NAME
    test_settings.SMTP_HOST = TEST_SMTP_HOST
    test_settings.SMTP_PORT = TEST_SMTP_PORT
    test_settings.SMTP_SENDER_EMAIL = TEST_SENDER
    test_settings.NON_PROD_EMAIL_RECEIVER_ADDRESSES = TEST_NON_PROD_EMAIL_RECEIVER_ADDRESSES

    email_service = EmailService(config=test_settings)
    yield email_service


@pytest.fixture
def email_service_prod():
    test_settings = Settings()
    test_settings.ENVIRONMENT = PROD_ENVIRONMENT_NAME
    test_settings.SMTP_HOST = TEST_SMTP_HOST
    test_settings.SMTP_PORT = TEST_SMTP_PORT
    test_settings.SMTP_SENDER_EMAIL = TEST_SENDER
    test_settings.NON_PROD_EMAIL_RECEIVER_ADDRESSES = TEST_NON_PROD_EMAIL_RECEIVER_ADDRESSES

    email_service = EmailService(config=test_settings)
    yield email_service


# @pytest.mark.asyncio
# async def test_send_email_in_non_prod_environment(mocker, email_service_non_prod):
#     sendmail_mock = mocker.patch("fedrisk_api.service.email_service.SMTP")
#     sendmail_mock.return_value.__enter__.return_value.sendmail = mock_send_non_prod

#     await email_service_non_prod.send_email(
#         to_email_addresses=TEST_INTENDED_TO_ADDRESS,
#         message=TEST_MESSAGE,
#         subject=TEST_SUBJECT,
#         use_ssl=False,
#     )
#     sendmail_mock.assert_called_once_with(TEST_SMTP_HOST, TEST_SMTP_PORT)


@pytest.mark.asyncio
async def test_send_email_in_prod_environment(mocker, email_service_prod):
    sendmail_mock = mocker.patch("fedrisk_api.service.email_service.SMTP")
    sendmail_mock.return_value.__enter__.return_value.sendmail = mock_send_prod

    await email_service_prod.send_email(
        to_email_addresses=TEST_INTENDED_TO_ADDRESS,
        message=TEST_MESSAGE,
        subject=TEST_SUBJECT,
        use_ssl=False,
    )
    sendmail_mock.assert_called_once_with(TEST_SMTP_HOST, TEST_SMTP_PORT)
