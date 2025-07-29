import logging
import os

from datetime import date

from sqlalchemy.orm import Session

from fastapi import HTTPException, status


from fedrisk_api.db.models import (
    AuditEvidence,
    AuditEvidenceReview,
    AuditEvidenceReviewProjectControl,
    AuditEvidenceFilterApp,
    AuditEvidenceFilterServiceProvider,
    AuditEvidenceFilterFramework,
    AuditEvidenceFilterProject,
    AuditEvidenceReviewDigSig,
    AuditEvidenceReviewProjContDigSig,
    ProjectControl,
    ProjectControlEvidence,
    DigitalSignature,
    Evidence,
    AppProjectControl,
    AppProject,
    App,
    ServiceProvider,
    User,
    ServiceProviderProjectControl,
    Control,
    FrameworkVersion,
    ControlFrameworkVersion,
    Framework,
)
from fedrisk_api.schema.audit_evidence import (
    CreateAuditEvidence,
    CreateAuditEvidenceReview,
    CreateAuditEvidenceReviewProjectControl,
    CreateAuditEvidenceFilterApp,
    CreateAuditEvidenceFilterFramework,
    CreateAuditEvidenceFilterProject,
    CreateAuditEvidenceFilterServiceProvider,
    CreateAuditEvidenceReviewDigSig,
    CreateAuditEvidenceReviewProjContDigSig,
    UpdateAuditEvidence,
    # DisplayAuditEvidenceReviewProjectControl,
)

from fedrisk_api.utils.email_util import send_auditor_email, send_evidence_rejected_email

LOGGER = logging.getLogger(__name__)

frontend_server_url = os.getenv("FRONTEND_SERVER_URL", "")


############ AuditEvidence ############
async def create_audit_evidence(db: Session, evidence: CreateAuditEvidence, tenant_id: int):
    my_new_evidence_dict = evidence.dict()
    new_evidence = AuditEvidence(**my_new_evidence_dict, tenant_id=tenant_id)
    db.add(new_evidence)
    db.commit()
    # send email to auditor_user_id
    auditor_user = db.query(User).filter(User.id == evidence.auditor_user_id).first()
    try:
        payload = {
            "subject": "You've been assigned as an auditor",
            "email": auditor_user.email,
            "link": f"{frontend_server_url}/audit_evidence/{new_evidence.id}",
        }

        await send_auditor_email(payload)
        LOGGER.info("Successfully sent auditor email")
        return new_evidence

    except Exception as e:
        LOGGER.exception("Unable to send auditor email")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


def update_audit_evidence_by_id(
    evidence: UpdateAuditEvidence,
    db: Session,
    evidence_id: int,
):
    queryset = db.query(AuditEvidence).filter(AuditEvidence.id == evidence_id)

    if not queryset.first():
        return False

    queryset.update(evidence.dict(exclude_unset=True))
    db.commit()
    return True


def get_audit_evidence_by_id(db: Session, audit_evidence_id: int):
    queryset = db.query(AuditEvidence).filter(AuditEvidence.id == audit_evidence_id).first()
    return queryset


