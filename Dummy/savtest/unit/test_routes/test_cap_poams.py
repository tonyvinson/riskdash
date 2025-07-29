import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fedrisk_api.db.database import Base, get_db
from main import app  # assuming this is your FastAPI app instance
from fedrisk_api.schema.cap_poam import CreateCapPoam, UpdateCapPoam
from fedrisk_api.db import cap_poam as db_cap_poam

# Set up test database engine and session
SQLALCHEMY_DATABASE_URL = (
    "sqlite:///./test.db"  # You can use an in-memory SQLite database for testing
)
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency to use the test database session
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Test client instance
client = TestClient(app)

# Test: Create CapPoam
@pytest.mark.asyncio
async def test_create_cap_poam():
    payload = {
        "name": "Test CAP",
        "description": "Test description",
        "project_id": 1,  # ensure project with this ID exists in the DB
        "owner_id": 1,  # ensure user with this ID exists in the DB
        "due_date": "2024-12-31",
        "criticality_rating": 5,
        "status": "open",
    }
    response = client.post("/cap_poams/", json=payload)
    assert response.status_code == 200  # Check if the response is successful
    data = response.json()
    assert data["name"] == payload["name"]  # Assert that the returned data matches the request
    assert data["description"] == payload["description"]


# Test: Get CapPoam by ID
@pytest.mark.asyncio
async def test_get_cap_poam_by_id():
    cap_poam_id = 1  # make sure you have a cap_poam with this ID in the DB for the test
    response = client.get(f"/cap_poams/{cap_poam_id}")
    assert response.status_code == 200  # Check if the response is successful
    data = response.json()
    assert data["id"] == cap_poam_id  # Assert that the returned data matches the cap_poam ID


# Test: Get CapPoams by Project ID
@pytest.mark.asyncio
async def test_get_cap_poams_by_project_id():
    project_id = 1  # Ensure project with this ID exists in the DB
    response = client.get(f"/cap_poams/project/{project_id}")
    assert response.status_code == 200  # Check if the response is successful
    data = response.json()
    assert isinstance(data, list)  # Should return a list of cap_poams
    assert len(data) > 0  # Assuming there are cap_poams for this project


# Test: Update CapPoam
@pytest.mark.asyncio
async def test_update_cap_poam():
    cap_poam_id = 1  # Ensure you have a cap_poam with this ID in the DB
    payload = {
        "name": "Updated Test CAP",
        "description": "Updated description",
        "due_date": "2024-12-25",
        "status": "closed",
        "criticality_rating": 4,
        "owner_id": 1,
    }
    response = client.put(f"/cap_poams/{cap_poam_id}", json=payload)
    assert response.status_code == 200  # Check if the response is successful
    data = response.json()
    assert data["name"] == payload["name"]  # Assert that the name was updated
    assert data["description"] == payload["description"]  # Assert that the description was updated


# Test: Delete CapPoam
@pytest.mark.asyncio
async def test_delete_cap_poam():
    cap_poam_id = 1  # Ensure you have a cap_poam with this ID in the DB
    response = client.delete(f"/cap_poams/{cap_poam_id}")
    assert response.status_code == 200  # Check if the response is successful
    assert response.json() == {"detail": "Successfully deleted cap_poam."}
