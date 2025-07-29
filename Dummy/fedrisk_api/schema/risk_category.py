from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class CreateRiskCategory(BaseModel):
    name: str
    description: str


class UpdateRiskCategory(BaseModel):
    name: Optional[str]
    description: Optional[str]


class DisplayRiskCategory(BaseModel):
    id: str
    name: str
    description: str
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
