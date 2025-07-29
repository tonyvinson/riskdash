from datetime import date, datetime
from typing import List

from pydantic import BaseModel
from typing import Optional, Any, Dict

from fedrisk_api.db.enums import (
    ExceptionReviewStatus,
    IsAssessmentConfirmed,
    ReviewFrequency,
    StatusType,
)

from fedrisk_api.db.models import AuditTestStatus, TestFrequency
from fedrisk_api.schema.cost import DisplayCost
from fedrisk_api.schema.approval_workflows import DisplayApprovalWorkflow


class DisplayObj(BaseModel):
    id: str = None

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


class CreateProjectControl(BaseModel):
    project_id: Optional[int]
    control_id: Optional[int]
    mitigation_percentage: Optional[float]
    control_family_id: Optional[int]
    control_phase_id: Optional[int]
    control_status_id: Optional[int]
    control_class_id: Optional[int]


class UpdateProjectControl(BaseModel):
    project_id: Optional[int]
    control_id: Optional[int]
    implementation_statement: Optional[str]
    mitigation_percentage: Optional[float]
    control_family_id: Optional[int]
    control_phase_id: Optional[int]
    control_status_id: Optional[int]
    control_class_id: Optional[int]
    cost_ids: Optional[List[int]]


class CreateProject(BaseModel):
    name: str
    description: str
    project_admin_id: Optional[int]
    project_group_id: Optional[int]
    status: Optional[str]


class UpdateProject(BaseModel):
    name: Optional[str]
    description: Optional[str]
    project_admin_id: Optional[int]
    project_group_id: Optional[int]
    status: Optional[str]
    cost_ids: Optional[List[int]]


