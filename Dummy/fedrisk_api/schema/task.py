from __future__ import annotations
from datetime import date, datetime
from typing import ForwardRef, List

from pydantic import BaseModel, validator

from fedrisk_api.s3 import S3Service
from fedrisk_api.schema.cost import DisplayCost
from fedrisk_api.schema.approval_workflows import DisplayApprovalWorkflow

# DisplayTask = ForwardRef('DisplayTask')

DisplayChildTask = ForwardRef("DisplayChildTask")


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


class TaskUpdateUser(BaseModel):
    id: str
    email: str
    first_name: str = None
    last_name: str = None

    class Config:
        orm_mode = True


class DisplayProject(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayWBS(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayControl(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayUser(BaseModel):
    id: str
    email: str = None
    first_name: str = None
    last_name: str = None
    profile_picture: str = None

    class Config:
        orm_mode = True

    @validator("profile_picture", pre=True, always=True)
    def profile_picture_url_s3(cls, value, values):
        expire_time = 86400
        s3_service = S3Service()
        profile_pic = values.get("profile_picture")
        user_folder = values.get("s3_bucket")
        tenant = values.get("tenant")
        if profile_pic is None:
            return ""
        file_key = user_folder + profile_pic
        value = s3_service.get_profile_picture_image_url(expire_time, tenant, file_key)
        return value


class DisplayTaskHistory(BaseModel):
    id: str
    task_id: str
    old_status: str = None
    new_status: str = None
    comments: str
    updated_by: TaskUpdateUser
    updated_date: datetime

    class Config:
        orm_mode = True

    @validator("old_status")
    @classmethod
    def transform_old_status(cls, value):
        return " ".join(map(lambda x: x.title(), value.split("_")))

    @validator("new_status")
    @classmethod
    def transform_new_status(cls, value):
        return " ".join(map(lambda x: x.title(), value.split("_")))


class FedriskObjectType(BaseModel):
    name: str = None

    class Config:
        orm_mode = True


class DisplayProjectControl(BaseModel):
    id: str
    control: DisplayControl = None

    class Config:
        orm_mode = True


class DisplayTaskDocument(BaseModel):
    id: str
    name: str
    title: str = None
    description: str = None
    fedrisk_object_type: str = None
    fedrisk_object_id: int = None
    fedrisk_object_object: FedriskObjectType = None
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayRisk(BaseModel):
    id: str
    name: str
    description: str = None
    tenant_id: str
    external_reference_id: str = None
    current_impact: float = 0.0
    risk_assessment: str = None
    affected_assets: str = None
    technology: str = None
    owner_supervisor: str = None
    comments: str = None
    additional_notes: str = None
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayAuditTest(BaseModel):
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
    project: DisplayProject
    last_test_date: date = None
    due_date: date = None

    class Config:
        orm_mode = True


class CreateTaskLink(BaseModel):
    source_id: str
    target_id: str
    type: str

    class Config:
        orm_mode = True


class CreateTaskResource(BaseModel):
    user_id: int
    task_id: int
    value: int = None
    # start_date: str = None
    # end_date: str = None

    class Config:
        orm_mode = True


class DisplayTaskSource(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayTaskLink(BaseModel):
    id: str
    source_id: str
    sources: DisplayTaskSource
    target_id: str
    type: str

    class Config:
        orm_mode = True


class CreateTask(BaseModel):
    title: str
    name: str
    description: str = None
    project_id: str = None
    wbs_id: int = None
    task_status_id: int = None
    task_category_id: int = None
    user_id: str
    # status: str = None
    priority: str = None
    due_date: date = None
    # category: str = None
    actual_start_date: date = None
    actual_end_date: date = None
    duration: str = None
    percent_complete: int = None
    milestone: bool = None
    assigned_to: str = None
    estimated_loe: str = None
    actual_loe: str = None
    child_task_order: int = None
    attachments: list[int] | None
    risks: list[int] | None
    audit_tests: list[int] | None
    project_controls: list[int] | None
    children: list[int] | None
    parents: list[int] | None
    resources: list[int] | None
    resources_value: list[int] | None
    import_id: int = None
    additional_stakeholder_ids: list[int] | None
    # resources_start_date: Optional[list[str]]
    # resources_end_date: Optional[list[str]]
    # task_link_targets: Optional[Set[CreateTaskLink]]

    class Config:
        orm_mode = True


class UpdateTask(BaseModel):
    title: str = None
    name: str = None
    description: str = None
    wbs_id: int = None
    task_status_id: int = None
    task_category_id: int = None
    # fedrisk_object_type: str = None
    # fedrisk_object_id: int = None
    # status: str = None
    priority: str = None
    comments: str = None
    due_date: date = None
    actual_start_date: date = None
    actual_end_date: date = None
    duration: str = None
    percent_complete: int = None
    milestone: bool = None
    assigned_to: str = None
    estimated_loe: str = None
    actual_loe: str = None
    child_task_order: int = None
    attachments: list[int] | None
    risks: list[int] | None
    audit_tests: list[int] | None
    project_controls: list[int] | None
    children: list[int] | None
    parents: list[int] | None
    category: str = None
    task_link_targets: list[int] | None
    task_link_types: list[str] | None
    # resources: Optional[list[CreateTaskResource]]
    resources: list[int] | None
    resources_value: list[int] | None
    cost_ids: list[int] | None
    additional_stakeholder_ids: list[int] | None
    # resources_start_date: Optional[list[str]]
    # resources_end_date: Optional[list[str]]

    class Config:
        orm_mode = True


class DisplayChildTask(BaseModel):
    # model_config = ConfigDict(extra='allow')
    id: str
    parent_task_id: int = None
    child_task_id: int = None
    # parent: DisplayTask = None
    # child: DisplayTask = None
    # model_config = ConfigDict(hide_input_in_errors=True)

    def to_serializable(self) -> dict:
        """Converts the model to a dictionary format that can be serialized."""
        # Serialize without children to avoid circular references
        serialized_data = self.dict(exclude={"child", "parent"})
        # Manually serialize the children and parent (only ID for simplicity)
        if self.parent:
            serialized_data["parent"] = self.parent_task_id
        if self.child:
            serialized_data["child"] = self.child_task_id
        return serialized_data

    class Config:
        orm_mode = True


class DisplayTaskResource(BaseModel):
    id: str
    user_id: str
    task_id: str
    resource: DisplayUser
    value: int = None
    # start_date: date = None
    # end_date: date = None

    class Config:
        orm_mode = True


class DisplayCalendarTask(BaseModel):
    id: str
    title: str
    name: str
    description: str = None
    # status: str = None
    priority: str = None
    due_date: date = None
    project_id: str = None

    class Config:
        orm_mode = True


class DisplayTaskStatus(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayTaskCategory(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayWorkflowFlowchart(BaseModel):
    id: str
    name: str
    status: str = None

    class Config:
        orm_mode = True


class DisplayWorkflowTaskMap(BaseModel):
    id: str
    workflow_flowchart: DisplayWorkflowFlowchart = None

    class Config:
        orm_mode = True


class DisplayTaskCost(BaseModel):
    task_id: int = None
    cost_id: int = None
    cost: DisplayCost = None

    class Config:
        orm_mode = True


class DisplayTaskStakeholders(BaseModel):
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


class DisplayTaskApprovalWorkflow(BaseModel):
    task_id: int = None
    approval_workflow_id: int = None
    approval_workflow: DisplayApprovalWorkflow = None

    class Config:
        orm_mode = True


class DisplayTask(BaseModel):
    # model_config = ConfigDict(extra='allow')
    # model: Optional['DisplayChildTask'] = None
    id: str
    title: str = None
    name: str = None
    description: str = None
    project: DisplayProject = None
    wbs: DisplayWBS = None
    user: DisplayUser = None
    tenant_id: str = None
    fedrisk_object_type: str = None
    fedrisk_object_id: int = None
    # status: str = None
    priority: str = None
    due_date: date = None
    # task_history: list[DisplayTaskHistory] = []
    created_at: datetime = None
    updated_at: datetime = None
    actual_start_date: date = None
    actual_end_date: date = None
    duration: str = None
    percent_complete: int = None
    milestone: bool = None
    assigned: DisplayUser = None
    estimated_loe: str = None
    actual_loe: str = None
    attachments: list[DisplayTaskDocument] = []
    risks: list[DisplayRisk] = []
    audit_tests: list[DisplayAuditTest] = []
    project_controls: list[DisplayProjectControl] = []
    parents: list[DisplayChildTask] = []
    children: list[DisplayChildTask] = []
    keywords: list[DisplayKeywordID] = []
    category: str = None
    # task_link_sources: list[DisplayTaskLink]
    task_link_targets: list[DisplayTaskLink] = []
    resources: list[DisplayTaskResource] = []
    task_status_id: int = None
    task_status: DisplayTaskStatus = None
    task_category: DisplayTaskCategory = None
    costs: list[DisplayTaskCost] = []
    additional_stakeholders: list[DisplayTaskStakeholders] = None
    workflow_task_mappings: list[DisplayWorkflowTaskMap] = None
    approval_workflows: list[DisplayTaskApprovalWorkflow] = []
    # model_config = ConfigDict(hide_input_in_errors=True)

    class Config:
        orm_mode = True


DisplayChildTask.update_forward_refs(parent=DisplayTask)
DisplayChildTask.update_forward_refs(child=DisplayTask)
# DisplayTask.update_forward_refs(parents=List[DisplayChildTask])
# DisplayTask.update_forward_refs(children=List[DisplayChildTask])


class DisplayTasks(BaseModel):
    items: list[DisplayTask] = []
    total: int

    class Config:
        orm_mode = True
        extra = "allow"
