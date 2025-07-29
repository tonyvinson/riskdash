import logging

from datetime import date

from sqlalchemy.orm import Session, joinedload

from fastapi import HTTPException

from sqlalchemy import func

from fedrisk_api.db.models import (
    Evidence,
    ProjectControlEvidence,
    ProjectControl,
    Project,
    Tenant,
    App,
    ServiceProvider,
    ServiceProviderApp,
    AppProject,
    AppProjectControl,
    AuditEvidence,
    AuditEvidenceFilterApp,
    AuditEvidenceFilterServiceProvider,
    AuditEvidenceFilterFramework,
    AuditEvidenceFilterProject,
    AuditEvidenceReviewProjectControl,
    AuditEvidenceReviewProjContDigSig,
    User,
    ServiceProviderProjectControl,
    Control,
    ControlFrameworkVersion,
    Framework,
    FrameworkVersion,
)
from fedrisk_api.schema.evidence import (
    CreateEvidence,
    UpdateEvidence,
    CreateProjectControlEvidence,
    CheckProjectControlOwner,
)


LOGGER = logging.getLogger(__name__)


# evidence
def create_evidence(db: Session, evidence: CreateEvidence):
    my_new_evidence_dict = evidence.dict()
    new_evidence = Evidence(**my_new_evidence_dict)
    db.add(new_evidence)
    db.commit()
    return new_evidence


def get_all_evidence_by_project_control_id(
    db: Session,
    project_control_id: int,
):
    evidence = (
        db.query(Evidence)
        .join(ProjectControlEvidence, Evidence.id == ProjectControlEvidence.evidence_id)
        .filter(ProjectControlEvidence.project_control_id == project_control_id)
        .all()
    )

    return evidence


def get_evidence_by_id(db: Session, evidence_id: int):
    queryset = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    return queryset


def update_evidence_by_id(
    evidence: UpdateEvidence,
    db: Session,
    evidence_id: int,
):
    queryset = db.query(Evidence).filter(Evidence.id == evidence_id)

    if not queryset.first():
        return False

    queryset.update(evidence.dict(exclude_unset=True))
    db.commit()
    return True


def delete_evidence_by_id(db: Session, evidence_id: int):
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()

    if not evidence:
        return False
    # delete all ProjectControlEvidence references
    db.query(ProjectControlEvidence).filter(
        ProjectControlEvidence.evidence_id == evidence_id
    ).delete()
    db.delete(evidence)
    db.commit()
    return True


def create_project_control_evidence(db: Session, pc_evidence: CreateProjectControlEvidence):
    my_new_pc_evidence_dict = pc_evidence.dict()
    new_pc_evidence = ProjectControlEvidence(**my_new_pc_evidence_dict)
    db.add(new_pc_evidence)
    db.commit()
    return new_pc_evidence


def check_project_control_owner(check: CheckProjectControlOwner, db: Session):
    project_control = (
        db.query(ProjectControl)
        .join(Project, Project.id == ProjectControl.project_id)
        .join(Tenant, Project.tenant_id == Tenant.id)
        .filter(Tenant.webhook_api_key == check.webhook_api_key)
        .filter(ProjectControl.id == int(check.project_control_id))
    )
    if project_control.first() is not None:
        return True
    else:
        return False


async def get_evidence_by_project_id(db: Session, project_id: int):
    project = db.query(Project).filter(Project.id == project_id).first()
    tenant = db.query(Tenant).filter(Tenant.id == project.tenant_id).first()

    return {
        "csp_information": {
            "csp_name": tenant.name,
            "app_name": project.name,
            "app_description": project.description,
            "hosting_environment": "",
            "submission_date": "",
            "contact_email": "",
            "submission_version": "",
        },
        "submission_summary": {
            "rationale": "FedRAMP 20X Phase One Pilot submission based on RFC-0006",
            "audit_level": "Low",
            "commercial_audit": "SOC 2 Type 2",
            "commercial_auditor_name": "Crowe LLP",
        },
        "3pao_summary": {
            "organization_name": "Excentium LLC",
            "contact_email": "user@excentium.com",
            "3PAO_digital_signature": "96b26f6cc52edd91cd52ac5baa1a802f4ff04daab07a308f0b2e897cc807e4bb",
            "review_date": "06-03-2025",
            "assessment_summary": "The 3PAO assessed Riskuity's compliance with the FedRamp20X Key Security Indicators, reviewed evidence, and continuous monitoring techniques.  The 3PAO determined Riskuity is compliant with FedRAMP Low 20x Phase One pilot Key Security Indicator requirements.",
        },
    }


