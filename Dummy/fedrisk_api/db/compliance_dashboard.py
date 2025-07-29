from collections import OrderedDict
from typing import Dict
import logging

from sqlalchemy import func, extract
from sqlalchemy.orm import Session

from fedrisk_api.db.dashboard import get_framework, get_project
from fedrisk_api.db.enums import AuditTestStatus, CapPoamStatus, Criticality
from fedrisk_api.db.models import (
    AuditTest,
    AuditTestInstance,
    # Control,
    Framework,
    # ProjectControl,
    # FrameworkVersion,
    CapPoam,
    Project,
)

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

AUDIT_TEST_STATUS = [member.value for member in AuditTestStatus]
CAP_POAM_STATUS = [member.value for member in CapPoamStatus]
CAP_POAM_CRITICALITY = [member.value for member in Criticality]


def get_compliance_dashboard_metrics(db: Session, project_id: int, framework_id: int, user: Dict):
    project = get_project(db=db, project_id=project_id, user=user)

    if not project:
        return {
            "project_id": -1,
            "project_name": "",
            "framework_id": -1,
            "framework_name": "",
            "total": 0,
            "monthly": [],
            "status": [],
        }

    framework = get_framework(db=db, framework_id=framework_id, project_id=project.id, user=user)

    if not framework:
        return {
            "project_id": -1,
            "project_name": "",
            "framework_id": -1,
            "framework_name": "",
            "total": 0,
            "monthly": [],
            "status": [],
        }

    audit_test_total_count = (
        db.query(AuditTestInstance)
        .join(AuditTest, AuditTestInstance.audit_test_id == AuditTest.id)
        .filter(AuditTestInstance.start_date != None)
        .filter(AuditTestInstance.status != None)
        .filter(AuditTest.project_id == project_id)
        .distinct()
        .count()
    )

    monthly_count = (
        db.query(
            func.to_char(func.date_trunc("month", AuditTestInstance.start_date), "Month").label(
                "month"
            ),
            func.count("*").label("count"),
        )
        .select_from(AuditTestInstance)
        .join(AuditTest, AuditTestInstance.audit_test_id == AuditTest.id)
        # .select_from(AuditTest)
        .filter(
            func.date_trunc("year", AuditTestInstance.start_date)
            == func.date_trunc("year", func.now())
        )
        .filter(AuditTest.project_id == project_id)
        .filter(AuditTestInstance.status != None)
        .group_by(func.date_trunc("month", AuditTestInstance.start_date))
        .all()
    )
    # LOGGER.info(f"monthly count {monthly_count}")

    audit_test_monthly_count = MONTHS.copy()
    for month in monthly_count:
        audit_test_monthly_count[month["month"].strip(" ")] += month["count"]
    audit_test_monthly_count = [
        {"name": month, "count": count} for month, count in audit_test_monthly_count.items()
    ]

    # LOGGER.info(f"audit_test_monthly_count {audit_test_monthly_count}")

    status_count = (
        db.query(AuditTestInstance.status.label("name"), func.count("*").label("count"))
        .select_from(AuditTestInstance)
        .join(AuditTest, AuditTestInstance.audit_test_id == AuditTest.id)
        .filter(AuditTest.project_id == project_id)
        .filter(AuditTestInstance.status != None)
        .filter(AuditTestInstance.start_date != None)
        .group_by(AuditTestInstance.status)
    )
    audit_test_status_count = {status: 0 for status in AUDIT_TEST_STATUS}
    for status in status_count:
        audit_test_status_count[status["name"]] += status["count"]
    audit_test_status_count = [
        {"name": status, "count": count} for status, count in audit_test_status_count.items()
    ]
    # LOGGER.info(f"audit_test_status_count {audit_test_status_count}")

    # Get framework name to display and return
    framework_name = ""
    framework = db.query(Framework).filter(Framework.id == framework_id).first()
    if framework is not None:
        framework_name = framework.name
    return {
        "project_id": project.id,
        "project_name": project.name,
        "framework_id": framework_id,
        "framework_name": framework_name,
        "total": audit_test_total_count,
        "monthly": audit_test_monthly_count,
        "status": audit_test_status_count,
    }


