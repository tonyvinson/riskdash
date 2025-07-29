from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class CreateFrequency(BaseModel):
    name: str
    description: str


class UpdateFrequency(BaseModel):
    name: Optional[str]
    description: Optional[str]


class DisplayFrequency(BaseModel):
    id: str
    name: str
    description: str
    tenant_id: str = None
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
