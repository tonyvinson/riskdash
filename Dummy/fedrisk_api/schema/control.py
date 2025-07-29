from datetime import datetime
from typing import List

from pydantic import BaseModel
from typing import Optional


class CreateControl(BaseModel):
    name: str
    description: Optional[str]
    guidance: Optional[str]
    framework_versions: List[Optional[int]]


class CreateBatchControlFrameworkVersion(BaseModel):
    control_id: str
    framework_version_id: Optional[str]


class CreateBatchControlsFrameworkVersion(BaseModel):
    controls: List[CreateBatchControlFrameworkVersion]


class CreatePreloadedControl(CreateControl):
    is_preloaded: bool


class UpdateControl(BaseModel):
    # A Control is created for / within a Framework
    # The concept of "moving" a control to a different
    # Framework is disallowed . . .
    # framework_id: Optional[str]
    name: Optional[str]
    description: Optional[str]
    guidance: Optional[str]
    # The metadata below is stored per project control used on a project.
    # It does not belong here.
    # control_family_id: Optional[int]
    # control_class_id: Optional[int]
    # control_status_id: Optional[int]
    # control_phase_id: Optional[int]
    # mitigation_percentage: Optional[float]


class DisplayControlFramework(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayControlFrameworkVersion(BaseModel):
    id: str
    framework: DisplayControlFramework
    version_prefix: Optional[str]
    version_suffix: Optional[str]
    description: str = None

    class Config:
        orm_mode = True


class DisplayControlClass(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayControlStatus(BaseModel):
    id: str
    name: str
    description: str

    class Config:
        orm_mode = True


class DisplayControlFamily(BaseModel):
    id: str
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayControlPhase(BaseModel):
    id: str
    name: str
    description: str = None

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


class DisplayControl(BaseModel):
    id: str = None
    name: str = None
    description: str = None
    guidance: str = None
    keywords: str = None
    tenant_id: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    framework_versions: List[DisplayControlFrameworkVersion] = []
    # control_phase: DisplayControlPhase = None
    # control_status: DisplayControlStatus = None
    # control_class: DisplayControlClass = None
    # control_family: DisplayControlFamily = None
    # mitigation_percentage: Union[float, int, str] = None
    used: bool = None
    documents: List[DisplayDocumentID] = []
    keywords: List[DisplayKeywordID] = []

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
