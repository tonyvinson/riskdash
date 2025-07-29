import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from datetime import datetime

from fedrisk_api.db.history import (
    get_assessment_history_by_id,
    get_all_assessment_history_by_project_id,
    get_audit_test_history_by_id,
    get_all_audit_test_history_by_project_id,
    get_document_history_by_id,
    get_all_document_history_by_project_id,
    get_exception_history_by_id,
    get_all_exception_history_by_project_id,
    get_project_control_history_by_id,
    get_all_project_control_history_by_project_id,
    get_project_evaluation_history_by_id,
    get_all_project_evaluation_history_by_project_id,
    get_project_history_by_id,
    get_all_project_history_by_project_id,
    get_task_history_by_id,
    get_all_task_history_by_project_id,
    get_all_project_user_history_by_project_id,
    get_risk_history_by_id,
    get_all_risk_history_by_project_id,
    get_wbs_history_by_id,
    get_all_wbs_history_by_project_id,
    create_user_watching,
    get_user_watching_by_project_id,
    get_all_projects_user_is_watching,
    update_user_watching_by_project_id,
)

from fedrisk_api.schema.history import CreateUserWatching, UpdateUserWatching
from fedrisk_api.db.models import (
    AssessmentHistory,
    Project,
    ProjectControl,
    AuditTestHistory,
    DocumentHistory,
    UserWatching,
)


@pytest.fixture
def db_session():
    """Mocked database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def example_project():
    """Mock Project instance."""
    return Project(id=1, name="Project Example")


@pytest.fixture
def mock_assessment_history():
    """Mock AssessmentHistory instance."""
    return AssessmentHistory(id=1, assessment_id=1, history="History Test", updated=datetime.now())


def test_get_assessment_history_by_id(db_session, mock_assessment_history):
    """Test retrieving an assessment history by ID."""
    db_session.query().filter().all.return_value = [mock_assessment_history]

    result = get_assessment_history_by_id(db=db_session, assessment_id=1)

    assert result[0].id == mock_assessment_history.id
    db_session.query().filter().all.assert_called_once()


def test_get_all_assessment_history_by_project_id(
    db_session, mock_assessment_history, example_project
):
    """Test retrieving all assessment histories by project ID."""
    db_session.query().join().join().filter().all.return_value = [mock_assessment_history]

    result = get_all_assessment_history_by_project_id(db=db_session, project_id=example_project.id)

    assert result[0].id == mock_assessment_history.id
    db_session.query().join().join().filter().all.assert_called_once()


def test_get_audit_test_history_by_id(db_session, example_project):
    """Test retrieving audit test history by ID."""
    audit_test_history = AuditTestHistory(
        id=1, audit_test_id=1, history="Test Audit", updated=datetime.now()
    )
    db_session.query().filter().all.return_value = [audit_test_history]

    result = get_audit_test_history_by_id(db=db_session, audit_test_id=1)

    assert result[0].id == audit_test_history.id
    db_session.query().filter().all.assert_called_once()


def test_create_user_watching(db_session):
    """Test creating a new user watching instance."""
    request = CreateUserWatching(user_id=1, project_id=1)
    new_user_watching = create_user_watching(request=request, db=db_session)

    assert new_user_watching is not None
    db_session.add.assert_called_once_with(new_user_watching)
    db_session.commit.assert_called_once()


def test_get_user_watching_by_project_id(db_session):
    """Test retrieving user watching by project ID."""
    user_watching = UserWatching(id=1, user_id=1, project_id=1)
    db_session.query().filter().first.return_value = user_watching

    result = get_user_watching_by_project_id(db=db_session, project_id=1)

    assert result.id == user_watching.id
    db_session.query().filter().first.assert_called_once()


def test_update_user_watching_by_project_id(db_session):
    """Test updating user watching by project ID."""
    existing_watching = UserWatching(id=1, user_id=1, project_id=1)
    db_session.query().filter().first.return_value = existing_watching

    update_request = UpdateUserWatching(user_id=1, project_id=1)
    result = update_user_watching_by_project_id(db=db_session, project_id=1, request=update_request)

    # assert result.watch_notifications == update_request.watch_notifications
    db_session.commit.assert_called_once()
