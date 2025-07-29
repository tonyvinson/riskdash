import logging
from sqlalchemy import func
from sqlalchemy.orm import contains_eager, selectinload
from sqlalchemy.orm.session import Session

from datetime import datetime, time

from fedrisk_api.db.models import (
    AuditTest,
    AuditTestInstance,
    Control,
    ControlFrameworkVersion,
    Framework,
    FrameworkVersion,
    Project,
    ProjectControl,
    ProjectUser,
    Risk,
    User,
    Assessment,
    RiskLikelihood,
    RiskImpact,
    ControlStatus,
    Exception,
    ExceptionReview,
)
from fedrisk_api.utils.utils import (
    filter_by_tenant,
    get_risk_mapping_metrics,
    get_risk_mapping_order,
)

risk_mapping_metrics = get_risk_mapping_metrics()
risk_mapping_order = get_risk_mapping_order()

LOGGER = logging.getLogger(__name__)

RISK_ATTRIBUTES = {
    "risk_score": {"10", "5", "1"},
    "risk_status": {"Active", "On Hold", "Completed", "Cancelled"},
    "risk_category": {
        "Access Management",
        "Environmental Resilience",
        "Monitoring",
        "Physical Security",
        "Policy & Procedure",
        "Sensitive Data Management",
        "Technical Vulnerability",
        "Third Party Management",
    },
    "risk_impact": {"Insignificant", "Minor", "Moderate", "Major", "Extreme"},
    "risk_likelihood": {"Very Likely", "Likely", "Possible", "Unlikely", "Very Unlikely"},
}


def get_governance_projects(db: Session, offset, limit, sort_by, order_type, tenant_id, user_id):
    user = db.query(User).filter(User.id == user_id).first()

    if user.is_superuser:
        projects = db.query(Project)
    elif user.is_tenant_admin:
        projects = filter_by_tenant(db, Project, tenant_id)
    else:
        projects = (
            filter_by_tenant(db, Project, tenant_id)
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .filter(ProjectUser.user_id == user_id)
        )

    if sort_by.lower() == "name":
        if order_type.lower() == "asc":
            return (
                projects.order_by(Project.name.asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.audit_tests),
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions)
                    .selectinload(FrameworkVersion.framework),
                    selectinload(Project.risks),
                )
                .all()
            )
        return (
            projects.order_by(Project.name.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                selectinload(Project.audit_tests),
                selectinload(Project.risks),
            )
            .all()
        )

    elif sort_by.lower() == "framework":
        if order_type.lower() == "asc":
            return (
                projects.outerjoin(ProjectControl)
                .outerjoin(Control)
                .outerjoin(Framework)
                .order_by(Framework.name.asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions),
                    selectinload(FrameworkVersion.framework),
                    selectinload(Project.audit_tests),
                    selectinload(Project.risks),
                )
                .all()
            )
        return (
            projects.outerjoin(ProjectControl)
            .outerjoin(Control)
            .outerjoin(Framework)
            .order_by(Framework.name.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.audit_tests),
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                selectinload(Project.risks),
            )
            .all()
        )

    elif sort_by.lower() == "controls":
        if order_type == "asc":
            return (
                projects.outerjoin(ProjectControl)
                .group_by(Project)
                .order_by(func.count(ProjectControl.id).asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.audit_tests),
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions),
                    selectinload(FrameworkVersion.framework),
                    selectinload(Project.risks),
                )
                .all()
            )
        return (
            projects.outerjoin(ProjectControl)
            .group_by(Project)
            .order_by(func.count(ProjectControl.id).desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.audit_tests),
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                selectinload(Project.risks),
            )
            .all()
        )

    elif sort_by.lower() == "risks":
        if order_type.lower() == "asc":
            return (
                projects.outerjoin(Risk, Project.id == Risk.project_id)
                .group_by(Project)
                .order_by(func.count(Risk.id).asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.audit_tests),
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions),
                    selectinload(FrameworkVersion.framework),
                    selectinload(Project.risks),
                )
                .all()
            )
        return (
            projects.outerjoin(Risk, Project.id == Risk.project_id)
            .group_by(Project)
            .order_by(func.count(Risk.id).desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.audit_tests),
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                selectinload(Project.risks),
            )
            .all()
        )

    elif sort_by.lower() == "audit_tests":
        if order_type.lower() == "asc":
            return (
                projects.outerjoin(AuditTest, Project.id == AuditTest.project_id)
                .group_by(Project)
                .order_by(func.count(AuditTest.id).asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.audit_tests),
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions),
                    selectinload(FrameworkVersion.framework),
                    selectinload(Project.risks),
                )
                .all()
            )
        return (
            projects.outerjoin(AuditTest, Project.id == AuditTest.project_id)
            .group_by(Project)
            .order_by(func.count(AuditTest.id).desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.audit_tests),
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                selectinload(Project.risks),
            )
            .all()
        )

    else:
        return (
            projects.order_by(Project.last_updated_date.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.audit_tests),
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                selectinload(Project.risks),
            )
            .all()
        )


