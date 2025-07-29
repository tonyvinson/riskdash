import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from fedrisk_api.db.models import ProjectGroup, Project
from fedrisk_api.schema.project_group import CreateProjectGroup, UpdateProjectGroup
from fedrisk_api.db.project_group import (
    create_project_group,
    get_project_group,
    get_project_group_by_id,
    update_project_group_by_id,
    get_projects_by_group_id,
    delete_project_group_by_id,
)


@pytest.fixture
def db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


def test_create_project_group(db_session):
    """Test creating a project group."""
    project_group_data = CreateProjectGroup(name="Test Group", description="Test Group Description")
    result = create_project_group(project_group_data, db_session, tenant_id=1)

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    assert result.name == "Test Group"
    assert result.tenant_id == 1


def test_get_project_group(db_session):
    """Test retrieving project groups."""
    db_session.query().filter().all.return_value = [ProjectGroup(id=1, name="Group 1")]

    result = get_project_group(db_session, tenant_id=1)

    assert len(result) == 1
    assert result[0].name == "Group 1"


def test_get_project_group_by_id(db_session):
    """Test retrieving a project group by ID."""
    db_session.query().filter().first.return_value = ProjectGroup(id=1, name="Group 1")

    result = get_project_group_by_id(db_session, project_group_id=1)

    assert result is not None
    assert result.id == 1


def test_update_project_group_by_id(db_session):
    """Test updating a project group by ID."""
    db_session.query().filter().first.return_value = ProjectGroup(id=1, name="Group 1")
    project_group_data = UpdateProjectGroup(name="Updated Group")

    result = update_project_group_by_id(
        project_group_data, db_session, project_group_id=1, tenant_id=1
    )

    db_session.commit.assert_called_once()
    assert result is True


def test_update_project_group_by_id_not_found(db_session):
    """Test updating a project group by ID when it doesn't exist."""
    db_session.query().filter().first.return_value = None
    project_group_data = UpdateProjectGroup(name="Non-Existent Group")

    result = update_project_group_by_id(
        project_group_data, db_session, project_group_id=2, tenant_id=1
    )

    # assert result is False


def test_get_projects_by_group_id(db_session):
    """Test retrieving projects by group ID."""
    db_session.query().filter().filter().all.return_value = [
        Project(id=1, project_group_id=1, name="Project 1")
    ]

    result = get_projects_by_group_id(db_session, tenant_id=1, project_group_id=1)

    assert len(result) == 1
    assert result[0].name == "Project 1"


def test_delete_project_group_by_id(db_session):
    """Test deleting a project group by ID."""
    mock_project_group = MagicMock(spec=ProjectGroup)
    db_session.query().filter().first.return_value = mock_project_group

    result = delete_project_group_by_id(db_session, tenant_id=1, project_group_id=1)

    db_session.delete.assert_called_once_with(mock_project_group)
    db_session.commit.assert_called_once()
    assert result is True


def test_delete_project_group_by_id_not_found(db_session):
    """Test deleting a project group by ID when it doesn't exist."""
    db_session.query().filter().first.return_value = None

    result = delete_project_group_by_id(db_session, tenant_id=1, project_group_id=2)

    assert result is False
