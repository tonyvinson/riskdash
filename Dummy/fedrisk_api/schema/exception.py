from datetime import date, datetime
from typing import List

from pydantic import BaseModel
from typing import Optional

from fedrisk_api.db.enums import (
    ExceptionReviewStatus,
    IsAssessmentConfirmed,
    ReviewFrequency,
    StatusType,
)

from fedrisk_api.schema.cost import DisplayCost

from fedrisk_api.schema.approval_workflows import DisplayApprovalWorkflow


class CreateException(BaseModel):
    project_control_id: str
    description: str = None
    justification: str = None
    start_date: date = None
    end_date: date = None
    next_review_date: date = None
    owner_id: int = None
    stakeholder_ids: Optional[List[int]] = []
    review_frequency: ReviewFrequency = None

    class Config:
        orm_mode = True


class UpdateException(BaseModel):
    description: Optional[str]
    justification: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    next_review_date: Optional[date]
    review_frequency: Optional[ReviewFrequency]
    stakeholder_ids: Optional[List[int]]
    owner_id: Optional[int]
    cost_ids: Optional[List[int]]

    class Config:
        orm_mode = True


class CreateExceptionReview(BaseModel):
    comments: str = None
    review_status: ExceptionReviewStatus = None
    exception_id: int = None

    class Config:
        orm_mode = True


class UpdateExceptionReview(BaseModel):
    comments: str = None
    review_status: ExceptionReviewStatus = None
    exception_id: int = None

    class Config:
        orm_mode = True


class DisplayProjectControlFramework(BaseModel):
    id: str
    name: str
    description: str

    class Config:
        orm_mode = True


class DisplayProjectControlFrameworkVersion(BaseModel):
    id: str
    version_prefix: str = None
    version_suffix: str = None
    framework: DisplayProjectControlFramework = None

    class Config:
        orm_mode = True


class DisplayProjectControlControl(BaseModel):
    id: str
    name: str
    description: str
    framework_versions: Optional[List[DisplayProjectControlFrameworkVersion]]

    class Config:
        orm_mode = True


class DisplayProjectControlAssessment(BaseModel):
    id: str
    name: str
    status: StatusType
    description: str
    comments: str = None
    is_assessment_confirmed: IsAssessmentConfirmed

    class Config:
        orm_mode = True


class DisplayProjectControlException(BaseModel):
    id: str
    name: str
    justification: str

    class Config:
        orm_mode = True


class DisplayProject(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayProjectControl(BaseModel):
    id: str
    control: DisplayProjectControlControl
    assessment: DisplayProjectControlAssessment = None
    mitigation_percentage: str = None
    control_family_id: str = None
    control_phase_id: str = None
    control_status_id: str = None
    control_class_id: str = None
    project: DisplayProject

    class Config:
        orm_mode = True


class DisplayUser(BaseModel):
    id: str
    email: str
    tenant_id: str
    is_superuser: bool
    is_tenant_admin: bool
    is_active: bool

    class Config:
        orm_mode = True


class DisplayDocument(BaseModel):
    id: str
    name: str = None
    title: str = None
    description: str = None

    class Config:
        orm_mode = True


class DisplayDocumentID(BaseModel):
    id: str
    document: DisplayDocument

    class Config:
        orm_mode = True


class DisplayExceptionShort(BaseModel):
    id: str
    name: str = None
    project_control_id: int = None

    class Config:
        orm_mode = True


class DisplayExceptionReview(BaseModel):
    id: str
    comments: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    review_status: ExceptionReviewStatus = None
    exception_id: int = None
    exception: DisplayExceptionShort = None

    class Config:
        orm_mode = True


class DisplayKeyword(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayKeywordID(BaseModel):
    id: str = None
    keyword: DisplayKeyword = None

    class Config:
        orm_mode = True


class DisplayExceptionCost(BaseModel):
    exception_id: int = None
    cost_id: int = None
    cost: DisplayCost = None

    class Config:
        orm_mode = True


class DisplayExceptionApprovalWorkflow(BaseModel):
    exception_id: int = None
    approval_workflow_id: int = None
    approval_workflow: DisplayApprovalWorkflow = None

    class Config:
        orm_mode = True


class DisplayException(BaseModel):
    id: str = None
    name: str = None
    description: str = None
    justification: str = None
    next_review_date: date = None
    review_frequency: ReviewFrequency = None
    tenant_id: str = None
    start_date: date = None
    end_date: date = None
    created_date: datetime = None
    last_updated_date: datetime = None
    project_control_id: str = None
    project_control: DisplayProjectControl = None
    owner: DisplayUser = None
    stakeholders: List[DisplayUser] = []
    documents: List[DisplayDocumentID] = []
    keywords: List[DisplayKeywordID] = []
    reviews: List[DisplayExceptionReview] = None
    costs: List[DisplayExceptionCost] = []
    approval_workflows: List[DisplayExceptionApprovalWorkflow] = []

    class Config:
        orm_mode = True
