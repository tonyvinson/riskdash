import pytest
from fedrisk_api.schema.exception import CreateException, UpdateException
from fedrisk_api.utils.email_util import send_control_exception_email
from sqlalchemy.orm import Session

from fedrisk_api.db.models import (
    Exception,
    Project,
    ProjectControl,
    Framework,
    FrameworkVersion,
    Control,
    Keyword,
    KeywordMapping,
    User,
)

from datetime import date

# Import functions from your module
from fedrisk_api.db.exception import (
    create_exception,
    get_exception,
    update_exception,
    delete_exception,
    get_all_exceptions,
    remove_old_keywords,
    add_keywords,
)

# from fedrisk_api.db.project import (
#     create_project,
#     add_control_to_project,
#     get_project_control_by_id,
# )

# from fedrisk_api.db.framework import (
#     create_framework,
# )

# from fedrisk_api.db.control import (
#     create_control,
# )

# from fedrisk_api.db.framework_version import (
#     create_framework_version,
# )

from unittest.mock import MagicMock, AsyncMock, patch

# Fixtures for common dependencies
@pytest.fixture
def db_session():
    """Mocked SQLAlchemy Session."""
    return MagicMock(spec=Session)


@pytest.fixture
def sample_create_exception():
    """Sample data for creating an exception."""
    return CreateException(
        project_control_id="1",
        description="Test Exception Description",
        stakeholder_ids=[1, 2, 3],
        next_review_date=date.today(),
        owner_id=1,
    )


@pytest.fixture
def sample_update_exception():
    """Sample data for updating an exception."""
    return UpdateException(
        description="Updated Exception Description",
        justification="Updated Justification",
        review_status="Not Started",
    )


@pytest.fixture
def mock_email_notification():
    with patch(
        "fedrisk_api.utils.email_util.send_control_exception_email", new_callable=AsyncMock
    ) as mock_send_email:
        yield mock_send_email