def get_compliance_dashboard_metrics_cap_poam(db: Session, project_id: int, user: Dict):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        return {
            "project_id": -1,
            "project_name": "",
            "total": 0,
            "monthly": [],
            "status": [],
        }

    cap_poam_total_count = (
        db.query(CapPoam)
        .filter(CapPoam.due_date != None)
        .filter(CapPoam.status != None)
        .filter(CapPoam.project_id == project.id)
        .distinct()
        .count()
    )

    monthly_count = (
        db.query(
            func.to_char(func.date_trunc("month", CapPoam.due_date), "Month").label("month"),
            func.count("*").label("count"),
        )
        .select_from(CapPoam)
        .filter(func.date_trunc("year", CapPoam.due_date) == func.date_trunc("year", func.now()))
        .filter(CapPoam.project_id == project.id)
        .filter(CapPoam.status != None)
        .group_by(func.date_trunc("month", CapPoam.due_date))
        .all()
    )

    cap_poam_monthly_count = MONTHS.copy()
    for month in monthly_count:
        cap_poam_monthly_count[month["month"].strip(" ")] += month["count"]
    cap_poam_monthly_count = [
        {"x": month, "y": count} for month, count in cap_poam_monthly_count.items()
    ]

    status_count = (
        db.query(CapPoam.status.label("name"), func.count("*").label("count"))
        .select_from(CapPoam)
        .filter(CapPoam.project_id == project.id)
        .filter(CapPoam.status != None)
        .filter(CapPoam.due_date != None)
        .group_by(CapPoam.status)
    )
    cap_poam_status_count = {status: 0 for status in CAP_POAM_STATUS}
    for status in status_count:
        cap_poam_status_count[status["name"]] += status["count"]
    cap_poam_status_count = [
        {"x": status, "y": count} for status, count in cap_poam_status_count.items()
    ]

    criticality_count = (
        db.query(CapPoam.criticality_rating.label("name"), func.count("*").label("count"))
        .select_from(CapPoam)
        .filter(CapPoam.project_id == project.id)
        .filter(CapPoam.criticality_rating != None)
        .filter(CapPoam.due_date != None)
        .group_by(CapPoam.criticality_rating)
    )
    cap_poam_criticality_count = {
        criticality_rating: 0 for criticality_rating in CAP_POAM_CRITICALITY
    }
    for criticality_rating in criticality_count:
        cap_poam_criticality_count[criticality_rating["name"]] += criticality_rating["count"]
    cap_poam_criticality_count = [
        {"x": criticality_rating, "y": count}
        for criticality_rating, count in cap_poam_criticality_count.items()
    ]

    return {
        "project_id": project.id,
        "project_name": project.name,
        "total": cap_poam_total_count,
        "monthly": cap_poam_monthly_count,
        "status": cap_poam_status_count,
        "criticality": cap_poam_criticality_count,
    }


def get_compliance_audit_test_by_month_for_year(db: Session, project_id: int, year: int):
    project = db.query(Project).filter(Project.id == project_id).first()

    if not project:
        return {
            "project_id": -1,
            "project_name": "",
            "total": 0,
            "monthly": [],
            "status": [],
        }
    status_count = (
        db.query(AuditTestInstance.status.label("name"), func.count("*").label("count"))
        .select_from(AuditTestInstance)
        # .select_from(AuditTest)
        .outerjoin(AuditTest, AuditTestInstance.audit_test_id == AuditTest.id)
        .filter(extract("year", AuditTestInstance.start_date) == year)
        .filter(AuditTest.project_id == project_id)
        .filter(AuditTestInstance.status != None)
        .filter(AuditTestInstance.start_date != None)
        .group_by(AuditTestInstance.status)
    )
    audit_test_status_count = {status: 0 for status in AUDIT_TEST_STATUS}
    for status in status_count:
        audit_test_status_count[status["name"]] += status["count"]
    audit_test_status_count = [
        {"x": status, "y": count} for status, count in audit_test_status_count.items()
    ]
    # LOGGER.info(f"audit_test_status_count {audit_test_status_count}")
    audit_test_total_count = (
        db.query(AuditTestInstance)
        .outerjoin(AuditTest, AuditTestInstance.audit_test_id == AuditTest.id)
        .filter(extract("year", AuditTestInstance.start_date) == year)
        .filter(AuditTestInstance.start_date != None)
        .filter(AuditTestInstance.status != None)
        .filter(AuditTest.project_id == project_id)
        .distinct()
        .count()
    )

    monthly_count = (
        db.query(
            func.to_char(func.date_trunc("month", AuditTestInstance.start_date), "Month").label(
                "month"
            ),
            func.count("*").label("count"),
        )
        .select_from(AuditTestInstance)
        # .select_from(AuditTest)
        .outerjoin(AuditTest, AuditTestInstance.audit_test_id == AuditTest.id)
        .filter(extract("year", AuditTestInstance.start_date) == year)
        .filter(AuditTest.project_id == project_id)
        .filter(AuditTestInstance.status != None)
        .group_by(func.date_trunc("month", AuditTestInstance.start_date))
        .all()
    )

    audit_test_monthly_count = MONTHS.copy()
    for month in monthly_count:
        audit_test_monthly_count[month["month"].strip(" ")] += month["count"]
    audit_test_monthly_count = [
        {"x": month, "y": count} for month, count in audit_test_monthly_count.items()
    ]
    # LOGGER.info(f"audit_test_monthly_count {audit_test_monthly_count}")
    return {
        "project_id": project.id,
        "project_name": project.name,
        "total": audit_test_total_count,
        "monthly": audit_test_monthly_count,
        "status": audit_test_status_count,
    }
