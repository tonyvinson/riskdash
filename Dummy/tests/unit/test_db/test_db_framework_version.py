import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from fedrisk_api.db.framework_version import (
    create_framework_version,
    get_all_framework_versions,
    get_framework_version,
    update_framework_version,
    delete_framework_version,
)
from fedrisk_api.db.models import FrameworkVersion, Keyword, KeywordMapping, Framework
from fedrisk_api.schema.framework_version import CreateFrameworkVersion, UpdateFrameworkVersion


@pytest.fixture
def db_session():
    """Mocked database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def create_framework_version_data():
    """Mock CreateFrameworkVersion data."""
    return CreateFrameworkVersion(
        version_prefix="v1", version_suffix="a", guidance="A new version", framework_id=1
    )


@pytest.fixture
def update_framework_version_data():
    """Mock UpdateFrameworkVersion data."""
    return UpdateFrameworkVersion(
        version_prefix="v1.1", guidance="An updated version", framework_id=1
    )


@pytest.fixture
def mock_framework_version():
    """Mock FrameworkVersion instance."""
    return FrameworkVersion(
        id=1, version_prefix="v1", version_suffix="a", guidance="A new version", framework_id=1
    )


def test_create_framework_version(db_session, create_framework_version_data):
    framework = Framework(id="1", name="Framework 1", description="Description for Framework 1")
    db_session.add(framework)
    db_session.commit()

    """Test creating a new framework version with keywords."""
    new_framework_version = create_framework_version(
        db=db_session,
        framework_version=create_framework_version_data,
        keywords="keyword1,keyword2",
        tenant_id=1,
    )

    assert new_framework_version is not None
    db_session.add.assert_called()
    db_session.commit.assert_called()
    db_session.refresh.assert_called_with(new_framework_version)


def test_get_all_framework_versions(db_session, mock_framework_version):
    """Test retrieving all framework versions with optional project and framework filtering."""
    db_session.query().join().distinct.return_value = [mock_framework_version]

    framework_versions = get_all_framework_versions(db=db_session, project_id=1, framework_id=1)

    assert framework_versions is not None
    # db_session.query().join().filter.assert_called()


def test_get_framework_version(db_session, mock_framework_version):
    """Test retrieving a single framework version by ID."""
    db_session.query().join().filter().options().first.return_value = mock_framework_version

    framework_version = get_framework_version(db=db_session, id=1)

    assert framework_version is not None
    # assert framework_version.id == mock_framework_version.id
    # db_session.query().join().filter().first.assert_called_once()


def test_update_framework_version(
    db_session, mock_framework_version, update_framework_version_data
):
    """Test updating an existing framework version with keywords."""
    db_session.query().filter().first.return_value = mock_framework_version

    result = update_framework_version(
        db=db_session,
        id=1,
        framework_version=update_framework_version_data,
        tenant_id=100,
        keywords="updated_keyword",
    )

    assert result is True
    # db_session.commit.assert_called_once()


def test_delete_framework_version(db_session, mock_framework_version):
    """Test deleting a framework version by ID."""
    db_session.query().filter().first.return_value = mock_framework_version

    result = delete_framework_version(db=db_session, id=1)

    assert result is True
    db_session.commit.assert_called_once()
    # db_session.query().filter().delete.assert_called_once()
