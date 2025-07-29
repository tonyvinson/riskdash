from datetime import datetime, date
from math import floor
from typing import List

from pydantic import BaseModel, validator
from typing import Optional

from fedrisk_api.schema.framework import DisplayFramework

from fedrisk_api.schema.control import (
    # DisplayControlClass,
    # DisplayControlFamily,
    # DisplayControlPhase,
    # DisplayControlStatus,
    DisplayControl,
)


class CreateFrameworkVersion(BaseModel):
    framework_id: int
    version_prefix: Optional[str]
    version_suffix: Optional[str]
    guidance: Optional[str]
    release_date: Optional[date]


class CreatePreloadedFrameworkVersion(CreateFrameworkVersion):
    is_preloaded: bool


class UpdateFrameworkVersion(BaseModel):
    framework_id: int
    version_prefix: Optional[str]
    version_suffix: Optional[str]
    guidance: Optional[str]
    release_date: Optional[date]


class DisplayFrameworkVersionControl(BaseModel):
    id: str
    control: DisplayControl
    # control_phase: DisplayControlPhase = None
    # control_status: DisplayControlStatus = None
    # control_class: DisplayControlClass = None
    # control_family: DisplayControlFamily = None
    # mitigation_percentage: float = None

    # @validator("mitigation_percentage")
    # def convert_mitigation_percentage(value):
    #     if value is None:
    #         return None
    #     value = floor(value)
    #     if 0 <= value <= 33:
    #         return "Low"
    #     elif 34 <= value <= 66:
    #         return "Medium"
    #     return "High"

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


class DisplayFrameworkVersion(BaseModel):
    id: str
    framework: DisplayFramework
    version_prefix: str = None
    version_suffix: str = None
    release_date: date = None
    guidance: str = None
    tenant_id: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    # controls: List[DisplayControl] = []
    documents: List[DisplayDocumentID] = []
    keywords: List[DisplayKeywordID] = []

    class Config:
        orm_mode = True
