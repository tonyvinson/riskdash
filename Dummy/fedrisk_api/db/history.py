import logging

# from sqlalchemy import func, or_
from sqlalchemy.orm import Session

# import json, operator

# import pandas as pd

from sqlalchemy.orm import joinedload

from fedrisk_api.db.models import (
    ApprovalWorkflowHistory,
    AssessmentHistory,
    Assessment,
    ProjectControl,
    AuditTest,
    AuditTestHistory,
    # AssessmentDocument,
    AuditTestDocument,
    CapPoam,
    CapPoamHistory,
    # ExceptionDocument,
    ProjectControlDocument,
    # ProjectEvaluationDocument,
    ProjectDocument,
    RiskDocument,
    # TaskDocument,
    # WBSDocument,
    DocumentHistory,
    Risk,
    ExceptionHistory,
    Exception,
    ProjectControlHistory,
    ProjectEvaluationHistory,
    ProjectEvaluation,
    ProjectHistory,
    TaskHistory,
    Task,
    ProjectUserHistory,
    RiskHistory,
    WBSHistory,
    WBS,
    WorkflowFlowchart,
    WorkflowFlowchartHistory,
    UserWatching,
    Project,
    Control,
    User,
    Document,
)

from fedrisk_api.schema.history import CreateUserWatching, UpdateUserWatching

# from fedrisk_api.utils.utils import filter_by_tenant, ordering_query

LOGGER = logging.getLogger(__name__)

# Assessments
def get_assessment_history_by_id(db: Session, assessment_id: int):
    queryset = (
        db.query(AssessmentHistory).filter(AssessmentHistory.assessment_id == assessment_id).all()
    )
    return queryset


def get_all_assessment_history_by_project_id(db: Session, project_id: int):
    queryset = (
        db.query(AssessmentHistory)
        .join(Assessment, Assessment.id == AssessmentHistory.assessment_id)
        .join(ProjectControl, Assessment.project_control_id == ProjectControl.id)
        .filter(ProjectControl.project_id == project_id)
        .all()
    )
    return queryset


# Audit Tests
def get_audit_test_history_by_id(db: Session, audit_test_id: int):
    queryset = (
        db.query(AuditTestHistory).filter(AuditTestHistory.audit_test_id == audit_test_id).all()
    )
    return queryset


def get_all_audit_test_history_by_project_id(db: Session, project_id: int):
    queryset = (
        db.query(AuditTestHistory)
        .join(AuditTest, AuditTest.id == AuditTestHistory.audit_test_id)
        .filter(AuditTest.project_id == project_id)
        .all()
    )
    histories = []
    project_res = db.query(Project).filter(Project.id == project_id).first()
    new_project = {"id": project_res.id, "name": project_res.name}
    for history in queryset:
        obj = {
            "id": history.id,
            "audit_test_id": history.audit_test_id,
            "author_id": history.author_id,
            "history": history.history,
            "updated": history.updated,
            "author": history.author,
            "audit_test": history.audit_test,
            "project": new_project,
        }
        histories.append(obj)
    return histories


# Cap Poam
def get_cap_poam_history_by_id(db: Session, cap_poam_id: int):
    queryset = db.query(CapPoamHistory).filter(CapPoamHistory.cap_poam_id == cap_poam_id).all()
    return queryset


def get_all_cap_poam_history_by_project_id(db: Session, project_id: int):
    queryset = (
        db.query(CapPoamHistory)
        .join(CapPoam, CapPoam.id == CapPoamHistory.cap_poam_id)
        .filter(CapPoam.project_id == project_id)
        .all()
    )
    histories = []
    project_res = db.query(Project).filter(Project.id == project_id).first()
    new_project = {"id": project_res.id, "name": project_res.name}
    for history in queryset:
        obj = {
            "id": history.id,
            "cap_poam_id": history.cap_poam_id,
            "author_id": history.author_id,
            "history": history.history,
            "updated": history.updated,
            "author": history.author,
            "cap_poam": history.cap_poam,
            "project": new_project,
        }
        histories.append(obj)
    return histories


# Documents
def get_document_history_by_id(db: Session, document_id: int):
    queryset = db.query(DocumentHistory).filter(DocumentHistory.document_id == document_id).all()
    return queryset


