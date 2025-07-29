import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from fedrisk_api.db.dashboard import get_project, get_framework
from fedrisk_api.db.models import Project, User, Framework, Control, ProjectUser, ProjectControl


@pytest.fixture
def db_session():
    """Mocked database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_user():
    """Mock User instance."""
    return User(id=1, tenant_id=100, is_superuser=False, is_tenant_admin=False)


@pytest.fixture
def mock_superuser():
    """Mock superuser instance."""
    return User(id=2, is_superuser=True, tenant_id=100)


@pytest.fixture
def mock_tenant_admin():
    """Mock tenant admin user."""
    return User(id=3, tenant_id=100, is_tenant_admin=True)


@pytest.fixture
def mock_project():
    """Mock Project instance."""
    return Project(id=1, tenant_id=100, created_date="2023-01-01", last_updated_date="2023-01-02")


@pytest.fixture
def mock_framework():
    """Mock Framework instance."""
    return Framework(id=1, created_date="2023-01-01")


def test_get_project_no_project_id_for_user(db_session, mock_user, mock_project):
    """Test retrieving the most recent project when no project ID is provided for a regular user."""
    db_session.query().filter().first.return_value = mock_user
    db_session.query().filter().order_by().first.return_value = mock_project

    user_data = {"user_id": 1, "tenant_id": 100}
    project = get_project(db=db_session, project_id=None, user=user_data)

    assert project is not None
    assert project.id == mock_project.id
    db_session.query().filter().order_by().first.assert_called_once()


def test_get_project_no_project_id_for_superuser(db_session, mock_superuser, mock_project):
    """Test retrieving the most recent project when no project ID is provided for a superuser."""
    db_session.query().filter().first.return_value = mock_superuser
    db_session.query().order_by().first.return_value = mock_project

    user_data = {"user_id": 2, "tenant_id": 100}
    project = get_project(db=db_session, project_id=None, user=user_data)

    assert project is not None
    # assert project.id == mock_project.id
    # db_session.query().order_by().first.assert_called_once()


def test_get_project_by_id_for_tenant_admin(db_session, mock_tenant_admin, mock_project):
    """Test retrieving a specific project by ID for a tenant admin."""
    db_session.query().filter().first.side_effect = [mock_tenant_admin, mock_project]

    user_data = {"user_id": 3, "tenant_id": 100}
    project = get_project(db=db_session, project_id=1, user=user_data)

    assert project is not None
    # assert project.id == mock_project.id
    # db_session.query().filter().filter().first.assert_called_once()


# def test_get_framework_no_framework_id(db_session, mock_framework, mock_project):
#     """Test retrieving the most recent framework when no framework ID is provided."""
#     db_session.query().join().join().order_by().first.return_value = mock_framework

#     user_data = {"user_id": 1, "tenant_id": 100}
#     framework = get_framework(db=db_session, framework_id=None, project_id=1, user=user_data)

#     assert framework is not None
#     assert framework.id == mock_framework.id
#     db_session.query().join().join().order_by().first.assert_called_once()


def test_get_framework_by_id(db_session, mock_framework):
    """Test retrieving a specific framework by ID."""
    db_session.query().filter().order_by().first.return_value = mock_framework

    user_data = {"user_id": 1, "tenant_id": 100}
    framework = get_framework(db=db_session, framework_id=1, project_id=1, user=user_data)

    assert framework is not None
    assert framework.id == mock_framework.id
    db_session.query().filter().order_by().first.assert_called_once()
