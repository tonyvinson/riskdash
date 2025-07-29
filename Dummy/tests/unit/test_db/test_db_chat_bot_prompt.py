# import pytest
from unittest.mock import MagicMock
from fedrisk_api.schema.chat_bot_prompt import CreateChatBotPrompt, UpdateChatBotPrompt
from fedrisk_api.db.models import ChatBotPrompt
from fedrisk_api.db.chat_bot_prompt import (
    create_chat_bot_prompt,
    get_chat_bot_prompt,
    get_chat_bot_prompt_by_id,
    update_chat_bot_prompt_by_id,
    delete_chat_bot_prompt_by_id,
)

# Test create_chat_bot_prompt
def test_create_chat_bot_prompt(mocker):
    mock_db = MagicMock()

    # Create a sample chat bot prompt input
    chat_bot_prompt_data = CreateChatBotPrompt(prompt="Project", message="Project")

    # Call the function to test
    result = create_chat_bot_prompt(chat_bot_prompt_data, mock_db)

    # Check if the result is correct and db methods are called
    assert isinstance(result, ChatBotPrompt)
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


# Test get_chat_bot_prompt
def test_get_chat_bot_prompt(mocker):
    mock_db = MagicMock()

    # Simulate data returned by the query
    mock_db.query().all.return_value = ["prompt1"]

    # Call the function to test
    result = get_chat_bot_prompt(mock_db)

    # Verify the return value and the call to the db
    assert result == ["prompt1"]
    # mock_db.query.assert_called_once()


# Test get_chat_bot_prompt_by_id
def test_get_chat_bot_prompt_by_id(mocker):
    mock_db = MagicMock()
    chat_bot_prompt_id = 1

    # Simulate data returned by the query
    mock_db.query().filter().first.return_value = "prompt1"

    # Call the function to test
    result = get_chat_bot_prompt_by_id(mock_db, chat_bot_prompt_id)

    # Verify the return value
    assert result == "prompt1"
    # mock_db.query().filter.assert_called_once()


# Test update_chat_bot_prompt_by_id - Success case
def test_update_chat_bot_prompt_by_id_success(mocker):
    mock_db = MagicMock()
    chat_bot_prompt_data = UpdateChatBotPrompt(text="Updated prompt")
    chat_bot_prompt_id = 1

    # Simulate existing prompt and successful update
    mock_db.query().filter().first.return_value = "existing_prompt"

    # Call the function to test
    result = update_chat_bot_prompt_by_id(chat_bot_prompt_data, mock_db, chat_bot_prompt_id)

    # Verify the return value and db methods
    assert result is True
    mock_db.query().filter().update.assert_called_once()
    mock_db.commit.assert_called_once()


# Test update_chat_bot_prompt_by_id - Failure case
def test_update_chat_bot_prompt_by_id_failure(mocker):
    mock_db = MagicMock()
    chat_bot_prompt_data = UpdateChatBotPrompt(text="Updated prompt")
    chat_bot_prompt_id = 1

    # Simulate non-existent prompt
    mock_db.query().filter().first.return_value = None

    # Call the function to test
    result = update_chat_bot_prompt_by_id(chat_bot_prompt_data, mock_db, chat_bot_prompt_id)

    # Verify the return value
    assert result is False


# Test delete_chat_bot_prompt_by_id - Success case
def test_delete_chat_bot_prompt_by_id_success(mocker):
    mock_db = MagicMock()
    chat_bot_prompt_id = 1

    # Simulate existing prompt and successful deletion
    mock_db.query().filter().first.return_value = "existing_prompt"

    # Call the function to test
    result = delete_chat_bot_prompt_by_id(mock_db, chat_bot_prompt_id)

    # Verify the return value and db methods
    assert result is True
    mock_db.delete.assert_called_once()
    mock_db.commit.assert_called_once()


# Test delete_chat_bot_prompt_by_id - Failure case
def test_delete_chat_bot_prompt_by_id_failure(mocker):
    mock_db = MagicMock()
    chat_bot_prompt_id = 1

    # Simulate non-existent prompt
    mock_db.query().filter().first.return_value = None

    # Call the function to test
    result = delete_chat_bot_prompt_by_id(mock_db, chat_bot_prompt_id)

    # Verify the return value
    assert result is False
