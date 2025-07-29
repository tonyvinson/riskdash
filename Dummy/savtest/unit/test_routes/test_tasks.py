import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from main import app  # Import your FastAPI app
from fedrisk_api.db.database import Base, get_db

# Set up a test database (SQLite in-memory for example)
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Override the dependency with the test database session
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

# Create test data in test database before running tests
@pytest.fixture(scope="module")
def setup_test_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Mock user authorization (custom_auth dependency)
@pytest.fixture
def mock_auth(monkeypatch):
    def mock_custom_auth():
        return {"tenant_id": 1, "user_id": 1}

    monkeypatch.setattr("fedrisk_api.utils.authentication.custom_auth", mock_custom_auth)


# 1. Test creating a task
@pytest.mark.asyncio
async def test_create_task(mock_auth, setup_test_db):
    response = client.post(
        "/tasks/task",
        json={
            "name": "Test Task",
            "description": "A test task description",
            "status": "pending",
            "priority": "medium",
            "project_id": 1,
        },
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Test Task"


# 2. Test getting all tasks
@pytest.mark.asyncio
async def test_get_all_tasks(mock_auth, setup_test_db):
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# 3. Test fetching a task by ID
@pytest.mark.asyncio
async def test_get_task_by_id(mock_auth, setup_test_db):
    # First, create a task to fetch
    task = client.post(
        "/tasks/task",
        json={
            "name": "Fetch Test Task",
            "description": "Task to be fetched",
            "status": "pending",
            "priority": "medium",
            "project_id": 1,
        },
    )
    task_id = task.json()["id"]

    # Fetch task by ID
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Fetch Test Task"


# 4. Test updating a task by ID
@pytest.mark.asyncio
async def test_update_task_by_id(mock_auth, setup_test_db):
    # First, create a task to update
    task = client.post(
        "/tasks/task",
        json={
            "name": "Update Test Task",
            "description": "Task to be updated",
            "status": "pending",
            "priority": "medium",
            "project_id": 1,
        },
    )
    task_id = task.json()["id"]

    # Update the task
    response = client.put(
        f"/tasks/{task_id}",
        json={"name": "Updated Task", "description": "Updated description"},
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated Task"


# 5. Test deleting a task by ID
@pytest.mark.asyncio
async def test_delete_task_by_id(mock_auth, setup_test_db):
    # First, create a task to delete
    task = client.post(
        "/tasks/task",
        json={
            "name": "Delete Test Task",
            "description": "Task to be deleted",
            "status": "pending",
            "priority": "medium",
            "project_id": 1,
        },
    )
    task_id = task.json()["id"]

    # Delete the task
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["detail"] == "Successfully deleted task"

    # Verify task deletion
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404


# 6. Test fetching tasks by WBS ID (assuming WBS ID filtering is implemented in db_task)
@pytest.mark.asyncio
async def test_get_tasks_by_wbs_id(mock_auth, setup_test_db):
    response = client.get("/tasks/wbs/1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# 7. Test fetching tasks in DHTMLX format by WBS ID
@pytest.mark.asyncio
async def test_get_tasks_by_wbs_dhtmlx_id(mock_auth, setup_test_db):
    response = client.get("/tasks/dhwbsgantt/1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# 8. Test fetching task chart data by project ID
@pytest.mark.asyncio
async def test_get_task_chart_data_by_project(mock_auth, setup_test_db):
    response = client.get("/tasks/charts/1")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
