import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, DataError, ProgrammingError

from fedrisk_api.schema.framework_version import (
    CreateFrameworkVersion,
    DisplayFrameworkVersion,
    UpdateFrameworkVersion,
)
from fedrisk_api.endpoints.framework_version import (
    create_framework_version,
    get_all_framework_versions,
    get_framework_by_version_id,
    update_framework_version_by_id,
    delete_framework_version_by_id,
)

# Fixtures


@pytest.fixture
def mock_db_session():
    return Mock()


@pytest.fixture
def sample_user():
    return {"tenant_id": 1, "user_id": 1}


@pytest.fixture
def sample_framework_version():
    return DisplayFrameworkVersion(id=1, name="Sample Framework Version")


@pytest.fixture
def create_framework_request():
    return CreateFrameworkVersion(name="New Framework Version")


@pytest.fixture
def update_framework_request():
    return UpdateFrameworkVersion(name="Updated Framework Version")


# Tests

# Test create_framework_version
@patch("framework_versions_router.db_framework_version.create_framework_version")
def test_create_framework_version_success(
    mock_create_framework,
    mock_db_session,
    sample_user,
    create_framework_request,
    sample_framework_version,
):
    mock_create_framework.return_value = sample_framework_version

    response = create_framework_version(
        request=create_framework_request,
        db=mock_db_session,
        user=sample_user,
    )

    assert response == sample_framework_version
    mock_create_framework.assert_called_once()


@patch("framework_versions_router.db_framework_version.create_framework_version")
def test_create_framework_version_integrity_error(
    mock_create_framework, mock_db_session, sample_user, create_framework_request
):
    mock_create_framework.side_effect = IntegrityError("mock", "params", "orig")

    with pytest.raises(HTTPException) as excinfo:
        create_framework_version(
            request=create_framework_request,
            db=mock_db_session,
            user=sample_user,
        )

    assert excinfo.value.status_code == status.HTTP_409_CONFLICT
    assert "Framework with name" in str(excinfo.value.detail)
    mock_create_framework.assert_called_once()


# Test get_all_framework_versions
@patch("framework_versions_router.db_framework_version.get_all_framework_versions")
def test_get_all_framework_versions_success(mock_get_all, mock_db_session, sample_user):
    mock_get_all.return_value = [DisplayFrameworkVersion(id=1, name="Framework 1")]

    response = get_all_framework_versions(
        db=mock_db_session,
        user=sample_user,
    )

    assert response["items"] == [DisplayFrameworkVersion(id=1, name="Framework 1")]
    mock_get_all.assert_called_once()


@patch("framework_versions_router.db_framework_version.get_all_framework_versions")
def test_get_all_framework_versions_data_error(mock_get_all, mock_db_session, sample_user):
    mock_get_all.side_effect = DataError("mock", "params", "orig")

    with pytest.raises(HTTPException) as excinfo:
        get_all_framework_versions(db=mock_db_session, user=sample_user)

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Please provide correct filter_value" in str(excinfo.value.detail)
    mock_get_all.assert_called_once()


# Test get_framework_by_version_id
@patch("framework_versions_router.db_framework_version.get_framework_version")
def test_get_framework_by_version_id_success(
    mock_get_framework, mock_db_session, sample_user, sample_framework_version
):
    mock_get_framework.return_value = sample_framework_version

    response = get_framework_by_version_id(
        id=1,
        db=mock_db_session,
        user=sample_user,
    )

    assert response == sample_framework_version
    mock_get_framework.assert_called_once_with(db=mock_db_session, id=1)


@patch("framework_versions_router.db_framework_version.get_framework_version")
def test_get_framework_by_version_id_not_found(mock_get_framework, mock_db_session, sample_user):
    mock_get_framework.return_value = None

    with pytest.raises(HTTPException) as excinfo:
        get_framework_by_version_id(id=1, db=mock_db_session, user=sample_user)

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Framework with id" in str(excinfo.value.detail)
    mock_get_framework.assert_called_once()


# Test update_framework_version_by_id
@patch("framework_versions_router.db_framework_version.update_framework_version")
def test_update_framework_version_success(
    mock_update_framework, mock_db_session, sample_user, update_framework_request
):
    mock_update_framework.return_value = True

    response = update_framework_version_by_id(
        id=1,
        request=update_framework_request,
        db=mock_db_session,
        user=sample_user,
    )

    assert response == {"detail": "Successfully updated framework version."}
    mock_update_framework.assert_called_once()


@patch("framework_versions_router.db_framework_version.update_framework_version")
def test_update_framework_version_not_found(
    mock_update_framework, mock_db_session, sample_user, update_framework_request
):
    mock_update_framework.return_value = False

    with pytest.raises(HTTPException) as excinfo:
        update_framework_version_by_id(
            id=1,
            request=update_framework_request,
            db=mock_db_session,
            user=sample_user,
        )

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Framework version with id" in str(excinfo.value.detail)
    mock_update_framework.assert_called_once()


# Test delete_framework_version_by_id
@patch("framework_versions_router.db_framework_version.delete_framework_version")
def test_delete_framework_version_success(mock_delete_framework, mock_db_session, sample_user):
    mock_delete_framework.return_value = True

    response = delete_framework_version_by_id(
        id=1,
        db=mock_db_session,
        user=sample_user,
    )

    assert response == {"detail": "Successfully deleted framework version."}
    mock_delete_framework.assert_called_once()


@patch("framework_versions_router.db_framework_version.delete_framework_version")
def test_delete_framework_version_not_found(mock_delete_framework, mock_db_session, sample_user):
    mock_delete_framework.return_value = False

    with pytest.raises(HTTPException) as excinfo:
        delete_framework_version_by_id(id=1, db=mock_db_session, user=sample_user)

    assert excinfo.value.status_code == status.HTTP_404_NOT_FOUND
    assert "Framework version with id" in str(excinfo.value.detail)
    mock_delete_framework.assert_called_once()
