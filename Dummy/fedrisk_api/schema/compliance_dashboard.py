from typing import List

from pydantic import BaseModel


class DisplayProject(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayFramework(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayComplianceCount(BaseModel):
    x: str = None
    y: int = None

    class Config:
        orm_mode = True


class DisplayComplianceMetrics(BaseModel):
    project_id: int = None
    project_name: str = None
    framework_id: str = None
    framework_name: str = None
    total: int = None
    monthly: List[DisplayComplianceCount] = []
    status: List[DisplayComplianceCount] = []

    class Config:
        orm_mode = True


class DisplayComplianceMetricsCapPoam(BaseModel):
    project_id: int = None
    project_name: str = None
    total: int = None
    monthly: List[DisplayComplianceCount] = []
    status: List[DisplayComplianceCount] = []
    criticality: List[DisplayComplianceCount] = []

    class Config:
        orm_mode = True
