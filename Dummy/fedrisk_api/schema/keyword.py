from typing import List
from datetime import datetime
from pydantic import BaseModel


class DisplayObj(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayControl(BaseModel):
    id: str = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayProjectControl(BaseModel):
    id: str = None
    control: DisplayControl = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayAssessment(BaseModel):
    id: str = None
    name: str = None
    project_control: DisplayProjectControl = None

    class Config:
        orm_mode = True


class DisplayAuditTest(BaseModel):
    id: str = None
    name: str = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayProjectRisk(BaseModel):
    id: str = None
    name: str = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayProjectEvaluation(BaseModel):
    id: str = None
    name: str = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayTask(BaseModel):
    id: str = None
    name: str = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayWBS(BaseModel):
    id: str = None
    name: str = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayMappingDocument(BaseModel):
    id: str = None
    keyword_id: int = None
    document_id: int = None
    document: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayMappingAssessment(BaseModel):
    id: str = None
    keyword_id: int = None
    assessment_id: int = None
    assessment: DisplayAssessment = None

    class Config:
        orm_mode = True


class DisplayMappingAuditTest(BaseModel):
    id: str = None
    keyword_id: int = None
    audit_test_id: int = None
    audit_test: DisplayAuditTest = None

    class Config:
        orm_mode = True


class DisplayMappingControl(BaseModel):
    id: str = None
    keyword_id: int = None
    control_id: int = None
    control: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayMappingException(BaseModel):
    id: str = None
    keyword_id: int = None
    exception_id: int = None
    exception: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayMappingFramework(BaseModel):
    id: str = None
    keyword_id: int = None
    framework_id: int = None
    framework: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayMappingFrameworkVersion(BaseModel):
    id: str = None
    keyword_id: int = None
    framework_version_id: int = None
    framework_version: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayMappingProject(BaseModel):
    id: str = None
    keyword_id: int = None
    project_id: int = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayMappingProjectControl(BaseModel):
    id: str = None
    keyword_id: int = None
    project_control_id: int = None
    project_control: DisplayProjectControl = None

    class Config:
        orm_mode = True


class DisplayMappingProjectEvaluation(BaseModel):
    id: str = None
    keyword_id: int = None
    project_evaluation_id: int = None
    project_evaluation: DisplayProjectEvaluation = None

    class Config:
        orm_mode = True


class DisplayMappingRisk(BaseModel):
    id: str = None
    keyword_id: int = None
    risk_id: int = None
    risk: DisplayProjectRisk = None

    class Config:
        orm_mode = True


class DisplayMappingTask(BaseModel):
    id: str = None
    keyword_id: int = None
    task_id: int = None
    task: DisplayTask = None

    class Config:
        orm_mode = True


class DisplayMappingWBS(BaseModel):
    id: str = None
    keyword_id: int = None
    wbs_id: int = None
    wbs: DisplayWBS = None

    class Config:
        orm_mode = True


class CreateKeyword(BaseModel):
    name: str

    class Config:
        orm_mode = True


class UpdateKeyword(BaseModel):
    id: str
    name: str

    class Config:
        orm_mode = True


class DisplayKeyword(BaseModel):
    id: str
    name: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    documents: List[DisplayMappingDocument] = []
    assessments: List[DisplayMappingAssessment] = []
    audit_tests: List[DisplayMappingAuditTest] = []
    controls: List[DisplayMappingControl] = []
    exceptions: List[DisplayMappingException] = []
    frameworks: List[DisplayMappingFramework] = []
    framework_versions: List[DisplayMappingFrameworkVersion] = []
    projects: List[DisplayMappingProject] = []
    project_controls: List[DisplayMappingProjectControl] = []
    project_evaluations: List[DisplayMappingProjectEvaluation] = []
    risks: List[DisplayMappingRisk] = []
    tasks: List[DisplayMappingTask] = []
    wbs: List[DisplayMappingWBS] = []

    class Config:
        orm_mode = True
