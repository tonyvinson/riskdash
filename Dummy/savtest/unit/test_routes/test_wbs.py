import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fedrisk_api.db.database import Base, get_db
from fedrisk_api.db.models import WBS

# Setup test database and client
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_wbs.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app.dependency_overrides[get_db] = TestingSessionLocal
client = TestClient(app)

# Setup and teardown for the test database
@pytest.fixture(scope="module")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Mock authentication to simulate user login
@pytest.fixture
def mock_auth(monkeypatch):
    def mock_custom_auth():
        return {"tenant_id": 1, "user_id": 1}

    monkeypatch.setattr("fedrisk_api.utils.authentication.custom_auth", mock_custom_auth)


@pytest.mark.asyncio
async def test_create_wbs(mock_auth, setup_test_db):
    response = client.post(
        "/wbs/",
        json={
            "name": "Test WBS",
            "description": "Description of Test WBS",
            "project_id": 1,
            "keywords": "test, wbs",
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test WBS"


def test_get_all_project_wbs(mock_auth, setup_test_db):
    response = client.get("/wbs/project/1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_wbs_by_id(mock_auth, setup_test_db):
    # First, create a WBS entry to retrieve
    wbs_entry = client.post(
        "/wbs/",
        json={
            "name": "Retrieve Test WBS",
            "description": "This WBS will be retrieved.",
            "project_id": 1,
            "keywords": "test, retrieve",
        },
    )
    wbs_id = wbs_entry.json()["id"]

    # Retrieve WBS by ID
    response = client.get(f"/wbs/{wbs_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Retrieve Test WBS"


@pytest.mark.asyncio
async def test_update_wbs_by_id(mock_auth, setup_test_db):
    # First, create a WBS entry to update
    wbs_entry = client.post(
        "/wbs/",
        json={
            "name": "Update Test WBS",
            "description": "This WBS will be updated.",
            "project_id": 1,
            "keywords": "test, update",
        },
    )
    wbs_id = wbs_entry.json()["id"]

    # Update the WBS entry
    response = client.put(
        f"/wbs/{wbs_id}", json={"name": "Updated WBS", "description": "Updated WBS description"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated WBS"


@pytest.mark.asyncio
async def test_delete_wbs_by_id(mock_auth, setup_test_db):
    # First, create a WBS entry to delete
    wbs_entry = client.post(
        "/wbs/",
        json={
            "name": "Delete Test WBS",
            "description": "This WBS will be deleted.",
            "project_id": 1,
            "keywords": "test, delete",
        },
    )
    wbs_id = wbs_entry.json()["id"]

    # Delete the WBS entry
    response = client.delete(f"/wbs/{wbs_id}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Successfully deleted wbs."}