async def get_audit_evidence_machine_readable_by_id(db: Session, audit_evidence_id: int):
    audit_evidence = db.query(AuditEvidence).filter(AuditEvidence.id == audit_evidence_id).first()
    if not audit_evidence:
        return {"error": "No matching audit evidence submission found."}

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

    framework_ids = [ff.framework_id for ff in framework_filters]
    project_ids = [pf.project_id for pf in project_filters]

    app = db.query(App).filter_by(id=app_filter.app_id).first()
    provider = db.query(ServiceProvider).filter_by(id=provider_filter.service_provider_id).first()
    submission_user = db.query(User).filter_by(id=audit_evidence.submission_user_id).first()

    audit_evidence_review = (
        db.query(AuditEvidenceReview).filter_by(audit_evidence_id=audit_evidence_id).first()
    )
    audit_evidence_review_dig_sig = None
    aer_dig_sig = None
    if audit_evidence_review:
        audit_evidence_review_dig_sig = (
            db.query(AuditEvidenceReviewDigSig)
            .filter_by(audit_evidence_review_id=audit_evidence_review.id)
            .first()
        )
        if audit_evidence_review_dig_sig:
            aer_dig_sig = (
                db.query(DigitalSignature)
                .filter_by(id=audit_evidence_review_dig_sig.digital_signature_id)
                .first()
            )

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
        db.query(
            ProjectControl, Evidence, Control, AuditEvidenceReviewProjContDigSig, DigitalSignature
        )
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
        .outerjoin(
            AuditEvidenceReviewProjectControl,
            AuditEvidenceReviewProjectControl.evidence_id == Evidence.id,
        )
        .outerjoin(
            AuditEvidenceReviewProjContDigSig,
            AuditEvidenceReviewProjContDigSig.audit_evidence_review_project_control_id
            == AuditEvidenceReviewProjectControl.id,
        )
        .outerjoin(
            DigitalSignature,
            DigitalSignature.id == AuditEvidenceReviewProjContDigSig.digital_signature_id,
        )
        .filter(AppProjectControl.app_id == app.id)
        .filter(ServiceProviderProjectControl.service_provider_id == provider.id)
        .all()
    )

    for pc, ev, control, aepcds, digsig in apc_evidence:
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
                    "digital_signature": digsig.checksum if digsig else None,
                    "signed_on": aepcds.signed_on if aepcds else None,
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
                db.query(
                    ProjectControlEvidence,
                    Evidence,
                    AuditEvidenceReviewProjContDigSig,
                    DigitalSignature,
                )
                .join(Evidence, ProjectControlEvidence.evidence_id == Evidence.id)
                .outerjoin(
                    AuditEvidenceReviewProjectControl,
                    AuditEvidenceReviewProjectControl.evidence_id == Evidence.id,
                )
                .outerjoin(
                    AuditEvidenceReviewProjContDigSig,
                    AuditEvidenceReviewProjContDigSig.audit_evidence_review_project_control_id
                    == AuditEvidenceReviewProjectControl.id,
                )
                .outerjoin(
                    DigitalSignature,
                    DigitalSignature.id == AuditEvidenceReviewProjContDigSig.digital_signature_id,
                )
                .filter(ProjectControlEvidence.project_control_id == pc.id)
                .all()
            )

            for pce, ev, aepcds, digsig in project_control_evidences:
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
                            "digital_signature": digsig.checksum if digsig else None,
                            "signed_on": aepcds.signed_on if aepcds else None,
                        }
                    )
                    seen_keys.add(key)

    return {
        "csp_information": {
            "csp_name": provider.name,
            "app_name": app.name,
            "app_description": app.description,
            "hosting_environment": provider.hosting_environment,
            "submission_date": (
                audit_evidence.submitted_on.date() if audit_evidence.submitted_on else date.today()
            ),
            "contact_email": provider.contact_email,
            "submission_version": audit_evidence.submission_version or "n/a",
        },
        "submission_summary": {
            "rationale": audit_evidence.rationale or "n/a",
            "audit_level": "Low",
            "commercial_audit": audit_evidence.commercial_audit_type or "n/a",
            "commercial_auditor_name": audit_evidence.auditor_name or "n/a",
        },
        "3pao_summary": {
            "organization_name": audit_evidence.external_organization or "n/a",
            "contact_email": submission_user.email or "n/a",
            "3PAO_digital_signature": aer_dig_sig.checksum if aer_dig_sig else "n/a",
            "review_date": (
                audit_evidence_review_dig_sig.signed_on if audit_evidence_review_dig_sig else "n/a"
            ),
            "assessment_summary": (
                audit_evidence_review.assessment_summary if audit_evidence_review else "n/a"
            ),
        },
        "evidence_summary": control_evidence_summary,
        "filters": {
            "projects": project_ids,
            "frameworks": framework_ids,
        },
    }


