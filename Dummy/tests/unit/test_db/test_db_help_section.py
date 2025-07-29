import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session

from fedrisk_api.db.help_section import (
    create_help_section,
    get_help_sections,
    get_help_section_by_id,
    update_help_section_by_id,
    delete_help_section_by_id,
)
from fedrisk_api.db.models import HelpSection
from fedrisk_api.schema.help_section import CreateHelpSection, UpdateHelpSection


@pytest.fixture
def db_session():
    """Mocked database session."""
    return MagicMock(spec=Session)


@pytest.fixture
def create_help_section_data():
    """Mock CreateHelpSection data."""
    return CreateHelpSection(title="Test Title", body="Test Content", order=1)


@pytest.fixture
def update_help_section_data():
    """Mock UpdateHelpSection data."""
    return UpdateHelpSection(title="Updated Title", body="Updated Content")


@pytest.fixture
def mock_help_section():
    """Mock HelpSection instance."""
    return HelpSection(id=1, title="Test Title", body="Test Content", divId="testTitle", order=1)


def test_create_help_section(db_session, create_help_section_data):
    """Test creating a new help section."""
    new_help_section = create_help_section(help_section=create_help_section_data, db=db_session)

    assert new_help_section is not None
    db_session.add.assert_called_once_with(new_help_section)
    db_session.commit.assert_called_once()


def test_get_help_sections(db_session, mock_help_section):
    """Test retrieving all help sections, ordered by 'order'."""
    db_session.query().order_by().all.return_value = [mock_help_section]

    help_sections = get_help_sections(db=db_session)

    assert help_sections is not None
    assert len(help_sections) == 1
    assert help_sections[0].title == "Test Title"
    db_session.query().order_by().all.assert_called_once()


def test_get_help_section_by_id(db_session, mock_help_section):
    """Test retrieving a help section by ID."""
    db_session.query().filter().first.return_value = mock_help_section

    help_section = get_help_section_by_id(db=db_session, help_section_id=1)

    assert help_section is not None
    assert help_section.id == mock_help_section.id
    db_session.query().filter().first.assert_called_once()


def test_update_help_section_by_id(db_session, update_help_section_data, mock_help_section):
    """Test updating an existing help section by ID."""
    db_session.query().filter().first.return_value = mock_help_section

    result = update_help_section_by_id(
        help_section=update_help_section_data, db=db_session, help_section_id=1
    )

    assert result is True
    db_session.commit.assert_called_once()


def test_delete_help_section_by_id(db_session, mock_help_section):
    """Test deleting a help section by ID."""
    db_session.query().filter().first.return_value = mock_help_section

    result = delete_help_section_by_id(db=db_session, help_section_id=1)

    assert result is True
    db_session.delete.assert_called_once_with(mock_help_section)
    db_session.commit.assert_called_once()
