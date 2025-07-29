import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from unittest.mock import MagicMock
from main import app  # Assuming your FastAPI app is defined in `main.py`
from fedrisk_api.db import feature as db_feature
from fedrisk_api.schema.feature import (
    CreateFeature,
    UpdateFeature,
    CreateFeatureProject,
    UpdateFeatureProject,
)

client = TestClient(app)

# Mock session fixture
@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_user():
    return {"tenant_id": 1, "user_id": 123}


### Test: Feature Routes ###


def test_create_feature_success(mock_db, mock_user, mocker):
    # Arrange
    mocker.patch("fedrisk_api.db.database.get_db", return_value=mock_db)
    mocker.patch("fedrisk_api.utils.authentication.custom_auth", return_value=mock_user)
    feature_data = {
        "name": "Test Feature",
        "description": "A test feature",
    }

    mock_create_feature = mocker.patch(
        "fedrisk_api.db.feature.create_feature", return_value=feature_data
    )

    # Act
    response = client.post("/features/", json=feature_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Test Feature"
    mock_create_feature.assert_called_once()


def test_create_feature_duplicate_error(mock_db, mock_user, mocker):
    # Arrange
    mocker.patch("fedrisk_api.db.database.get_db", return_value=mock_db)
    mocker.patch("fedrisk_api.utils.authentication.custom_auth", return_value=mock_user)
    feature_data = {
        "name": "Duplicate Feature",
        "description": "A test feature",
    }

    mocker.patch("fedrisk_api.db.feature.create_feature", side_effect=IntegrityError("", {}, None))

    # Act
    response = client.post("/features/", json=feature_data)

    # Assert
    assert response.status_code == 409
    assert response.json()["detail"] == "Feature with name 'Duplicate Feature' already exists"


def test_get_all_features(mock_db, mock_user, mocker):
    # Arrange
    mocker.patch("fedrisk_api.db.database.get_db", return_value=mock_db)
    mocker.patch("fedrisk_api.utils.authentication.custom_auth", return_value=mock_user)
    mocker.patch("fedrisk_api.db.feature.get_feature", return_value=[{"name": "Test Feature"}])

    # Act
    response = client.get("/features/")

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["name"] == "Test Feature"


def test_get_feature_by_id(mock_db, mock_user, mocker):
    # Arrange
    mocker.patch("fedrisk_api.db.database.get_db", return_value=mock_db)
    mocker.patch("fedrisk_api.utils.authentication.custom_auth", return_value=mock_user)
    mocker.patch("fedrisk_api.db.feature.get_feature_by_id", return_value={"name": "Test Feature"})

    # Act
    response = client.get("/features/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["name"] == "Test Feature"


def test_update_feature_by_id(mock_db, mock_user, mocker):
    # Arrange
    mocker.patch("fedrisk_api.db.database.get_db", return_value=mock_db)
    mocker.patch("fedrisk_api.utils.authentication.custom_auth", return_value=mock_user)
    update_data = {
        "name": "Updated Feature",
    }

    mock_update_feature = mocker.patch(
        "fedrisk_api.db.feature.update_feature_by_id", return_value=True
    )

    # Act
    response = client.put("/features/1", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated Feature."
    mock_update_feature.assert_called_once()


def test_delete_feature_by_id(mock_db, mock_user, mocker):
    # Arrange
    mocker.patch("fedrisk_api.db.database.get_db", return_value=mock_db)
    mocker.patch("fedrisk_api.utils.authentication.custom_auth", return_value=mock_user)
    mock_delete_feature = mocker.patch(
        "fedrisk_api.db.feature.delete_feature_by_id", return_value=True
    )

    # Act
    response = client.delete("/features/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted Feature."
    mock_delete_feature.assert_called_once()


### Test: FeatureProject Routes ###


def test_create_feature_project_success(mock_db, mock_user, mocker):
    # Arrange
    mocker.patch("fedrisk_api.db.database.get_db", return_value=mock_db)
    mocker.patch("fedrisk_api.utils.authentication.custom_auth", return_value=mock_user)
    project_data = {
        "feature_id": 1,
        "project_id": 1,
    }

    mock_create_feature_project = mocker.patch(
        "fedrisk_api.db.feature.create_feature_project", return_value=project_data
    )

    # Act
    response = client.post("/features/feature_project", json=project_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["feature_id"] == 1
    mock_create_feature_project.assert_called_once()


def test_get_feature_project_by_id(mock_db, mock_user, mocker):
    # Arrange
    mocker.patch("fedrisk_api.db.database.get_db", return_value=mock_db)
    mocker.patch("fedrisk_api.utils.authentication.custom_auth", return_value=mock_user)
    mocker.patch(
        "fedrisk_api.db.feature.get_feature_project_by_id",
        return_value={"feature_id": 1, "project_id": 1},
    )

    # Act
    response = client.get("/features/feature_project/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["feature_id"] == 1


def test_update_feature_project_by_id(mock_db, mock_user, mocker):
    # Arrange
    mocker.patch("fedrisk_api.db.database.get_db", return_value=mock_db)
    mocker.patch("fedrisk_api.utils.authentication.custom_auth", return_value=mock_user)
    update_data = {
        "project_id": 2,
    }

    mock_update_feature_project = mocker.patch(
        "fedrisk_api.db.feature.update_feature_project_by_id", return_value=True
    )

    # Act
    response = client.put("/features/feature_project/1", json=update_data)

    # Assert
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully updated Feature Project."
    mock_update_feature_project.assert_called_once()


def test_delete_feature_project_by_id(mock_db, mock_user, mocker):
    # Arrange
    mocker.patch("fedrisk_api.db.database.get_db", return_value=mock_db)
    mocker.patch("fedrisk_api.utils.authentication.custom_auth", return_value=mock_user)
    mock_delete_feature_project = mocker.patch(
        "fedrisk_api.db.feature.delete_feature_project_by_id", return_value=True
    )

    # Act
    response = client.delete("/features/feature_project/1")

    # Assert
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted Feature Project."
    mock_delete_feature_project.assert_called_once()
