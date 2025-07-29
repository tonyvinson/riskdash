from datetime import datetime

from pydantic import BaseModel, validator
from typing import Optional, List
from fedrisk_api.schema.assessment import DisplayAssessment
from fedrisk_api.schema.audit_test import DisplayAuditTest
from fedrisk_api.schema.project import DisplayProject, DisplayProjectControl
from fedrisk_api.schema.control import DisplayControl
from fedrisk_api.schema.project_evaluation import DisplayProjectEvaluation
from fedrisk_api.schema.exception import DisplayException
from fedrisk_api.schema.framework import DisplayFramework
from fedrisk_api.schema.framework_version import DisplayFrameworkVersion
from fedrisk_api.schema.risk import DisplayRisk
from fedrisk_api.schema.task import DisplayTask
from fedrisk_api.schema.wbs import DisplayWBS
from fedrisk_api.s3 import S3Service

from fedrisk_api.schema.approval_workflows import DisplayApprovalWorkflow


class CreateDocument(BaseModel):
    name: str
    description: str
    project_id: Optional[str]
    title: str
    fedrisk_object_type: Optional[str]
    fedrisk_object_id: Optional[str]
    owner_id: str
    version: Optional[str]


class UpdateDocument(BaseModel):
    # id: int
    name: Optional[str]
    description: Optional[str]
    title: Optional[str]
    fedrisk_object_type: Optional[str]
    fedrisk_object_id: Optional[int]
    owner_id: Optional[str]
    version: Optional[str]


class DisplayObj(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayMappingProject(BaseModel):
    id: str = None
    project: DisplayProject = None

    class Config:
        orm_mode = True


class DisplayMappingAssessment(BaseModel):
    id: str = None
    asssessment: DisplayAssessment = None

    class Config:
        orm_mode = True


class DisplayMappingControl(BaseModel):
    id: str = None
    control: DisplayControl = None

    class Config:
        orm_mode = True


class DisplayMappingException(BaseModel):
    id: str = None
    exception: DisplayException = None

    class Config:
        orm_mode = True


class DisplayMappingAuditTest(BaseModel):
    id: str = None
    audit_test: DisplayAuditTest = None

    class Config:
        orm_mode = True


class DisplayMappingRisk(BaseModel):
    id: str = None
    risk: DisplayRisk = None

    class Config:
        orm_mode = True


class DisplayMappingTask(BaseModel):
    id: str = None
    task: DisplayTask = None

    class Config:
        orm_mode = True


class DisplayMappingWBS(BaseModel):
    id: str = None
    wbs: DisplayWBS = None

    class Config:
        orm_mode = True


class DisplayMappingProjectEvaluation(BaseModel):
    id: str = None
    project_evaluation: DisplayProjectEvaluation = None

    class Config:
        orm_mode = True


class DisplayMappingProjectControl(BaseModel):
    id: str = None
    project_control: DisplayProjectControl = None

    class Config:
        orm_mode = True


class DisplayMappingFramework(BaseModel):
    id: str = None
    framework: DisplayFramework = None

    class Config:
        orm_mode = True


class DisplayMappingFrameworkVersion(BaseModel):
    id: str = None
    framework_version: DisplayFrameworkVersion = None

    class Config:
        orm_mode = True


class DisplayKeyword(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayKeywordID(BaseModel):
    id: str = None
    keyword: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayOwner(BaseModel):
    id: str
    email: str
    first_name: str = None
    last_name: str = None

    class Config:
        orm_mode = True


class DisplayTenant(BaseModel):
    id: str
    name: str
    is_active: bool
    s3_bucket: str

    class Config:
        orm_mode = True


class DisplayDocumentApprovalWorkflow(BaseModel):
    document_id: int = None
    approval_workflow_id: int = None
    approval_workflow: DisplayApprovalWorkflow = None

    class Config:
        orm_mode = True


class DisplayDocument(BaseModel):
    id: str
    name: str
    description: str
    tenant_id: str = None
    tenant: DisplayTenant
    file_content_type: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    projects: List[DisplayMappingProject] = []
    assessments: List[DisplayMappingAssessment] = []
    audit_tests: List[DisplayMappingAuditTest] = []
    controls: List[DisplayMappingControl] = []
    exceptions: List[DisplayMappingException] = []
    risks: List[DisplayMappingRisk] = []
    tasks: List[DisplayMappingTask] = []
    wbs: List[DisplayMappingWBS] = []
    project_evaluations: List[DisplayMappingProjectEvaluation] = []
    project_controls: List[DisplayMappingProjectControl] = []
    frameworks: List[DisplayMappingFramework] = []
    framework_versions: List[DisplayMappingFrameworkVersion] = []
    keywords: List[DisplayKeywordID] = []
    title: str = None
    fedrisk_object_type: str = None
    fedrisk_object_id: int = None
    owner_id: str = None
    owner: DisplayOwner = None
    version: str = None
    project_id: int = None
    document_tags: Optional[str] = None
    approval_workflows: List[DisplayDocumentApprovalWorkflow] = []

    class Config:
        orm_mode = True

    @validator("document_tags", pre=True, always=True)
    def document_scan_results(cls, value, values):
        try:
            s3_service = S3Service()
            doc_file_key = values.get("name")
            doc_id = values.get("id")
            tenant = values.get("tenant")
            file_key = f"documents/{doc_id}-{doc_file_key}"
            print(f"🔎 Checking S3 key: {file_key} in bucket: {tenant.s3_bucket}")

            response = s3_service.get_object_tags(tenant.s3_bucket, file_key)
            tag_set = response.get("TagSet", [])
            if tag_set:
                value = tag_set[0].get("Value", "Not Scanned")
            else:
                value = "Not Scanned"
        except Exception as e:
            print(f"🛑 Failed to get S3 object tags: {e}")
            value = "Not Scanned"

        return value
