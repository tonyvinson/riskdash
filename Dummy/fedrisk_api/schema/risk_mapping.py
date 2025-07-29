from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class CreateRiskMapping(BaseModel):
    name: str
    description: str


class UpdateRiskMapping(BaseModel):
    name: Optional[str]
    description: Optional[str]


class DisplayRiskMapping(BaseModel):
    id: str
    name: str
    description: str
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
