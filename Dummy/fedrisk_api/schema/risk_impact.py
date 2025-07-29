from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class CreateRiskImpact(BaseModel):
    name: str
    description: str


class UpdateRiskImpact(BaseModel):
    name: Optional[str]
    description: Optional[str]


class DisplayRiskImpact(BaseModel):
    id: str
    name: str
    description: str
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