def get_all_document_history_by_project_id(db: Session, project_id: int):
    all_history = []
    project_res = db.query(Project).filter(Project.id == project_id).first()
    new_project = {"id": project_res.id, "name": project_res.name}
    audit_test_history = (
        db.query(DocumentHistory, AuditTest, User, Document)
        .join(AuditTestDocument, AuditTestDocument.document_id == DocumentHistory.document_id)
        .join(AuditTest, AuditTest.id == AuditTestDocument.audit_test_id)
        .join(User, DocumentHistory.author_id == User.id)
        .join(Document, DocumentHistory.document_id == Document.id)
        .filter(AuditTest.project_id == project_id)
        .all()
    )
    audit_test_history_w_proj = []
    for history in audit_test_history:
        obj = {
            "id": history.DocumentHistory.id,
            "history": history.DocumentHistory.history,
            "audit_test": {"id": history.AuditTest.id, "name": history.AuditTest.name},
            "author": {
                "id": history.User.id,
                "email": history.User.email,
            },
            "document": {
                "id": history.Document.id,
                "name": history.Document.name,
            },
            "updated": history.DocumentHistory.updated,
            "project": new_project,
        }
        audit_test_history_w_proj.append(obj)

    all_history.append(audit_test_history_w_proj)
    # project
    project_history = (
        db.query(DocumentHistory, Document, User)
        .join(ProjectDocument, ProjectDocument.document_id == DocumentHistory.document_id)
        .join(Document, DocumentHistory.document_id == Document.id)
        .join(User, User.id == DocumentHistory.author_id)
        .filter(ProjectDocument.project_id == project_id)
        .all()
    )
    project_history_w_proj = []
    for history in project_history:
        obj = {
            "id": history.DocumentHistory.id,
            "history": history.DocumentHistory.history,
            "author": {
                "id": history.User.id,
                "email": history.User.email,
            },
            "document": {
                "id": history.Document.id,
                "name": history.Document.name,
            },
            "updated": history.DocumentHistory.updated,
            "project": new_project,
        }
        project_history_w_proj.append(obj)

    all_history.append(project_history_w_proj)
    # project control
    project_control_history = (
        db.query(DocumentHistory, ProjectControl, User, Control, Document)
        .join(
            ProjectControlDocument,
            ProjectControlDocument.document_id == DocumentHistory.document_id,
        )
        .join(ProjectControl, ProjectControlDocument.project_control_id == ProjectControl.id)
        .join(Control, ProjectControl.control_id == Control.id)
        .join(User, DocumentHistory.author_id == User.id)
        .join(Document, Document.id == DocumentHistory.document_id)
        .filter(ProjectControl.project_id == project_id)
        .all()
    )
    project_control_history_w_proj = []
    for history in project_control_history:
        obj = {
            "id": history.DocumentHistory.id,
            "history": history.DocumentHistory.history,
            "project_control": {"id": history.ProjectControl.id, "name": history.Control.name},
            "author": {
                "id": history.User.id,
                "email": history.User.email,
            },
            "document": {
                "id": history.Document.id,
                "name": history.Document.name,
            },
            "updated": history.DocumentHistory.updated,
            "project": new_project,
        }
        project_control_history_w_proj.append(obj)

    all_history.append(project_control_history_w_proj)
    # risk
    risk_history = (
        db.query(DocumentHistory, Document, User, Risk)
        .join(RiskDocument, RiskDocument.document_id == DocumentHistory.document_id)
        .join(Risk, Risk.id == RiskDocument.risk_id)
        .join(Document, Document.id == DocumentHistory.document_id)
        .join(User, User.id == DocumentHistory.author_id)
        .filter(Risk.project_id == project_id)
        .all()
    )
    risk_history_w_proj = []
    for history in risk_history:
        obj = {
            "id": history.DocumentHistory.id,
            "history": history.DocumentHistory.history,
            "risk": {"id": history.Risk.id, "name": history.Risk.name},
            "author": {
                "id": history.User.id,
                "email": history.User.email,
            },
            "document": {
                "id": history.Document.id,
                "name": history.Document.name,
            },
            "updated": history.DocumentHistory.updated,
            "project": new_project,
        }
        risk_history_w_proj.append(obj)

    all_history.append(risk_history_w_proj)
    return all_history


