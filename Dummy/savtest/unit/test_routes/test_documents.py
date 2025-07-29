import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from botocore.exceptions import ClientError
from main import app  # Replace 'main' with your actual app import

from fedrisk_api.db.database import get_db
from fedrisk_api.utils.authentication import custom_auth

client = TestClient(app)

# Fixtures and Mock Setup
@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides = {
        get_db: lambda: MagicMock(),
        custom_auth: lambda: {"user_id": 1, "tenant_id": 1},
    }
    yield
    app.dependency_overrides = {}


def mock_s3_service():
    service = MagicMock()
    service.upload_fileobj.return_value = True
    service.delete_fileobj.return_value = True
    service.get_file_object.return_value = {"Body": MagicMock()}
    return service


# Helper function to create mock document
def create_mock_document(id=1, name="test_doc.pdf"):
    return {
        "id": id,
        "name": name,
        "title": "Test Document",
        "description": "Test Description",
        "file_content_type": "application/pdf",
        "owner_id": 1,
        "project_id": 1,
        "fedrisk_object_type": "test_type",
        "fedrisk_object_id": 1,
    }


# Test creating a document
@patch("fedrisk_api.db.document.create_document")
@patch("fedrisk_api.s3.S3Service", new_callable=mock_s3_service)
def test_create_document(mock_s3_service, mock_create_document):
    mock_create_document.return_value = create_mock_document()
    response = client.post(
        "/documents/",
        files={"fileobject": ("test_doc.pdf", b"fake content", "application/pdf")},
        data={
            "title": "Test Document",
            "description": "Test Description",
            "owner_id": 1,
            "project_id": 1,
            "fedrisk_object_type": "test_type",
            "fedrisk_object_id": 1,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_doc.pdf"
    assert mock_s3_service.upload_fileobj.called


# Test fetching all documents
@patch("fedrisk_api.db.document.get_all_documents")
def test_get_all_documents(mock_get_all_documents):
    mock_get_all_documents.return_value = [create_mock_document()]
    response = client.get("/documents/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "test_doc.pdf"


# Test fetching a single document by ID
@patch("fedrisk_api.db.document.get_document")
def test_get_document_by_id(mock_get_document):
    mock_get_document.return_value = create_mock_document()
    response = client.get("/documents/1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == 1
    assert data["name"] == "test_doc.pdf"


# Test updating a document
@patch("fedrisk_api.db.document.update_document")
@patch("fedrisk_api.s3.S3Service", new_callable=mock_s3_service)
def test_update_document(mock_s3_service, mock_update_document):
    mock_update_document.return_value = create_mock_document()
    response = client.put(
        "/documents/1",
        files={"fileobject": ("updated_test_doc.pdf", b"new content", "application/pdf")},
        data={
            "title": "Updated Document",
            "description": "Updated Description",
            "owner_id": 1,
            "project_id": 1,
            "fedrisk_object_type": "test_type",
            "fedrisk_object_id": 1,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "test_doc.pdf"
    assert mock_s3_service.upload_fileobj.called


# Test deleting a document
@patch("fedrisk_api.db.document.get_document")
@patch("fedrisk_api.db.document.delete_document")
@patch("fedrisk_api.s3.S3Service", new_callable=mock_s3_service)
def test_delete_document(mock_s3_service, mock_delete_document, mock_get_document):
    mock_get_document.return_value = create_mock_document()
    mock_delete_document.return_value = True
    response = client.delete("/documents/1")
    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Successfully deleted document."
    assert mock_s3_service.delete_fileobj.called


# Test downloading a document
@patch("fedrisk_api.db.document.get_document")
@patch("fedrisk_api.s3.S3Service", new_callable=mock_s3_service)
def test_download_document(mock_s3_service, mock_get_document):
    mock_get_document.return_value = create_mock_document()
    response = client.get("/documents/download/1")
    assert response.status_code == 200
    assert response.headers["content-disposition"] == 'attachment;filename="test_doc.pdf"'
    assert mock_s3_service.get_file_object.called


# Test document not found during download
@patch("fedrisk_api.db.document.get_document", return_value=None)
def test_download_document_not_found(mock_get_document):
    response = client.get("/documents/download/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Document with id 999 does not exist"
