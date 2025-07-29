import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from fastapi import FastAPI
from main import app  # Adjust the import to your app module
from typing import Any
from config.config import Settings

settings = Settings()

app = FastAPI(title=settings.PROJECT_TITLE, version=settings.PROJECT_VERSION)

client = TestClient(app)


@pytest.fixture
def mock_create_aws_control(mocker):
    return mocker.patch("fedrisk_api.db.aws_control.create_aws_control", return_value={})


@pytest.fixture
def mock_get_all_aws_controls(mocker):
    return mocker.patch("fedrisk_api.db.aws_control.get_aws_control", return_value=[])


@pytest.fixture
def mock_get_aws_control_by_id(mocker):
    return mocker.patch("fedrisk_api.db.aws_control.get_aws_control_by_id", return_value={})


@pytest.fixture
def mock_update_aws_control(mocker):
    return mocker.patch("fedrisk_api.db.aws_control.update_aws_control_by_id", return_value=True)


@pytest.fixture
def mock_delete_aws_control(mocker):
    return mocker.patch("fedrisk_api.db.aws_control.delete_aws_control_by_id", return_value=True)


@pytest.mark.asyncio
async def test_create_aws_control(mock_create_aws_control):
    response = await client.post("/aws_controls/", json={"aws_id": "test-aws-id"})
    assert response.status_code == 200
    mock_create_aws_control.assert_called_once()


def test_get_all_aws_controls(mock_get_all_aws_controls):
    response = client.get("/aws_controls/")
    assert response.status_code == 200
    mock_get_all_aws_controls.assert_called_once()


def test_get_aws_control_by_id(mock_get_aws_control_by_id):
    response = client.get("/aws_controls/1")
    assert response.status_code == 200
    mock_get_aws_control_by_id.assert_called_once_with(db=Any, aws_control_id=1)


def test_get_aws_control_not_found(mock_get_aws_control_by_id):
    mock_get_aws_control_by_id.return_value = None
    response = client.get("/aws_controls/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "AWS Control with specified id does not exists"}


@pytest.mark.asyncio
async def test_update_aws_control(mock_update_aws_control):
    response = await client.put("/aws_controls/1", json={"aws_id": "updated-aws-id"})
    assert response.status_code == 200
    mock_update_aws_control.assert_called_once()


def test_update_aws_control_not_found(mock_update_aws_control):
    mock_update_aws_control.return_value = False
    response = client.put("/aws_controls/999", json={"aws_id": "updated-aws-id"})
    assert response.status_code == 404
    assert response.json() == {"detail": "AWS Control with specified id does not exists"}


@pytest.mark.asyncio
async def test_delete_aws_control(mock_delete_aws_control):
    response = await client.delete("/aws_controls/1")
    assert response.status_code == 200
    assert response.json() == {"detail": "Successfully deleted AWS Control."}
    mock_delete_aws_control.assert_called_once()


def test_delete_aws_control_not_found(mock_delete_aws_control):
    mock_delete_aws_control.return_value = False
    response = client.delete("/aws_controls/999")
    assert response.status_code == 404
    assert response.json() == {"detail": "AWS Control with sepcified id does not exists"}
