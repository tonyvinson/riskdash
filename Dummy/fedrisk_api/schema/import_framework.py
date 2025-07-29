from datetime import datetime

from pydantic import BaseModel
from typing import Optional


class CreateImportFramework(BaseModel):
    name: str


class DisplayImportFramework(BaseModel):
    id: str
    name: str
    tenant_id: str = None
    file_content_type: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    imported: bool = None
    import_results: str = None

    class Config:
        orm_mode = True
