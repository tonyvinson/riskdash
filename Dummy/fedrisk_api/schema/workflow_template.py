from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

# from fedrisk_api.db.enums import WorkflowFlowchartStatus


# Workflow Template
class CreateWorkflowTemplate(BaseModel):
    name: str = None
    description: str = None
    node_data: Optional[List] = None  # Allow list
    link_data: Optional[List] = None  # Allow list
    created_date: datetime = None
    last_updated_date: datetime = None


class UpdateWorkflowTemplate(BaseModel):
    name: str = None
    description: str = None
    node_data: Optional[List] = None  # Allow list
    link_data: Optional[List] = None  # Allow list
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayWorkflowTemplateEvent(BaseModel):
    id: int = None
    name: str = None
    workflow_template_node_id: int = None
    # trigger_logic
    # event_logic

    class Config:
        orm_mode = True


class DisplayWorkflowTemplate(BaseModel):
    id: int
    name: str = None
    description: str = None
    node_data: Optional[List] = None  # Allow list
    link_data: Optional[List] = None  # Allow list
    created_date: datetime = None
    last_updated_date: datetime = None
    events: List[DisplayWorkflowTemplateEvent] = []

    class Config:
        orm_mode = True