# Exceptions
def get_exception_history_by_id(db: Session, exception_id: int):
    queryset = (
        db.query(ExceptionHistory).filter(ExceptionHistory.exception_id == exception_id).all()
    )
    return queryset


def get_all_exception_history_by_project_id(db: Session, project_id: int):
    queryset = (
        db.query(ExceptionHistory)
        .join(Exception, Exception.id == ExceptionHistory.exception_id)
        .join(ProjectControl, Exception.project_control_id == ProjectControl.id)
        .filter(ProjectControl.project_id == project_id)
        .all()
    )
    return queryset


# Project Controls
def get_project_control_history_by_id(db: Session, project_control_id: int):
    queryset = (
        db.query(ProjectControlHistory)
        .filter(ProjectControlHistory.project_control_id == project_control_id)
        .all()
    )
    return queryset


def get_all_project_control_history_by_project_id(db: Session, project_id: int):
    history = (
        db.query(ProjectControlHistory)
        .join(
            ProjectControl, ProjectControlHistory.project_control_id == ProjectControl.id
        )  # Ensure the relationship is joined
        .options(
            joinedload(ProjectControlHistory.project_control).joinedload(ProjectControl.project)
        )
        .filter(ProjectControl.project_id == project_id)  # Now this works properly
        .all()
    )
    project_control_histories = []
    project_res = db.query(Project).filter(Project.id == project_id).first()
    new_project = {"id": project_res.id, "name": project_res.name}
    for hist in history:
        control = (
            db.query(Control)
            .join(ProjectControl, ProjectControl.control_id == Control.id)
            .filter(ProjectControl.id == hist.project_control_id)
            .first()
        )

        new_proj_control = {"id": hist.project_control_id, "name": control.name}
        new_history = {
            "id": hist.id,
            "project_control_id": hist.project_control_id,
            "author_id": hist.author_id,
            "history": hist.history,
            "updated": hist.updated,
            "author": hist.author,
            "project_control": new_proj_control,
            "project": new_project,
        }
        project_control_histories.append(new_history)
    return project_control_histories


# Project Evaluations
def get_project_evaluation_history_by_id(db: Session, project_evaluation_id: int):
    queryset = (
        db.query(ProjectEvaluationHistory)
        .filter(ProjectEvaluationHistory.project_evaluation_id == project_evaluation_id)
        .all()
    )
    return queryset


def get_all_project_evaluation_history_by_project_id(db: Session, project_id: int):
    project_eval_history = (
        db.query(ProjectEvaluationHistory)
        .join(
            ProjectEvaluation,
            ProjectEvaluation.id == ProjectEvaluationHistory.project_evaluation_id,
        )
        .filter(ProjectEvaluation.project_id == project_id)
        .all()
    )
    project_eval_histories = []
    project_res = db.query(Project).filter(Project.id == project_id).first()
    new_project = {"id": project_res.id, "name": project_res.name}
    for history in project_eval_history:
        eval_obj = {
            "id": history.id,
            "project_evaluation_id": history.project_evaluation_id,
            "author_id": history.author_id,
            "history": history.history,
            "updated": history.updated,
            "author": history.author,
            "project_evaluation": history.project_evaluation,
            "project": new_project,
        }
        project_eval_histories.append(eval_obj)
    return project_eval_histories


# Projects
def get_project_history_by_id(db: Session, id: int):
    queryset = db.query(ProjectHistory).filter(ProjectHistory.id == id).all()
    return queryset


def get_all_project_history_by_project_id(db: Session, project_id: int):
    queryset = db.query(ProjectHistory).filter(ProjectHistory.project_id == project_id).all()
    return queryset


# Tasks
def get_task_history_by_id(db: Session, task_id: int):
    queryset = db.query(TaskHistory).filter(TaskHistory.task_id == task_id).all()
    return queryset


def get_all_task_history_by_project_id(db: Session, project_id: int):
    queryset = (
        db.query(TaskHistory)
        .join(Task, Task.id == TaskHistory.task_id)
        .filter(Task.project_id == project_id)
        .all()
    )
    return queryset


