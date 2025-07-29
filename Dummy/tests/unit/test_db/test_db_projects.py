import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from sqlalchemy.orm import Session

from fedrisk_api.db.project import (
    create_project,
    update_project,
    add_users_to_project,
    add_control_to_project,
    remove_control_from_project,
    get_project,
    get_all_projects,
    get_all_tenant_projects,
    delete_project,
    update_control_on_project,
    get_available_controls_for_adding_to_project,
    get_project_controls_by_project_id,
    get_project_control_by_id,
    get_project_controls_by_project_id_by_framework_version_id,
    get_audit_tests_by_project_id,
    get_risks_by_project_id,
    get_assessments_by_project_id,
    get_wbs_by_project_id,
    get_evaluations_by_project_id,
    create_exception_for_control_on_project,
    add_batch_project_controls_to_project,
    remove_user_from_project,
    change_user_role_in_project,
    get_project_user_permission,
    get_project_associated_user,
    get_project_pending_task,
    add_users_to_multiple_project,
    add_a_user_to_project,
)
from fedrisk_api.db.models import Project, User, Role, ProjectControl
from fedrisk_api.schema.project import (
    CreateProject,
    UpdateProject,
    AddProjectUsers,
    AddProjectControls,
    AddProjectControl,
    ChangeProjectUserRole,
    AddProjectUser,
)
from fedrisk_api.utils.email_util import send_watch_email
from fedrisk_api.utils.sms_util import publish_notification