def get_risk_items(db: Session, offset, limit, sort_by, order_type, tenant_id, user_id):
    user = db.query(User).filter(User.id == user_id).first()

    if user.is_superuser:
        projects = db.query(Project)
    elif user.is_tenant_admin:
        projects = filter_by_tenant(db, Project, tenant_id)
    else:
        projects = (
            filter_by_tenant(db, Project, tenant_id)
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .filter(ProjectUser.user_id == user_id)
        )

    if sort_by.lower() == "name":
        if order_type.lower() == "asc":
            return (
                projects.join(Risk, Project.id == Risk.project_id)
                .order_by(Project.name.asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions),
                    selectinload(FrameworkVersion.framework),
                    contains_eager(Project.risks).selectinload(Risk.risk_score),
                )
                .distinct()
                .all()
            )
        return (
            projects.join(Risk, Project.id == Risk.project_id)
            .order_by(Project.name.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                contains_eager(Project.risks).selectinload(Risk.risk_score),
            )
            .distinct()
            .all()
        )

    elif sort_by.lower() == "framework":
        if order_type.lower() == "asc":
            return (
                projects.join(ProjectControl)
                .join(Control)
                .join(Framework)
                .filter(Project.id == Risk.project_id)
                .order_by(Framework.name.asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions),
                    selectinload(FrameworkVersion.framework),
                    selectinload(Project.risks).selectinload(Risk.risk_score),
                )
                .distinct()
                .all()
            )
        return (
            projects.join(ProjectControl)
            .join(Control)
            .join(Framework)
            .filter(Project.id == Risk.project_id)
            .order_by(Framework.name.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                selectinload(Project.risks).selectinload(Risk.risk_score),
            )
            .distinct()
            .all()
        )

    elif sort_by.lower() == "risks":
        if order_type.lower() == "asc":
            return (
                projects.join(Risk, Project.id == Risk.project_id)
                .group_by(Project)
                .order_by(func.count(Risk.id).asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions),
                    selectinload(FrameworkVersion.framework),
                    selectinload(Project.risks).selectinload(Risk.risk_score),
                )
                .all()
            )
        return (
            projects.join(Risk, Project.id == Risk.project_id)
            .group_by(Project)
            .order_by(func.count(Risk.id).desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                selectinload(Project.risks).selectinload(Risk.risk_score),
            )
            .all()
        )

    else:
        return (
            projects.join(Risk, Project.id == Risk.project_id)
            .order_by(Risk.last_updated_date.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                selectinload(Project.risks).selectinload(Risk.risk_score),
            )
            .distinct()
            .all()
        )