# Project Users
def get_all_project_user_history_by_project_id(db: Session, project_id: int):
    project_users = (
        db.query(ProjectUserHistory, User, Project)
        .join(User, ProjectUserHistory.author_id == User.id)
        .join(Project, Project.id == project_id)
        .filter(ProjectUserHistory.project_id == project_id)
        .all()
    )
    all_proj_users = []
    for proj_user in project_users:
        assigned = (
            db.query(User).filter(User.id == proj_user.ProjectUserHistory.assigned_user_id).first()
        )
        obj = {
            "id": proj_user.ProjectUserHistory.id,
            "project_id": proj_user.ProjectUserHistory.project_id,
            "author": proj_user.User,
            "assigned_user_id": proj_user.ProjectUserHistory.assigned_user_id,
            "assigned": assigned,
            "role": proj_user.ProjectUserHistory.role,
            "updated": proj_user.ProjectUserHistory.updated,
            "history": proj_user.ProjectUserHistory.history,
            "project": {
                "id": proj_user.Project.id,
                "name": proj_user.Project.name,
            },
        }
        all_proj_users.append(obj)
    return all_proj_users


# Risks
def get_risk_history_by_id(db: Session, risk_id: int):
    queryset = db.query(RiskHistory).filter(RiskHistory.risk_id == risk_id).all()
    return queryset


def get_all_risk_history_by_project_id(db: Session, project_id: int):
    risk_histories = []
    risk_history = (
        db.query(RiskHistory)
        .join(Risk, Risk.id == RiskHistory.risk_id)
        .filter(Risk.project_id == project_id)
        .all()
    )

    project_res = db.query(Project).filter(Project.id == project_id).first()
    new_project = {"id": project_res.id, "name": project_res.name}
    for history in risk_history:
        risk_obj = {
            "id": history.id,
            "risk_id": history.risk_id,
            "author_id": history.author_id,
            "history": history.history,
            "updated": history.updated,
            "author": history.author,
            "risk": history.risk,
            "project": new_project,
        }
        risk_histories.append(risk_obj)
    return risk_histories


# WBS
def get_wbs_history_by_id(db: Session, wbs_id: int):
    queryset = db.query(WBSHistory).filter(WBSHistory.wbs_id == wbs_id).all()
    return queryset


def get_all_wbs_history_by_project_id(db: Session, project_id: int):
    queryset = (
        db.query(WBSHistory)
        .join(WBS, WBS.id == WBSHistory.wbs_id)
        .filter(WBS.project_id == project_id)
        .all()
    )
    return queryset


# WorkflowFlowchart
def get_workflow_flowchart_history_by_id(db: Session, workflow_flowchart_id: int):
    queryset = (
        db.query(WorkflowFlowchartHistory)
        .filter(WorkflowFlowchartHistory.workflow_flowchart_id == workflow_flowchart_id)
        .all()
    )
    return queryset


def get_all_workflow_flowchart_history_by_project_id(db: Session, project_id: int):
    queryset = (
        db.query(WorkflowFlowchartHistory)
        .join(
            WorkflowFlowchart,
            WorkflowFlowchart.id == WorkflowFlowchartHistory.workflow_flowchart_id,
        )
        .filter(WorkflowFlowchart.project_id == project_id)
        .all()
    )
    return queryset


# ApprovalWorkflow
def get_approval_workflow_history_by_id(db: Session, approval_workflow_id: int):
    queryset = (
        db.query(ApprovalWorkflowHistory)
        .filter(ApprovalWorkflowHistory.approval_workflow_id == approval_workflow_id)
        .all()
    )
    LOGGER.info(queryset)
    return queryset


# Create user watching
def create_user_watching(request: CreateUserWatching, db: Session):
    new_user_watching = UserWatching(**request.dict())
    db.add(new_user_watching)
    db.commit()
    db.refresh(new_user_watching)
    return new_user_watching


# Get user watching by project id
def get_user_watching_by_project_id(db: Session, project_id: int):
    queryset = db.query(UserWatching).filter(UserWatching.project_id == project_id).first()
    return queryset


def get_all_projects_user_is_watching(db: Session, user_id: int):
    user_projects = db.query(UserWatching).filter(UserWatching.user_id == user_id).all()
    return user_projects


# update user watching
def update_user_watching_by_project_id(db: Session, project_id: int, request: UpdateUserWatching):
    existing_user_watching = db.query(UserWatching).filter(UserWatching.project_id == project_id)
    if not existing_user_watching.first():
        return False
    existing_user_watching.update(request.dict(exclude_unset=True))
    db.commit()
    return existing_user_watching.first()
