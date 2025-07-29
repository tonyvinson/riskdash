from typing import List

from pydantic import BaseModel


class DisplayProjectControlFramework(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayProjectControlControl(BaseModel):
    id: str
    framework: DisplayProjectControlFramework

    class Config:
        orm_mode = True


class DisplayProjectControl(BaseModel):
    id: str
    control: DisplayProjectControlControl = None

    class Config:
        orm_mode = True


class DisplayGovernanceProject(BaseModel):
    id: str
    name: str
    project_controls: List[DisplayProjectControl] = []
    total_project_controls: int
    total_risks: int
    total_audit_test: int

    class Config:
        orm_mode = True
        extra = "allow"


class DisplayGovernance(BaseModel):
    items: List[DisplayGovernanceProject]
    total: int


class RiskItemsDisplay(BaseModel):
    id: str
    name: str
    project_controls: List[DisplayProjectControl] = []
    total_risks: int
    risk_score: int

    class Config:
        orm_mode = True
        extra = "allow"


class FinalDisplayRiskItems(BaseModel):
    items: List[RiskItemsDisplay]
    total: int


class CompilanceDisplay(BaseModel):
    id: str
    name: str
    project_controls: List[DisplayProjectControl] = []
    audit_test_count: int

    class Config:
        orm_mode = True
        extra = "allow"


class FinalCompilanceDisplay(BaseModel):
    items: List[CompilanceDisplay]
    total: int


class DisplayTasks(BaseModel):
    id: str
    name: str
    project_controls: List[DisplayProjectControl] = []
    total_tasks: int

    class Config:
        orm_mode = True
        extra = "allow"


class FinalDisplayTask(BaseModel):
    items: List[DisplayTasks]
    total: int