@pytest.fixture
def mock_db_session():
    """Fixture to mock the SQLAlchemy database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_project_control():
    """Fixture to mock a ProjectControl object."""
    return ProjectControl(
        id=1,
        project_id=1,
        control=MagicMock(name="Mock Control"),
        project=MagicMock(name="Mock Project"),
    )


@pytest.fixture
def mock_create_exception_request():
    """Fixture to mock a CreateException request schema."""
    return CreateException(
        project_control_id=1,
        description="Test Exception",
        justification="Test Justification",
        owner_id=1,
        stakeholder_ids=[2, 3],
        next_review_date=date.today(),
    )


@pytest.fixture
def mock_owner():
    """Fixture to mock an Owner User object."""
    return User(id=1, email="owner@example.com")


@pytest.fixture
def mock_stakeholders():
    """Fixture to mock stakeholder User objects."""
    stakeholder_1 = User(id=2, email="stakeholder2@example.com")
    stakeholder_2 = User(id=3, email="stakeholder3@example.com")
    return [stakeholder_1, stakeholder_2]


@pytest.fixture
def mock_new_exception():
    """Fixture to mock a newly created Exception object."""
    return Exception(
        id=1,
        name="Test Exception",
        project_control_id=1,
        owner_id=1,
        tenant_id=1,
    )


@pytest.mark.asyncio
async def test_add_keywords(db_session):
    # Seed test data
    tenant_id = 1
    exception_id = 1
    # db_session.add(Exception(id=exception_id, name="Test Exception", tenant_id=tenant_id))
    # db_session.commit()

    keywords = "security, compliance, risk"

    # Call the function
    await add_keywords(db_session, keywords, exception_id, tenant_id)

    # Assertions
    # db_keywords = test_db.query(Keyword).filter(Keyword.tenant_id == tenant_id).all()
    # assert len(db_keywords) == 3  # Check that three keywords were added

    # db_mappings = test_db.query(KeywordMapping).filter(KeywordMapping.exception_id == exception_id).all()
    # assert len(db_mappings) == 3  # Check that mappings were created

    # # Check specific keyword names
    # keyword_names = {kw.name for kw in db_keywords}
    # assert keyword_names == {"security", "compliance", "risk"}


@pytest.mark.asyncio
async def test_remove_old_keywords(db_session):
    # Seed test data
    tenant_id = 1
    exception_id = 1
    # db_session.add(Exception(id=exception_id, name="Test Exception", tenant_id=tenant_id))
    keyword1 = Keyword(name="security", tenant_id=tenant_id)
    keyword2 = Keyword(name="compliance", tenant_id=tenant_id)
    db_session.add_all([keyword1, keyword2])
    db_session.commit()

    db_session.add_all(
        [
            KeywordMapping(keyword_id=keyword1.id, exception_id=exception_id),
            KeywordMapping(keyword_id=keyword2.id, exception_id=exception_id),
        ]
    )
    db_session.commit()

    # Call the function to keep only "security"
    await remove_old_keywords(db_session, "security", exception_id)

    # # Assertions
    # remaining_mappings = test_db.query(KeywordMapping).filter(KeywordMapping.exception_id == exception_id).all()
    # assert len(remaining_mappings) == 1
    # assert remaining_mappings[0].keyword_id == keyword1.id  # Only "security" remains


# @pytest.mark.asyncio
# async def test_create_exception_success(
#     mock_db_session,
#     mock_project_control,
#     mock_create_exception_request,
#     mock_owner,
#     mock_stakeholders,
#     mock_new_exception,
# ):
#     # Arrange
#     mock_db_session.query().filter().first.side_effect = [
#         mock_project_control,  # ProjectControl query
#         mock_owner,            # Owner query
#         mock_project_control.project,  # Project query
#     ]
#     mock_db_session.query().filter().all.return_value = mock_stakeholders
#     mock_db_session.add = MagicMock()
#     mock_db_session.commit = MagicMock()
#     mock_db_session.refresh = MagicMock()

#     # Mock external functions
#     notify_user = AsyncMock()
#     send_control_exception_email = AsyncMock()

#     # Act
#     result = await create_exception(
#         db=mock_db_session,
#         exception=mock_create_exception_request,
#         keywords="keyword1,keyword2",
#         tenant_id=1,
#         user_id=1,
#     )

#     # Assert
#     assert result.id == 123
#     mock_db_session.add.assert_called_with(mock_new_exception)
#     mock_db_session.commit.assert_called()
#     notify_user.assert_called()  # Ensure notify_user is called
#     send_control_exception_email.assert_called()  # Ensure email is sent


@pytest.mark.asyncio
async def test_create_exception_no_project_control(mock_db_session, mock_create_exception_request):
    # Arrange
    mock_db_session.query().filter().first.return_value = None  # No ProjectControl found

    # Act
    result = await create_exception(
        db=mock_db_session,
        exception=mock_create_exception_request,
        keywords="keyword1,keyword2",
        tenant_id=1,
        user_id=1,
    )

    # Assert
    assert result == -1
    mock_db_session.add.assert_not_called()  # Nothing should be added
    mock_db_session.commit.assert_not_called()


# @pytest.mark.asyncio
# async def test_create_exception_stakeholder_notifications(
#     mock_db_session,
#     mock_project_control,
#     mock_create_exception_request,
#     mock_owner,
#     mock_stakeholders,
#     mock_new_exception,
# ):
#     # Arrange
#     mock_db_session.query().filter().first.side_effect = [
#         mock_project_control,  # ProjectControl query
#         mock_owner,            # Owner query
#         mock_project_control.project,  # Project query
#     ]
#     mock_db_session.query().filter().all.return_value = mock_stakeholders
#     mock_db_session.add = MagicMock()
#     mock_db_session.commit = MagicMock()

#     # Mock notify_user
#     notify_user = AsyncMock()

#     # Act
#     await create_exception(
#         db=mock_db_session,
#         exception=mock_create_exception_request,
#         keywords="keyword1,keyword2",
#         tenant_id=1,
#         user_id=1,
#     )

#     # Assert stakeholder notifications
#     for stakeholder in mock_stakeholders:
#         notify_user.assert_any_call(
#             stakeholder,
#             f"You've been added as a stakeholder on exception {mock_new_exception.name}",
#             f"/projects/{mock_project_control.project.id}/controls/{mock_project_control.id}/exceptions/{mock_new_exception.id}",
#             None,  # Notification settings mock can be added here
#         )


# @pytest.mark.asyncio
# async def test_create_exception_add_keywords(
#     mock_db_session, mock_project_control, mock_create_exception_request, mock_new_exception
# ):
#     # Arrange
#     mock_db_session.query().filter().first.side_effect = [
#         mock_project_control,  # ProjectControl query
#     ]
#     mock_db_session.add = MagicMock()
#     mock_db_session.commit = MagicMock()

#     # Mock external functions
#     add_keywords = AsyncMock()

#     # Act
#     result = await create_exception(
#         db=mock_db_session,
#         exception=mock_create_exception_request,
#         keywords="keyword1,keyword2",
#         tenant_id=1,
#         user_id=1,
#     )

#     # Assert
#     add_keywords.assert_called_once_with(
#         mock_db_session, "keyword1,keyword2", mock_new_exception.id, 1
#     )
#     assert result.id == 123


@pytest.mark.asyncio
async def test_create_exception_project_control_not_found(db_session, sample_create_exception):
    # Simulate ProjectControl not found
    db_session.query().filter().first.side_effect = [None]

    sample_create_exception = CreateException(
        project_control_id="1",
        description="Test Exception Description",
        stakeholder_ids=[1, 2, 3],
        next_review_date=date.today(),
    )

    # Call create_exception and expect a specific return value for missing control
    result = await create_exception(
        db=db_session,
        exception=sample_create_exception,
        keywords="risk,compliance",
        tenant_id=1,
        user_id=1,
    )

    assert result == -1  # Indicates that the ProjectControl was not found


def test_get_all_exceptions(db_session):
    # Simulate fetching all exceptions for a project
    db_session.query().options().all.return_value = [
        MagicMock(id=1, description="Exception 1"),
        MagicMock(id=2, description="Exception 2"),
    ]

    # Call get_all_exceptions
    result = get_all_exceptions(db_session, tenant_id=1, project_id=1, user_id=1)

    # Assertions
    # assert len(result) == 2  # Check that two exceptions were returned
    # db_session.query().options().all.assert_called_once()  # Ensure query was executed


# @pytest.mark.asyncio
# async def test_update_exception(db_session, sample_update_exception):
#     db_session.query().filter().first.side_effect = [MagicMock(id=1, description="Old Description")]


#     # Call update_exception
#     result = await update_exception(
#         db=db_session,
#         id=1,
#         exception=sample_update_exception,
#         keywords="updated,keywords",
#         tenant_id=1,
#         user_id=1,
#     )

#     # Assertions
#     assert result is not None  # Indicates successful update by returning ID
#     # db_session.commit.assert_called()  # Ensure commit was executed


async def test_delete_exception(db_session):
    # db_session.query().filter().first.side_effect = [MagicMock(id=1, project_control_id=1)]
    # Sample data for the test
    project = Project(id=1, tenant_id=1, name="Test Project")
    framework = Framework(id=1, name="Framework 1", description="Framework 1 description")
    framework_version = FrameworkVersion(
        id=1, version_prefix="prefix", version_suffix="suffix", guidance="guidance", framework_id=1
    )
    control = Control(
        id=1,
        name="Control 1",
        description="Control 1 description",
        guidance="Guidance",
        tenant_id=1,
    )
    project_control = ProjectControl(id=1, project_id=1, control_id=1)
    db_session.add_all([project, framework, framework_version, control, project_control])
    db_session.commit()

    # Call create_exception
    result = await create_exception(
        db=db_session,
        exception=sample_create_exception,
        keywords="risk,compliance",
        tenant_id=1,
        user_id=1,
    )

    # Call delete_exception
    result = delete_exception(db_session, id=1, tenant_id=1)

    # Assertions
    assert result is True  # Indicates successful deletion
    # db_session.commit.assert_called()  # Ensure commit was executed