def get_compliance(db: Session, offset, limit, sort_by, order_type, tenant_id, user_id):
    user = db.query(User).filter(User.id == user_id).first()

    if user.is_superuser:
        projects = db.query(Project)
    elif user.is_tenant_admin:
        projects = filter_by_tenant(db, Project, tenant_id)
    else:
        projects = (
            filter_by_tenant(db, Project, tenant_id)
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .filter(ProjectUser.user_id == user_id)
        )

    if sort_by.lower() == "name":
        if order_type.lower() == "asc":
            return (
                projects.join(AuditTest, Project.id == AuditTest.project_id)
                .order_by(Project.name.asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions),
                    selectinload(FrameworkVersion.framework),
                    contains_eager(Project.audit_tests),
                )
                .distinct()
                .all()
            )
        return (
            projects.join(AuditTest, Project.id == AuditTest.project_id)
            .order_by(Project.name.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                contains_eager(Project.audit_tests),
            )
            .distinct()
            .all()
        )

    elif sort_by.lower() == "framework":
        if order_type.lower() == "asc":
            return (
                projects.join(ProjectControl)
                .join(Control)
                .join(Framework)
                .filter(Project.id == AuditTest.project_id)
                .order_by(Framework.name.asc())
                .limit(limit)
                .offset(offset)
                .options(
                    contains_eager(Project.project_controls)
                    .contains_eager(ProjectControl.control)
                    .contains_eager(Control.framework_versions),
                    contains_eager(FrameworkVersion.framework),
                    contains_eager(Project.audit_tests),
                )
                .distinct()
                .distinct()
                .all()
            )
        return (
            projects.join(ProjectControl)
            .join(Control)
            .join(Framework)
            .filter(Project.id == AuditTest.project_id)
            .order_by(Framework.name.desc())
            .limit(limit)
            .offset(offset)
            .options(
                contains_eager(Project.project_controls)
                .contains_eager(ProjectControl.control)
                .contains_eager(Control.framework_versions),
                contains_eager(FrameworkVersion.framework),
                contains_eager(Project.audit_tests),
            )
            .distinct()
            .all()
        )

    elif sort_by.lower() == "audit_tests":
        if order_type.lower() == "asc":
            return (
                projects.join(AuditTest, Project.id == AuditTest.project_id)
                .group_by(Project)
                .order_by(func.count(AuditTest.id).asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions),
                    selectinload(FrameworkVersion.framework),
                    selectinload(Project.audit_tests),
                )
                .all()
            )
        return (
            projects.join(AuditTest, Project.id == AuditTest.project_id)
            .group_by(Project)
            .order_by(func.count(AuditTest.id).desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                selectinload(Project.audit_tests),
            )
            .all()
        )

    else:
        return (
            projects.join(AuditTest, Project.id == AuditTest.project_id)
            .order_by(AuditTest.id.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
                contains_eager(Project.audit_tests),
            )
            .distinct()
            .all()
        )


def get_projects_tasks(db: Session, offset, limit, sort_by, order_type, tenant_id, user_id):
    user = db.query(User).filter(User.id == user_id).first()

    if user.is_superuser:
        projects = db.query(Project)
    elif user.is_tenant_admin:
        projects = filter_by_tenant(db, Project, tenant_id)
    else:
        projects = (
            filter_by_tenant(db, Project, tenant_id)
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .filter(ProjectUser.user_id == user_id)
        )

    if sort_by.lower() == "name":
        if order_type.lower() == "asc":
            return (
                projects.order_by(Project.name.asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions)
                    .selectinload(FrameworkVersion.framework),
                )
                .all()
            )
        return (
            projects.order_by(Project.name.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
            )
            .all()
        )

    elif sort_by.lower() == "framework":
        if order_type.lower() == "asc":
            return (
                projects.outerjoin(ProjectControl)
                .outerjoin(Control)
                .outerjoin(Framework)
                .order_by(Framework.name.asc())
                .limit(limit)
                .offset(offset)
                .options(
                    selectinload(Project.project_controls)
                    .selectinload(ProjectControl.control)
                    .selectinload(Control.framework_versions),
                    selectinload(FrameworkVersion.framework),
                )
                .all()
            )
        return (
            projects.outerjoin(ProjectControl)
            .outerjoin(Control)
            .outerjoin(Framework)
            .order_by(Framework.name.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
            )
            .all()
        )

    else:
        return (
            projects.order_by(Project.created_date.desc())
            .limit(limit)
            .offset(offset)
            .options(
                selectinload(Project.project_controls)
                .selectinload(ProjectControl.control)
                .selectinload(Control.framework_versions),
                selectinload(FrameworkVersion.framework),
            )
            .all()
        )


