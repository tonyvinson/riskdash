from collections import OrderedDict

# from typing import Dict

from sqlalchemy import func, extract
from sqlalchemy.orm import Session, selectinload

# from fedrisk_api.utils.utils import filter_by_tenant

# from fedrisk_api.db.enums import AuditTestStatus
from fedrisk_api.db.models import (
    Risk,
    RiskCategory,
    Project,
    User,
    ProjectUser,
    ProjectControl,
    # Control,
    RiskStatus,
    RiskScore,
    RiskLikelihood,
    RiskImpact,
    AuditTest,
    AuditTestInstance,
    ReportingSettings,
    CapPoam,
)
from fedrisk_api.schema.reporting_dashboard import (
    CreateReportingSettings,
    UpdateReportingSettings,
    # DisplayReportingSettings,
)

import logging
from fedrisk_api.utils.utils import get_risk_mapping_metrics

risk_mapping_metrics = get_risk_mapping_metrics()

LOGGER = logging.getLogger(__name__)

MONTHS = OrderedDict(
    {
        "January": 0,
        "February": 0,
        "March": 0,
        "April": 0,
        "May": 0,
        "June": 0,
        "July": 0,
        "August": 0,
        "September": 0,
        "October": 0,
        "November": 0,
        "December": 0,
    }
)

RISK_ATTRIBUTES = {
    "risk_score": {"10", "5", "1"},
    "risk_status": {"Active", "On Hold", "Completed", "Cancelled"},
    "risk_impact": {"Insignificant", "Minor", "Moderate", "Major", "Extreme"},
    "risk_likelihood": {"Very Likely", "Likely", "Possible", "Unlikely", "Very Unlikely"},
}


def get_risk_by_category_count(db: Session, project_id: int, year: int):

    risk_total_count = (
        db.query(Risk)
        .join(RiskCategory, Risk.risk_category_id == RiskCategory.id)
        .filter(Risk.risk_category_id != None)
        .filter(Risk.project_id == project_id)
        .distinct()
        .count()
    )

    risk_status_completed_count = (
        db.query(Risk)
        .filter(Risk.risk_status_id == 3)
        .filter(Risk.project_id == project_id)
        .distinct()
        .count()
    )

    monthly_count = (
        db.query(
            func.to_char(func.date_trunc("month", Risk.created_date), "Month").label("month"),
            func.count("*").label("count"),
            RiskCategory.name,
        )
        .select_from(Risk, RiskCategory)
        .join(RiskCategory, Risk.risk_category_id == RiskCategory.id)
        # .filter(func.date_trunc("year", Risk.created_date) == func.date_trunc("year", func.now()))
        .filter(extract("year", Risk.created_date) == year)
        .filter(Risk.project_id == project_id)
        .filter(Risk.risk_category_id != None)
        .group_by(RiskCategory.name)
        .group_by(func.date_trunc("month", Risk.created_date))
        .all()
    )
    print(f"monthly count {monthly_count}")

    monthnametotals = []
    for month in monthly_count:
        monthnametotals.append(
            {"month": month["month"].strip(" "), "count": month["count"], "category": month["name"]}
        )

    if risk_total_count != 0 and risk_status_completed_count != 0:
        return {
            "total": risk_total_count,
            "percent_completed": format(
                risk_status_completed_count / risk_total_count * 100, ".2f"
            ),
            "monthly": monthnametotals,
        }
    else:
        return {
            "total": risk_total_count,
            "percent_completed": "0.00",
            "monthly": monthnametotals,
        }


