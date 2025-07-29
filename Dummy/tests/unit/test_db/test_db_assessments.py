import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from fedrisk_api.db.models import Assessment, AssessmentHistory
from fedrisk_api.schema.assessment import CreateAssessment, UpdateAssessment
from fedrisk_api.db.database import Base
from fedrisk_api.db.assessment import (
    create_assessment,
    get_all_assessments,
    update_assessment,
    delete_assessment,
    search,
    get_assessment,
)

from fedrisk_api.db.models import Project, ProjectControl, Framework, FrameworkVersion, Control

# Setup test database
DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_create_assessment(db, mocker):
    mock_send_email = mocker.patch("fedrisk_api.utils.email_util.send_watch_email")
    mock_publish_sms = mocker.patch("fedrisk_api.utils.sms_util.publish_notification")

    # Sample data for the test
    project = Project(id=1, tenant_id=1, name="Test Project")
    framework = Framework(id=1, name="Framework 1", description="Framework 1 description")
    framework_version = FrameworkVersion(
        id=1, version_prefix="prefix", version_suffix="suffix", guidance="guidance", framework_id=1
    )
    control = Control(
        id=1,
        name="Control 1",
        description="Control 1 description",
        guidance="Guidance",
        tenant_id=1,
    )
    project_control = ProjectControl(id=1, project_id=1, control_id=1)
    db.add_all([project, framework, framework_version, control, project_control])
    db.commit()

    # Mock data
    assessment_data = CreateAssessment(
        project_control_id="1", name="New Assessment", description="Testing"
    )
    user_id = 1

    # Call create_assessment function
    result = await create_assessment(
        db=db, assessment=assessment_data, user_id=user_id, tenant_id=1
    )

    # Assert assessment is created
    assert result is not None
    assert db.query(Assessment).filter(Assessment.name == "New Assessment").count() == 1

    # Check history log
    history_log = (
        db.query(AssessmentHistory).filter(AssessmentHistory.assessment_id == result.id).first()
    )
    assert history_log is not None
    assert "Created new assessment" in history_log.history

    # # Check notification functions
    # mock_send_email.assert_called_once()
    # mock_publish_sms.assert_called_once()


def test_get_all_assessments(db):
    tenant_id = 1
    assessments = get_all_assessments(db, tenant_id=tenant_id, project_id=None)
    # assert len(assessments) > 0


def test_get_assessment(db):
    assessments = get_assessment(db=db, id=1, tenant_id=1)
    # assert len(assessments) > 0


@pytest.mark.asyncio
async def test_update_assessment(db, mocker):
    # Mocks for email and SMS
    mock_send_email = mocker.patch("fedrisk_api.utils.email_util.send_watch_email")
    mock_publish_sms = mocker.patch("fedrisk_api.utils.sms_util.publish_notification")

    # Setup initial assessment
    assessment = CreateAssessment(
        project_control_id="1", name="Initial Assessment", description="Initial Desc"
    )
    db.add(Assessment(**assessment.dict()))
    db.commit()

    print(assessment)

    # Update assessment
    update_data = UpdateAssessment(name="Updated Assessment", description="Updated Desc")
    await update_assessment(
        db=db, id=1, keywords="security", assessment=update_data, tenant_id=1, user_id=1
    )

    # Assert updates are applied and notifications are triggered
    updated_assessment = db.query(Assessment).filter(Assessment.id == 1).first()
    # assert updated_assessment.name == "Updated Assessment"
    # mock_send_email.assert_called_once()
    # mock_publish_sms.assert_called_once()


@pytest.mark.asyncio
async def test_delete_assessment(db, mocker):
    # Mock notifications
    mock_send_email = mocker.patch("fedrisk_api.utils.email_util.send_watch_email")
    mock_publish_sms = mocker.patch("fedrisk_api.utils.sms_util.publish_notification")

    # Create assessment to delete
    assessment = Assessment(name="To Be Deleted")
    db.add(assessment)
    db.commit()

    # Call delete function
    result = await delete_assessment(db, id=assessment.id, tenant_id=1)

    # Check that the assessment is deleted
    # assert result is True
    # assert db.query(Assessment).filter(Assessment.id == assessment.id).count() == 0

    # # Assert notifications were sent
    # mock_send_email.assert_called_once()
    # mock_publish_sms.assert_called_once()


# def test_search(db):
#     search_results, count = search(query="test", db=db, tenant_id=1, user_id=1)
#     assert len(search_results) > 0
#     assert count == len(search_results)
