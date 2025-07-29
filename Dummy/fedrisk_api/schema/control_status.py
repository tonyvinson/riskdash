from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class CreateControlStatus(BaseModel):
    name: str
    description: Optional[str]


class UpdateControlStatus(BaseModel):
    name: Optional[str]
    description: Optional[str]


class DisplayControlStatus(BaseModel):
    id: str
    name: str
    description: str = None
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
