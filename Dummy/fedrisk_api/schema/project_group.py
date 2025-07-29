from datetime import datetime

from pydantic import BaseModel


class CreateProjectGroup(BaseModel):
    name: str
    description: str


class UpdateProjectGroup(BaseModel):
    name: str = None
    description: str = None

    class Config:
        orm_mode = True


class DisplayProject(BaseModel):
    id: int
    name: str
    description: str
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayProjectGroup(BaseModel):
    id: str
    name: str
    description: str
    tenant_id: str
    created_date: datetime
    last_updated_date: datetime

    class Config:
        orm_mode = True
