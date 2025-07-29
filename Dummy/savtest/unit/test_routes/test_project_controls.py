import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from fedrisk_api.db.project import (
    NO_SUCH_PROJECT,
    NO_SUCH_CONTROL,
    PROJECT_CONTROL_ALREADY_EXISTS,
)
from fedrisk_api.schema.project import DisplayProject, DisplayProjectControl
from fedrisk_api.endpoints.project_control import (
    add_control_to_project,
    get_project_control_by_id,
    update_project_control,
)

# Fixtures


@pytest.fixture
def mock_db_session():
    return Mock()


@pytest.fixture
def sample_user():
    return {"tenant_id": 1, "user_id": 1}


@pytest.fixture
def sample_project_control():
    return DisplayProjectControl(id=1, name="Sample Control")


@pytest.fixture
def sample_project():
    return DisplayProject(id=1, name="Sample Project")


@pytest.fixture
def control_id():
    return 1


@pytest.fixture
def project_id():
    return 1


# Tests

# Test add_control_to_project
@patch("project_controls_router.db_project.add_control_to_project")
async def test_add_control_to_project_success(
    mock_add_control, mock_db_session, sample_user, project_id, control_id, sample_project
):
    mock_add_control.return_value = sample_project

    response = await add_control_to_project(
        project_id=project_id,
        control_id=control_id,
        db=mock_db_session,
        user=sample_user,
    )

    assert response == sample_project
    mock_add_control.assert_called_once()


@patch("project_controls_router.db_project.add_control_to_project")
async def test_add_control_to_project_no_such_project(
    mock_add_control, mock_db_session, sample_user, project_id, control_id
):
    mock_add_control.return_value = NO_SUCH_PROJECT

    with pytest.raises(HTTPException) as excinfo:
        await add_control_to_project(
            project_id=project_id,
            control_id=control_id,
            db=mock_db_session,
            user=sample_user,
        )

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert str(excinfo.value.detail) == f"Project with id '{project_id}' does not exist"
    mock_add_control.assert_called_once()


@patch("project_controls_router.db_project.add_control_to_project")
async def test_add_control_to_project_integrity_error(
    mock_add_control, mock_db_session, sample_user, project_id, control_id
):
    mock_add_control.side_effect = IntegrityError("mock", "params", "orig")

    with pytest.raises(HTTPException) as excinfo:
        await add_control_to_project(
            project_id=project_id,
            control_id=control_id,
            db=mock_db_session,
            user=sample_user,
        )

    assert excinfo.value.status_code == status.HTTP_409_CONFLICT
    assert "already contains Control" in excinfo.value.detail
    mock_add_control.assert_called_once()


# Test get_project_control_by_id
@patch("project_controls_router.db_project.get_project_control_by_id")
def test_get_project_control_by_id_success(
    mock_get_project_control, mock_db_session, sample_user, sample_project_control
):
    mock_get_project_control.return_value = sample_project_control

    response = get_project_control_by_id(
        project_control_id=1,
        db=mock_db_session,
        user=sample_user,
    )

    assert response == sample_project_control
    mock_get_project_control.assert_called_once_with(db=mock_db_session, project_control_id=1)


# Test update_project_control
@patch("project_controls_router.db_project.update_control_on_project")
async def test_update_project_control_success(
    mock_update_control, mock_db_session, sample_user, project_id, control_id, sample_project
):
    mock_update_control.return_value = sample_project

    response = await update_project_control(
        project_id=project_id,
        control_id=control_id,
        db=mock_db_session,
        user=sample_user,
    )

    assert response == sample_project
    mock_update_control.assert_called_once()


@patch("project_controls_router.db_project.update_control_on_project")
async def test_update_project_control_no_such_project(
    mock_update_control, mock_db_session, sample_user, project_id, control_id
):
    mock_update_control.return_value = NO_SUCH_PROJECT

    with pytest.raises(HTTPException) as excinfo:
        await update_project_control(
            project_id=project_id,
            control_id=control_id,
            db=mock_db_session,
            user=sample_user,
        )

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert str(excinfo.value.detail) == f"Project with id '{project_id}' does not exist"
    mock_update_control.assert_called_once()


@patch("project_controls_router.db_project.update_control_on_project")
async def test_update_project_control_no_such_control(
    mock_update_control, mock_db_session, sample_user, project_id, control_id
):
    mock_update_control.return_value = NO_SUCH_CONTROL

    with pytest.raises(HTTPException) as excinfo:
        await update_project_control(
            project_id=project_id,
            control_id=control_id,
            db=mock_db_session,
            user=sample_user,
        )

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert str(excinfo.value.detail) == f"Control with id '{control_id}' does not exist"
    mock_update_control.assert_called_once()
