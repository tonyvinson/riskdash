from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class CreateRiskLikelihood(BaseModel):
    name: str
    description: str


class UpdateRiskLikelihood(BaseModel):
    name: Optional[str]
    description: Optional[str]


class DisplayRiskLikelihood(BaseModel):
    id: str
    name: str
    description: str
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