def get_summary_chart_data_by_project(db: Session, project_id, tenant_id, user_id):
    project_query = (
        db.query(
            Project.name.label("name"),
            Project.id.label("id"),
            Project.created_date.label("created_date"),
            Project.last_updated_date.label("last_updated_date"),
            Project.project_admin_id.label("project_admin_id"),
        )
        .select_from(Project)
        .filter(Project.id == project_id)
        .first()
    )
    user_query = (
        db.query(
            User.email.label("email"),
            User.id.label("id"),
        )
        .select_from(User)
        .filter(User.id == project_query.project_admin_id)
        .first()
    )
    risks = (
        db.query(
            RiskLikelihood.name.label("current_likelihood"), RiskImpact.name.label("risk_impact")
        )
        .select_from(Risk)
        .join(RiskLikelihood, RiskLikelihood.id == Risk.current_likelihood_id)
        .join(RiskImpact, RiskImpact.id == Risk.risk_impact_id)
        .filter(Risk.project_id == project_id)
        .all()
    )

    low_count = 0
    low_medium_count = 0
    medium_count = 0
    medium_high_count = 0
    high_count = 0
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

    num_risks_over_5 = 0

    num_risks_over_5_query = (
        db.query(Risk).filter(Risk.risk_score_id > 5).filter(Risk.project_id == project_id).count()
    )

    if num_risks_over_5_query != 0:
        num_risks = db.query(Risk).filter(Risk.project_id == project_id).count()
        num_risks_over_5 = num_risks_over_5_query / num_risks * 100

    audit_test_count = db.query(AuditTest).filter(AuditTest.project_id == project_id).count()

    audit_test_completed = (
        db.query(AuditTestInstance)
        .join(AuditTest, AuditTest.id == AuditTestInstance.audit_test_id)
        .filter(AuditTest.project_id == project_id)
        .filter(AuditTestInstance.status == "complete")
        .count()
    )

    audit_test_not_started = (
        db.query(AuditTestInstance)
        .join(AuditTest, AuditTest.id == AuditTestInstance.audit_test_id)
        .filter(AuditTest.project_id == project_id)
        .filter(AuditTestInstance.status == "not_started")
        .count()
    )

    audit_test_on_hold = (
        db.query(AuditTestInstance)
        .join(AuditTest, AuditTest.id == AuditTestInstance.audit_test_id)
        .filter(AuditTest.project_id == project_id)
        .filter(AuditTestInstance.status == "on_hold")
        .count()
    )

    audit_test_pending = audit_test_not_started + audit_test_on_hold

    project_control_count = (
        db.query(ProjectControl).filter(ProjectControl.project_id == project_id).count()
    )

    total_assessments = (
        db.query(Assessment)
        .join(ProjectControl, ProjectControl.id == Assessment.project_control_id)
        .filter(ProjectControl.project_id == project_id)
        .count()
    )

    assessments_complete = (
        db.query(Assessment)
        .join(ProjectControl, ProjectControl.id == Assessment.project_control_id)
        .filter(ProjectControl.project_id == project_id)
        .filter(Assessment.status == "complete")
        .count()
    )

    # get status string name
    control_status_classes = (
        db.query(ControlStatus)
        .join(ProjectControl, ProjectControl.control_status_id == ControlStatus.id)
        .filter(ProjectControl.project_id == project_id)
        .all()
    )

    control_status_ids = (
        db.query(ProjectControl.control_status_id.label("control_status_id"))
        .select_from(ProjectControl)
        .filter(ProjectControl.project_id == project_id)
        .all()
    )
    matchescount = 0
    matches = []
    # get matches for status id on project controls
    for status in control_status_classes:
        for index, id in enumerate(control_status_ids):
            id_trim = []
            id_trim.extend(id)
            if status.id == id_trim[0]:
                matchescount = matchescount + 1
        matches.append(matchescount)
        matchescount = 0

    statuses = []
    for status in control_status_classes:
        statuses.append(status.name)

    control_status_data = []
    index = 0
    for status in statuses:
        control_status_data.append({"x": status, "y": matches[index]})
        index = index + 1

    # get status string name
    exceptions_statuses = (
        db.query(ExceptionReview.review_status.label("review_status"))
        .select_from(ExceptionReview)
        .join(Exception, Exception.id == ExceptionReview.exception_id)
        .join(ProjectControl, ProjectControl.id == Exception.project_control_id)
        .filter(ProjectControl.project_id == project_id)
        .distinct()
        .all()
    )

    exceptions_status_values = (
        db.query(ExceptionReview.review_status.label("review_status"))
        .select_from(ExceptionReview)
        .join(Exception, Exception.id == ExceptionReview.exception_id)
        .join(ProjectControl, ProjectControl.id == Exception.project_control_id)
        .filter(ProjectControl.project_id == project_id)
        .all()
    )

    excp_matches_count = 0
    excp_matches = []

    # get matches for status id on project controls
    for exception in exceptions_statuses:
        for index, id in enumerate(exceptions_status_values):
            id_trim = []
            id_trim.extend(id)
            if exception.review_status == id.review_status:
                excp_matches_count = excp_matches_count + 1
        excp_matches.append(excp_matches_count)
        excp_matches_count = 0

    exceptions_status_data = []
    excp_index = 0
    for exception in exceptions_statuses:
        exceptions_status_data.append({"x": exception.review_status, "y": excp_matches[excp_index]})
        excp_index = excp_index + 1

    # get audit test data
    audit_tests = (
        db.query(
            AuditTest.name.label("name"),
            AuditTest.id.label("id"),
            AuditTest.start_date.label("start_date"),
            AuditTest.end_date.label("end_date"),
            AuditTest.status.label("status"),
        )
        .filter(AuditTest.project_id == project_id)
        .all()
    )
    scheduled_audits_data = []
    for audit in audit_tests:
        if not audit.start_date or not audit.end_date:
            continue  # Skip if start or end date is missing
        scheduled_audits_data.append(
            {
                "x": audit.name,
                "y": [
                    audit.start_date,
                    audit.end_date,
                ],
            }
        )
    incomplete_audit_tests = (
        db.query(
            AuditTest.name.label("name"),
            AuditTest.id.label("id"),
            AuditTest.start_date.label("start_date"),
            AuditTest.end_date.label("end_date"),
            AuditTest.status.label("status"),
        )
        .filter(AuditTest.status != "complete")
        .filter(AuditTest.project_id == project_id)
        .all()
    )

    frameworks = (
        db.query(Framework.name.label("name"), Framework.id.label("id"))
        .select_from(Framework)
        .join(FrameworkVersion, FrameworkVersion.framework_id == Framework.id)
        .join(
            ControlFrameworkVersion,
            ControlFrameworkVersion.framework_version_id == FrameworkVersion.id,
        )
        .join(Control, Control.id == ControlFrameworkVersion.control_id)
        .join(ProjectControl, ProjectControl.control_id == Control.id)
        .filter(ProjectControl.project_id == project_id)
        .distinct()
    )
    frameworkList = []
    for frame in frameworks:
        frameworkList.append({"name": frame[0], "id": frame[1]})

    project_data = {
        "name": project_query.name,
        "id": project_query.id,
        "total_assessments": total_assessments,
        "assessments_complete": assessments_complete,
        "low_risks": low_count,
        "low_medium_risks": low_medium_count,
        "medium_risks": medium_count,
        "medium_high_risks": medium_high_count,
        "high_risks": high_count,
        "num_risks_over_5": num_risks_over_5,
        "controls": project_control_count,
        "audit_tests": audit_test_count,
        "audit_tests_pending": audit_test_pending,
        "audit_tests_completed": audit_test_completed,
        "created_date": project_query.created_date,
        "last_updated": project_query.last_updated_date,
        "project_administrator_id": user_query.id,
        "project_administrator_email": user_query.email,
        "control_status_data": control_status_data,
        "frameworks": frameworkList,
        "exceptions_status_data": exceptions_status_data,
        "scheduled_audits_data": scheduled_audits_data,
        "incomplete_audit_tests": incomplete_audit_tests,
    }
    return project_data
