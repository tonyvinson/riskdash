from pydantic import BaseModel
from datetime import datetime

# Workflow Event
class CreateWorkflowEventLog(BaseModel):
    workflow_event_id: int = None
    event_type: str = None
    event_description: str = None
    link: str = None
    created_date: datetime = None


class UpdateWorkflowEventLog(BaseModel):
    workflow_event_id: int = None
    event_type: str = None
    event_description: str = None
    link: str = None
    created_date: datetime = None

    class Config:
        orm_mode = True


class DisplayWorkflowEventLog(BaseModel):
    id: int
    workflow_event_id: int = None
    event_type: str = None
    event_description: str = None
    link: str = None
    created_date: datetime = None

    class Config:
        orm_mode = True