def get_data_for_pivot(db: Session, tenant_id: int, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user.system_role in [1, 4]:
        queryset = db.query(Project).filter(
            Project.tenant_id == tenant_id,
            Project.project_group_id.isnot(None),  # Only include projects with a project group
        )
    else:
        queryset = (
            db.query(Project)
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .filter(
                ProjectUser.user_id == user_id,
                Project.project_group_id.isnot(None),  # Only include projects with a project group
            )
        )

    queryset = queryset.options(selectinload(Project.project_group)).all()

    # for query in queryset:

    results = []
    for query in queryset:
        # go through each risk and get mapping data and add to appropriate tally
        low_count = 0
        low_medium_count = 0
        medium_count = 0
        medium_high_count = 0
        high_count = 0
        project_risk = db.query(Risk).filter(Risk.project_id == query.id).all()

        all_risks_ids = {risk.id for risk in project_risk}

        risk_status = (
            db.query(
                RiskStatus.name,
                func.count("*").label("count"),
            )
            .select_from(Risk)
            .join(RiskStatus, RiskStatus.id == Risk.risk_status_id)
            .filter(Risk.id.in_(all_risks_ids))
            .group_by(RiskStatus.name)
            .filter(Risk.project_id == query.id)
            .all()
        )

        risk_score = (
            db.query(
                RiskScore.name,
                func.count("*").label("count"),
            )
            .select_from(Risk)
            .join(RiskScore, RiskScore.id == Risk.risk_score_id)
            .filter(Risk.id.in_(all_risks_ids))
            .group_by(RiskScore.name)
            .filter(Risk.project_id == query.id)
            .all()
        )

        risk_impact = (
            db.query(RiskImpact.name, func.count("*").label("count"))
            .select_from(Risk)
            .join(RiskImpact, RiskImpact.id == Risk.risk_impact_id)
            .filter(Risk.id.in_(all_risks_ids))
            .group_by(RiskImpact.name)
            .filter(Risk.project_id == query.id)
            .all()
        )

        risk_likelihood = (
            db.query(
                RiskLikelihood.name,
                func.count("*").label("count"),
            )
            .select_from(Risk)
            .join(RiskLikelihood, RiskLikelihood.id == Risk.current_likelihood_id)
            .filter(Risk.id.in_(all_risks_ids))
            .group_by(RiskLikelihood.name)
            .filter(Risk.project_id == query.id)
            .all()
        )

        default_mapping = [
            (risk_status, RISK_ATTRIBUTES["risk_status"].copy()),
            (risk_score, RISK_ATTRIBUTES["risk_score"].copy()),
            (risk_impact, RISK_ATTRIBUTES["risk_impact"].copy()),
            (risk_likelihood, RISK_ATTRIBUTES["risk_likelihood"].copy()),
        ]

        for risk_attr_value in default_mapping:
            missing_values = risk_attr_value[1] - {obj.name for obj in risk_attr_value[0]}
            for missing_value in missing_values:
                risk_attr_value[0].append({"name": missing_value, "count": 0})

        risks = (
            db.query(
                RiskLikelihood.name.label("current_likelihood"),
                RiskImpact.name.label("risk_impact"),
            )
            .select_from(Risk)
            .join(RiskLikelihood, RiskLikelihood.id == Risk.current_likelihood_id)
            .join(RiskImpact, RiskImpact.id == Risk.risk_impact_id)
            .filter(Risk.id.in_(all_risks_ids))
            .filter(Risk.project_id == query.id)
            .group_by(RiskLikelihood.name)
            .group_by(RiskImpact.name)
            .all()
        )

        for risk in risks:
            current_likelihood_name = "_".join(risk.current_likelihood.split(" "))
            risk_matrics_key = f"{current_likelihood_name}__{risk.risk_impact}".lower()
            for key, value in risk_mapping_metrics.items():
                for risk_matrics in set(value):
                    if risk_matrics_key == risk_matrics:
                        if key == "low":
                            low_count += 1
                        elif key == "low_medium":
                            low_medium_count += 1
                        elif key == "medium":
                            medium_count += 1
                        elif key == "medium_high":
                            medium_high_count += 1
                        elif key == "high":
                            high_count += 1
        # get audit tests by status
        # not_started = "Not Started"
        # on_going = "On Going"
        # complete = "Complete"
        # on_hold = "On Hold"
        audit_test_not_started = (
            db.query(AuditTestInstance)
            .join(AuditTest, AuditTest.id == AuditTestInstance.audit_test_id)
            .filter(AuditTest.project_id == query.id)
            .filter(AuditTestInstance.status == "not_started")
        ).count()
        audit_test_on_going = (
            db.query(AuditTestInstance)
            .join(AuditTest, AuditTest.id == AuditTestInstance.audit_test_id)
            .filter(AuditTest.project_id == query.id)
            .filter(AuditTestInstance.status == "on_going")
        ).count()
        audit_test_complete = (
            db.query(AuditTestInstance)
            .join(AuditTest, AuditTest.id == AuditTestInstance.audit_test_id)
            .filter(AuditTest.project_id == query.id)
            .filter(AuditTestInstance.status == "complete")
        ).count()
        audit_test_on_hold = (
            db.query(AuditTestInstance)
            .join(AuditTest, AuditTest.id == AuditTestInstance.audit_test_id)
            .filter(AuditTest.project_id == query.id)
            .filter(AuditTestInstance.status == "on_hold")
        ).count()

        project_control_count = (
            db.query(ProjectControl).filter(ProjectControl.project_id == query.id)
        ).count()
        mitigation_percentages = (
            db.query(ProjectControl).filter(ProjectControl.project_id == query.id)
        ).all()
        control_mitigation_percent = 0.00
        control_count_perc = 0
        control_mitigation_percent_sum = 0
        for mp in mitigation_percentages:
            control_mitigation_percent += float(mp.mitigation_percentage)
            if float(mp.mitigation_percentage) > 0:
                control_count_perc += 1
        if project_control_count > 0:
            control_mitigation_percent_sum = float(control_mitigation_percent) / float(
                project_control_count
            )
        # get cap poams by status
        # not_started = "Not Started"
        # in_progress = "In Progress"
        # completed = "Completed"
        cap_poam_not_started = (
            db.query(CapPoam)
            .filter(CapPoam.project_id == query.id)
            .filter(CapPoam.status == "not_started")
        ).count()
        cap_poam_in_progress = (
            db.query(CapPoam)
            .filter(CapPoam.project_id == query.id)
            .filter(CapPoam.status == "in_progress")
        ).count()
        cap_poam_completed = (
            db.query(CapPoam)
            .filter(CapPoam.project_id == query.id)
            .filter(CapPoam.status == "completed")
        ).count()
        # get cap poams by criticality rating
        # low = "low"
        # medium = "medium"
        # high = "high"
        cap_poam_criticality_low = (
            db.query(CapPoam)
            .filter(CapPoam.project_id == query.id)
            .filter(CapPoam.criticality_rating == "low")
        ).count()
        cap_poam_criticality_medium = (
            db.query(CapPoam)
            .filter(CapPoam.project_id == query.id)
            .filter(CapPoam.criticality_rating == "medium")
        ).count()
        cap_poam_criticality_high = (
            db.query(CapPoam)
            .filter(CapPoam.project_id == query.id)
            .filter(CapPoam.criticality_rating == "high")
        ).count()
        # control_mit_sum = round(control_mitigation_percent_sum, 3)
        result = {
            "id": query.id,
            "name": query.name,
            "status": query.status,
            "created_date": query.created_date,
            "last_updated_date": query.last_updated_date,
            "project_group_id": query.project_group_id,
            "project_group_name": query.project_group.name,
            "risk_low_count": low_count,
            "risk_low_medium_count": low_medium_count,
            "risk_medium_count": medium_count,
            "risk_medium_high_count": medium_high_count,
            "risk_high_count": high_count,
            "audit_test_not_started": audit_test_not_started,
            "audit_test_on_going": audit_test_on_going,
            "audit_test_complete": audit_test_complete,
            "audit_test_on_hold": audit_test_on_hold,
            "control_mitigation_percent": control_mitigation_percent_sum,
            "project_control_count": project_control_count,
            "cap_poam_criticality_low": cap_poam_criticality_low,
            "cap_poam_criticality_medium": cap_poam_criticality_medium,
            "cap_poam_criticality_high": cap_poam_criticality_high,
            "cap_poam_not_started": cap_poam_not_started,
            "cap_poam_in_progress": cap_poam_in_progress,
            "cap_poam_completed": cap_poam_completed,
        }
        results.append(result)
    return results


def create_reporting_settings_user(settings: CreateReportingSettings, db: Session):
    reporting_settings = ReportingSettings(**settings.dict())
    db.add(reporting_settings)
    db.commit()
    return reporting_settings


def update_reporting_settings_user(settings: UpdateReportingSettings, db: Session):
    queryset = db.query(ReportingSettings).filter(ReportingSettings.user_id == settings.user_id)

    if not queryset.first():
        return False

    queryset.update(settings.dict(exclude_unset=True))
    db.commit()
    return True


def get_reporting_settings_for_user(db: Session, user_id: int):
    reporting_settings = db.query(ReportingSettings).filter(ReportingSettings.user_id == user_id)
    if not reporting_settings.first():
        return "There are no settings for this user"
    return reporting_settings.first()


def delete_reporting_settings_by_user_id(db: Session, user_id: int):
    settings = db.query(ReportingSettings).filter(ReportingSettings.user_id == user_id).all()

    if not settings:
        return False

    db.delete(settings)
    db.commit()
    return True
