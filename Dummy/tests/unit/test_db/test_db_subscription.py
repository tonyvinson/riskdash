import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.subscription import get_tenant_customer_id, get_tenant_subscription_id


@pytest.fixture
def mock_session():
    session = MagicMock(spec=Session)
    return session


@pytest.mark.asyncio
async def test_get_tenant_customer_id(mock_session):
    # Create a mock tenant with a customer_id
    mock_tenant = MagicMock()
    mock_tenant.customer_id = "cust_12345"
    mock_session.query().filter().first.return_value = mock_tenant

    # Call the function
    result = get_tenant_customer_id(tenant_id=1, db=mock_session)

    # Assert the result is as expected
    assert result == "cust_12345"


@pytest.mark.asyncio
async def test_get_tenant_subscription_id_with_subscription(mock_session):
    # Create a mock tenant with a subscription
    mock_tenant = MagicMock()
    mock_tenant.subscription.subscription_id = "sub_67890"
    mock_session.query().filter().first.return_value = mock_tenant

    # Call the function
    result = get_tenant_subscription_id(tenant_id=1, db=mock_session)

    # Assert the result is as expected
    assert result == "sub_67890"


@pytest.mark.asyncio
async def test_get_tenant_subscription_id_without_subscription(mock_session):
    # Create a mock tenant without a subscription
    mock_tenant = MagicMock()
    mock_tenant.subscription = None
    mock_session.query().filter().first.return_value = mock_tenant

    # Call the function
    result = get_tenant_subscription_id(tenant_id=1, db=mock_session)

    # Assert the result is None when there is no subscription
    assert result is None
