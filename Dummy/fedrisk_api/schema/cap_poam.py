from datetime import date, datetime
from typing import List

from pydantic import BaseModel
from typing import Optional

from fedrisk_api.db.models import CapPoamStatus, Criticality  # ProjectControl
from fedrisk_api.schema.cost import DisplayCost

from fedrisk_api.schema.approval_workflows import DisplayApprovalWorkflow


class CreateCapPoam(BaseModel):
    user_defined_id: Optional[str]
    name: str
    project_id: str
    audit_test_id: Optional[str]
    description: Optional[str]
    comments: Optional[str]
    owner_id: Optional[str]
    stakeholder_ids: Optional[List[int]]
    project_control_ids: Optional[List[int]]
    task_ids: Optional[List[int]]
    status: Optional[CapPoamStatus]
    due_date: Optional[date]
    criticality_rating: Optional[Criticality]


class UpdateCapPoam(BaseModel):
    user_defined_id: Optional[str]
    name: Optional[str]
    project_id: Optional[str]
    audit_test_id: Optional[str]
    description: Optional[str]
    comments: Optional[str]
    owner_id: Optional[str]
    stakeholder_ids: Optional[List[int]]
    project_control_ids: Optional[List[int]]
    task_ids: Optional[List[int]]
    status: Optional[CapPoamStatus]
    due_date: Optional[date]
    criticality_rating: Optional[Criticality]
    cost_ids: Optional[List[int]]


class DisplayOwner(BaseModel):
    id: str
    email: str
    tenant_id: str
    is_superuser: bool
    is_tenant_admin: bool
    is_active: bool

    class Config:
        orm_mode = True


class DisplayStakeholder(BaseModel):
    id: str
    email: str
    tenant_id: str
    is_superuser: bool
    is_tenant_admin: bool
    is_active: bool

    class Config:
        orm_mode = True


class DisplayProjectControlControl(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayAuditTest(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayProject(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayProjectControlProjectControl(BaseModel):
    id: str
    mitigation_percentage: str
    control: DisplayProjectControlControl

    class Config:
        orm_mode = True


class DisplayRelatedTask(BaseModel):
    id: str
    name: str
    description: str = None
    actual_start_date: date = None
    actual_end_date: date = None
    priority: str = None
    due_date: date = None
    assigned_to: str = None
    task_status_id: int = None
    task_category_id: int = None
    percent_complete: int = None
    milestone: bool = None
    estimated_loe: str = None
    actual_loe: str = None
    estimated_cost: float = None
    actual_cost: float = None

    class Config:
        orm_mode = True


class DisplayProjectControl(BaseModel):
    id: str
    project_control: DisplayProjectControlProjectControl

    class Config:
        orm_mode = True


class DisplayTask(BaseModel):
    id: str
    task: DisplayRelatedTask

    class Config:
        orm_mode = True


class DisplayCapPoamCost(BaseModel):
    cap_poam_id: int = None
    cost_id: int = None
    cost: DisplayCost = None

    class Config:
        orm_mode = True


class DisplayCapPoamApprovalWorkflow(BaseModel):
    cap_poam_id: int = None
    approval_workflow_id: int = None
    approval_workflow: DisplayApprovalWorkflow = None

    class Config:
        orm_mode = True


class DisplayCapPoam(BaseModel):
    id: str = None
    project_id: str = None
    audit_test_id: str = None
    owner_id: str = None
    name: str = None
    description: str = None
    comments: str = None
    user_defined_id: str = None
    due_date: date = None
    owner: DisplayOwner = None
    audit_test: DisplayAuditTest = None
    project: DisplayProject = None
    stakeholders: List[DisplayStakeholder] = []
    status: CapPoamStatus = None
    criticality_rating: Criticality = None
    project_controls: List[DisplayProjectControl] = []
    tasks: List[DisplayTask] = []
    created_date: datetime
    costs: List[DisplayCapPoamCost] = []
    approval_workflows: List[DisplayCapPoamApprovalWorkflow] = []

    class Config:
        orm_mode = True
