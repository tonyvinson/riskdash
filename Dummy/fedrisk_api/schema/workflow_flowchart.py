from pydantic import BaseModel
from datetime import datetime, date
from typing import Optional, List

from fedrisk_api.schema.cost import DisplayCost
from fedrisk_api.schema.approval_workflows import DisplayApprovalWorkflow

# from fedrisk_api.db.enums import WorkflowFlowchartStatus


class CreateWorkflowProjectTemplate(BaseModel):
    project_id: int = None
    template_id: int = None


# Workflow Flowchart
class CreateWorkflowFlowchart(BaseModel):
    name: str
    node_data: Optional[List] = None  # Allow list
    link_data: Optional[List] = None  # Allow list
    created_date: datetime = None
    last_updated_date: datetime = None
    project_id: int = None
    start_date: date = None
    due_date: date = None
    status: str = None


class UpdateWorkflowFlowchart(BaseModel):
    name: str = None
    node_data: Optional[List] = None  # Allow list
    link_data: Optional[List] = None  # Allow list
    last_updated_date: datetime = None
    project_id: int = None
    start_date: date = None
    due_date: date = None
    status: str = None
    cost_ids: Optional[List[int]]

    class Config:
        orm_mode = True


class DisplayWorkflowFlowchartCost(BaseModel):
    workflow_flowchart_id: int = None
    cost_id: int = None
    cost: DisplayCost = None

    class Config:
        orm_mode = True


class DisplayWorkflowFlowchartEvent(BaseModel):
    id: int = None
    name: str = None
    workflow_flowchart_node_id: int = None
    # trigger_logic
    # event_logic

    class Config:
        orm_mode = True


class DisplayShortProject(BaseModel):
    id: int = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayTask(BaseModel):
    id: int = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayWorkflowTaskMap(BaseModel):
    id: str
    task: DisplayTask = None

    class Config:
        orm_mode = True


class DisplayWorkflowFlowchartApprovalWorkflow(BaseModel):
    workflow_flowchart_id: int = None
    approval_workflow_id: int = None
    approval_workflow: DisplayApprovalWorkflow = None

    class Config:
        orm_mode = True


class DisplayWorkflowFlowchart(BaseModel):
    id: int
    name: str
    node_data: Optional[List] = None  # Allow list
    link_data: Optional[List] = None  # Allow list
    created_date: datetime = None
    last_updated_date: datetime = None
    project_id: int = None
    project: DisplayShortProject = None
    start_date: date = None
    due_date: date = None
    status: str = None
    costs: List[DisplayWorkflowFlowchartCost] = []
    events: List[DisplayWorkflowFlowchartEvent] = []
    workflow_task_mappings: List[DisplayWorkflowTaskMap] = []
    approval_workflows: List[DisplayWorkflowFlowchartApprovalWorkflow] = []

    class Config:
        orm_mode = True
