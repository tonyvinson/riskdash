import pytest
from fastapi.testclient import TestClient
from main import app  # Import your FastAPI app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fedrisk_api.db.database import Base, get_db
from fedrisk_api.db.models import User

# Setup test database and client
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_user.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app.dependency_overrides[get_db] = TestingSessionLocal
client = TestClient(app)

# Setup and teardown test database
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


def test_get_all_users(mock_auth, setup_test_db):
    response = client.get("/users/")
    assert response.status_code == 200
    assert "items" in response.json()


def test_get_user_by_id(mock_auth, setup_test_db):
    # Create a test user
    db = TestingSessionLocal()
    user = User(id=1, email="user1@example.com", tenant_id=1, is_active=True)
    db.add(user)
    db.commit()

    # Test endpoint
    response = client.get("/users/1/")
    assert response.status_code == 200
    assert response.json()["email"] == "user1@example.com"
    db.close()


def test_update_user_profile_by_id(mock_auth, setup_test_db):
    response = client.put(
        "/users/1/update_profile", json={"first_name": "Updated", "last_name": "User"}
    )
    assert response.status_code == 200
    assert response.json() == {"detail": "Successfully updated profile"}


def test_deactivate_user(mock_auth, setup_test_db):
    response = client.delete("/users/1/")
    assert response.status_code == 200
    assert response.json() == {"detail": "Successfully deactivated User"}


def test_get_auth_token(mock_auth, setup_test_db):
    response = client.post(
        "/users/get-auth-token", json={"email": "user1@example.com", "password": "securepassword"}
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
