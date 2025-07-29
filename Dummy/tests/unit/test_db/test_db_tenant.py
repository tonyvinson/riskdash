import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.tenant import (
    create_user_invitation,
    create_user_invite,
    verify_invitation,
    resend_invitation_mail,
    update_user,
    check_unique_email,
    tenant_signup,
    tenant_user_signup,
    update_tenant_customer,
    update_tenant_user_licenses,
    get_tenant_by_id,
    get_active_member_count,
    get_user_invites,
)
from fedrisk_api.schema.tenant import TenantUserDetails
from fedrisk_api.db.models import Tenant, User, UserInvitation


@pytest.fixture
def mock_session():
    session = MagicMock(spec=Session)
    return session


def test_create_user_invitation(mock_session):
    mock_session.add = MagicMock()
    mock_session.commit = MagicMock()
    mock_session.refresh = MagicMock()

    emails = ["test1@example.com", "test2@example.com"]
    tenant_id = 1

    result = create_user_invitation(emails, mock_session, tenant_id)

    assert len(result) == len(emails)
    for invitation in result:
        assert invitation.email in emails
        assert invitation.tenant_id == tenant_id


# def test_create_user_invite(mock_session):
#     mock_session.add = MagicMock()
#     mock_session.commit = MagicMock()
#     mock_session.refresh = MagicMock()

#     email = "test@example.com"
#     tenant_id = 1
#     role = 2

#     result = create_user_invite(email, mock_session, tenant_id, role)

#     assert result.email == email
#     assert result.tenant_id == tenant_id


def test_verify_invitation(mock_session):
    token = "test_token"
    mock_invitation = MagicMock()
    mock_invitation.is_expired = False
    mock_session.query().filter().filter().first.return_value = mock_invitation

    result = verify_invitation(token, mock_session)

    assert result == mock_invitation


def test_resend_invitation_mail(mock_session):
    email = "test@example.com"
    tenant_id = 1
    mock_user = MagicMock()
    mock_user.id = 123
    mock_session.query().filter().first.return_value = mock_user

    result = resend_invitation_mail(email, mock_session, tenant_id)

    assert result.email == email
    assert result.tenant_id == tenant_id


def test_update_user(mock_session):
    response = MagicMock()
    response.dict.return_value = {
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "phone_no": "1234567890",
    }
    mock_session.query().filter().update = MagicMock()

    result = update_user(response, mock_session)

    assert result is True


def test_check_unique_email(mock_session):
    email = "unique@example.com"
    mock_session.query().filter().first.return_value = None

    result = check_unique_email(email, mock_session)

    assert result is None


# def test_tenant_signup(mocker):
#     db = MagicMock()
#     mock_request = MagicMock()
#     mock_request.first_name = "John"
#     mock_request.last_name = "Doe"
#     mock_request.email = "john.doe@example.com"
#     mock_request.organization = "Test Organization"

#     mocker.patch("fedrisk_api.db.util.data_creation_utils.create_tenant_s3_bucket")
#     mocker.patch("fedrisk_api.db.util.data_creation_utils.create_tenant_user_folder_s3")

#     result = tenant_signup(mock_request, db)

#     assert result["tenant"].name == "Test Organization"
#     assert result["user"].email == "john.doe@example.com"


def test_tenant_user_signup(mock_session):
    request = TenantUserDetails(
        first_name="John",
        last_name="Doe",
        email="existing_user@example.com",
        organization="ExampleOrg",
        password="Testing123!",
        confirm_password="Testing123!",
    )
    mock_session.query().filter().first.return_value = MagicMock()

    result = tenant_user_signup(request, mock_session)

    assert result is not False


def test_update_tenant_customer(mock_session):
    customer_id = "cust_12345"
    tenant_id = 1
    mock_session.query().filter().first.return_value = MagicMock()

    result = update_tenant_customer(customer_id, tenant_id, mock_session)

    assert result is True


def test_update_tenant_user_licenses(mock_session):
    user_licence = 50
    tenant_id = 1
    mock_session.query().filter().first.return_value = MagicMock()

    result = update_tenant_user_licenses(user_licence, tenant_id, mock_session)

    assert result is True


def test_get_tenant_by_id(mock_session):
    tenant_id = 1
    mock_tenant = MagicMock()
    mock_session.query().filter().first.return_value = mock_tenant

    result = get_tenant_by_id(tenant_id, mock_session)

    assert result == mock_tenant


def test_get_active_member_count(mock_session):
    tenant_id = 1
    mock_session.query().filter().filter().count.return_value = 10

    result = get_active_member_count(tenant_id, mock_session)

    assert result == 10


def test_get_user_invites(mock_session):
    tenant_id = 1
    mock_invites = [MagicMock(), MagicMock()]
    mock_session.query().filter().all.return_value = mock_invites

    result = get_user_invites(tenant_id, mock_session)

    assert result == mock_invites
