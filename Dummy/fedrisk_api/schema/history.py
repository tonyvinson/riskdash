from datetime import datetime
from pydantic import BaseModel

from typing import Optional
from datetime import date

from fedrisk_api.schema.assessment import DisplayAssessment


class CreateUserWatching(BaseModel):
    project_id: int
    user_id: int
    project_overview: bool = None
    project_controls: bool = None
    project_assessments: bool = None
    project_risks: bool = None
    project_evaluations: bool = None
    project_audit_tests: bool = None
    project_documents: bool = None
    project_users: bool = None
    project_tasks: bool = None
    project_wbs: bool = None
    project_cap_poams: bool = None
    project_workflow_flowcharts: bool = None


class CreateAssessmentHistory(BaseModel):
    assessment_id: int = None
    author_id: int = None
    history: str = None


class CreateAuditTestHistory(BaseModel):
    audit_test_id: int = None
    author_id: int = None
    history: str = None


class CreateDocumentHistory(BaseModel):
    document_id: int = None
    author_id: int = None
    history: str = None


class CreateExceptionHistory(BaseModel):
    exception_id: int = None
    author_id: int = None
    history: str = None


class CreateProjectControltHistory(BaseModel):
    project_control_id: int = None
    author_id: int = None
    history: str = None


class CreateProjectEvaluationHistory(BaseModel):
    project_evaluation_id: int = None
    author_id: int = None
    history: str = None


class CreateProjectHistory(BaseModel):
    project_id: int = None
    author_id: int = None
    history: str = None


class CreateProjectTaskHistory(BaseModel):
    task_id: int = None
    author_id: int = None
    history: str = None


class CreateProjectUserHistory(BaseModel):
    project_id: int = None
    author_id: int = None
    assigned_user_id: int = None
    role: str = None


class CreateRiskHistory(BaseModel):
    risk_id: int = None
    author_id: int = None
    history: str = None


class CreateWBSHistory(BaseModel):
    wbs_id: int = None
    author_id: int = None
    history: str = None


class CreateWorkflowFlowchartHistory(BaseModel):
    workflow_flowchart_id: int = None
    author_id: int = None
    history: str = None


class CreateCapPoamHistory(BaseModel):
    cap_poam_id: int = None
    author_id: int = None
    history: str = None


class DisplayAuthor(BaseModel):
    email: str = None
    id: int = None

    class Config:
        orm_mode = True


class DisplayObj(BaseModel):
    id: int = None
    name: str = None

    class Config:
        orm_mode = True


class DisplayAssessmentHistory(BaseModel):
    id: int = None
    assessment_id: int = None
    author_id: int = None
    author: DisplayAuthor = None
    assessment: DisplayAssessment = None
    history: str = None
    updated: datetime = None

    class Config:
        orm_mode = True


class DisplayAuditTestHistory(BaseModel):
    id: int
    audit_test_id: int = None
    audit_test: DisplayObj = None
    author_id: int = None
    author: DisplayAuthor = None
    history: str = None
    updated: datetime = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayDocumentHistory(BaseModel):
    id: int = None
    document_id: int = None
    author_id: int = None
    history: str = None
    updated: datetime = None
    author: DisplayAuthor = None
    document: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayExceptionHistory(BaseModel):
    id: int
    exception_id: int = None
    author_id: int = None
    history: str = None
    updated: datetime = None
    author: DisplayAuthor = None
    exception: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayProjectControlHistory(BaseModel):
    id: int
    project_control_id: int = None
    author_id: int = None
    history: str = None
    updated: datetime = None
    author: DisplayAuthor = None
    project_control: DisplayObj = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayProjectEvaluationHistory(BaseModel):
    id: int
    project_evaluation_id: int = None
    author_id: int = None
    history: str = None
    updated: datetime = None
    author: DisplayAuthor = None
    project_evaluation: DisplayObj = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayProjectHistory(BaseModel):
    id: int
    project_id: int = None
    author_id: int = None
    history: str = None
    updated: datetime = None
    author: DisplayAuthor = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayTaskHistory(BaseModel):
    id: int
    task_id: int = None
    author_id: int = None
    history: str = None
    updated: datetime = None
    author: DisplayAuthor = None
    task: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayRiskHistory(BaseModel):
    id: int
    risk_id: int = None
    author_id: int = None
    history: str = None
    updated: datetime = None
    author: DisplayAuthor = None
    risk: DisplayObj = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayWBSHistory(BaseModel):
    id: int
    wbs_id: int = None
    author_id: int = None
    history: str = None
    updated: datetime = None
    author: DisplayAuthor = None
    risk: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayWorkflowFlowchartHistory(BaseModel):
    id: int
    workflow_flowchart_id: int = None
    author_id: int = None
    history: str = None
    updated: datetime = None
    author: DisplayAuthor = None

    class Config:
        orm_mode = True


class DisplayCapPoamHistory(BaseModel):
    id: int
    author_id: int = None
    history: str = None
    updated: datetime = None
    author: DisplayAuthor = None
    cap_poam: DisplayObj = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class CreateProjectUserHistory(BaseModel):
    project_id: int = None
    author_id: int = None
    assigned_user_id: int = None
    role: str = None
    history: str = None

    class Config:
        orm_mode = True


class DisplayProjectUserHistory(BaseModel):
    id: int = None
    project_id: int = None
    author: DisplayAuthor = None
    assigned_user_id: int = None
    role: str = None
    updated: datetime = None
    history: str = None
    # author: DisplayAuthor = None
    assigned: DisplayAuthor = None
    project: DisplayObj = None

    class Config:
        orm_mode = True


class DisplayUserWatching(BaseModel):
    id: int = None
    project_id: int = None
    user_id: int = None
    project_overview: bool = None
    project_controls: bool = None
    project_assessments: bool = None
    project_risks: bool = None
    project_evaluations: bool = None
    project_audit_tests: bool = None
    project_documents: bool = None
    project_users: bool = None
    project_tasks: bool = None
    project_wbs: bool = None
    project_cap_poams: bool = None
    project_workflow_flowcharts: bool = None

    class Config:
        orm_mode = True


class UpdateUserWatching(BaseModel):
    project_id: int
    user_id: int
    project_overview: bool = None
    project_controls: bool = None
    project_assessments: bool = None
    project_risks: bool = None
    project_evaluations: bool = None
    project_audit_tests: bool = None
    project_documents: bool = None
    project_users: bool = None
    project_tasks: bool = None
    project_wbs: bool = None
    project_cap_poams: bool = None
    project_workflow_flowcharts: bool = None

    class Config:
        orm_mode = True


######## ApprovalWorkflowHistory #########

# CreateApprovalWorkflowHistory
class CreateApprovalWorkflowHistory(BaseModel):
    approval_workflow_id: int
    author_id: int
    history: str = None


# UpdateApprovalWorkflowHistory
class UpdateApprovalWorkflowHistory(BaseModel):
    approval_workflow_id: int = None
    author_id: int = None
    history: str = None


# DisplayApprovalWorkflowHistory
class DisplayApprovalWorkflowHistory(BaseModel):
    id: int = None
    approval_workflow_id: int = None
    author_id: int = None
    author: DisplayAuthor = None
    history: str = None
    updated: datetime = None

    class Config:
        orm_mode = True