def get_all_audit_evidence_by_tenant_id(db: Session, tenant_id: int):
    LOGGER.info(tenant_id)
    queryset = db.query(AuditEvidence).filter(AuditEvidence.tenant_id == tenant_id).all()
    return queryset


def delete_audit_evidence_by_id(db: Session, audit_evidence_id: int):
    evidence = db.query(AuditEvidence).filter(AuditEvidence.id == audit_evidence_id).first()

    if not evidence:
        return False

    # delete all AuditEvidenceReview references
    audit_evidence_reviews = (
        db.query(AuditEvidenceReview)
        .filter(AuditEvidenceReview.audit_evidence_id == audit_evidence_id)
        .all()
    )
    for aer in audit_evidence_reviews:
        # delete all AuditEvidenceDigSig references
        db.query(AuditEvidenceReviewDigSig).filter(
            AuditEvidenceReviewDigSig.audit_evidence_review_id == aer.id
        ).delete()
    db.query(AuditEvidenceReview).filter(
        AuditEvidenceReview.audit_evidence_id == audit_evidence_id
    ).delete()
    # delete all AuditEvidenceReviewProjectControl references
    project_controls = db.query(AuditEvidenceReviewProjectControl).filter(
        AuditEvidenceReviewProjectControl.project_control_id == audit_evidence_id
    )
    for pc in project_controls:
        # delete digital signatures assocaited with project control evidence
        db.query(AuditEvidenceReviewProjContDigSig).filter(
            AuditEvidenceReviewProjContDigSig.audit_evidence_review_project_control_id
            == pc.project_control_id
        ).delete()
    project_controls.delete()
    # delete all AuditEvidenceFilterApp references
    db.query(AuditEvidenceFilterApp).filter(
        AuditEvidenceFilterApp.audit_evidence_id == audit_evidence_id
    ).delete()
    # delete all AuditEvidenceFilterServiceProvider references
    db.query(AuditEvidenceFilterServiceProvider).filter(
        AuditEvidenceFilterServiceProvider.audit_evidence_id == audit_evidence_id
    ).delete()
    # delete all AuditEvidenceFilterFramework references
    db.query(AuditEvidenceFilterFramework).filter(
        AuditEvidenceFilterFramework.audit_evidence_id == audit_evidence_id
    ).delete()
    # delete all AuditEvidenceFilterProject references
    db.query(AuditEvidenceFilterProject).filter(
        AuditEvidenceFilterProject.audit_evidence_id == audit_evidence_id
    ).delete()

    db.delete(evidence)
    db.commit()
    return True


############ AuditEvidenceReview ############
async def create_audit_evidence_review(db: Session, evidence: CreateAuditEvidenceReview):
    my_new_evidence_dict = evidence.dict()
    new_evidence = AuditEvidenceReview(**my_new_evidence_dict)
    db.add(new_evidence)
    db.commit()

    if evidence.approved == False:
        try:
            audit_evidence_submitter = (
                db.query(User)
                .join(User, AuditEvidence.submission_user_id == User.id)
                .filter(AuditEvidence.id == evidence.audit_evidence_id)
                .first()
            )
            payload = {
                "subject": "Evidence has been rejected",
                "email": audit_evidence_submitter.email,
                "link": f"{frontend_server_url}/audit_evidence/{new_evidence.id}",
            }

            await send_auditor_email(payload)
            LOGGER.info("Successfully sent auditor email")
            return new_evidence

        except Exception as e:
            LOGGER.exception("Unable to send auditor email")
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return new_evidence


def get_audit_evidence_review_by_id(db: Session, audit_evidence_review_id: int):
    queryset = (
        db.query(AuditEvidenceReview)
        .filter(AuditEvidenceReview.id == audit_evidence_review_id)
        .first()
    )
    return queryset


