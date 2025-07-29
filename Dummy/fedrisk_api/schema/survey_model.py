from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Any, Dict


# Survey Model
class TestCounts(BaseModel):
    test_true: int
    test_false: int


class CreateSurveyProjectTemplate(BaseModel):
    project_id: int = None
    template_id: int = None


class CreateSurveyModel(BaseModel):
    name: str
    survey_json: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None
    project_id: int
    published: bool = None


class UpdateSurveyModel(BaseModel):
    name: str = None
    survey_json: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None
    project_id: int = None
    published: bool = None

    class Config:
        orm_mode = True


class DisplaySurveyModel(BaseModel):
    id: int
    name: str
    survey_json: Optional[Dict[str, Any]] = None  # Accept any JSON-compatible object
    created_date: datetime = None
    last_updated_date: datetime = None
    project_id: int
    published: bool = None
    test_counts: Optional[TestCounts] = None

    class Config:
        orm_mode = True
