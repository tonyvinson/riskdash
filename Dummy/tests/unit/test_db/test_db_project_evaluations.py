import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.orm import Session

from fedrisk_api.db.project_evaluation import (
    create_project_evaluation,
    update_project_evaluation,
    delete_project_evaluation,
    get_all_project_evaluations,
    get_project_evaluation,
    search,
)
from fedrisk_api.db.models import (
    Project,
    ProjectEvaluation,
    User,
    UserWatching,
    UserNotificationSettings,
)
from fedrisk_api.schema.project_evaluation import CreateProjectEvaluation, UpdateProjectEvaluation

from fedrisk_api.utils.email_util import send_watch_email
from fedrisk_api.utils.sms_util import publish_notification


@pytest.fixture
def db_session():
    """Mock database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_project():
    """Mock Project instance."""
    project = Project(id=1, tenant_id=100, name="Project A")
    return project


@pytest.fixture
def mock_project_evaluation():
    """Mock ProjectEvaluation instance."""
    project_evaluation = ProjectEvaluation(id=1, name="Evaluation 1", project_id=1, tenant_id=100)
    return project_evaluation


@pytest.fixture
def create_evaluation_schema():
    """Mock CreateProjectEvaluation schema."""
    return CreateProjectEvaluation(
        project_id="1",
        name="Test Evaluation",
        description="Test Description",
        comments="Some comments",
    )


@pytest.fixture
def update_evaluation_schema():
    """Mock UpdateProjectEvaluation schema."""
    return UpdateProjectEvaluation(
        name="Updated Evaluation", description="Updated Description", comments="Updated Comments"
    )


@patch("fedrisk_api.utils.email_util.send_watch_email", new_callable=AsyncMock)
@patch("fedrisk_api.utils.sms_util.publish_notification", new_callable=AsyncMock)
async def test_create_project_evaluation(
    mock_send_email, mock_publish_sms, db_session, create_evaluation_schema, mock_project
):
    """Test the creation of a project evaluation with notifications."""
    db_session.query().filter().first.side_effect = [mock_project]

    new_eval = await create_project_evaluation(
        db=db_session,
        project_evaluation=create_evaluation_schema,
        tenant_id=100,
        keywords="keyword1, keyword2",
        user_id=1,
    )

    assert new_eval is not None
    db_session.add.assert_called()
    db_session.commit.assert_called()

    # Ensure notifications were sent
    mock_send_email.assert_called()
    mock_publish_sms.assert_called()


@patch("fedrisk_api.utils.email_util.send_watch_email", new_callable=AsyncMock)
@patch("fedrisk_api.utils.sms_util.publish_notification", new_callable=AsyncMock)
async def test_update_project_evaluation(
    mock_send_email,
    mock_publish_sms,
    db_session,
    mock_project_evaluation,
    update_evaluation_schema,
    mock_project,
):
    """Test the update of a project evaluation with notifications."""
    db_session.query().filter().first.side_effect = [mock_project_evaluation, mock_project]

    updated_eval = await update_project_evaluation(
        db=db_session,
        id=1,
        project_evaluation=update_evaluation_schema,
        tenant_id=100,
        keywords="keyword1, keyword3",
        user_id=1,
    )

    assert updated_eval is not None
    db_session.commit.assert_called()
    mock_send_email.assert_called()
    mock_publish_sms.assert_called()


@patch("fedrisk_api.utils.email_util.send_watch_email", new_callable=AsyncMock)
@patch("fedrisk_api.utils.sms_util.publish_notification", new_callable=AsyncMock)
async def test_delete_project_evaluation(
    mock_send_email, mock_publish_sms, db_session, mock_project_evaluation, mock_project
):
    """Test the deletion of a project evaluation and related notifications."""
    db_session.query().filter().first.side_effect = [mock_project_evaluation, mock_project]

    result = await delete_project_evaluation(db=db_session, id=1, tenant_id=100)

    assert result is True
    db_session.commit.assert_called()
    mock_send_email.assert_called()
    mock_publish_sms.assert_called()


def test_search_superuser(db_session, mock_project_evaluation):
    """Test search function as a superuser with mock data."""
    db_session.query().filter().all.return_value = [mock_project_evaluation]
    db_session.query().filter().count.return_value = 1

    count, results = search("evaluation", db_session, tenant_id=100, user_id=1)

    assert count == 1
    assert results == [mock_project_evaluation]
    db_session.query().filter().count.assert_called()


def test_search_non_superuser(db_session, mock_project_evaluation):
    """Test search function as a non-superuser with mock data."""
    db_session.query().filter().all.return_value = [mock_project_evaluation]
    db_session.query().filter().count.return_value = 1

    count, results = search("evaluation", db_session, tenant_id=100, user_id=2)

    assert count == 1
    assert results == [mock_project_evaluation]
    db_session.query().filter().count.assert_called()


def test_get_all_project_evaluations(db_session):
    result = get_all_project_evaluations(db=db_session, tenant_id=1, user_id=1)
    assert result is not None


def test_get_project_evaluation(db_session):
    result = get_project_evaluation(db=db_session, id=1, tenant_id=1, user_id=1)
    assert result is not None
