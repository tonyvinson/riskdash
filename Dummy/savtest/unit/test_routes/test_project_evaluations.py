import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from fedrisk_api.schema.project_evaluation import (
    CreateProjectEvaluation,
    DisplayProjectEvaluation,
    UpdateProjectEvaluation,
)
from fedrisk_api.endpoints.project_evaluation import (
    create_project_evaluation,
    get_all_project_evaluations,
    get_project_evaluation_by_id,
    update_project_evaluation_by_id,
    delete_project_evaluation_by_id,
)

# Fixtures


@pytest.fixture
def mock_db_session():
    return Mock()


@pytest.fixture
def sample_user():
    return {"tenant_id": 1, "user_id": 1}


@pytest.fixture
def sample_project_evaluation():
    return DisplayProjectEvaluation(id=1, name="Sample Project Evaluation")


@pytest.fixture
def project_evaluation_request():
    return CreateProjectEvaluation(name="New Evaluation", project_id=1)


@pytest.fixture
def update_project_evaluation_request():
    return UpdateProjectEvaluation(name="Updated Evaluation")


# Tests

# Test create_project_evaluation
@patch("project_evaluations_router.db_project_evaluation.create_project_evaluation")
async def test_create_project_evaluation_success(
    mock_create_evaluation,
    mock_db_session,
    sample_user,
    project_evaluation_request,
    sample_project_evaluation,
):
    mock_create_evaluation.return_value = sample_project_evaluation

    response = await create_project_evaluation(
        request=project_evaluation_request,
        db=mock_db_session,
        user=sample_user,
    )

    assert response == sample_project_evaluation
    mock_create_evaluation.assert_called_once()


@patch("project_evaluations_router.db_project_evaluation.create_project_evaluation")
async def test_create_project_evaluation_not_found(
    mock_create_evaluation, mock_db_session, sample_user, project_evaluation_request
):
    mock_create_evaluation.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        await create_project_evaluation(
            request=project_evaluation_request,
            db=mock_db_session,
            user=sample_user,
        )

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert "tenant with specified id does not have project id" in str(excinfo.value.detail)
    mock_create_evaluation.assert_called_once()


@patch("project_evaluations_router.db_project_evaluation.create_project_evaluation")
async def test_create_project_evaluation_integrity_error(
    mock_create_evaluation, mock_db_session, sample_user, project_evaluation_request
):
    mock_create_evaluation.side_effect = IntegrityError("mock", "params", "orig")

    with pytest.raises(HTTPException) as excinfo:
        await create_project_evaluation(
            request=project_evaluation_request,
            db=mock_db_session,
            user=sample_user,
        )

    assert excinfo.value.status_code == status.HTTP_409_CONFLICT
    assert "ProjectEvaluation with name" in str(excinfo.value.detail)
    mock_create_evaluation.assert_called_once()


# Test get_all_project_evaluations
@patch("project_evaluations_router.db_project_evaluation.get_all_project_evaluations")
def test_get_all_project_evaluations_success(
    mock_get_all_evaluations, mock_db_session, sample_user
):
    mock_get_all_evaluations.return_value = [DisplayProjectEvaluation(id=1, name="Evaluation 1")]

    response = get_all_project_evaluations(
        db=mock_db_session,
        user=sample_user,
    )

    assert response == [DisplayProjectEvaluation(id=1, name="Evaluation 1")]
    mock_get_all_evaluations.assert_called_once_with(
        mock_db_session, sample_user["tenant_id"], sample_user["user_id"]
    )


# Test get_project_evaluation_by_id
@patch("project_evaluations_router.db_project_evaluation.get_project_evaluation")
def test_get_project_evaluation_by_id_success(
    mock_get_evaluation, mock_db_session, sample_user, sample_project_evaluation
):
    mock_get_evaluation.return_value = sample_project_evaluation

    response = get_project_evaluation_by_id(
        id=1,
        db=mock_db_session,
        user=sample_user,
    )

    assert response == sample_project_evaluation
    mock_get_evaluation.assert_called_once_with(
        db=mock_db_session, id=1, tenant_id=sample_user["tenant_id"], user_id=sample_user["user_id"]
    )


@patch("project_evaluations_router.db_project_evaluation.get_project_evaluation")
def test_get_project_evaluation_by_id_not_found(mock_get_evaluation, mock_db_session, sample_user):
    mock_get_evaluation.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        get_project_evaluation_by_id(
            id=1,
            db=mock_db_session,
            user=sample_user,
        )

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert "ProjectEvaluation with id" in str(excinfo.value.detail)
    mock_get_evaluation.assert_called_once()


# Test update_project_evaluation_by_id
@patch("project_evaluations_router.db_project_evaluation.update_project_evaluation")
async def test_update_project_evaluation_success(
    mock_update_evaluation, mock_db_session, sample_user, update_project_evaluation_request
):
    mock_update_evaluation.return_value = True

    response = await update_project_evaluation_by_id(
        id=1,
        request=update_project_evaluation_request,
        db=mock_db_session,
        user=sample_user,
    )

    assert response == {"detail": "Successfully updated project_evaluation."}
    mock_update_evaluation.assert_called_once()


@patch("project_evaluations_router.db_project_evaluation.update_project_evaluation")
async def test_update_project_evaluation_not_found(
    mock_update_evaluation, mock_db_session, sample_user, update_project_evaluation_request
):
    mock_update_evaluation.return_value = False

    with pytest.raises(HTTPException) as excinfo:
        await update_project_evaluation_by_id(
            id=1,
            request=update_project_evaluation_request,
            db=mock_db_session,
            user=sample_user,
        )

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert "ProjectEvaluation with id" in str(excinfo.value.detail)
    mock_update_evaluation.assert_called_once()


# Test delete_project_evaluation_by_id
@patch("project_evaluations_router.db_project_evaluation.delete_project_evaluation")
async def test_delete_project_evaluation_success(
    mock_delete_evaluation, mock_db_session, sample_user
):
    mock_delete_evaluation.return_value = True

    response = await delete_project_evaluation_by_id(
        id=1,
        db=mock_db_session,
        user=sample_user,
    )

    assert response == {"detail": "Successfully deleted project_evaluation."}
    mock_delete_evaluation.assert_called_once()


@patch("project_evaluations_router.db_project_evaluation.delete_project_evaluation")
async def test_delete_project_evaluation_not_found(
    mock_delete_evaluation, mock_db_session, sample_user
):
    mock_delete_evaluation.return_value = False

    with pytest.raises(HTTPException) as excinfo:
        await delete_project_evaluation_by_id(
            id=1,
            db=mock_db_session,
            user=sample_user,
        )

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert "ProjectEvaluation with id" in str(excinfo.value.detail)
    mock_delete_evaluation.assert_called_once()
