from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict


# Survey Template
class CreateSurveyTemplate(BaseModel):
    name: str
    survey_json: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None


class UpdateSurveyTemplate(BaseModel):
    name: str = None
    survey_json: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplaySurveyTemplate(BaseModel):
    id: int
    name: str
    survey_json: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
