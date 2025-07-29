import pytest
from fastapi.testclient import TestClient
from main import app
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fedrisk_api.db.database import Base, get_db
from fedrisk_api.db.models import User

# Setup test database and client
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_user_notifications.db"
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


def test_create_user_notification(mock_auth, setup_test_db):
    response = client.post(
        "/user_notifications/",
        json={
            "title": "New Notification",
            "message": "You have a new alert!",
            "user_id": 1,
            "notification_type": "info",
        },
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Notification"


def test_get_all_user_notifications(mock_auth, setup_test_db):
    response = client.get("/user_notifications/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_delete_user_notification_by_id(mock_auth, setup_test_db):
    # First, create a notification to delete
    notification = client.post(
        "/user_notifications/",
        json={
            "title": "Delete This Notification",
            "message": "This will be deleted.",
            "user_id": 1,
            "notification_type": "info",
        },
    )
    notification_id = notification.json()["id"]

    # Now delete it
    response = client.delete(f"/user_notifications/{notification_id}")
    assert response.status_code == 200
    assert response.json() == {"detail": "Successfully deleted user Notification."}


def test_create_user_notification_settings(mock_auth, setup_test_db):
    response = client.post(
        "/user_notifications/settings/",
        json={
            "user_id": 1,
            "email_notifications": True,
            "sms_notifications": False,
            "push_notifications": True,
        },
    )
    assert response.status_code == 200
    assert response.json()["email_notifications"] is True


def test_get_user_notification_settings_by_user_id(mock_auth, setup_test_db):
    response = client.get("/user_notifications/settings/1")
    assert response.status_code == 200
    assert response.json()["user_id"] == 1


def test_get_scheduled_emails(mock_auth, setup_test_db):
    response = client.get("/user_notifications/scheduled-emails")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_post_scheduled_notifications(mock_auth, setup_test_db):
    response = client.post("/user_notifications/scheduled-notifications")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
