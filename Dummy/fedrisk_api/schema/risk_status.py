from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class CreateRiskStatus(BaseModel):
    name: str
    description: str


class UpdateRiskStatus(BaseModel):
    name: Optional[str]
    description: Optional[str]


class DisplayRiskStatus(BaseModel):
    id: str
    name: str
    description: str
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
