from datetime import datetime

from pydantic import BaseModel


class CreateHelpSection(BaseModel):
    title: str
    body: str = None
    divId: str = None
    order: int = None


class UpdateHelpSection(BaseModel):
    title: str = None
    body: str = None
    divId: str = None
    order: int = None

    class Config:
        orm_mode = True


class DisplayHelpSection(BaseModel):
    id: int
    title: str
    body: str
    divId: str = None
    order: int = None
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True
