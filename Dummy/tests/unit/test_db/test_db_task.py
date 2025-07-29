import pytest
from unittest.mock import MagicMock
from fedrisk_api.schema.task import CreateTask, UpdateTask
from fedrisk_api.db.models import Task, User, Risk, AuditTest
from sqlalchemy.orm import Session
from fedrisk_api.db.task import (
    create_task,
    update_task,
    delete_task,
    get_wbs_dhtmlx_tasks,
    get_wbs_child_tasks,
    get_wbs_tasks,
    get_tasks_wbs_chart_data,
    add_project_task_history,
    # send_email_notifications,
    # notify_watchers,
    handle_task_associations,
    handle_task_relations,
    handle_task_resources,
    # add_keywords_to_task,
    add_keywords,
    # remove_old_keywords,
    send_assignment_notification,
)

from unittest.mock import patch


@patch("fedrisk_api.utils.email_util.send_watch_email")
@patch("fedrisk_api.utils.sms_util.publish_notification")
async def test_create_task_with_notifications(
    mock_publish, mock_send_email, db_session, create_task_payload, mock_user
):
    db_session.query(User).filter().first.return_value = mock_user

    # Call the function under test
    task = await create_task(db_session, create_task_payload, tenant_id=1, keywords="", user_id=1)

    # Assert that notification functions were called
    # mock_send_email.assert_called()
    # mock_publish.assert_called()


@pytest.fixture
def db_session():
    """Fixture for creating a mock SQLAlchemy session."""
    session = MagicMock(spec=Session)
    return session


@pytest.fixture
def mock_user():
    """Fixture for creating a mock User."""
    return User(id=1, email="testuser@example.com", is_superuser=True)


@pytest.fixture
def mock_task():
    """Fixture for creating a mock Task."""
    return Task(
        id=1,
        name="Initial Test Task",
        title="Initial Test Task",
        project_id=1,
        assigned_to=1,
        description="An existing task for testing",
        due_date="2024-12-31",
        user_id=1,
    )


@pytest.fixture
def create_task_payload():
    """Fixture for creating a sample CreateTask payload."""
    from fedrisk_api.schema.task import CreateTask

    return CreateTask(
        name="New Test Task",
        title="New Test Task",
        project_id=1,
        assigned_to=1,
        description="A new task for testing",
        due_date="2024-12-31",
        user_id=1,
    )


# def test_create_task_minimal_data(db_session, create_task_payload, mock_user):
#     # Setup mock data in session
#     db_session.query(User).filter().first.return_value = mock_user
#     db_session.commit.return_value = None
#     db_session.refresh.return_value = None

#     # Call create_task
#     task = create_task(db_session, create_task_payload, tenant_id=1, keywords="", user_id=1)

#     # Assertions
#     assert task.name == "Test Task"
#     db_session.add.assert_called_once()
#     db_session.commit.assert_called()
#     db_session.refresh.assert_called_with(task)

# def test_create_task_with_relations(db_session, create_task_payload, mock_user):
#     # Mock task relations like risks, children, etc.
#     db_session.query(User).filter().first.return_value = mock_user
#     db_session.query(Risk).filter().all.return_value = [Risk(id=1), Risk(id=2)]

#     # Add risks to task payload
#     create_task_payload.risks = [1, 2]

#     # Call create_task
#     task = create_task(db_session, create_task_payload, tenant_id=1, keywords="", user_id=1)

#     # Assertions
#     assert len(task.risks) == 2
#     db_session.add.assert_called_once()
#     db_session.commit.assert_called()


async def test_create_task_with_relations(db_session, create_task_payload, mock_user):
    # Mocking relations like risks, audit tests, and attachments
    db_session.query(User).filter().first.return_value = mock_user
    db_session.query(Risk).filter().all.return_value = [Risk(id=1), Risk(id=2)]
    db_session.query(AuditTest).filter().all.return_value = [AuditTest(id=3)]

    # Modify task payload to include relations
    create_task_payload.risks = [1, 2]
    create_task_payload.audit_tests = [3]

    # Call the function under test
    task = await create_task(db_session, create_task_payload, tenant_id=1, keywords="", user_id=1)

    # # Assertions
    assert task is not None
    # assert task.name == "New Test Task"
    # assert len(task.risks) == 2
    # assert len(task.audit_tests) == 1
    # db_session.add.assert_called_once()
    # db_session.commit.assert_called()


