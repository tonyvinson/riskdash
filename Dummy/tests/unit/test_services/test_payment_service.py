import pytest
import os
import json
from unittest.mock import MagicMock
from fedrisk_api.service.payment_service import PaymentService
from fedrisk_api.schema.payment import TenantAdminUserDetail, TenantAdminUpdateUserDetail

stripe_secret_key = os.getenv("STRIPE_SECRET_KEY", "")
stripe_test_customer_id = os.getenv("STRIPE_TEST_CUSTOMER_ID", "")


def test_create_customer(mocker):
    # Mock Stripe module and API key
    stripe_mock = mocker.patch("fedrisk_api.service.payment_service")
    config_mock = MagicMock(STRIPE_SECRET_KEY=stripe_secret_key)
    service = PaymentService(config_mock)

    # Mock input and expected output
    # profile = MagicMock(first_name="John", last_name="Doe", email="john.doe@example.com")
    stripe_mock.Customer.create.return_value = {"id": "cus_12345"}

    profile = TenantAdminUserDetail(
        first_name="John",
        last_name="Doe",
        email="john.doe@example.com",
        organization="TestOrg",
        tenant_id=1,
    )
    # Call the method
    result = service.create_customer(profile)

    # # Assert Stripe's Customer.create was called with correct parameters
    # stripe_mock.Customer.create.assert_called_once_with(
    #     name="John Doe", email="john.doe@example.com", metadata=profile.dict()
    # )

    # # Assert result
    # assert result == {"id": "cus_12345"}


# def test_update_customer(mocker):
#     # Mock Stripe module and API key
#     stripe_mock = mocker.patch("fedrisk_api.service.payment_service")
#     config_mock = MagicMock(STRIPE_SECRET_KEY=stripe_secret_key)
#     service = PaymentService(config_mock)

#     updated_profile = TenantAdminUpdateUserDetail(
#         first_name = "Johnathan",
#         last_name = "Doethan",
#         email = "john.doe2@example.com",
#         organization = "TestOrg2",
#     )
#     returned_profile = updated_profile.dict(exclude_none=True)
#     # Mock input and expected output
#     # profile = MagicMock(first_name="John", last_name="Doe", email="john.doe@example.com")
#     stripe_mock.Customer.modify.return_value = {"cus_12345", dict(**returned_profile)}


#     # Call the method
#     result = service.update_customer("cus_12345", updated_profile)


def test_get_customer_by_id(mocker):
    # Mock Stripe module and API key
    stripe_mock = mocker.patch("fedrisk_api.service.payment_service")
    config_mock = MagicMock(STRIPE_SECRET_KEY=stripe_secret_key)
    service = PaymentService(config_mock)

    # Mock input and expected output
    # profile = MagicMock(first_name="John", last_name="Doe", email="john.doe@example.com")
    stripe_mock.Customer.retrieve.return_value = stripe_test_customer_id
    result = service.get_customer_by_id(stripe_test_customer_id)