class DisplayProjectControlFramework(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayProjectControlFrameworkVersion(BaseModel):
    id: str
    version_prefix: str
    version_suffix: str
    framework: DisplayProjectControlFramework
    keywords: List[DisplayKeywordID] = []

    class Config:
        orm_mode = True


class DisplayProjectControlAssessment(BaseModel):
    id: str
    name: str
    status: StatusType
    description: str = None
    comments: str = None
    keywords: List[DisplayKeywordID] = []
    is_assessment_confirmed: IsAssessmentConfirmed = None
    project_control: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayUser(BaseModel):
    id: str
    email: str
    first_name: str = None
    last_name: str = None
    phone_no: str = None
    tenant_id: str
    is_superuser: bool
    is_tenant_admin: bool
    is_active: bool

    class Config:
        orm_mode = True


# class DisplayProjectGroup(BaseModel):
# id: int
# name: str
# description: str = None

# class Config:
# orm_mode = True


class DisplayProjectAdmin(BaseModel):
    id: str
    first_name: str = None
    last_name: str = None
    email: str
    tenant_id: str
    is_superuser: bool
    is_tenant_admin: bool
    is_active: bool

    class Config:
        orm_mode = True


class DisplayProjectControlException(BaseModel):
    id: str
    name: str
    description: str = None
    justification: str
    next_review_date: date = None
    review_frequency: ReviewFrequency = None
    created_date: datetime = None
    last_updated_date: datetime = None
    owner: DisplayUser = None
    stakeholders: List[DisplayUser]
    review_status: ExceptionReviewStatus = None
    review_status: str = None
    keywords: List[DisplayKeywordID] = []

    class Config:
        orm_mode = True


class DisplayProjectControlControl(BaseModel):
    id: str
    name: str
    description: str = None
    framework_versions: List[DisplayProjectControlFrameworkVersion] = []
    keywords: List[DisplayKeywordID] = []

    class Config:
        orm_mode = True


class AddProjectControl(BaseModel):
    project_id: int
    control_id: int
    mitigation_percentage: int = None
    control_family_id: int = None
    control_phase_id: int = None
    control_status_id: int = None
    control_class_id: int = None


class AddProjectControls(BaseModel):
    controls: List[AddProjectControl]


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


class DisplayProjectEvaluation(BaseModel):
    id: str
    name: str
    comments: str = None
    description: str = None
    status: StatusType
    created_date: datetime = None
    last_updated_date: datetime = None

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


class DisplayTester(BaseModel):
    id: str
    email: str
    tenant_id: str
    is_superuser: bool
    is_tenant_admin: bool
    is_active: bool

    class Config:
        orm_mode = True


class DisplayProjectControlAuditTest(BaseModel):
    id: str
    control: DisplayProjectControlControl

    class Config:
        orm_mode = True


class FedriskObjectType(BaseModel):
    name: str = None

    class Config:
        orm_mode = True


class DisplayProjectGroup(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class AddProjectUser(BaseModel):
    user_id: int
    role_id: int


class AddProjectsUser(AddProjectUser):
    project_id: int


class AddProjectUsers(BaseModel):
    users: List[AddProjectUser]


class AddProjectsUsers(BaseModel):
    users: List[AddProjectsUser]


class AddAProjectUser(BaseModel):
    id: int
    user_id: int
    role_id: int


class ChangeProjectUserRole(AddProjectUser):
    pass


class DisplayUserProject(BaseModel):
    id: str
    name: str
    description: str = None
    tenant_id: str
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayRole(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayProjectInUser(BaseModel):
    user: DisplayUser
    role: DisplayRole
    project: DisplayUserProject

    class Config:
        orm_mode = True


class DisplayProjectUsers(BaseModel):
    users: List[DisplayProjectInUser] = []

    class Config:
        orm_mode = True


class RemoveProjectUser(BaseModel):
    user_id: int


class ProjectAssociatedUser(BaseModel):
    user: DisplayUser
    role: DisplayRole

    class Config:
        orm_mode = True


class ProjectPendingTask(BaseModel):
    project_id: int
    project_name: str
    task_pending_count: int

    class Config:
        orm_mode = True


class ProjectPendingTasks(BaseModel):
    items: List[ProjectPendingTask] = []

    class Config:
        orm_mode = True


class DisplayProjectControlStatus(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayDocument(BaseModel):
    id: str = None
    name: str = None
    title: str = None
    description: str = None
    keywords: List[DisplayKeywordID] = []
    owner_id: str = None
    version: str = None
    fedrisk_object_type: str = None
    fedrisk_object_id: int = None
    fedrisk_object_object: FedriskObjectType = None
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayDocumentID(BaseModel):
    id: str = None
    document: DisplayDocument = None

    class Config:
        orm_mode = True


class DisplayProjectAuditTest(BaseModel):
    id: str
    name: str
    description: str = None
    tenant_id: str = None
    external_reference_id: str = None
    objective: str = None
    approximate_time_to_complete: str = None
    expected_results: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    # project: DisplayProject
    project_control: DisplayProjectControlAuditTest = None
    tester: DisplayTester = None
    stakeholders: List[DisplayStakeholders] = []
    test_frequency: TestFrequency = None
    last_test_date: date = None
    due_date: date = None
    start_date: date = None
    status: AuditTestStatus = None
    documents: List[DisplayDocumentID] = []
    keywords: List[DisplayKeywordID] = []

    class Config:
        orm_mode = True


class DisplayProjectControlRisk(BaseModel):
    id: str = None
    control: DisplayProjectControlControl = None

    class Config:
        orm_mode = True


class DisplayProjectRisk(BaseModel):
    id: str
    name: str
    description: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    control: DisplayRiskControl = None
    audit_test: DisplayRiskAuditTest = None
    owner: DisplayUser = None
    documents: List[DisplayDocumentID] = []
    keywords: List[DisplayKeywordID] = []
    external_reference_id: str = None
    current_impact: float = None
    risk_assessment: str = None
    affected_assets: str = None
    technology: str = None
    additional_stakeholders: List[DisplayStakeholders] = []
    owner_id: int = None
    owner_supervisor: str = None
    comments: str = None
    additional_notes: str = None
    current_likelihood_id: str = None
    risk_score_id: str = None
    risk_category_id: str = None
    risk_impact_id: str = None
    risk_status_id: str = None
    project_control: DisplayProjectControlRisk = None

    class Config:
        orm_mode = True


class DisplayControlFamily(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayControlPhase(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayControlStatus(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayControlClass(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayAssociatedProject(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayAWSControl(BaseModel):
    id: int
    aws_id: str = None
    aws_title: str = None
    aws_control_status: str = None
    aws_severity: str = None
    aws_failed_checks: int = None
    aws_unknown_checks: int = None
    aws_not_available_checks: int = None
    aws_passed_checks: int = None
    aws_related_requirements: str = None
    aws_custom_parameters: str = None
    created: datetime = None

    class Config:
        orm_mode = True


class DisplayAWSControlProjectControl(BaseModel):
    aws_control_id: str = None
    project_control_id: str = None
    aws_control: DisplayAWSControl = None

    class Config:
        orm_mode = True


class DisplayProjectControlCost(BaseModel):
    project_evaluation_id: int = None
    cost_id: int = None
    cost: DisplayCost = None

    class Config:
        orm_mode = True


class DisplayProjectControlEvidence(BaseModel):
    evidence_id: int = None
    machine_readable: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object

    class Config:
        orm_mode = True


class DisplayProjectControlServiceProvider(BaseModel):
    service_provider_id: int = None

    class Config:
        orm_mode = True


class DisplayProjectControlApp(BaseModel):
    app_id: int = None

    class Config:
        orm_mode = True


class DisplayProjectControl(BaseModel):
    id: str
    control: DisplayProjectControlControl = None
    implementation_statement: str = None
    mitigation_percentage: str = None
    control_family_id: str = None
    control_family: DisplayControlFamily = None
    control_phase_id: str = None
    control_phase: DisplayControlPhase = None
    control_status_id: str = None
    control_status: DisplayControlStatus = None
    control_class_id: str = None
    control_class: DisplayControlClass = None
    documents: List[DisplayDocumentID] = []
    control_status: DisplayProjectControlStatus = None
    assessment: DisplayProjectControlAssessment = None
    exception: DisplayProjectControlException = None
    project: DisplayAssociatedProject = None
    keywords: List[DisplayKeywordID] = []
    aws_controls: List[DisplayAWSControlProjectControl] = []
    costs: List[DisplayProjectControlCost] = []
    evidence: List[DisplayProjectControlEvidence] = []
    service_provider_project_controls: List[DisplayProjectControlServiceProvider] = []
    app_project_controls: List[DisplayProjectControlApp] = []

    class Config:
        orm_mode = True


class DisplayProjectCost(BaseModel):
    project_id: int = None
    cost_id: int = None
    cost: DisplayCost = None

    class Config:
        orm_mode = True


class DisplayProjectApprovalWorkflow(BaseModel):
    project_id: int = None
    approval_workflow_id: int = None
    approval_workflow: DisplayApprovalWorkflow = None

    class Config:
        orm_mode = True


class DisplayProject(BaseModel):
    id: str = None
    name: str = None
    description: str = None
    tenant_id: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    # project_controls: List[DisplayProjectControl] = []
    project_evaluations: List[DisplayProjectEvaluation] = []
    risks: List[DisplayProjectRisk] = []
    audit_tests: List[DisplayProjectAuditTest] = []
    documents: List[DisplayDocumentID] = []
    project_group: DisplayProjectGroup = None
    project_admin: DisplayProjectAdmin = None
    my_role: str = None
    status: str = None
    keywords: List[DisplayKeywordID] = []
    costs: List[DisplayProjectCost] = []
    approval_workflows: List[DisplayProjectApprovalWorkflow] = []

    class Config:
        orm_mode = True
        extra = "allow"