async def get_evidence_by_app_id(db: Session, app_id: int):
    # Step 1: Fetch all service providers linked to this app
    app_service_providers = (
        db.query(App, ServiceProvider)
        .join(ServiceProviderApp, ServiceProviderApp.app_id == App.id)
        .join(ServiceProvider, ServiceProvider.id == ServiceProviderApp.service_provider_id)
        .filter(App.id == app_id)
        .all()
    )

    if not app_service_providers:
        return {"error": "No matching app/service provider found."}

    # Use first app-service_provider tuple for metadata (you could aggregate if needed)
    app, provider = app_service_providers[0]

    # Step 2: Get all project control evidence associated with this app
    project_controls = (
        db.query(ProjectControl, Evidence)
        .join(
            ProjectControlEvidence, ProjectControl.id == ProjectControlEvidence.project_control_id
        )
        .join(Evidence, ProjectControlEvidence.evidence_id == Evidence.id)
        .join(AppProjectControl, AppProjectControl.project_control_id == ProjectControl.id)
        .filter(AppProjectControl.app_id == app_id)
        .all()
    )

    control_evidence_summary = []
    for pc, ev in project_controls:
        control_evidence_summary.append(
            {
                "project_control_id": pc.id,
                # "control_name": pc.control.name if pc.control else None,
                "evidence_id": ev.id,
                "evidence_name": ev.name,
                "evidence_description": ev.description,
                "machine_readable": ev.machine_readable,
            }
        )

    return {
        "csp_information": {
            "csp_name": provider.name,
            "app_name": app.name,
            "app_description": app.description,
            "hosting_environment": provider.hosting_environment,
            "submission_date": date.today(),
            "contact_email": provider.contact_email,
            "submission_version": "1.0",
        },
        "submission_summary": {
            "rationale": "FedRAMP 20X Phase One Pilot submission based on RFC-0006",
            "audit_level": "Low",
            "commercial_audit": "SOC 2 Type 2",
            "commercial_auditor_name": "Crowe LLP",
        },
        "3pao_summary": {
            "organization_name": "Excentium LLC",
            "contact_email": "user@excentium.com",
            "3PAO_digital_signature": "96b26f6cc52edd91cd52ac5baa1a802f4ff04daab07a308f0b2e897cc807e4bb",
            "review_date": "06-03-2025",
            "assessment_summary": (
                "The 3PAO assessed Riskuity's compliance with the FedRamp20X Key Security Indicators, "
                "reviewed evidence, and continuous monitoring techniques. "
                "The 3PAO determined Riskuity is compliant with FedRAMP Low 20x Phase One pilot Key Security Indicator requirements."
            ),
        },
        "evidence_summary": control_evidence_summary,
    }


