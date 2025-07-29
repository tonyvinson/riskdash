from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Any, Dict

# from fedrisk_api.db.enums import WorkflowFlowchartStatus

# Workflow Event
class CreateWorkflowEvent(BaseModel):
    name: str
    workflow_flowchart_node_id: int = None
    workflow_flowchart_id: int = None
    trigger_logic: Optional[List] = None  # Allow list
    event_config: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None


class UpdateWorkflowEvent(BaseModel):
    name: str = None
    workflow_flowchart_node_id: int = None
    workflow_flowchart_id: int = None
    trigger_logic: Optional[List] = None  # Allow list
    event_config: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayWorkflowEventLog(BaseModel):
    id: int
    event_type: str = None
    event_description: str = None
    link: str = None
    created_date: datetime = None

    class Config:
        orm_mode = True


class DisplayWorkflowEvent(BaseModel):
    id: int
    name: str
    workflow_flowchart_node_id: int = None
    workflow_flowchart_id: int = None
    trigger_logic: Optional[List] = None  # Allow list
    event_config: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None
    logs: List[DisplayWorkflowEventLog] = []

    class Config:
        orm_mode = True
