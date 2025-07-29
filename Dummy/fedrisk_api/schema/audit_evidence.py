from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict, List

# from fedrisk_api.schema.service_provider import DisplayApp, DisplayServiceProvider

# AuditEvidence and AuditEvidenceFilter Models


############## Audit Evidence Review ##############
class CreateAuditEvidenceReview(BaseModel):
    audit_evidence_id: int = None
    assessment_summary: str = None
    approved: bool = None


class DisplayDigitalSignature(BaseModel):
    id: int
    filename: str = None
    checksum: str = None
    created_date: datetime = None

    class Config:
        orm_mode = True


class DisplayAuditEvidenceReviewDigSig(BaseModel):
    id: int
    audit_evidence_review_id: int
    digital_signature_id: int
    signed_on: datetime
    digital_signature: DisplayDigitalSignature = None

    class Config:
        orm_mode = True


class DisplayAuditEvidenceReview(BaseModel):
    id: int
    audit_evidence_id: int = None
    assessment_summary: str = None
    approved: bool = None
    reviewed_on: datetime = None
    audit_evidence_review_dig_sig: DisplayAuditEvidenceReviewDigSig = None

    class Config:
        orm_mode = True


############## Audit Evidence ##############
class CreateAuditEvidence(BaseModel):
    external_organization: str = None
    rationale: str = None
    commercial_audit_type: str = None
    auditor_user_id: int = None
    submission_user_id: int = None
    submission_version: str = None
    cc_emails: str = None
    auditor_name: str = None


class UpdateAuditEvidence(BaseModel):
    external_organization: str = None
    rationale: str = None
    commercial_audit_type: str = None
    auditor_user_id: int = None
    submission_user_id: int = None
    submission_version: str = None
    cc_emails: str = None
    auditor_name: str = None


class DisplaySimpleObj(BaseModel):
    id: int
    name: str = None

    class Config:
        orm_mode = True


class DisplayAppMap(BaseModel):
    id: int
    app: DisplaySimpleObj = None

    class Config:
        orm_mode = True


class DisplayServiceProviderMap(BaseModel):
    id: int
    service_provider: DisplaySimpleObj = None

    class Config:
        orm_mode = True


class DisplayProjectMap(BaseModel):
    id: int
    project: DisplaySimpleObj = None

    class Config:
        orm_mode = True


class DisplayFrameworkMap(BaseModel):
    id: int
    framework: DisplaySimpleObj = None

    class Config:
        orm_mode = True


class DisplayAuditorUser(BaseModel):
    id: int
    email: str = None

    class Config:
        orm_mode = True


class DisplaySubmittorUser(BaseModel):
    id: int
    email: str = None

    class Config:
        orm_mode = True


class DisplayAuditEvidence(BaseModel):
    id: int
    external_organization: str = None
    rationale: str = None
    commercial_audit_type: str = None
    auditor_user_id: int = None
    submission_user_id: int = None
    auditor_submitter: DisplaySubmittorUser = None
    auditor_user: DisplayAuditorUser = None
    auditor_name: str = None
    submission_version: str = None
    cc_emails: str = None
    submitted_on: datetime = None
    audit_evidence_app: List[DisplayAppMap] = []
    audit_evidence_service_provider: List[DisplayServiceProviderMap] = []
    audit_evidence_project: List[DisplayProjectMap] = []
    audit_evidence_framework: List[DisplayFrameworkMap] = []
    audit_evidence_review: DisplayAuditEvidenceReview = None

    class Config:
        orm_mode = True


############## Audit Evidence Review Project Control ##############
class CreateAuditEvidenceReviewProjectControl(BaseModel):
    audit_evidence_id: int = None
    project_control_id: int = None
    evidence_id: int = None
    assessment_summary: str = None
    approved: bool = None


class DisplayAuditEvidenceReviewProjectControl(BaseModel):
    id: int
    audit_evidence_id: int = None
    project_control_id: int = None
    evidence_id: int = None
    assessment_summary: str = None
    approved: bool = None
    reviewed_on: datetime = None

    class Config:
        orm_mode = True


############## Audit Evidence Filter App ##############
class CreateAuditEvidenceFilterApp(BaseModel):
    audit_evidence_id: int = None
    app_id: int = None


class DisplayAuditEvidenceFilterApp(BaseModel):
    id: int
    audit_evidence_id: int = None
    app_id: int = None

    class Config:
        orm_mode = True


############## Audit Evidence Filter Service Provider ##############
class CreateAuditEvidenceFilterServiceProvider(BaseModel):
    audit_evidence_id: int = None
    service_provider_id: int = None


class DisplayAuditEvidenceFilterServiceProvider(BaseModel):
    id: int
    audit_evidence_id: int = None
    service_provider_id: int = None

    class Config:
        orm_mode = True


############## Audit Evidence Filter Project ##############
class CreateAuditEvidenceFilterProject(BaseModel):
    audit_evidence_id: int = None
    project_id: int = None


class DisplayAuditEvidenceFilterProject(BaseModel):
    id: int
    audit_evidence_id: int = None
    project_id: int = None

    class Config:
        orm_mode = True


############## Audit Evidence Filter Framework ##############
class CreateAuditEvidenceFilterFramework(BaseModel):
    audit_evidence_id: int = None
    framework_id: int = None


class DisplayAuditEvidenceFilterFramework(BaseModel):
    id: int
    audit_evidence_id: int = None
    framework_id: int = None

    class Config:
        orm_mode = True


############## Audit Evidence Review Digital Signature ##############
class CreateAuditEvidenceReviewDigSig(BaseModel):
    audit_evidence_review_id: int = None
    digital_signature_id: int = None


############## Audit Evidence Review Project Control Digital Signature ##############
class CreateAuditEvidenceReviewProjContDigSig(BaseModel):
    audit_evidence_review_project_control_id: int = None
    digital_signature_id: int = None


class DisplayAuditEvidenceReviewProjContDigSig(BaseModel):
    id: int
    audit_evidence_review_project_control_id: int = None
    digital_signature_id: int = None
    signed_on: datetime = None

    class Config:
        orm_mode = True
