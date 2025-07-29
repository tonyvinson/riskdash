import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from unittest.mock import AsyncMock, MagicMock, patch

from main import app  # Your FastAPI app entry point
from fedrisk_api.schema.import_framework import CreateImportFramework, DisplayImportFramework

client = TestClient(app)

# Mock AWS S3 bucket for testing
AWS_S3_BUCKET = "fedriskapi-frameworks-bucket"


@pytest.fixture
def mock_db():
    db = MagicMock()
    return db


@pytest.fixture
def mock_s3_service():
    s3_service = AsyncMock()
    return s3_service


# Test create_import_framework endpoint
@patch(
    "fedrisk_api.db.import_framework.create_import_framework",
    return_value=CreateImportFramework(name="test_framework"),
)
@patch("fedrisk_api.s3.S3Service.upload_fileobj")
@patch("fedrisk_api.db.util.import_framework_utils.load_data_from_dataframe")
def test_create_import_framework(
    mock_create_framework, mock_upload_fileobj, mock_load_data, mock_db, mock_s3_service
):
    mock_upload_fileobj.return_value = True
    mock_load_data.return_value = (1, 1, 1)
    file_data = {"fileobject": ("test.xlsx", "content of the file", "application/vnd.ms-excel")}

    response = client.put("/import_frameworks/", files=file_data)

    assert response.status_code == 200
    assert "test_framework" in response.json()["name"]
    mock_upload_fileobj.assert_called_once()


# Test get_all_import_frameworks endpoint
@patch(
    "fedrisk_api.db.import_framework.get_all_import_frameworks",
    return_value=[DisplayImportFramework(id="1", name="test_framework")],
)
def test_get_all_import_frameworks(mock_get_all, mock_db):
    response = client.get("/import_frameworks/")
    assert response.status_code == 200
    assert len(response.json()) > 0
    assert response.json()[0]["name"] == "test_framework"


# Test get_import_framework_by_id endpoint
@patch(
    "fedrisk_api.db.import_framework.get_import_framework",
    return_value=DisplayImportFramework(id="1", name="test_framework"),
)
def test_get_import_framework_by_id(mock_get_by_id, mock_db):
    response = client.get("/import_frameworks/1")
    assert response.status_code == 200
    assert response.json()["name"] == "test_framework"


# Test delete_import_framework endpoint
@patch("fedrisk_api.db.import_framework.delete_import_framework", return_value=True)
@patch("fedrisk_api.s3.S3Service.delete_fileobj")
@patch(
    "fedrisk_api.db.import_framework.get_import_framework",
    return_value=DisplayImportFramework(id="1", name="test_framework"),
)
def test_delete_import_framework_by_id(
    mock_get_by_id, mock_delete_fileobj, mock_delete_framework, mock_db
):
    response = client.delete("/import_frameworks/1")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted import framework."
    mock_delete_fileobj.assert_called_once()


# Test download_import_framework_file endpoint
@patch(
    "fedrisk_api.db.import_framework.get_import_framework",
    return_value=DisplayImportFramework(
        id="1", name="test_framework", file_content_type="application/vnd.ms-excel"
    ),
)
@patch("fedrisk_api.s3.S3Service.get_file_object")
@pytest.mark.asyncio
async def test_download_import_framework_file(
    mock_get_file_object, mock_get_import_framework, mock_db
):
    mock_get_file_object.return_value = {"Body": io.BytesIO(b"file content")}

    response = await client.get("/import_frameworks/download/1")
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment;filename=test_framework"
    assert b"file content" in response.content