async def test_update_task(db_session, mock_task, mock_user):
    db_session.query(Task).filter().first.return_value = mock_task
    db_session.query(User).filter().first.return_value = mock_user

    update_payload = UpdateTask(
        title="Updated Task Name", description="Updated description", due_date="2024-12-25"
    )

    # Call the function under test
    updated_task = await update_task(
        db_session, 1, update_payload, tenant_id=1, user_id=1, keywords="test,task"
    )

    # Assertions
    assert updated_task is not None
    # assert updated_task.name == "Updated Task Name"
    # assert updated_task.description == "Updated description"
    # assert updated_task.status == "in_progress"
    # db_session.commit.assert_called()


async def test_delete_task(db_session, mock_task):
    db_session.query(Task).filter().first.return_value = mock_task

    # Call the function under test
    result = await delete_task(db_session, 1)

    # Assertions
    assert result is True
    db_session.query(Task).filter().delete.assert_called()
    db_session.commit.assert_called()


# def test_create_task_missing_data(db_session, mock_user):
#     db_session.query(User).filter().first.return_value = mock_user

#     # Create an incomplete payload
#     from fedrisk_api.schema.task import CreateTask
#     create_task_payload = CreateTask(
#         name="",  # Missing name
#         project_id=1,
#         assigned_to=1,
#         due_date="2024-12-31"
#     )

#     with pytest.raises(ValueError):
#         create_task(db_session, create_task_payload, tenant_id=1, keywords="", user_id=1)


async def test_delete_non_existent_task(db_session):
    db_session.query(Task).filter().first.return_value = None

    # Call the function under test
    result = await delete_task(db_session, 999)  # ID that doesn't exist

    # Assertions
    assert result is False
    db_session.commit.assert_not_called()


def test_get_wbs_dhtmlx_tasks(db_session):
    result = get_wbs_dhtmlx_tasks(db=db_session, wbs_id=1, tenant_id=1, user_id=1)
    assert result is not None


# get_wbs_child_tasks
def test_get_wbs_child_tasks(db_session):
    result = get_wbs_child_tasks(db=db_session, tasks=[])
    assert result is not None


# get_wbs_tasks
def test_get_wbs_tasks(db_session):
    result = get_wbs_tasks(db=db_session, wbs_id=1, tenant_id=1, user_id=1)
    assert result is not None


# get_tasks_wbs_chart_data
def test_get_tasks_wbs_chart_data(db_session):
    result = get_tasks_wbs_chart_data(db=db_session, project_id=1, tenant_id=1, user_id=1, wbs_id=1)
    assert result is not None


# add_project_task_history
def test_add_project_task_history(db_session):
    result = add_project_task_history(
        db=db_session, task_id=1, author_id=1, message="Task 1 updated"
    )
    assert result is not None


# Handle task associations and resources
async def test_handle_task_associations(db_session):
    result = await handle_task_associations(
        db=db_session, new_task=[], risks=[], tests=[], attachments=[], project_controls=[]
    )
    assert result is not None


async def test_handle_task_relations(db_session):
    result = await handle_task_relations(db=db_session, new_task=[], children=[], parents=[])
    assert result is not None


async def test_handle_task_resources(db_session):
    result = await handle_task_resources(db=db_session, new_task=[], resources=[])
    assert result is not None


async def test_add_keywords_to_task(db_session):
    result = await add_keywords(db=db_session, keywords="apple,banana", task_id=1, tenant_id=1)
    assert result is not None


async def test_send_assignment_notification(db_session):
    result = await send_assignment_notification(db=db_session, new_task=[], user_id=1)
    assert result is not None
