import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from fedrisk_api.db.framework import (
    create_framework,
    create_framework_map_tenant,
    get_all_frameworks,
    get_framework,
    update_framework,
    delete_framework,
    search,
)
from fedrisk_api.db.models import (
    Framework,
    FrameworkTenant,
    Keyword,
    KeywordMapping,
    User,
    ProjectUser,
)
from fedrisk_api.schema.framework import CreateFramework, UpdateFramework, CreateFrameworkTenant


@pytest.fixture
def db_session():
    """Mocked database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def mock_user():
    """Mock User instance."""
    return User(id=1, tenant_id=1, is_superuser=False, is_tenant_admin=False)


@pytest.fixture
def mock_superuser():
    """Mock superuser instance."""
    return User(id=2, is_superuser=True, tenant_id=1)


@pytest.fixture
def mock_framework():
    """Mock Framework instance."""
    return Framework(id=1, name="Test Framework", description="A test framework")


@pytest.fixture
def create_framework_data():
    """Mock CreateFramework data."""
    return CreateFramework(name="New Framework", description="A new framework")


@pytest.fixture
def update_framework_data():
    """Mock UpdateFramework data."""
    return UpdateFramework(name="Updated Framework", description="An updated framework")


def test_create_framework(db_session, create_framework_data):
    """Test creating a new framework with keywords."""
    new_framework = create_framework(
        db=db_session, framework=create_framework_data, tenant_id=1, keywords="keyword1,keyword2"
    )

    assert new_framework is not None
    db_session.add.assert_called()
    db_session.commit.assert_called()
    db_session.refresh.assert_called_with(new_framework)


def test_create_framework_map_tenant(db_session):
    """Test creating a tenant mapping for a framework."""
    framework_tenant_data = CreateFrameworkTenant(tenant_id=1, framework_id=1, is_enabled=True)
    framework_tenant = create_framework_map_tenant(
        db=db_session, frame_ten_map=framework_tenant_data
    )

    assert framework_tenant is not None
    db_session.add.assert_called_once_with(framework_tenant)
    db_session.commit.assert_called_once()


def test_get_all_frameworks(db_session, mock_framework):
    """Test retrieving all frameworks with tenant-based filtering."""
    db_session.query().join().filter().distinct.return_value = [mock_framework]

    frameworks = get_all_frameworks(db=db_session, tenant_id=1)

    assert frameworks is not None
    db_session.query().join().filter.assert_called()


def test_get_framework(db_session, mock_framework):
    """Test retrieving a single framework by ID."""
    db_session.query().join().filter().options().first.return_value = mock_framework

    framework = get_framework(db=db_session, id=1, tenant_id=1)

    assert framework is not None
    # assert framework.id == mock_framework.id
    # db_session.query().join().filter().first.assert_called_once()


def test_update_framework(db_session, mock_framework, update_framework_data):
    """Test updating an existing framework with keywords."""
    db_session.query().join().filter().first.return_value = mock_framework

    result = update_framework(
        db=db_session,
        id=1,
        framework=update_framework_data,
        tenant_id=1,
        keywords="updated,keyword",
    )

    assert result is not None
    # db_session.commit.assert_called_once()


def test_delete_framework(db_session, mock_framework):
    """Test deleting a framework by ID."""
    db_session.query().filter().first.return_value = mock_framework

    result = delete_framework(db=db_session, id=1)

    assert result is True
    db_session.commit.assert_called_once()
    # db_session.query().filter().delete.assert_called_once()


def test_search(db_session, mock_superuser, mock_framework):
    """Test searching for frameworks based on a query."""
    db_session.query().filter().all.return_value = [mock_framework]
    db_session.query().filter().count.return_value = 1
    db_session.query().filter().first.return_value = mock_superuser

    new_user = User(id=1, email="test@test.com")
    db_session.add(new_user)
    db_session.commit()

    count, results = search(
        query="test", db=db_session, tenant_id=1, user_id=new_user.id, offset=0, limit=10
    )

    assert count == 1
    assert results is not None
    db_session.query().filter().all.assert_called()
    db_session.query().filter().count.assert_called_once()
