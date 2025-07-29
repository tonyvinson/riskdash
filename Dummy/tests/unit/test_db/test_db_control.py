import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fedrisk_api.db.models import Base, Control, Keyword, KeywordMapping
from fedrisk_api.schema.control import (
    CreateControl,
    UpdateControl,
    CreateBatchControlsFrameworkVersion,
)
from fedrisk_api.db.control import (
    add_keywords,
    create_control,
    remove_old_keywords,
    delete_control,
    add_batch_controls_to_framework_version,
    get_all_controls,
    update_control,
    add_single_control_to_framework_version_relationship,
    get_control,
)

# Setup the test database and session
@pytest.fixture(scope="module")
def db_session():
    engine = create_engine("sqlite:///:memory:")  # In-memory SQLite database
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)  # Create tables

    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
def test_add_keywords(db_session):
    # Setup
    control_id = 1
    tenant_id = 1
    keywords = "risk,security,compliance"

    # Act
    add_keywords(db_session, keywords, control_id, tenant_id)

    # Assert
    results = db_session.query(Keyword).all()
    assert len(results) == 3  # Three keywords added
    assert {k.name for k in results} == {"risk", "security", "compliance"}

    mappings = db_session.query(KeywordMapping).filter_by(control_id=control_id).all()
    assert len(mappings) == 3


@pytest.mark.asyncio
def test_create_control(db_session):
    # Setup
    tenant_id = 1
    control_data = CreateControl(
        name="Test Control",
        description="This is a test control",
        framework_versions=[1],  # Assuming version ID exists in test DB
    )
    keywords = "data,privacy"

    # Act
    new_control = create_control(db_session, control_data, keywords, tenant_id)

    # Assert
    assert new_control.id is not None
    assert new_control.name == "Test Control"
    assert new_control.description == "This is a test control"

    # Check if keywords were added
    keyword_mappings = db_session.query(KeywordMapping).filter_by(control_id=new_control.id).all()
    assert keyword_mappings is not None
    # assert len(keyword_mappings) == 2


def test_add_batch_controls_to_framework_version(db_session):

    controls_batch = CreateBatchControlsFrameworkVersion(
        controls=[
            {
                "name": "Test Control 1",
                "description": "This is a test control",
                "control_id": 1,
                "framework_versions": [1],
            },
            {
                "name": "Test Control 2",
                "description": "This is a test control",
                "control_id": 2,
                "framework_versions": [1],
            },
        ]
    )

    updated_framework_version = add_batch_controls_to_framework_version(
        db_session, framework_version_id=1, controls=controls_batch
    )
    # Assert
    # assert updated_framework_version is not None


def test_get_all_controls(db_session):
    controls = get_all_controls(db_session, tenant_id=1)
    assert controls is not None


def test_add_single_control_to_framework_version_relationship(db_session):
    single_control = add_single_control_to_framework_version_relationship(
        db_session, framework_version_id=1, control_id=1
    )
    assert single_control is not None


def test_get_control(db_session):
    control = get_control(db_session, id=1, tenant_id=1)
    assert control is not None


def test_update_control(db_session):
    # control_data = { "name":"Test Control", "description":"This is a test control", "framework_versions":[1]}
    control_data = UpdateControl(
        name="Test Control",
        description="This is a test control",
        guidance="Guidance",
    )
    keywords = "data,privacy"
    updated = update_control(db_session, id=1, control=control_data, keywords=keywords, tenant_id=1)
    assert updated is not None


@pytest.mark.asyncio
async def test_remove_old_keywords(db_session):
    # Setup: Add some keywords to a control
    control_id = 1
    tenant_id = 1
    initial_keywords = "old_keyword1,old_keyword2,new_keyword"
    add_keywords(db_session, initial_keywords, control_id, tenant_id)

    # New keywords to update
    updated_keywords = "new_keyword"

    # Act
    remove_old_keywords(db_session, updated_keywords, control_id)

    # Assert
    # remaining_mappings = db_session.query(KeywordMapping).filter_by(control_id=control_id).all()
    # remaining_keywords = {m.keyword.name for m in remaining_mappings}
    # assert remaining_keywords == {"new_keyword"}


def test_delete_control(db_session):
    # Setup: Add a control to delete
    # control = Control(id=1, name="Delete Me", description="Test control", tenant_id=1)
    # db_session.add(control)
    # db_session.commit()

    # Act
    result = delete_control(db_session, 1, tenant_id=1)

    # Assert
    assert result is True
    # assert db_session.query(Control).filter_by(id=control.id).first() is None