def delete_audit_evidence_review_by_id(db: Session, audit_evidence_review_id: int):
    evidence = (
        db.query(AuditEvidenceReview)
        .filter(AuditEvidenceReview.id == audit_evidence_review_id)
        .first()
    )

    if not evidence:
        return False

    db.delete(evidence)
    db.commit()
    return True


############ AuditEvidenceReviewProjectControl ############
def create_audit_evidence_review_project_control(
    db: Session, evidence: CreateAuditEvidenceReviewProjectControl
):
    my_new_evidence_dict = evidence.dict()
    new_evidence = AuditEvidenceReviewProjectControl(**my_new_evidence_dict)
    db.add(new_evidence)
    db.commit()
    return new_evidence


def get_audit_evidence_review_project_control_by_id(
    db: Session, audit_evidence_review_project_control_id: int
):
    queryset = (
        db.query(AuditEvidenceReviewProjectControl)
        .filter(AuditEvidenceReviewProjectControl.id == audit_evidence_review_project_control_id)
        .first()
    )
    return queryset


def delete_audit_evidence_review_project_control_by_id(
    db: Session, audit_evidence_review_project_control_id: int
):
    evidence = (
        db.query(AuditEvidenceReviewProjectControl)
        .filter(AuditEvidenceReviewProjectControl.id == audit_evidence_review_project_control_id)
        .first()
    )

    if not evidence:
        return False

    db.delete(evidence)
    db.commit()
    return True


############ AuditEvidenceFilterApp ############
def create_audit_evidence_filter_app(db: Session, evidence: CreateAuditEvidenceFilterApp):
    my_new_evidence_dict = evidence.dict()
    new_evidence = AuditEvidenceFilterApp(**my_new_evidence_dict)
    db.add(new_evidence)
    db.commit()
    return new_evidence


def get_audit_evidence_filter_app_by_id(db: Session, audit_evidence_filter_app_id: int):
    queryset = (
        db.query(AuditEvidenceFilterApp)
        .filter(AuditEvidenceFilterApp.id == audit_evidence_filter_app_id)
        .first()
    )
    return queryset


def delete_audit_evidence_filter_app_by_id(db: Session, audit_evidence_filter_app_id: int):
    evidence = (
        db.query(AuditEvidenceFilterApp)
        .filter(AuditEvidenceFilterApp.id == audit_evidence_filter_app_id)
        .first()
    )

    if not evidence:
        return False

    db.delete(evidence)
    db.commit()
    return True


############ AuditEvidenceFilterServiceProvider ############
def create_audit_evidence_filter_sp(
    db: Session, evidence: CreateAuditEvidenceFilterServiceProvider
):
    my_new_evidence_dict = evidence.dict()
    new_evidence = AuditEvidenceFilterServiceProvider(**my_new_evidence_dict)
    db.add(new_evidence)
    db.commit()
    return new_evidence


def get_audit_evidence_filter_sp_by_id(db: Session, audit_evidence_filter_sp_id: int):
    queryset = (
        db.query(AuditEvidenceFilterServiceProvider)
        .filter(AuditEvidenceFilterServiceProvider.id == audit_evidence_filter_sp_id)
        .first()
    )
    return queryset


def delete_audit_evidence_filter_sp_by_id(db: Session, audit_evidence_filter_sp_id: int):
    evidence = (
        db.query(AuditEvidenceFilterServiceProvider)
        .filter(AuditEvidenceFilterServiceProvider.id == AuditEvidenceFilterServiceProvider)
        .first()
    )

    if not evidence:
        return False

    db.delete(evidence)
    db.commit()
    return True


############ AuditEvidenceFilterFramework ############
def create_audit_evidence_filter_framework(
    db: Session, evidence: CreateAuditEvidenceFilterFramework
):
    my_new_evidence_dict = evidence.dict()
    new_evidence = AuditEvidenceFilterFramework(**my_new_evidence_dict)
    db.add(new_evidence)
    db.commit()
    return new_evidence


