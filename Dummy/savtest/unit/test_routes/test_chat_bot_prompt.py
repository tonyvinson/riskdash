import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from fastapi import status

# from fedrisk_api import FastAPI  # Assuming 'app' is created in the main module
from main import app  # Adjust the import to your app module
from fedrisk_api.db import chat_bot_prompt as db_chat_bot_prompt
from fedrisk_api.schema.chat_bot_prompt import CreateChatBotPrompt, UpdateChatBotPrompt

from config.config import Settings

settings = Settings()

# app = FastAPI(title=settings.PROJECT_TITLE, version=settings.PROJECT_VERSION)

client = TestClient(app)

# Mock authentication and permissions
@pytest.fixture
def mock_auth_permission(mocker):
    mocker.patch("fedrisk_api.utils.authentication.custom_auth", return_value="mock_user")
    mocker.patch(
        "fedrisk_api.utils.permissions.create_chat_bot_prompt_permission", return_value=True
    )
    mocker.patch(
        "fedrisk_api.utils.permissions.delete_chat_bot_prompt_permission", return_value=True
    )
    mocker.patch(
        "fedrisk_api.utils.permissions.update_chat_bot_prompt_permission", return_value=True
    )
    mocker.patch("fedrisk_api.utils.permissions.view_chat_bot_prompt_permission", return_value=True)


# Test create_chat_bot_prompt
def test_create_chat_bot_prompt(mock_auth_permission, mocker):
    mock_db = MagicMock()

    # Mock the DB function to avoid real DB interaction
    mocker.patch(
        "fedrisk_api.db.chat_bot_prompt.create_chat_bot_prompt",
        return_value={"id": 1, "prompt": "Test Prompt"},
    )

    response = client.post("/chat_bot_prompts/", json={"prompt": "Test Prompt"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["prompt"] == "Test Prompt"


# Test create_chat_bot_prompt - IntegrityError
def test_create_chat_bot_prompt_integrity_error(mock_auth_permission, mocker):
    mock_db = MagicMock()

    # Simulate an IntegrityError from the DB
    mocker.patch(
        "fedrisk_api.db.chat_bot_prompt.create_chat_bot_prompt",
        side_effect=IntegrityError("duplicate", None, None),
    )

    response = client.post("/chat_bot_prompts/", json={"prompt": "Duplicate Prompt"})

    assert response.status_code == status.HTTP_409_CONFLICT
    assert "already exists" in response.json()["detail"]


# Test get_all_chat_bot_prompts
def test_get_all_chat_bot_prompts(mock_auth_permission, mocker):
    mock_db = MagicMock()

    # Mock the DB function
    mocker.patch(
        "fedrisk_api.db.chat_bot_prompt.get_chat_bot_prompt",
        return_value=[{"id": 1, "prompt": "Prompt 1"}, {"id": 2, "prompt": "Prompt 2"}],
    )

    response = client.get("/chat_bot_prompts/")

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 2


# Test get_chat_bot_prompt_by_id
def test_get_chat_bot_prompt_by_id(mock_auth_permission, mocker):
    mock_db = MagicMock()

    # Mock the DB function
    mocker.patch(
        "fedrisk_api.db.chat_bot_prompt.get_chat_bot_prompt_by_id",
        return_value={"id": 1, "prompt": "Prompt 1"},
    )

    response = client.get("/chat_bot_prompts/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"] == 1


# Test get_chat_bot_prompt_by_id - Not Found
def test_get_chat_bot_prompt_by_id_not_found(mock_auth_permission, mocker):
    mock_db = MagicMock()

    # Simulate no result from the DB
    mocker.patch("fedrisk_api.db.chat_bot_prompt.get_chat_bot_prompt_by_id", return_value=None)

    response = client.get("/chat_bot_prompts/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "ChatBot prompt with specified id does not exists"


# Test update_chat_bot_prompt_by_id
def test_update_chat_bot_prompt_by_id(mock_auth_permission, mocker):
    mock_db = MagicMock()

    # Mock the DB function
    mocker.patch("fedrisk_api.db.chat_bot_prompt.update_chat_bot_prompt_by_id", return_value=True)

    response = client.put("/chat_bot_prompts/1", json={"prompt": "Updated Prompt"})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["detail"] == "Successfully updated ChatBot Prompt."


# Test update_chat_bot_prompt_by_id - Not Found
def test_update_chat_bot_prompt_by_id_not_found(mock_auth_permission, mocker):
    mock_db = MagicMock()

    # Simulate no result from the DB
    mocker.patch("fedrisk_api.db.chat_bot_prompt.update_chat_bot_prompt_by_id", return_value=False)

    response = client.put("/chat_bot_prompts/999", json={"prompt": "Updated Prompt"})

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "ChatBot Prompt with specified id does not exists"


# Test delete_chat_bot_prompt_by_id
def test_delete_chat_bot_prompt_by_id(mock_auth_permission, mocker):
    mock_db = MagicMock()

    # Mock the DB function
    mocker.patch("fedrisk_api.db.chat_bot_prompt.delete_chat_bot_prompt_by_id", return_value=True)

    response = client.delete("/chat_bot_prompts/1")

    assert response.status_code == status.HTTP_200_OK
    assert response.json()["detail"] == "Successfully deleted ChatBot Prompt."


# Test delete_chat_bot_prompt_by_id - Not Found
def test_delete_chat_bot_prompt_by_id_not_found(mock_auth_permission, mocker):
    mock_db = MagicMock()

    # Simulate no result from the DB
    mocker.patch("fedrisk_api.db.chat_bot_prompt.delete_chat_bot_prompt_by_id", return_value=False)

    response = client.delete("/chat_bot_prompts/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == "ChatBot Prompt with sepcified id does not exists"
