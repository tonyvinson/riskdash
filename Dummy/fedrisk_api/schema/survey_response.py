from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict


# Survey Model
class CreateSurveyResponse(BaseModel):
    survey_response: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None
    user_id: int
    survey_model_id: int
    test: bool = None


class UpdateSurveyResponse(BaseModel):
    survey_response: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None
    user_id: int = None
    survey_model_id: int = None
    test: bool = None

    class Config:
        orm_mode = True


class DisplaySurveyResponse(BaseModel):
    id: int
    survey_response: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None
    user_id: int
    survey_model_id: int
    test: bool = None

    class Config:
        orm_mode = True
