import pytest

from config.config import Settings
from fedrisk_api.service.email_service import EmailService

# python -m smtpd -c DebuggingServer -n 127.0.0.1:1025


@pytest.fixture
def email_service():
    email_service = EmailService(config=Settings())
    yield email_service


# @pytest.mark.asyncio
# async def test_send_email(email_service):

#     await email_service.send_email("richardwolf@gmail.com", "Test Message", "Test Subject")
#     assert False
