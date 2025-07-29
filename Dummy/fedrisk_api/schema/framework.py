from datetime import datetime

# from math import floor
from typing import List

from pydantic import BaseModel, validator
from typing import Optional


class CreateFrameworkTenant(BaseModel):
    tenant_id: Optional[int]
    framework_id: Optional[int]
    is_enabled: Optional[bool]


class UpdateFrameworkTenant(BaseModel):
    tenant_id: Optional[int]
    framework_id: Optional[int]
    is_enabled: Optional[bool]


class CreateFramework(BaseModel):
    name: str
    description: str
    is_global: Optional[bool]


class CreatePreloadedFramework(CreateFramework):
    is_preloaded: bool


class UpdateFramework(BaseModel):
    name: Optional[str]
    description: Optional[str]
    is_global: Optional[bool]


class DisplayFrameworkTenant(BaseModel):
    tenant_id: int = None
    framework_id: int = None
    is_enabled: bool = None

    class Config:
        orm_mode = True


class DisplayDocument(BaseModel):
    id: str
    name: str = None
    title: str = None
    description: str = None
    # fedrisk_object_type: str = None
    # fedrisk_object_id: int = None
    # fedrisk_object_object: FedriskObjectType = None
    # created_date: datetime = None
    # last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayDocumentID(BaseModel):
    id: str
    document: DisplayDocument

    class Config:
        orm_mode = True


class DisplayKeyword(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayKeywordID(BaseModel):
    id: str = None
    keyword: DisplayKeyword = None

    class Config:
        orm_mode = True


class DisplayFramework(BaseModel):
    id: str
    name: str
    description: str = None
    tenant_id: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    documents: List[DisplayDocumentID] = []
    keywords: List[DisplayKeywordID] = []
    is_global: bool = None
    framework_tenant: List[DisplayFrameworkTenant] = []

    class Config:
        orm_mode = True
