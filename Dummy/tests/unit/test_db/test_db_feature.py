import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.models import Feature, FeatureProject
from fedrisk_api.schema.feature import (
    CreateFeature,
    UpdateFeature,
    CreateFeatureProject,
    UpdateFeatureProject,
)
from fedrisk_api.db import feature

# Mock session fixture
@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    yield db


# Tenant id mock
@pytest.fixture
def tenant_id():
    return 1


### Test: Feature Functions ###


# def test_create_feature(mock_db, tenant_id):
#     # Arrange
#     new_feature_data = CreateFeature(name="Test Feature", is_active=True)
#     expected_feature = Feature(id=1, name="Test Feature", is_active=True, tenant_id=tenant_id)

#     # Mock the add and commit calls
#     mock_db.add.return_value = None
#     mock_db.commit.return_value = None

#     # Act
#     created_feature = feature.create_feature(new_feature_data, mock_db, tenant_id)

#     # Assert
#     mock_db.add.assert_called_once()
#     mock_db.commit.assert_called_once()
#     assert created_feature.name == expected_feature.name
#     assert created_feature.tenant_id == expected_feature.tenant_id


def test_get_feature(mock_db, tenant_id, mocker):
    # Arrange
    expected_features = [Feature(id=1, name="Test Feature", tenant_id=tenant_id)]

    mock_filter_by_tenant = mocker.patch(
        "fedrisk_api.utils.utils.filter_by_tenant", return_value=expected_features
    )

    # Act
    features = feature.get_feature(mock_db, tenant_id)

    # Assert
    # assert len(features) == 1
    # assert features[0].name == "Test Feature"
    # mock_filter_by_tenant.assert_called_once_with(db=mock_db, model=Feature, tenant_id=tenant_id)


def test_update_feature_by_id(mock_db, tenant_id):
    # Arrange
    update_data = UpdateFeature(name="Updated Feature")
    mock_db.query.return_value.filter.return_value.first.return_value = True

    # Act
    result = feature.update_feature_by_id(update_data, mock_db, feature_id=1, tenant_id=tenant_id)

    # Assert
    assert result is True
    mock_db.commit.assert_called_once()


def test_delete_feature_by_id_success(mock_db, tenant_id):
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = Feature(
        id=1, name="Test Feature", tenant_id=tenant_id
    )

    # Act
    result = feature.delete_feature_by_id(mock_db, tenant_id=tenant_id, feature_id=1)

    # Assert
    assert result is True
    mock_db.commit.assert_called_once()


def test_delete_feature_by_id_not_found(mock_db, tenant_id):
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Act
    result = feature.delete_feature_by_id(mock_db, tenant_id=tenant_id, feature_id=1)

    # Assert
    assert result is False
    mock_db.commit.assert_not_called()


### Test: FeatureProject Functions ###


def test_create_feature_project(mock_db):
    # Arrange
    new_feature_project_data = CreateFeatureProject(feature_id=1, project_id=1, is_active=True)
    expected_feature_project = FeatureProject(id=1, feature_id=1, project_id=1, is_active=True)

    # Mock the add and commit calls
    mock_db.add.return_value = None
    mock_db.commit.return_value = None

    # Act
    created_feature_project = feature.create_feature_project(new_feature_project_data, mock_db)

    # Assert
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    # assert created_feature_project.feature_id == expected_feature_project.feature_id
    # assert created_feature_project.project_id == expected_feature_project.project_id


def test_get_feature_project_by_id(mock_db):
    # Arrange
    expected_feature_project = FeatureProject(id=1, feature_id=1, project_id=1)
    mock_db.query.return_value.join.return_value.filter.return_value.filter.return_value.first.return_value = (
        expected_feature_project
    )

    # Act
    feature_project = feature.get_feature_project_by_id(mock_db, feature_project_id=1)

    # Assert
    assert feature_project.feature_id == expected_feature_project.feature_id
    assert feature_project.project_id == expected_feature_project.project_id


def test_update_feature_project_by_id(mock_db):
    # Arrange
    update_data = UpdateFeatureProject(project_id=2)
    mock_db.query.return_value.filter.return_value.first.return_value = True

    # Act
    result = feature.update_feature_project_by_id(update_data, mock_db, id=1)

    # Assert
    assert result is True
    mock_db.commit.assert_called_once()


def test_delete_feature_project_by_id_success(mock_db):
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = FeatureProject(
        id=1, feature_id=1, project_id=1
    )

    # Act
    result = feature.delete_feature_project_by_id(mock_db, id=1)

    # Assert
    assert result is True
    mock_db.commit.assert_called_once()


def test_delete_feature_project_by_id_not_found(mock_db):
    # Arrange
    mock_db.query.return_value.filter.return_value.first.return_value = None

    # Act
    result = feature.delete_feature_project_by_id(mock_db, id=1)

    # Assert
    assert result is False
    mock_db.commit.assert_not_called()
