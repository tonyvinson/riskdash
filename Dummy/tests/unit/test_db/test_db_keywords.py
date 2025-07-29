import pytest
from sqlalchemy.orm import Session
from unittest.mock import MagicMock
from fedrisk_api.db.models import Keyword, KeywordMapping
from fedrisk_api.schema.keyword import CreateKeyword, UpdateKeyword
from fedrisk_api.utils.utils import filter_by_tenant
from fedrisk_api.db.keyword import (
    create_keyword,
    get_keyword,
    get_all_keywords,
    update_keyword,
    delete_keyword,
)


@pytest.fixture
def mock_db():
    return MagicMock()


# Test create_keyword function
def test_create_keyword_success(mock_db):
    # Arrange
    mock_db = MagicMock(spec=Session)
    new_keyword_data = CreateKeyword(name="Test Keyword")
    tenant_id = 1
    mock_db.query(Keyword).filter().filter().first.return_value = None

    # Act
    result = create_keyword(mock_db, new_keyword_data, tenant_id)

    # Assert
    assert result is not False
    assert result.name == "Test Keyword"
    mock_db.add.assert_called_once_with(result)
    mock_db.commit.assert_called_once()


def test_create_keyword_duplicate(mock_db):
    # Arrange
    mock_db = MagicMock(spec=Session)
    new_keyword_data = CreateKeyword(name="Test Keyword")
    tenant_id = 1
    mock_db.query(Keyword).filter().filter().first.return_value = True

    # Act
    result = create_keyword(mock_db, new_keyword_data, tenant_id)

    # Assert
    assert result is False
    mock_db.commit.assert_not_called()


# Test get_keyword function
def test_get_keyword(mock_db):
    # Arrange
    mock_db = MagicMock(spec=Session)
    keyword_id = 1
    tenant_id = 1
    keyword_instance = Keyword(id=keyword_id, name="Test Keyword", tenant_id=tenant_id)
    mock_db.query(Keyword).filter_by().first.return_value = keyword_instance

    # Act
    result = get_keyword(mock_db, keyword_id, tenant_id)

    # Assert
    # assert result == keyword_instance


# Test get_all_keywords function
def test_get_all_keywords(mock_db):
    # Arrange
    mock_db = MagicMock(spec=Session)
    tenant_id = 1
    keywords = [
        Keyword(id=1, name="Keyword 1", tenant_id=tenant_id),
        Keyword(id=2, name="Keyword 2", tenant_id=tenant_id),
    ]
    mock_db.query(Keyword).filter_by().all.return_value = keywords

    # Act
    result = get_all_keywords(mock_db, tenant_id)

    # Assert
    # assert result == keywords


# Test update_keyword function
def test_update_keyword_success(mock_db):
    # Arrange
    mock_db = MagicMock(spec=Session)
    keyword_id = 1
    update_data = UpdateKeyword(id="1", name="Updated Keyword")
    existing_keyword = Keyword(id=keyword_id, name="Old Keyword")
    mock_db.query(Keyword).filter().first.return_value = existing_keyword

    # Act
    result = update_keyword(mock_db, keyword_id, update_data)

    # Assert
    # assert result.name == "Updated Keyword"
    # mock_db.commit.assert_called_once()


def test_update_keyword_not_found(mock_db):
    # Arrange
    mock_db = MagicMock(spec=Session)
    keyword_id = 1
    update_data = UpdateKeyword(id="1", name="Updated Keyword")
    mock_db.query(Keyword).filter().first.return_value = None

    # Act
    result = update_keyword(mock_db, keyword_id, update_data)

    # Assert
    assert result is False
    mock_db.commit.assert_not_called()


# Test delete_keyword function
def test_delete_keyword_success(mock_db):
    # Arrange
    mock_db = MagicMock(spec=Session)
    keyword_id = 1
    existing_keyword = Keyword(id=keyword_id, name="Old Keyword")
    mock_db.query(Keyword).filter().first.return_value = existing_keyword

    # Act
    result = delete_keyword(mock_db, keyword_id)

    # Assert
    assert result is True
    mock_db.commit.assert_called_once()


def test_delete_keyword_not_found(mock_db):
    # Arrange
    mock_db = MagicMock(spec=Session)
    keyword_id = 1
    mock_db.query(Keyword).filter().first.return_value = None

    # Act
    result = delete_keyword(mock_db, keyword_id)

    # Assert
    assert result is False
    mock_db.commit.assert_not_called()
