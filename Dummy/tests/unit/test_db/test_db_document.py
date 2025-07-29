import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from sqlalchemy.orm import Session
from fedrisk_api.schema.document import CreateDocument, UpdateDocument

from fedrisk_api.db.document import create_document, update_document, delete_document

# Sample data for testing
@pytest.fixture
def db_session():
    """Mocked SQLAlchemy Session for database interactions."""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_document():
    """Sample document data for testing."""
    return CreateDocument(
        title="Test Document",
        name="TestDocument",
        description="A sample document for testing.",
        version="1.0",
    )


@pytest.fixture
def sample_update_document():
    """Sample updated document data for testing."""
    return UpdateDocument(
        title="Updated Document Title",
        description="Updated description for testing.",
        version="1.1",
    )


@pytest.fixture
def mock_notifications():
    """Mocks for asynchronous notification functions."""
    with patch(
        "fedrisk_api.utils.email_util.send_watch_email", new_callable=AsyncMock
    ) as mock_email, patch(
        "fedrisk_api.utils.sms_util.publish_notification", new_callable=AsyncMock
    ) as mock_sms:
        yield mock_email, mock_sms


# @pytest.mark.asyncio
# async def test_create_document(db_session, sample_document, mock_notifications):
#     mock_email, mock_sms = mock_notifications

#     # Invoke create_document with mocked dependencies
#     document = await create_document(
#         db=db_session,
#         document=sample_document,
#         fedrisk_object_type="projects",
#         fedrisk_object_id="1",
#         file_content_type="application/pdf",
#         tenant_id=1,
#         keywords="risk,compliance",
#         user_id=1,
#         project_id=1,
#     )

#     # Assertions to check the behavior of create_document
#     db_session.add.assert_called()  # Ensures `add` was called at least once
#     db_session.commit.assert_called()  # Ensures `commit` was called at least once
#     assert document is not None

#     # Verify email and SMS notifications were sent
#     # await mock_email.assert_awaited()
#     # await mock_sms.assert_awaited()


@pytest.mark.asyncio
async def test_update_document(db_session, sample_update_document, mock_notifications):
    mock_email, mock_sms = mock_notifications

    # Assume an existing document with certain attributes
    db_session.query().filter().first.return_value = MagicMock(
        id=1, title="Old Title", version="1.0"
    )

    # Invoke update_document with mocked dependencies
    result = await update_document(
        db=db_session,
        id=1,
        file_content_type="application/pdf",
        document=sample_update_document,
        tenant_id=1,
        keywords="updated,keywords",
        fedrisk_object_type="projects",
        fedrisk_object_id=1,
        user_id=1,
    )

    # Assertions to check the behavior of update_document
    assert result is not None  # Should return the updated document
    db_session.commit.assert_called()  # Ensures `commit` was called
    # await mock_email.assert_awaited()  # Check that email notification was sent if applicable
    # await mock_sms.assert_awaited()  # Check that SMS notification was sent if applicable


@pytest.mark.asyncio
async def test_delete_document(db_session, mock_notifications):
    mock_email, mock_sms = mock_notifications

    # Assume an existing document reference
    db_session.query().filter().first.return_value = MagicMock(id=1, title="Test Document")

    # Invoke delete_document with mocked dependencies
    result = await delete_document(
        db=db_session,
        id=1,
        tenant_id=1,
    )

    # Assertions to check the behavior of delete_document
    assert result is True  # Should return True on successful deletion
    db_session.commit.assert_called()  # Ensures `commit` was called
    # await mock_email.assert_awaited()  # Check that email notification was sent if applicable
    # await mock_sms.assert_awaited()  # Check that SMS notification was sent if applicable