def get_audit_evidence_filter_framework_by_id(db: Session, audit_evidence_filter_fr_id: int):
    queryset = (
        db.query(AuditEvidenceFilterFramework)
        .filter(AuditEvidenceFilterFramework.id == audit_evidence_filter_fr_id)
        .first()
    )
    return queryset


def delete_audit_evidence_filter_framework_by_id(db: Session, audit_evidence_filter_fr_id: int):
    evidence = (
        db.query(AuditEvidenceFilterFramework)
        .filter(AuditEvidenceFilterFramework.id == audit_evidence_filter_fr_id)
        .first()
    )

    if not evidence:
        return False

    db.delete(evidence)
    db.commit()
    return True


############ AuditEvidenceFilterProject ############
def create_audit_evidence_filter_project(db: Session, evidence: CreateAuditEvidenceFilterProject):
    my_new_evidence_dict = evidence.dict()
    new_evidence = AuditEvidenceFilterProject(**my_new_evidence_dict)
    db.add(new_evidence)
    db.commit()
    return new_evidence


def get_audit_evidence_filter_project_by_id(db: Session, audit_evidence_filter_pr_id: int):
    queryset = (
        db.query(AuditEvidenceFilterProject)
        .filter(AuditEvidenceFilterProject.id == audit_evidence_filter_pr_id)
        .first()
    )
    return queryset


def delete_audit_evidence_filter_project_by_id(db: Session, audit_evidence_filter_pr_id: int):
    evidence = (
        db.query(AuditEvidenceFilterProject)
        .filter(AuditEvidenceFilterProject.id == audit_evidence_filter_pr_id)
        .first()
    )

    if not evidence:
        return False

    db.delete(evidence)
    db.commit()
    return True


############ AuditEvidenceReviewDigSig ############
def create_audit_evidence_review_dig_sig(db: Session, evidence: CreateAuditEvidenceReviewDigSig):
    my_new_evidence_dict = evidence.dict()
    new_evidence = AuditEvidenceReviewDigSig(**my_new_evidence_dict)
    db.add(new_evidence)
    db.commit()
    return new_evidence


def get_audit_evidence_review_dig_sig_by_id(db: Session, audit_evidence_review_id: int):
    queryset = (
        db.query(AuditEvidenceReviewDigSig)
        .filter(AuditEvidenceReviewDigSig.audit_evidence_review_id == audit_evidence_review_id)
        .first()
    )
    return queryset


def delete_audit_evidence_review_dig_sig_by_id(db: Session, id: int):
    evidence = (
        db.query(AuditEvidenceReviewDigSig).filter(AuditEvidenceReviewDigSig.id == id).first()
    )

    if not evidence:
        return False

    db.delete(evidence)
    db.commit()
    return True


############ AuditEvidenceReviewProjectControlDigSig ############
def create_audit_evidence_review_proj_cont_dig_sig(
    db: Session, evidence: CreateAuditEvidenceReviewProjContDigSig
):
    my_new_evidence_dict = evidence.dict()
    new_evidence = AuditEvidenceReviewProjContDigSig(**my_new_evidence_dict)
    db.add(new_evidence)
    db.commit()
    return new_evidence


def get_audit_evidence_review_proj_cont_dig_sig_by_id(db: Session, project_control_id: int):
    queryset = (
        db.query(AuditEvidenceReviewProjContDigSig)
        .join(
            AuditEvidenceReviewProjectControl,
            AuditEvidenceReviewProjContDigSig.audit_evidence_review_project_control_id
            == AuditEvidenceReviewProjectControl.id,
        )
        .filter(AuditEvidenceReviewProjectControl.project_control_id == project_control_id)
        .first()
    )
    return queryset


def delete_audit_evidence_review_proj_cont_dig_sig_by_id(db: Session, id: int):
    evidence = (
        db.query(AuditEvidenceReviewProjContDigSig)
        .filter(AuditEvidenceReviewProjContDigSig.id == id)
        .first()
    )

    if not evidence:
        return False

    db.delete(evidence)
    db.commit()
    return True
