from typing import List

from pydantic import BaseModel

from fedrisk_api.db.enums import ExceptionReviewStatus, StatusType


class DisplayControlClassMetrics(BaseModel):
    name: str
    count: int
    mitigation_percentage: int


class DisplayControlPhaseMetrics(BaseModel):
    name: str
    count: int
    mitigation_percentage: int


class DisplayControlStatusMetrics(BaseModel):
    name: str
    count: int
    mitigation_percentage: int


class DisplayControlFamilyMetrics(BaseModel):
    name: str
    count: int
    mitigation_percentage: int


class DisplayControlMitigation(BaseModel):
    name: str
    count: int


class DisplayControlAssessment(BaseModel):
    name: str
    count: int


class DisplayGovernanceDashboardMetrics(BaseModel):
    project_id: int
    project_name: str
    framework_name: str
    framework_id: int
    control_class: List[DisplayControlClassMetrics]
    control_phase: List[DisplayControlPhaseMetrics]
    control_status: List[DisplayControlStatusMetrics]
    control_family: List[DisplayControlFamilyMetrics]
    control_mitigation: List[DisplayControlMitigation]
    control_assessment: List[DisplayControlAssessment]
    control_exception_count: int


class DisplayFramework(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class DisplayControlClass(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class DisplayControlStatus(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class DisplayControlFamily(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class DisplayControlPhase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class DisplayControls(BaseModel):
    id: int
    name: str
    description: str
    framework: DisplayFramework
    control_class: DisplayControlClass
    control_phase: DisplayControlPhase
    control_status: DisplayControlStatus
    control_family: DisplayControlFamily
    mitigation_percentage: float

    class Config:
        orm_mode = True


class DisplayProject(BaseModel):
    id: int
    name: str
    description: str = None

    class Config:
        orm_mode = True


class DisplayProjectControl(BaseModel):
    project: DisplayProject
    control: DisplayControls

    class Config:
        orm_mode = True


class DisplayExceptions(BaseModel):
    id: int
    name: str
    description: str = None
    justification: str = None
    project_control: DisplayProjectControl
    # review_status: ExceptionReviewStatus

    class Config:
        orm_mode = True


class DisplayAssessments(BaseModel):
    id: int
    name: str
    description: str = None
    status: StatusType
    project_control: DisplayProjectControl

    class Config:
        orm_mode = True
