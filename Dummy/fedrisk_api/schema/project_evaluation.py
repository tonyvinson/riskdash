from datetime import datetime

from pydantic import BaseModel
from typing import Optional, List

from fedrisk_api.db.enums import StatusType

from fedrisk_api.schema.cost import DisplayCost

from fedrisk_api.schema.approval_workflows import DisplayApprovalWorkflow


class CreateProjectEvaluation(BaseModel):
    project_id: str
    name: str
    description: str
    comments: Optional[str]
    status: Optional[StatusType]


class UpdateProjectEvaluation(BaseModel):
    name: Optional[str]
    description: Optional[str]
    comments: Optional[str]
    status: Optional[StatusType]
    cost_ids: Optional[List[int]]


class DisplayProject(BaseModel):
    id: str
    name: str
    description: str

    class Config:
        orm_mode = True


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


class DisplayProjectEvaluationCost(BaseModel):
    project_evaluation_id: int = None
    cost_id: int = None
    cost: DisplayCost = None

    class Config:
        orm_mode = True


class DisplayProjectEvaluationApprovalWorkflow(BaseModel):
    project_evaluation_id: int = None
    approval_workflow_id: int = None
    approval_workflow: DisplayApprovalWorkflow = None

    class Config:
        orm_mode = True


class DisplayProjectEvaluation(BaseModel):
    id: str
    name: str
    description: str
    status: StatusType
    comments: str = None
    keywords: str = None
    tenant_id: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    project: DisplayProject
    documents: List[DisplayDocumentID] = []
    keywords: List[DisplayKeywordID] = []
    costs: List[DisplayProjectEvaluationCost] = []
    approval_workflows: List[DisplayProjectEvaluationApprovalWorkflow] = []

    class Config:
        orm_mode = True
