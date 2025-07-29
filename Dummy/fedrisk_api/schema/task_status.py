from datetime import datetime
from pydantic import BaseModel, ConfigDict
from typing import Optional


class CreateTaskStatus(BaseModel):
    name: str
    description: str


class UpdateTaskStatus(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class DisplayTaskStatus(BaseModel):
    id: int = None
    name: str = None
    description: str = None
    created_date: Optional[datetime] = None
    last_updated_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)  # Use this if on Pydantic v2

    class Config:  # Keep this if using Pydantic v1
        orm_mode = True
