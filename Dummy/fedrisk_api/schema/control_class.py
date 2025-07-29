from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class CreateControlClass(BaseModel):
    name: str
    description: str


class UpdateControlClass(BaseModel):
    name: Optional[str]
    description: Optional[str]


class DisplayControlClass(BaseModel):
    id: str
    name: str
    description: str = None
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
