from datetime import date, datetime
from typing import List

from pydantic import BaseModel
from typing import Optional

from fedrisk_api.db.models import AuditTestStatus, TestFrequency

from fedrisk_api.schema.cost import DisplayCost
from fedrisk_api.schema.approval_workflows import DisplayApprovalWorkflow


class CreateAuditTest(BaseModel):
    project_id: str
    name: str
    description: Optional[str]
    project_control_id: Optional[str]
    tester_id: Optional[str]
    stakeholder_ids: Optional[List[int]]
    test_frequency: Optional[TestFrequency]
    last_test_date: Optional[date]
    external_reference_id: Optional[str]
    objective: Optional[str]
    approximate_days_to_complete: Optional[int]
    expected_results: Optional[str]
    start_date: date
    end_date: date
    status: Optional[AuditTestStatus]
    outcome_passed: Optional[bool]


class UpdateAuditTest(BaseModel):
    name: Optional[str]
    description: Optional[str]
    external_reference_id: Optional[str]
    objective: Optional[str]
    approximate_days_to_complete: Optional[int]
    stakeholder_ids: Optional[List[int]]
    expected_results: Optional[str]
    project_control_id: Optional[str]
    tester_id: Optional[str]
    test_frequency: Optional[str]
    last_test_date: Optional[date]
    start_date: Optional[date]
    end_date: Optional[date]
    status: Optional[AuditTestStatus]
    outcome_passed: Optional[bool]
    cost_ids: Optional[List[int]]


class CreateAuditTestInstance(BaseModel):
    audit_test_id: str
    start_date: Optional[date]
    end_date: Optional[date]
    status: Optional[AuditTestStatus]
    outcome_passed: Optional[bool]
    comments: Optional[str]


class UpdateAuditTestInstance(BaseModel):
    audit_test_id: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    status: Optional[AuditTestStatus]
    outcome_passed: Optional[bool]
    comments: Optional[str]


class DisplayProject(BaseModel):
    id: str
    name: str
    description: str

    class Config:
        orm_mode = True


class DisplayProjectControlControl(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayCapPoam(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayAuditTestInstanceTest(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayAuditTestInstance(BaseModel):
    id: int = None
    audit_test_id: str = None
    start_date: Optional[date]
    end_date: Optional[date]
    status: Optional[AuditTestStatus]
    outcome_passed: Optional[bool]
    audit_test: DisplayAuditTestInstanceTest = None
    comments: str = None

    class Config:
        orm_mode = True


class DisplayProjectControl(BaseModel):
    id: str
    control: DisplayProjectControlControl

    class Config:
        orm_mode = True


class DisplayTester(BaseModel):
    id: str
    email: str
    tenant_id: str
    is_superuser: bool
    is_tenant_admin: bool
    is_active: bool

    class Config:
        orm_mode = True


class DisplayStakeholders(BaseModel):
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


class DisplayAuditTestCost(BaseModel):
    audit_test_id: int = None
    cost_id: int = None
    cost: DisplayCost = None

    class Config:
        orm_mode = True


class DisplayAuditTestApprovalWorkflow(BaseModel):
    audit_test_id: int = None
    approval_workflow_id: int = None
    approval_workflow: DisplayApprovalWorkflow = None

    class Config:
        orm_mode = True


class DisplayAuditTest(BaseModel):
    id: str = None
    name: str = None
    description: str = None
    tenant_id: str = None
    keywords: str = None
    external_reference_id: str = None
    objective: str = None
    approximate_days_to_complete: int = None
    expected_results: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    project: DisplayProject = None
    project_control: DisplayProjectControl = None
    tester: DisplayTester = None
    stakeholders: List[DisplayStakeholders] = []
    test_frequency: TestFrequency = None
    last_test_date: date = None
    start_date: Optional[date]
    end_date: date = None
    status: AuditTestStatus = None
    documents: List[DisplayDocumentID] = []
    keywords: List[DisplayKeywordID] = []
    outcome_passed: bool = None
    cap_poams: List[DisplayCapPoam] = None
    audit_test_instances: List[DisplayAuditTestInstance] = None
    costs: List[DisplayAuditTestCost] = []
    approval_workflows: List[DisplayAuditTestApprovalWorkflow] = []

    class Config:
        orm_mode = True
