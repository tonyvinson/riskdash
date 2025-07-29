import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from unittest.mock import MagicMock

from main import app  # Assuming your FastAPI app is defined in `main.py`
from fedrisk_api.schema.exception import CreateException, UpdateException
from fedrisk_api.db import exception as db_exception
from fedrisk_api.utils.authentication import custom_auth

from sqlalchemy.orm import Session

client = TestClient(app)
get_db = Session
# Mock the `get_db` and `custom_auth` dependency
@pytest.fixture
def mock_db():
    db = MagicMock()
    yield db


@pytest.fixture
def mock_user():
    return {"tenant_id": 1, "user_id": 1}


# Mock authentication and database dependency
app.dependency_overrides[custom_auth] = lambda: {"tenant_id": 1, "user_id": 1}
app.dependency_overrides[get_db] = mock_db

### Test: Create Exception ###
def test_create_exception_success(mock_db, mock_user, mocker):
    # Arrange
    request_data = {
        "name": "Test Exception",
        "project_control_id": 1,
        "owner_id": 1,
    }

    # Mock DB function to return the new exception object
    mock_db_exception = mocker.patch(
        "fedrisk_api.db.exception.create_exception", return_value=request_data
    )

    # Act
    response = client.post("/exceptions/", json=request_data)

    # Assert
    assert response.status_code == 200
    assert response.json() == request_data
    mock_db_exception.assert_called_once()


def test_create_exception_duplicate(mock_db, mock_user, mocker):
    # Arrange
    request_data = {
        "name": "Duplicate Exception",
        "project_control_id": 1,
        "owner_id": 1,
    }

    # Mock the DB function to raise an IntegrityError for duplicates
    mock_db_exception = mocker.patch(
        "fedrisk_api.db.exception.create_exception",
        side_effect=IntegrityError("UNIQUE constraint failed", None, None),
    )

    # Act
    response = client.post("/exceptions/", json=request_data)

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == "An Exception already exists for the target Project Control"
    mock_db_exception.assert_called_once()


def test_create_exception_invalid_foreign_key(mock_db, mock_user, mocker):
    # Arrange
    request_data = {
        "name": "Test Exception",
        "project_control_id": 1,
        "owner_id": 999,  # Invalid owner_id
    }

    # Mock the DB function to raise an IntegrityError for foreign key constraint
    mock_db_exception = mocker.patch(
        "fedrisk_api.db.exception.create_exception",
        side_effect=IntegrityError("foreign key constraint failed", None, None),
    )

    # Act
    response = client.post("/exceptions/", json=request_data)

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == "Owner with Id '999' does not exists"
    mock_db_exception.assert_called_once()


### Test: Get All Exceptions ###
def test_get_all_exceptions(mock_db, mock_user, mocker):
    # Arrange
    expected_data = [
        {"id": 1, "name": "Test Exception 1", "project_control_id": 1, "owner_id": 1},
        {"id": 2, "name": "Test Exception 2", "project_control_id": 2, "owner_id": 1},
    ]

    # Mock the DB function to return a list of exceptions
    mock_db_exception = mocker.patch(
        "fedrisk_api.db.exception.get_all_exceptions", return_value=expected_data
    )

    # Act
    response = client.get("/exceptions/")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_data
    mock_db_exception.assert_called_once()


### Test: Get Exception By ID ###
def test_get_exception_by_id_success(mock_db, mock_user, mocker):
    # Arrange
    expected_data = {"id": 1, "name": "Test Exception", "project_control_id": 1, "owner_id": 1}

    # Mock the DB function to return a single exception object
    mock_db_exception = mocker.patch(
        "fedrisk_api.db.exception.get_exception", return_value=expected_data
    )

    # Act
    response = client.get("/exceptions/1")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_data
    mock_db_exception.assert_called_once()


def test_get_exception_by_id_not_found(mock_db, mock_user, mocker):
    # Arrange
    mock_db_exception = mocker.patch(
        "fedrisk_api.db.exception.get_exception", return_value=None  # Simulate no exception found
    )

    # Act
    response = client.get("/exceptions/999")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Exception with id 999 does not exist"
    mock_db_exception.assert_called_once()


### Test: Update Exception ###
def test_update_exception_success(mock_db, mock_user, mocker):
    # Arrange
    request_data = {"name": "Updated Exception", "owner_id": 1}

    # Mock the DB function to return a successful update
    mock_db_exception = mocker.patch("fedrisk_api.db.exception.update_exception", return_value=True)

    # Act
    response = client.put("/exceptions/1", json=request_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["id"] == 1
    mock_db_exception.assert_called_once()


def test_update_exception_not_found(mock_db, mock_user, mocker):
    # Arrange
    request_data = {"name": "Updated Exception", "owner_id": 1}

    # Mock the DB function to return `None` (not found)
    mock_db_exception = mocker.patch(
        "fedrisk_api.db.exception.update_exception", return_value=False
    )

    # Act
    response = client.put("/exceptions/999", json=request_data)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Exception with id 999 does not exist"
    mock_db_exception.assert_called_once()


### Test: Delete Exception ###
def test_delete_exception_success(mock_db, mock_user, mocker):
    # Arrange
    mock_db_exception = mocker.patch("fedrisk_api.db.exception.delete_exception", return_value=True)

    mock_delete_documents = mocker.patch(
        "fedrisk_api.utils.utils.delete_documents_for_fedrisk_object"
    )

    # Act
    response = client.delete("/exceptions/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted exception."
    mock_db_exception.assert_called_once()
    mock_delete_documents.assert_called_once()


def test_delete_exception_not_found(mock_db, mock_user, mocker):
    # Arrange
    mock_db_exception = mocker.patch(
        "fedrisk_api.db.exception.delete_exception", return_value=False
    )

    mock_delete_documents = mocker.patch(
        "fedrisk_api.utils.utils.delete_documents_for_fedrisk_object"
    )

    # Act
    response = client.delete("/exceptions/999")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Exception with id 999 does not exist"
    mock_db_exception.assert_called_once()
    mock_delete_documents.assert_not_called()
