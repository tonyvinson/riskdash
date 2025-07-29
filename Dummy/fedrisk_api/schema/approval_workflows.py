from datetime import date, datetime

from pydantic import BaseModel, root_validator
from typing import Optional, List

from fedrisk_api.db.util.encrypt_pii_utils import decrypt_value

from fedrisk_api.schema.digital_signature import DisplayDigitalSignature


######## Re-Usable Objects #########
# DisplayUser
class DisplayUser(BaseModel):
    id: int
    email: str
    first_name: str = None
    last_name: str = None

    @root_validator(pre=True)
    def decrypt_all_encrypted_fields(cls, values):
        # Force values into a real dictionary
        real_values = dict(values)

        for field, value in real_values.items():
            if isinstance(value, str) and value.startswith("ENC::"):
                real_values[field] = decrypt_value(value[5:])

        return real_values

    class Config:
        orm_mode = True


# DisplayApproval
class DisplayApprovalUser(BaseModel):
    id: int
    user_id: int
    # approval_digital_signature: DisplayDigitalSignature = None
    # user: DisplayUser = None

    class Config:
        orm_mode = True


# DisplayObject
class DisplayObject(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


######## ApprovalWorkflowMappings #########
# DisplayTaskMapping
class DisplayTaskMapping(BaseModel):
    id: int
    task_id: int
    task: DisplayObject = None

    class Config:
        orm_mode = True


# DisplayRiskMapping
class DisplayRiskMapping(BaseModel):
    id: int
    risk_id: int
    risk: DisplayObject = None

    class Config:
        orm_mode = True


# DisplayAuditTestMapping
class DisplayAuditTestMapping(BaseModel):
    id: int
    audit_test_id: int
    audit_test: DisplayObject = None

    class Config:
        orm_mode = True


# DisplayAssessmentMapping
class DisplayAssessmentMapping(BaseModel):
    id: int
    assessment_id: int
    assessment: DisplayObject = None

    class Config:
        orm_mode = True


# DisplayExceptionMapping
class DisplayExceptionMapping(BaseModel):
    id: int
    exception_id: int
    exception: DisplayObject = None

    class Config:
        orm_mode = True


# DisplayProjectControlMapping
class DisplayProjectControlMapping(BaseModel):
    id: int
    project_control_id: int
    project_control: DisplayObject = None

    class Config:
        orm_mode = True


# DisplayProjectMapping
class DisplayProjectMapping(BaseModel):
    id: int
    project_id: int
    project: DisplayObject = None

    class Config:
        orm_mode = True


# DisplayWBSMapping
class DisplayWBSMapping(BaseModel):
    id: int
    wbs_id: int
    wbs: DisplayObject = None

    class Config:
        orm_mode = True


# DisplayWorkflowFlowchartMapping
class DisplayWorkflowFlowchartMapping(BaseModel):
    id: int
    workflow_flowchart_id: int
    workflow_flowchart: DisplayObject = None

    class Config:
        orm_mode = True


# DisplayCapPoamMapping
class DisplayCapPoamMapping(BaseModel):
    id: int
    cap_poam_id: int
    cap_poam: DisplayObject = None

    class Config:
        orm_mode = True


# DisplayDocumentMapping
class DisplayDocumentMapping(BaseModel):
    id: int
    document_id: int
    document: DisplayObject = None

    class Config:
        orm_mode = True


# DisplayProjectEvaluationMapping
class DisplayProjectEvaluationMapping(BaseModel):
    id: int
    project_evaluation_id: int
    project_evaluation: DisplayObject = None

    class Config:
        orm_mode = True


######## ApprovalWorkflowTemplate #########


# CreateApprovalWorkflowTemplate
class CreateApprovalWorkflowTemplate(BaseModel):
    name: str
    description: str
    approvals: Optional[List] = None  # Allow list
    stakeholders: Optional[List] = None
    due_date: Optional[date]
    is_private: Optional[bool]
    owner_id: Optional[int]


# UpdateApprovalWorkflowTemplate
class UpdateApprovalWorkflowTemplate(BaseModel):
    name: Optional[str]
    description: Optional[str]
    approvals: Optional[List] = None  # Allow list
    stakeholders: Optional[List] = None
    due_date: Optional[date]
    is_private: Optional[bool]
    digital_signature: Optional[bool]
    owner_id: Optional[int]


# DisplayApprovalWorkflowTemplate
class DisplayApprovalWorkflowTemplate(BaseModel):
    id: str
    name: str
    description: str = None
    approvals: Optional[List] = None
    stakeholders: Optional[List] = None
    due_date: Optional[date]
    is_private: Optional[bool]
    digital_signature: Optional[bool]
    owner_id: Optional[int]

    class Config:
        orm_mode = True


######## ApprovalWorkflow #########


class CreateApprovalWorkflowUseTemplate(BaseModel):
    object_id: int = None
    data_type: str = None
    template_id: int = None


# CreateApprovalWorkflow
class CreateApprovalWorkflow(BaseModel):
    name: str
    description: str
    status: str = None
    due_date: Optional[date]
    is_private: Optional[bool]
    owner_id: Optional[int]
    digital_signature: Optional[bool]


# UpdateApprovalWorkflow
class UpdateApprovalWorkflow(BaseModel):
    name: str = None
    description: str = None
    status: str = None
    due_date: Optional[date]
    is_private: Optional[bool]
    owner_id: Optional[int]
    digital_signature: bool = None


# DisplayApprovalWorkflow
class DisplayApprovalWorkflow(BaseModel):
    id: str
    name: str
    description: str = None
    status: str = None
    due_date: Optional[date]
    is_private: Optional[bool]
    digital_signature: bool = None
    owner_id: Optional[int]
    owner: DisplayUser = None
    approvals: List[DisplayApprovalUser] = None
    approval_stakeholders: List[DisplayApprovalUser] = None
    tasks: List[DisplayTaskMapping] = None
    risks: List[DisplayRiskMapping] = None
    audit_tests: List[DisplayAuditTestMapping] = None
    assessments: List[DisplayAssessmentMapping] = None
    exceptions: List[DisplayExceptionMapping] = None
    project_controls: List[DisplayProjectControlMapping] = None
    project_evaluations: List[DisplayProjectEvaluationMapping] = None
    projects: List[DisplayProjectMapping] = None
    wbss: List[DisplayWBSMapping] = None
    workflow_flowcharts: List[DisplayWorkflowFlowchartMapping] = None
    cap_poams: List[DisplayCapPoamMapping] = None
    documents: List[DisplayDocumentMapping] = None

    class Config:
        orm_mode = True


######## Approval #########


# CreateApproval
class CreateApproval(BaseModel):
    approval_workflow_id: int
    user_id: int
    status: str = None
    weight: int = None
    completed_date: date = None


# UpdateApproval
class UpdateApproval(BaseModel):
    approval_workflow_id: int
    user_id: int = None
    status: str = None
    weight: int = None
    completed_date: date = None


# ApprovalDigitalSignature
class ApprovalDigitalSignature(BaseModel):
    id: str = None
    approval_id: int = None
    digital_signature_id: int = None
    created_date: date = None
    digital_signature: DisplayDigitalSignature = None

    class Config:
        orm_mode = True


# DisplayApproval
class DisplayApproval(BaseModel):
    id: str = None
    approval_workflow_id: int = None
    user_id: int = None
    user: DisplayUser = None
    status: str = None
    weight: int = None
    completed_date: datetime = None
    approval_digital_signature: ApprovalDigitalSignature = None  # <--- fix here

    class Config:
        orm_mode = True


######## ApprovalStakeholder #########


# CreateApprovalStakeholder
class CreateApprovalStakeholder(BaseModel):
    approval_workflow_id: int
    user_id: int


# UpdateApprovalStakeholder
class UpdateApprovalStakeholder(BaseModel):
    approval_workflow_id: int
    user_id: int = None


# DisplayApprovalStakeholder
class DisplayApprovalStakeholder(BaseModel):
    id: str
    approval_workflow_id: int
    user_id: int
    user: DisplayUser

    class Config:
        orm_mode = True


######## TaskApproval #########


# CreateTaskApproval
class CreateTaskApproval(BaseModel):
    task_id: int
    approval_workflow_id: int


# UpdateTaskApproval
class UpdateTaskApproval(BaseModel):
    task_id: int = None
    approval_workflow_id: int = None


# DisplayTaskApproval
class DisplayTaskApproval(BaseModel):
    id: str
    task_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True


######## RiskApproval #########


# CreateRiskApproval
class CreateRiskApproval(BaseModel):
    risk_id: int
    approval_workflow_id: int


# UpdateRiskApproval
class UpdateRiskApproval(BaseModel):
    risk_id: int = None
    approval_workflow_id: int = None


# DisplayRiskApproval
class DisplayRiskApproval(BaseModel):
    id: str
    risk_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True


######## AuditTestApproval #########


# CreateAuditTestApproval
class CreateAuditTestApproval(BaseModel):
    audit_test_id: int
    approval_workflow_id: int


# UpdateAuditTestApproval
class UpdateAuditTestApproval(BaseModel):
    audit_test_id: int = None
    approval_workflow_id: int = None


# DisplayAuditTestApproval
class DisplayAuditTestApproval(BaseModel):
    id: str
    audit_test_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True


######## ProjectEvaluationApproval #########


# CreateProjectEvaluationApproval
class CreateProjectEvaluationApproval(BaseModel):
    project_evaluation_id: int
    approval_workflow_id: int


# UpdateProjectEvaluationApproval
class UpdateProjectEvaluationApproval(BaseModel):
    project_evaluation_id: int = None
    approval_workflow_id: int = None


# DisplayProjectEvaluationApproval
class DisplayProjectEvaluationApproval(BaseModel):
    id: str
    project_evaluation_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True


######## AssessmentApproval #########


# CreateAssessmentApproval
class CreateAssessmentApproval(BaseModel):
    assessment_id: int
    approval_workflow_id: int


# UpdateAssessmentApproval
class UpdateAssessmentApproval(BaseModel):
    assessment_id: int = None
    approval_workflow_id: int = None


# DisplayAssessmentApproval
class DisplayAssessmentApproval(BaseModel):
    id: str
    assessment_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True


######## ExceptionApproval #########


# CreateExceptionApproval
class CreateExceptionApproval(BaseModel):
    exception_id: int
    approval_workflow_id: int


# UpdateExceptionApproval
class UpdateExceptionApproval(BaseModel):
    exception_id: int = None
    approval_workflow_id: int = None


# DisplayExceptionApproval
class DisplayExceptionApproval(BaseModel):
    id: str
    exception_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True


######## DocumentApproval #########


# CreateDocumentApproval
class CreateDocumentApproval(BaseModel):
    document_id: int
    approval_workflow_id: int


# UpdateDocumentApproval
class UpdateDocumentApproval(BaseModel):
    document_id: int = None
    approval_workflow_id: int = None


# DisplayDocumentApproval
class DisplayDocumentApproval(BaseModel):
    id: str
    document_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True


######## CapPoamApproval #########


# CreateCapPoamApproval
class CreateCapPoamApproval(BaseModel):
    cap_poam_id: int
    approval_workflow_id: int


# UpdateCapPoamApproval
class UpdateCapPoamApproval(BaseModel):
    cap_poam_id: int = None
    approval_workflow_id: int = None


# DisplayCapPoamApproval
class DisplayCapPoamApproval(BaseModel):
    id: str
    cap_poam_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True


######## WBSApproval #########


# CreateWBSApproval
class CreateWBSApproval(BaseModel):
    wbs_id: int
    approval_workflow_id: int


# UpdateWBSApproval
class UpdateWBSApproval(BaseModel):
    wbs_id: int = None
    approval_workflow_id: int = None


# DisplayWBSApproval
class DisplayWBSApproval(BaseModel):
    id: str
    wbs_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True


######## WorkflowFlowchartApproval #########


# CreateWorkflowFlowchartApproval
class CreateWorkflowFlowchartApproval(BaseModel):
    workflow_flowchart_id: int
    approval_workflow_id: int


# UpdateWorkflowFlowchartApproval
class UpdateWorkflowFlowchartApproval(BaseModel):
    workflow_flowchart_id: int = None
    approval_workflow_id: int = None


# DisplayWorkflowFlowchartApproval
class DisplayWorkflowFlowchartApproval(BaseModel):
    id: str
    workflow_flowchart_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True


######## ProjectApproval #########


# CreateProjectApproval
class CreateProjectApproval(BaseModel):
    project_id: int
    approval_workflow_id: int


# UpdateProjectApproval
class UpdateProjectApproval(BaseModel):
    project_id: int = None
    approval_workflow_id: int = None


# DisplayProjectApproval
class DisplayProjectApproval(BaseModel):
    id: str
    project_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True


######## ProjectControlApproval #########


# CreateProjectControlApproval
class CreateProjectControlApproval(BaseModel):
    project_control_id: int
    approval_workflow_id: int


# UpdateProjectControlApproval
class UpdateProjectControlApproval(BaseModel):
    project_control_id: int = None
    approval_workflow_id: int = None


# DisplayProjectControlApproval
class DisplayProjectControlApproval(BaseModel):
    id: str
    project_control_id: int = None
    approval_workflow_id: int = None

    class Config:
        orm_mode = True
