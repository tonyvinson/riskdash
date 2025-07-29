from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict, List


# Evidence and ProjectControlEvidence Model


class CreateProjectControlEvidence(BaseModel):
    project_control_id: int = None
    evidence_id: int = None


class CheckProjectControlOwner(BaseModel):
    project_control_id: str = None
    webhook_api_key: str = None


class CreateEvidence(BaseModel):
    name: str = None
    description: str = None
    machine_readable: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None


class UpdateEvidence(BaseModel):
    name: str = None
    description: str = None
    machine_readable: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    last_updated_date: datetime = None


class DisplayControl(BaseModel):
    name: str = None

    class Config:
        orm_mode = True


class DisplayProject(BaseModel):
    name: str = None

    class Config:
        orm_mode = True


class DisplayProjectControl(BaseModel):
    id: int = None
    control: DisplayControl = None
    project: DisplayProject = None

    class Config:
        orm_mode = True


class DisplayEvidenceProjectControl(BaseModel):
    project_control_id: int = None
    project_control: DisplayProjectControl = None

    class Config:
        orm_mode = True


class DisplayEvidence(BaseModel):
    id: int
    name: str = None
    description: str = None
    machine_readable: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None
    project_controls: List[DisplayEvidenceProjectControl] = []

    class Config:
        orm_mode = True
