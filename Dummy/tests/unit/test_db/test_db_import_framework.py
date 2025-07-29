import pytest
from unittest.mock import MagicMock
from fedrisk_api.db.models import ImportFramework, User
from fedrisk_api.db.import_framework import (
    get_user_framework_import,
    create_import_framework,
    get_all_import_frameworks,
    get_import_framework,
    delete_import_framework,
)
from fedrisk_api.schema.import_framework import CreateImportFramework


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def tenant_id():
    return 1


### Test: get_user_framework_import ###
def test_get_user_framework_import(mock_db):
    # Arrange
    mock_user = User(id=1, email="test@test.com")
    mock_db.query().filter().first.return_value = mock_user

    # Act
    user_details = get_user_framework_import(mock_db, user_id=1)

    # Assert
    assert user_details.id == 1
    assert user_details.email == "test@test.com"
    # mock_db.query().filter.assert_called_once()


### Test: create_import_framework ###
def test_create_import_framework(mock_db, tenant_id):
    # Arrange
    framework_data = CreateImportFramework(name="Test Framework", description="Sample description")
    mock_framework = ImportFramework(id=1, name="Test Framework", tenant_id=tenant_id)

    mock_db.add = MagicMock()
    mock_db.commit = MagicMock()
    mock_db.refresh = MagicMock()

    # Act
    new_framework = create_import_framework(mock_db, framework_data, "application/pdf", tenant_id)

    # Assert
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    assert new_framework is not None
    assert new_framework.tenant_id == tenant_id


### Test: get_all_import_frameworks ###
def test_get_all_import_frameworks(mock_db, tenant_id):
    # Arrange
    mock_db.query().filter().all.return_value = [
        ImportFramework(id=1, name="Framework 1", tenant_id=tenant_id)
    ]

    # Act
    frameworks = get_all_import_frameworks(mock_db, tenant_id)

    # Assert
    # assert len(frameworks) == 1
    # assert frameworks[0].name == "Framework 1"
    # mock_db.query().filter.assert_called_once()


### Test: get_import_framework ###
def test_get_import_framework(mock_db, tenant_id):
    # Arrange
    mock_framework = ImportFramework(id=1, name="Test Framework", tenant_id=tenant_id)
    mock_db.query().filter().first.return_value = mock_framework

    # Act
    framework = get_import_framework(mock_db, id=1, tenant_id=tenant_id)

    # Assert
    # assert framework.id == 1
    # assert framework.name == "Test Framework"
    # mock_db.query().filter.assert_called_once()


### Test: delete_import_framework ###
def test_delete_import_framework(mock_db, tenant_id):
    # Arrange
    mock_db.query().filter().first.return_value = ImportFramework(
        id=1, name="Test Framework", tenant_id=tenant_id
    )

    # Act
    result = delete_import_framework(mock_db, id=1, tenant_id=tenant_id)

    # Assert
    assert result is True
    # mock_db.query().filter().delete.assert_called_once()
    # mock_db.commit.assert_called_once()


def test_delete_import_framework_not_found(mock_db, tenant_id):
    # Arrange
    mock_db.query().filter().first.return_value = None  # Framework not found

    # Act
    result = delete_import_framework(mock_db, id=999, tenant_id=tenant_id)

    # Assert
    # assert result is False
    # mock_db.query().filter.assert_called_once()
    # mock_db.commit.assert_not_called()
