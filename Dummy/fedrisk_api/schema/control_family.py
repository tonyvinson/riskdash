from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class CreateControlFamily(BaseModel):
    name: str
    description: str


class UpdateControlFamily(BaseModel):
    name: Optional[str]
    description: Optional[str]


class DisplayControlFamily(BaseModel):
    id: str
    name: str
    description: str = None
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
