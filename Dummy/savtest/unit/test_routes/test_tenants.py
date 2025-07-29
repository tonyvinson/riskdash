import pytest
from fastapi.testclient import TestClient
from main import app  # Import your FastAPI app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fedrisk_api.db.database import Base, get_db
from fedrisk_api.db.models import Tenant, User

# Setup test database and client
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tenant.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
app.dependency_overrides[get_db] = TestingSessionLocal
client = TestClient(app)

# Set up and tear down test database
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
async def test_user_invitation(mock_auth, setup_test_db):
    response = client.post(
        "/tenants/user_invitation",
        json={"emails": ["newuser1@example.com", "newuser2@example.com"]},
    )
    assert response.status_code == 200
    assert response.json() == {"details": "Invitation sent Successfully"}


@pytest.mark.asyncio
async def test_user_invitation(mock_auth, setup_test_db):
    response = client.post(
        "/tenants/user_invitation",
        json={"emails": ["newuser1@example.com", "newuser2@example.com"]},
    )
    assert response.status_code == 200
    assert response.json() == {"details": "Invitation sent Successfully"}


@pytest.mark.asyncio
async def test_resend_invite_email(mock_auth, setup_test_db):
    # Mock user data setup
    db = TestingSessionLocal()
    user = User(email="newuser@example.com", tenant_id=1, is_email_verified=False)
    db.add(user)
    db.commit()

    response = client.post("/tenants/resend_invite_email", json={"email": "newuser@example.com"})
    assert response.status_code == 200
    assert response.json() == {"details": "Invitation sent Successfully"}
    db.close()


@pytest.mark.asyncio
async def test_verify_invitation_token(mock_auth, setup_test_db):
    # Mock token setup for test case
    db = TestingSessionLocal()
    tenant = Tenant(id=1, name="Test Tenant")
    db.add(tenant)
    db.commit()

    response = client.get("/tenants/user_invitation/verify/mock_token")
    assert response.status_code == 400
    assert "Link Expired" in response.json()["detail"]
    db.close()


@pytest.mark.asyncio
async def test_tenant_signup(mock_auth, setup_test_db):
    response = client.post(
        "/tenants/register",
        json={
            "first_name": "Test",
            "last_name": "User",
            "email": "testuser@example.com",
            "password": "StrongPassword123",
            "organization": "Test Org",
        },
    )
    assert response.status_code == 200
    assert response.json()["details"] == "Signup Successfully"


def test_check_unique_email(mock_auth, setup_test_db):
    # Create a duplicate email in the database
    db = TestingSessionLocal()
    user = User(email="unique@example.com", tenant_id=1)
    db.add(user)
    db.commit()

    response = client.post("/tenants/check_unique_email", json={"email": "unique@example.com"})
    assert response.status_code == 409
    assert "email already exists" in response.json()["detail"]
    db.close()
