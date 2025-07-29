from datetime import datetime
from typing import List

from pydantic import BaseModel
from typing import Optional
from fedrisk_api.schema.cost import DisplayCost
from fedrisk_api.schema.approval_workflows import DisplayApprovalWorkflow


class DisplayProjectControl(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayProjectControlID(BaseModel):
    id: str = None
    control: DisplayProjectControl = None

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


class CreateRisk(BaseModel):
    project_id: str
    project_control_id: Optional[str]
    audit_test_id: Optional[str]
    current_likelihood_id: Optional[str]
    risk_score_id: Optional[str]
    risk_category_id: Optional[str]
    risk_impact_id: Optional[str]
    risk_status_id: Optional[str]
    name: str
    description: Optional[str]
    external_reference_id: Optional[str]
    current_impact: Optional[float] = 0.0
    risk_assessment: Optional[str]
    affected_assets: Optional[str]
    technology: Optional[str]
    additional_stakeholder_ids: Optional[List[int]]
    owner_id: Optional[int]
    owner_supervisor: Optional[str]
    comments: Optional[str]
    additional_notes: Optional[str]


class UpdateRisk(BaseModel):
    # A Risk is created for / within a Project
    # The concept of "moving" a risk to a different
    # Project is disallowed . . .
    # project_id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    project_control_id: Optional[str]
    audit_test_id: Optional[str]
    external_reference_id: Optional[str]
    current_impact: Optional[float]
    risk_assessment: Optional[str]
    affected_assets: Optional[str]
    technology: Optional[str]
    owner_id: Optional[str]
    owner_supervisor: Optional[str]
    comments: Optional[str]
    additional_notes: Optional[str]
    additional_stakeholder_ids: Optional[List[int]]
    current_likelihood_id: Optional[str]
    risk_score_id: Optional[str]
    risk_category_id: Optional[str]
    risk_impact_id: Optional[str]
    risk_status_id: Optional[str]
    cost_ids: Optional[List[int]]


class DisplayRiskProject(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayRiskCurrentLikelihood(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayRiskScore(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayRiskImpact(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayRiskCategory(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayRiskMapping(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayRiskStatus(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayRiskControl(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayRiskAuditTest(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayTask(BaseModel):
    id: str
    title: str
    name: str

    class Config:
        orm_mode = True


class DisplayRiskStakeholders(BaseModel):
    id: str
    email: str
    first_name: str = None
    last_name: str = None
    tenant_id: str
    is_superuser: bool
    is_tenant_admin: bool
    is_active: bool

    class Config:
        orm_mode = True


class DisplayRiskOwner(DisplayRiskStakeholders):
    pass


class DisplayDocument(BaseModel):
    id: str
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
    id: str
    document: DisplayDocument

    class Config:
        orm_mode = True


class DisplayRiskCost(BaseModel):
    risk_id: int = None
    cost_id: int = None
    cost: DisplayCost = None

    class Config:
        orm_mode = True


class DisplayRiskApprovalWorkflow(BaseModel):
    risk_id: int = None
    approval_workflow_id: int = None
    approval_workflow: DisplayApprovalWorkflow = None

    class Config:
        orm_mode = True


class DisplayRisk(BaseModel):
    id: str
    name: str
    description: str = None
    tenant_id: str
    external_reference_id: str = None
    current_impact: float = None
    risk_assessment: str = None
    affected_assets: str = None
    technology: str = None
    owner: DisplayRiskOwner = None
    owner_supervisor: str = None
    comments: str = None
    additional_notes: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    project: DisplayRiskProject
    current_likelihood: DisplayRiskCurrentLikelihood = None
    risk_score: DisplayRiskScore = None
    risk_category: DisplayRiskCategory = None
    risk_impact: DisplayRiskImpact = None
    risk_status: DisplayRiskStatus = None
    control: DisplayRiskControl = None
    audit_test: DisplayRiskAuditTest = None
    additional_stakeholders: List[DisplayRiskStakeholders] = None
    tasks: List[DisplayTask] = None
    risk_mapping: str = None
    documents: List[DisplayDocumentID] = None
    keywords: List[DisplayKeywordID] = []
    project_control: DisplayProjectControlID = None
    costs: List[DisplayRiskCost] = []
    approval_workflows: List[DisplayRiskApprovalWorkflow] = []

    class Config:
        orm_mode = True
