from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any, Dict

# from fedrisk_api.db.enums import WorkflowFlowchartStatus

# Workflow Event
class CreateWorkflowTemplateEvent(BaseModel):
    name: str
    workflow_template_node_id: int = None
    workflow_template_id: int = None
    trigger_logic: Optional[List] = None  # Allow list
    event_config: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None


class UpdateWorkflowTemplateEvent(BaseModel):
    name: str = None
    workflow_template_node_id: int = None
    workflow_template_id: int = None
    trigger_logic: Optional[List] = None  # Allow list
    event_config: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayWorkflowTemplateEvent(BaseModel):
    id: int
    name: str
    workflow_template_node_id: int = None
    workflow_template_id: int = None
    trigger_logic: Optional[List] = None  # Allow list
    event_config: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