@pytest.fixture
def db_session():
    """Mocked database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def example_user():
    """Mock User instance."""
    user = User(id=1, email="user@example.com", system_role=1, tenant_id=1)
    return user


@pytest.fixture
def example_role():
    """Mock Role instance."""
    role = Role(id=1, name="Project Manager")
    return role


@pytest.fixture
def example_project_data():
    """Mock project creation schema data."""
    return CreateProject(
        name="New Project",
        description="Project description",
        project_admin_id=1,
    )


@pytest.fixture
def updated_project_data():
    """Mock project update schema data."""
    return UpdateProject(
        name="Updated Project",
        description="Updated description",
    )


def test_create_project(db_session, example_project_data, example_user):
    """Test creating a new project."""
    db_session.query().filter_by().first.return_value = example_user
    with patch("fedrisk_api.utils.email_util.send_watch_email", new_callable=AsyncMock):
        new_project = create_project(
            db=db_session,
            project=example_project_data,
            tenant_id=1,
            keywords="keyword",
            user_id=example_user.id,
        )

    # assert new_project.name == example_project_data.name
    # db_session.add.assert_called()
    # db_session.commit.assert_called()


async def test_update_project(db_session, updated_project_data, example_user):
    """Test updating an existing project."""
    db_session.query().filter().first.return_value = Project(id=1, name="Existing Project")
    db_session.query().filter_by().first.return_value = example_user

    result = await update_project(
        db=db_session,
        id=1,
        project=updated_project_data,
        tenant_id=1,
        keywords="",
        user_id=example_user.id,
    )

    # assert result is True
    # db_session.commit.assert_called()


async def test_add_users_to_project(db_session, example_project_data):
    """Test adding users to a project."""
    project_users = AddProjectUsers(users=[{"user_id": 1, "role_id": 1}])

    with patch("fedrisk_api.utils.email_util.send_watch_email", new_callable=AsyncMock):
        result = await add_users_to_project(
            db=db_session, id=1, project_users=project_users, tenant_id=1, user_id=1
        )

    assert result
    # db_session.commit.assert_called()


async def test_add_control_to_project(db_session, example_project_data):
    """Test adding a control to a project."""
    db_session.query().filter().first.return_value = Project(id=1, name="Existing Project")

    with patch("fedrisk_api.utils.email_util.send_watch_email", new_callable=AsyncMock):
        result = await add_control_to_project(
            db=db_session, id=1, control_id=1, tenant_id=1, user_id=1
        )

    assert result
    # db_session.commit.assert_called()


async def test_remove_control_from_project(db_session):
    """Test removing a control from a project."""
    db_session.query().filter().first.return_value = Project(id=1, name="Existing Project")
    db_session.query().filter().filter().first.return_value = ProjectControl(id=1)

    result = await remove_control_from_project(
        db=db_session, id=1, project_control_id=1, tenant_id=1, user_id=1
    )

    # assert result[0] is True
    # db_session.commit.assert_called()


async def test_get_project(db_session, example_user):
    """Test retrieving a project."""
    project = Project(id=1, name="Example Project")
    db_session.query().filter().first.return_value = example_user
    db_session.query().filter().first.return_value = project

    result = await get_project(db=db_session, id=1, tenant_id=1, user_id=example_user.id)

    # assert result.name == "Example Project"
    # db_session.query().filter().first.assert_called()


def test_get_all_projects(db_session):
    result = get_all_projects(
        db=db_session,
        tenant_id=1,
        user_id=1,
        q=None,
        filter_by=None,
        sort_by=None,
        filter_value=None,
    )
    assert result is not None


def test_get_all_tenant_projects(db_session):
    result = get_all_tenant_projects(db=db_session, tenant_id=1)
    assert result is not None


def test_delete_project(db_session, example_user, example_project_data):
    db_session.query().filter_by().first.return_value = example_user
    with patch("fedrisk_api.utils.email_util.send_watch_email", new_callable=AsyncMock):
        new_project = create_project(
            db=db_session,
            project=example_project_data,
            tenant_id=1,
            keywords="keyword",
            user_id=example_user.id,
        )

    # assert new_project.name == example_project_data.name
    result = delete_project(db=db_session, id=1, tenant_id=1)
    assert result is not None


async def test_update_control_on_project(db_session):
    result = await update_control_on_project(
        db=db_session, id=1, control_id=1, tenant_id=1, mitigation_percentage=0.80
    )
    assert result is not None


def test_get_available_controls_for_adding_to_project(db_session):
    result = get_available_controls_for_adding_to_project(db=db_session, id=1, tenant_id=1)
    assert result is not None


def test_get_project_controls_by_project_id(db_session):
    result = get_project_controls_by_project_id(db=db_session, project_id=1)
    assert result is not None


def test_get_project_control_by_id(db_session):
    result = get_project_control_by_id(db=db_session, project_control_id=1)
    assert result is not None


def test_get_project_controls_by_project_id_by_framework_version_id(db_session):
    result = get_project_controls_by_project_id_by_framework_version_id(
        db=db_session, project_id=1, framework_version_id=1
    )
    assert result is not None


def test_get_audit_tests_by_project_id(db_session):
    result = get_audit_tests_by_project_id(db=db_session, project_id=1)
    assert result is not None


def test_get_risks_by_project_id(db_session):
    result = get_risks_by_project_id(db=db_session, project_id=1)
    assert result is not None


def test_get_assessments_by_project_id(db_session):
    result = get_assessments_by_project_id(db=db_session, project_id=1)
    assert result is not None


def test_get_wbs_by_project_id(db_session):
    result = get_wbs_by_project_id(db=db_session, project_id=1)
    assert result is not None


def test_get_evaluations_by_project_id(db_session):
    result = get_evaluations_by_project_id(db=db_session, project_id=1)
    assert result is not None


async def test_create_exception_for_control_on_project(
    db_session, example_user, example_project_data
):
    db_session.query().filter_by().first.return_value = example_user
    # with patch("fedrisk_api.utils.email_util.send_watch_email", new_callable=AsyncMock):
    new_project = await create_project(
        db=db_session,
        project=example_project_data,
        tenant_id=1,
        keywords="keyword",
        user_id=example_user.id,
    )
    result_control = add_control_to_project(
        db=db_session, id=new_project.id, control_id=1, tenant_id=1, user_id=1
    )
    assert result_control is not None
    result = create_exception_for_control_on_project(db=db_session, id=new_project.id, control_id=1)
    assert result is not None


async def test_add_batch_project_controls_to_project(
    db_session, example_project_data, example_user
):
    db_session.query().filter_by().first.return_value = example_user
    new_project = create_project(
        db=db_session,
        project=example_project_data,
        tenant_id=1,
        keywords="keyword",
        user_id=example_user.id,
    )
    project_control_1 = AddProjectControl(
        project_id=1,
        control_id=1,
    )
    project_control_2 = AddProjectControl(
        project_id=1,
        control_id=12,
    )
    assert new_project is not None
    controls_list = []
    controls_list.append(project_control_1)
    controls_list.append(project_control_2)
    project_controls = AddProjectControls(controls=list(controls_list))
    result = await add_batch_project_controls_to_project(
        db=db_session, project_id=1, project_controls=project_controls, tenant_id=1, user_id=1
    )
    assert result is not None


async def test_remove_user_from_project(db_session):
    result = await remove_user_from_project(db=db_session, id=1, user_id=1)
    assert result is not None


async def test_change_user_role_in_project(db_session):
    user = ChangeProjectUserRole(user_id=1, role_id=1)
    result = await change_user_role_in_project(db=db_session, id=1, user_details=user, user_id=1)
    assert result is not None


def test_get_project_user_permission(db_session):
    result = get_project_user_permission(db=db_session, id=1, user_id=1)
    assert result is not None


def test_get_project_associated_user(db_session):
    test_user = {
        "tenant_id": 1,
        "email": "tests@test.com",
        "system_role": 1,
    }
    result = get_project_associated_user(
        db=db_session, id=1, q=None, filter_value=None, filter_by=None, sort_by=None, user=test_user
    )
    assert result is not None


def test_get_project_pending_task(db_session):
    test_user = {
        "tenant_id": 1,
        "email": "tests@test.com",
        "system_role": 1,
        "user_id": 1,
    }
    result = get_project_pending_task(db=db_session, user=test_user)
    assert result is not None


# def test_add_users_to_multiple_project(db_session):
#     project_user_1 = AddProjectUser(
#         user_id=1,
#         role_id=1,
#     )
#     project_user_2 = AddProjectUser(
#         user_id=1,
#         role_id=2,
#     )
#     users = []
#     users.append(project_user_1)
#     users.append(project_user_2)
#     project_users = AddProjectUsers(users=list(users))
#     result = add_users_to_multiple_project(db=db_session, project_users=project_users, tenant_id=1)
#     assert result is not None


def test_add_a_user_to_project(db_session):
    result = add_a_user_to_project(db=db_session, id=1, user_id=1, role_id=1, author_id=1)
    assert result is not None
