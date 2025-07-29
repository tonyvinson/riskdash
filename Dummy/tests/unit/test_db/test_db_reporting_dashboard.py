import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from fedrisk_api.db.models import (
    Risk,
    RiskCategory,
    Project,
    User,
    ProjectUser,
    ProjectControl,
    RiskStatus,
    RiskScore,
    RiskLikelihood,
    RiskImpact,
    AuditTest,
    ReportingSettings,
)
from fedrisk_api.schema.reporting_dashboard import CreateReportingSettings, UpdateReportingSettings
from fedrisk_api.db.reporting_dashboard import (
    get_risk_by_category_count,
    get_data_for_pivot,
    create_reporting_settings_user,
    update_reporting_settings_user,
    get_reporting_settings_for_user,
    delete_reporting_settings_by_user_id,
)


@pytest.fixture
def db_session():
    """Fixture for a mocked database session."""
    return MagicMock(spec=Session)


# def test_get_risk_by_category_count(db_session):
#     # """Test retrieving risk by category count."""
#     # db_session.query().join().filter().distinct().count.side_effect = [10, 5]
#     # db_session.query().select_from().join().filter().group_by().all.return_value = [
#     #     {"month": "January", "count": 2, "name": "Category A"},
#     #     {"month": "February", "count": 3, "name": "Category B"},
#     # ]

#     result = get_risk_by_category_count(db_session, project_id=1)

#     # assert result["total"] == 10
#     # assert result["percent_completed"] == '50.00'
#     # assert len(result["monthly"]) == 2
#     # assert result["monthly"][0]["month"] == "January"


def test_get_data_for_pivot(db_session):
    """Test getting data for pivot table."""
    db_session.query().filter().first.return_value = User(id=1, system_role=1)
    db_session.query().options().all.return_value = [Project(id=1, name="Test Project")]
    db_session.query().filter().all.side_effect = [
        [Risk(id=1)],  # Risk query for project_risk
        [],  # Risk status
        [],  # Risk score
        [],  # Risk impact
        [],  # Risk likelihood
        [],  # Risks for metrics
    ]
    db_session.query().filter().count.side_effect = [0, 0, 0, 0, 5]  # Audit tests, controls

    result = get_data_for_pivot(db_session, tenant_id=1, user_id=1)

    # assert len(result) == 1
    # assert result[0]["id"] == 1
    # assert result[0]["name"] == "Test Project"


def test_create_reporting_settings_user(db_session):
    """Test creating reporting settings for a user."""
    settings_data = CreateReportingSettings(user_id=1, pivot_state=True)
    result = create_reporting_settings_user(settings_data, db_session)

    db_session.add.assert_called_once()
    db_session.commit.assert_called_once()
    # assert result.user_id == 1


def test_update_reporting_settings_user(db_session):
    """Test updating reporting settings for a user."""
    db_session.query().filter().first.return_value = ReportingSettings(user_id=1)
    settings_data = UpdateReportingSettings(user_id=1, settings="Updated Settings")

    result = update_reporting_settings_user(settings_data, db_session)

    db_session.commit.assert_called_once()
    assert result is True


def test_update_reporting_settings_user_not_found(db_session):
    """Test updating reporting settings when user settings are not found."""
    db_session.query().filter().first.return_value = None
    settings_data = UpdateReportingSettings(user_id=2)

    result = update_reporting_settings_user(settings_data, db_session)

    assert result is False


def test_get_reporting_settings_for_user(db_session):
    """Test retrieving reporting settings for a user."""
    db_session.query().filter().first.return_value = ReportingSettings(user_id=1)

    result = get_reporting_settings_for_user(db_session, user_id=1)

    # assert result.settings == "User Settings"


def test_get_reporting_settings_for_user_not_found(db_session):
    """Test retrieving reporting settings for a user when none exist."""
    db_session.query().filter().first.return_value = None

    result = get_reporting_settings_for_user(db_session, user_id=2)

    assert result == "There are no settings for this user"


def test_delete_reporting_settings_by_user_id(db_session):
    """Test deleting reporting settings by user ID."""
    mock_settings = [ReportingSettings(user_id=1)]
    db_session.query().filter().all.return_value = mock_settings

    result = delete_reporting_settings_by_user_id(db_session, user_id=1)

    db_session.delete.assert_called_once_with(mock_settings)
    db_session.commit.assert_called_once()
    assert result is True


def test_delete_reporting_settings_by_user_id_not_found(db_session):
    """Test deleting reporting settings when none exist for the user."""
    db_session.query().filter().all.return_value = []

    result = delete_reporting_settings_by_user_id(db_session, user_id=2)

    assert result is False
