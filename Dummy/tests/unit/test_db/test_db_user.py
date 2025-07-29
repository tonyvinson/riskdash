import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.models import User, Tenant, UserInvitation
from fedrisk_api.schema.user import UpdateUserProfile, UpdateUserRole
from fedrisk_api.db.user import (
    get_all_users,
    get_user_by_id,
    get_user_by_email,
    deactivate_user,
    make_user_tenant_admin,
    activate_user,
    check_unique_user_email,
    update_user_profile_by_id,
    update_profile_picture,
    remove_profile_picture,
    delete_user,
    update_user_role_by_id,
    deactivate_users,
)


@pytest.fixture
def db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


def test_get_all_users(db_session):
    """Test retrieving all users."""
    db_session.query().filter().first.return_value = User(id=1, is_superuser=True)
    db_session.query().all.return_value = [User(id=2, email="user@example.com")]

    result = get_all_users(
        db_session, user={"user_id": 1}, q="", sort_by="", filter_by="", filter_value=""
    )

    # assert len(result) == 1
    # assert result[0].email == "user@example.com"


def test_get_user_by_id(db_session):
    """Test retrieving a user by ID."""
    db_session.query().filter().first.return_value = User(id=1, email="user@example.com")

    result = get_user_by_id(db_session, id=1, tenant_id=1)

    assert result is not None
    assert result.email == "user@example.com"


def test_get_user_by_email(db_session):
    """Test retrieving a user by email."""
    db_session.query().filter().first.return_value = User(id=1, email="user@example.com")

    result = get_user_by_email(db_session, email="user@example.com", tenant_id=1)

    assert result is not None
    assert result.email == "user@example.com"


def test_deactivate_user(db_session):
    """Test deactivating a user."""
    db_session.query().filter().first.side_effect = [
        User(id=1, system_role=4),
        User(id=2, is_active=True),
    ]

    result = deactivate_user(id=2, user={"user_id": 1}, db=db_session)

    db_session.commit.assert_called_once()
    assert result is True


def test_make_user_tenant_admin(db_session):
    """Test making a user a tenant admin."""
    db_session.query().filter().first.side_effect = [
        User(id=1, is_superuser=True),
        User(id=2, is_active=True, is_email_verified=True),
    ]

    result = make_user_tenant_admin(id=2, user={"user_id": 1}, db=db_session)

    db_session.commit.assert_called_once()
    assert result is True


def test_activate_user(db_session):
    """Test activating a user."""
    db_session.query().filter().first.side_effect = [
        User(id=1, system_role=4),
        User(id=2, is_active=False),
        Tenant(id=1, user_licence=10),
    ]
    db_session.query().filter().count.return_value = 5

    result, status_code, message = activate_user(id=2, user={"user_id": 1}, db=db_session)

    db_session.commit.assert_called_once()
    assert result is True
    assert status_code == 200
    assert message == "Successfully activated User"


def test_check_unique_user_email(db_session):
    """Test checking for unique user email."""
    db_session.query().filter().first.return_value = None

    result = check_unique_user_email(db_session, user_email="unique@example.com")

    assert result is None


def test_update_user_profile_by_id(db_session):
    """Test updating a user's profile."""
    db_session.query().filter().first.return_value = User(id=1, email="user@example.com")
    profile_data = UpdateUserProfile(name="Updated Name")

    result = update_user_profile_by_id(id=1, request=profile_data, user_id=1, db=db_session)

    # db_session.commit.assert_called_once()
    assert result is True


def test_update_profile_picture(db_session):
    """Test updating a user's profile picture."""
    db_session.query().filter().first.return_value = User(id=1, profile_picture="old_picture.jpg")

    result = update_profile_picture(user_id=1, profile_picture="new_picture", db=db_session)

    db_session.commit.assert_called_once()
    # assert result.profile_picture.startswith("1-new_picture")


def test_remove_profile_picture(db_session):
    """Test removing a user's profile picture."""
    db_session.query().filter().first.return_value = User(id=1, profile_picture="profile.jpg")

    result = remove_profile_picture(user_id=1, db=db_session)

    db_session.commit.assert_called_once()
    assert result is True


# def test_delete_user(db_session):
#     """Test deleting a user."""
#     db_session.query().filter().first.side_effect = [User(id=1, is_superuser=True), User(id=2, email="user@example.com")]
#     db_session.query().filter().all.return_value = []

#     user_to_delete = {"user_id": 1, "tenant_id": 1}
#     result = delete_user(user_id=1, db=db_session, user=user_to_delete)

#     db_session.commit.assert_called_once()
#     assert result is not None
#     # assert status_code == 200
#     # assert message == "User deleted successfully"


def test_update_user_role_by_id(db_session):
    """Test updating a user's role."""
    db_session.query().filter().first.return_value = User(id=1, system_role=2)
    role_data = UpdateUserRole(system_role=3)

    result = update_user_role_by_id(id=1, request=role_data, user_id=1, db=db_session)

    db_session.commit.assert_called_once()
    assert result is True


def test_deactivate_users(db_session):
    """Test deactivating multiple users."""
    db_session.query().filter().first.side_effect = [
        User(id=1, is_active=True),
        User(id=2, is_active=True),
    ]

    result, status_code, message = deactivate_users(users=[User(id=1), User(id=2)], db=db_session)

    db_session.commit.assert_called()
    assert result is True
    assert status_code == 200
    assert message == "Users deactivated successfully"