async def get_evidence_by_audit_evidence_id(db: Session, audit_evidence_id: int):
    audit_evidence = (
        db.query(AuditEvidence)
        .options(
            joinedload(AuditEvidence.auditor_user),
            joinedload(AuditEvidence.auditor_submitter),
        )
        .filter(AuditEvidence.id == audit_evidence_id)
        .first()
    )

    if not audit_evidence:
        raise HTTPException(status_code=404, detail="Audit evidence not found.")

    # Filters
    app_filter = (
        db.query(AuditEvidenceFilterApp).filter_by(audit_evidence_id=audit_evidence_id).first()
    )
    provider_filter = (
        db.query(AuditEvidenceFilterServiceProvider)
        .filter_by(audit_evidence_id=audit_evidence_id)
        .first()
    )
    framework_filters = (
        db.query(AuditEvidenceFilterFramework).filter_by(audit_evidence_id=audit_evidence_id).all()
    )
    project_filters = (
        db.query(AuditEvidenceFilterProject).filter_by(audit_evidence_id=audit_evidence_id).all()
    )

    if not app_filter or not provider_filter:
        return {
            "error": "Audit evidence must have at least one associated app and service provider."
        }

    app = db.query(App).filter_by(id=app_filter.app_id).first()
    provider = db.query(ServiceProvider).filter_by(id=provider_filter.service_provider_id).first()

    if not app or not provider:
        return {"error": "App or Service Provider data is incomplete."}

    framework_ids = [f.framework_id for f in framework_filters]
    project_ids = [p.project_id for p in project_filters]

    # Preload review map by (project_control_id, evidence_id)
    reviews = (
        db.query(AuditEvidenceReviewProjectControl)
        .filter(AuditEvidenceReviewProjectControl.audit_evidence_id == audit_evidence_id)
        .all()
    )
    review_map = {(r.project_control_id, r.evidence_id): r for r in reviews}

    # Main evidence list
    control_evidence_summary = []
    seen_keys = set()

    # Step 1: ProjectControl evidence via AppProjectControl + ServiceProviderProjectControl
    apc_evidence = (
        db.query(ProjectControl, Evidence, Control)
        .join(
            ProjectControlEvidence, ProjectControl.id == ProjectControlEvidence.project_control_id
        )
        .join(Evidence, ProjectControlEvidence.evidence_id == Evidence.id)
        .join(AppProjectControl, AppProjectControl.project_control_id == ProjectControl.id)
        .join(
            ServiceProviderProjectControl,
            ServiceProviderProjectControl.project_control_id == ProjectControl.id,
        )
        .join(Control, Control.id == ProjectControl.control_id)
        .filter(AppProjectControl.app_id == app.id)
        .filter(ServiceProviderProjectControl.service_provider_id == provider.id)
        .all()
    )

    for pc, ev, control in apc_evidence:
        key = (pc.id, ev.id)
        if key not in seen_keys:
            review = review_map.get(key)
            control_evidence_summary.append(
                {
                    "project_id": pc.project_id,
                    "control_name": control.name,
                    "project_control_id": pc.id,
                    "evidence_id": ev.id,
                    "evidence_name": ev.name,
                    "evidence_description": ev.description,
                    "machine_readable": ev.machine_readable,
                    "assessment_summary": review.assessment_summary if review else "Not found",
                    "approver": audit_evidence.auditor_user_id,
                    "approved": review.approved if review else None,
                    "reviewed_on": (
                        review.reviewed_on.isoformat() if review and review.reviewed_on else None
                    ),
                }
            )
            seen_keys.add(key)

    # Step 2: ProjectControl evidence via AppProject → Project
    app_projects = db.query(AppProject).filter(AppProject.app_id == app.id).all()

    for ap in app_projects:
        query = (
            db.query(ProjectControl, Control)
            .join(Control, Control.id == ProjectControl.control_id)
            .join(ControlFrameworkVersion, ControlFrameworkVersion.control_id == Control.id)
            .join(
                FrameworkVersion,
                FrameworkVersion.id == ControlFrameworkVersion.framework_version_id,
            )
            .join(Framework, FrameworkVersion.framework_id == Framework.id)
            .filter(ProjectControl.project_id == ap.project_id)
        )

        if project_ids:
            query = query.filter(ProjectControl.project_id.in_(project_ids))
        if framework_ids:
            query = query.filter(Framework.id.in_(framework_ids))

        project_controls = query.all()

        for pc, control in project_controls:
            project_control_evidences = (
                db.query(ProjectControlEvidence, Evidence)
                .join(Evidence, ProjectControlEvidence.evidence_id == Evidence.id)
                .filter(ProjectControlEvidence.project_control_id == pc.id)
                .all()
            )

            for pce, ev in project_control_evidences:
                key = (pc.id, ev.id)
                if key not in seen_keys:
                    review = review_map.get(key)
                    control_evidence_summary.append(
                        {
                            "project_id": pc.project_id,
                            "control_name": control.name,
                            "project_control_id": pc.id,
                            "evidence_id": ev.id,
                            "evidence_name": ev.name,
                            "evidence_description": ev.description,
                            "machine_readable": ev.machine_readable,
                            "assessment_summary": (
                                review.assessment_summary if review else "Not found"
                            ),
                            "approver": audit_evidence.auditor_user_id,
                            "approved": review.approved if review else None,
                            "reviewed_on": (
                                review.reviewed_on.isoformat()
                                if review and review.reviewed_on
                                else None
                            ),
                        }
                    )
                    seen_keys.add(key)

    return control_evidence_summary
