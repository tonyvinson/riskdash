from datetime import datetime, date

from pydantic import BaseModel
from typing import Optional, List

from fedrisk_api.db.enums import IsAssessmentConfirmed, StatusType, AssessmentInstanceStatus

from fedrisk_api.schema.cost import DisplayCost

from fedrisk_api.schema.approval_workflows import DisplayApprovalWorkflow


class CreateAssessment(BaseModel):
    project_control_id: str
    name: str
    description: str
    comments: Optional[str]
    is_assessment_confirmed: Optional[IsAssessmentConfirmed]
    start_date: Optional[date]
    end_date: Optional[date]
    test_frequency: Optional[str]


class UpdateAssessment(BaseModel):
    name: Optional[str]
    description: Optional[str]
    comments: Optional[str]
    status: Optional[StatusType]
    is_assessment_confirmed: Optional[IsAssessmentConfirmed]
    cost_ids: Optional[List[int]]
    start_date: Optional[date]
    end_date: Optional[date]
    test_frequency: Optional[str]


class CreateAssessmentInstance(BaseModel):
    assessment_id: str
    review_status: Optional[AssessmentInstanceStatus]
    comments: Optional[str]


class UpdateAssessmentInstance(BaseModel):
    assessment_id: Optional[str]
    review_status: Optional[AssessmentInstanceStatus]
    comments: Optional[str]


class DisplayAssessmentControlFrameworkVersionFramework(BaseModel):
    id: str
    name: str
    description: str
    # keywords: str = None

    class Config:
        orm_mode = True


class DisplayAssessmentControlFrameworkVersion(BaseModel):
    id: str
    framework: DisplayAssessmentControlFrameworkVersionFramework = None

    class Config:
        orm_mode = True


class DisplayAssessmentControl(BaseModel):
    id: str
    name: str
    description: str
    created_date: datetime = None
    last_updated_date: datetime = None
    framework_versions: List[DisplayAssessmentControlFrameworkVersion] = []

    class Config:
        orm_mode = True


class DisplayProject(BaseModel):
    id: str
    name: str
    description: str

    class Config:
        orm_mode = True


class DisplayDocument(BaseModel):
    id: str = None
    name: str = None
    title: str = None
    description: str = None
    # fedrisk_object_type: str = None
    # fedrisk_object_id: int = None
    # fedrisk_object_object: FedriskObjectType = None
    # created_date: datetime = None
    # last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayDocumentID(BaseModel):
    id: str = None
    document: DisplayDocument = None

    class Config:
        orm_mode = True


class DisplayControlObj(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayProjectControl(BaseModel):
    id: str
    project: DisplayControlObj = None
    control: DisplayControlObj = None
    control_family: DisplayControlObj = None
    control_phase: DisplayControlObj = None
    control_status: DisplayControlObj = None
    control_class: DisplayControlObj = None
    mitigation_percentage: str = None

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


class DisplayAssessmentCost(BaseModel):
    assessment_id: int = None
    cost_id: int = None
    cost: DisplayCost = None

    class Config:
        orm_mode = True


class DisplayAssessmentInstanceTest(BaseModel):
    id: str

    class Config:
        orm_mode = True


class DisplayAssessmentInstance(BaseModel):
    id: int = None
    assessment_id: str = None
    review_status: Optional[AssessmentInstanceStatus]
    assessment: DisplayAssessmentInstanceTest = None
    comments: str = None

    class Config:
        orm_mode = True


class DisplayAssessmentApprovalWorkflow(BaseModel):
    assessment_id: int = None
    approval_workflow_id: int = None
    approval_workflow: DisplayApprovalWorkflow = None

    class Config:
        orm_mode = True


class DisplayAssessment(BaseModel):
    id: str = None
    name: str = None
    status: StatusType = None
    description: str = None
    comments: str = None
    keywords: str = None
    tenant_id: str = None
    project_control_id: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    start_date: date = None
    end_date: date = None
    is_assessment_confirmed: IsAssessmentConfirmed = None
    project_control: DisplayProjectControl = None
    documents: List[DisplayDocumentID] = []
    keywords: List[DisplayKeywordID] = []
    costs: List[DisplayAssessmentCost] = []
    instances: List[DisplayAssessmentInstance] = None
    test_frequency: str = None
    approval_workflows: List[DisplayAssessmentApprovalWorkflow] = []

    class Config:
        orm_mode = True
