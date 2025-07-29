import logging
from fastapi import status
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import Session

from fastapi import HTTPException, status

from fedrisk_api.db.models import (
    AppProject,
    AppProjectControl,
    Assessment,
    AssessmentApprovalWorkflow,
    AssessmentCost,
    AssessmentDocument,
    AssessmentHistory,
    AssessmentInstance,
    AuditTest,
    AuditTestApprovalWorkflow,
    AuditTestCost,
    AuditTestInstance,
    AuditTestStakeHolder,
    AuditTestHistory,
    AuditTestDocument,
    AWSControl,
    AWSControlProjectControl,
    CapPoam,
    CapPoamApprovalWorkflow,
    CapPoamCost,
    CapPoamHistory,
    CapPoamStakeHolder,
    CapPoamProjectControl,
    CapPoamTask,
    Control,
    ControlFrameworkVersion,
    Cost,
    DocumentApprovalWorkflow,
    Framework,
    FrameworkVersion,
    # ControlClass,
    # ControlFamily,
    # ControlPhase,
    # ControlStatus,
    Document,
    DocumentHistory,
    Evidence,
    Exception,
    ExceptionStakeholder,
    ExceptionDocument,
    ExceptionHistory,
    ExceptionApprovalWorkflow,
    ExceptionCost,
    ExceptionReview,
    FeatureProject,
    ImportTask,
    KeywordMapping,
    Permission,
    PermissionRole,
    Project,
    ProjectApprovalWorkflow,
    ProjectControl,
    ProjectControlApprovalWorkflow,
    ProjectControlCost,
    ProjectControlDocument,
    ProjectCost,
    ProjectEvaluation,
    ProjectEvaluationApprovalWorkflow,
    ProjectEvaluationCost,
    ProjectEvaluationDocument,
    ProjectControlEvidence,
    ProjectGroup,
    ProjectUser,
    ProjectTaskHistory,
    RiskApprovalWorkflow,
    RiskStakeholder,
    Risk,
    RiskCost,
    RiskDocument,
    RiskHistory,
    Role,
    SurveyModel,
    Task,
    TaskApprovalWorkflow,
    TaskAuditTest,
    TaskChild,
    TaskCost,
    TaskRisk,
    TaskHistory,
    TaskResource,
    TaskLink,
    TaskDocument,
    TaskStakeholder,
    User,
    TaskProjectControl,
    ProjectControlDocument,
    ProjectControlHistory,
    Keyword,
    KeywordMapping,
    ProjectDocument,
    AssessmentHistory,
    ProjectHistory,
    ProjectEvaluationHistory,
    ProjectUserHistory,
    ServiceProviderProjectControl,
    ServiceProviderProject,
    UserNotifications,
    UserWatching,
    # UserNotificationSettings,
    WorkflowFlowchart,
    WorkflowTaskMapping,
    WBS,
    WBSApprovalWorkflow,
    WBSCost,
    WBSHistory,
    WBSDocument,
)
from fedrisk_api.schema.project import (
    AddProjectsUsers,
    AddProjectUsers,
    AddProjectControls,
    ChangeProjectUserRole,
    CreateProject,
    UpdateProject,
    CreateProjectControl,
    UpdateProjectControl,
)
from fedrisk_api.utils.utils import filter_by_tenant, ordering_query

# from fedrisk_api.utils.email_util import send_watch_email

# from fedrisk_api.utils.sms_util import publish_notification

from fedrisk_api.schema.assessment import CreateAssessment

from fedrisk_api.db.assessment import create_assessment

from fedrisk_api.db.util.notifications_utils import (
    # notify_user,
    # add_notification,
    manage_notifications,
)

LOGGER = logging.getLogger(__name__)

NO_SUCH_PROJECT = -1
NO_SUCH_CONTROL = -2
PROJECT_CONTROL_ALREADY_EXISTS = -3
NO_SUCH_PROJECT_CONTROL = -4
NO_SUCH_CONTROL_FAMILY = -5
NO_SUCH_CONTROL_CLASS = -6
NO_SUCH_CONTROL_PHASE = -7
NO_SUCH_CONTROL_STATUS = -8

PROJECT_ADMIN_ROLE = "PROJECT_MANAGER"


# Keyword Management Functions
async def add_keywords(db, keywords, project_id, tenant_id):
    """Link keywords to project."""
    if not keywords:
        return
    keyword_names = set(keywords.split(","))
    for name in keyword_names:
        if name != "":
            keyword = db.query(Keyword).filter_by(tenant_id=tenant_id, name=name).first()
            if not keyword:
                keyword = Keyword(name=name, tenant_id=tenant_id)
                db.add(keyword)
                db.commit()
            if (
                not db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, project_id=project_id)
                .first()
            ):
                db.add(KeywordMapping(keyword_id=keyword.id, project_id=project_id))
    db.commit()


async def remove_old_keywords(db, keywords, project_id):
    """Remove keywords from project that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(project_id=project_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = (
        db.query(Keyword).join(KeywordMapping).filter_by(project_id=project_id).all()
    )

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, project_id=project_id)
                .first()
            )
            db.delete(mapping)
    db.commit()


async def add_pc_keywords(db, keywords, project_control_id, tenant_id):
    """Link keywords to project control."""
    if not keywords:
        return
    keyword_names = set(keywords.split(","))
    for name in keyword_names:
        if name != "":
            keyword = db.query(Keyword).filter_by(tenant_id=tenant_id, name=name).first()
            if not keyword:
                keyword = Keyword(name=name, tenant_id=tenant_id)
                db.add(keyword)
                db.commit()
            if (
                not db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, project_control_id=project_control_id)
                .first()
            ):
                db.add(KeywordMapping(keyword_id=keyword.id, project_control_id=project_control_id))
    db.commit()


async def remove_old_pc_keywords(db, keywords, project_control_id):
    """Remove keywords from project control that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(project_control_id=project_control_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = (
        db.query(Keyword)
        .join(KeywordMapping)
        .filter_by(project_control_id=project_control_id)
        .all()
    )

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, project_control_id=project_control_id)
                .first()
            )
            db.delete(mapping)
    db.commit()


async def create_project(
    db: Session, project: CreateProject, tenant_id: int, keywords: str, user_id: int
):
    new_project = Project(**project.dict(), tenant_id=tenant_id)
    db.add(new_project)
    db.flush()
    db.refresh(new_project)
    # Add history
    history = {
        "project_id": new_project.id,
        "author_id": user_id,
        "history": f"Created new project {new_project.name}",
    }
    new_history = ProjectHistory(**history)
    db.add(new_history)
    db.commit()
    project_admin_id = project.dict().get("project_admin_id", None)
    if project_admin_id:
        role = db.query(Role).filter(Role.name == PROJECT_ADMIN_ROLE).first()
        project_user = ProjectUser(
            project_id=new_project.id, user_id=project_admin_id, role_id=role.id
        )
        db.add(project_user)
    # add keywords
    await add_keywords(db, keywords, new_project.id, tenant_id)
    db.commit()
    return new_project


def get_all_projects(
    db: Session,
    tenant_id: int,
    user_id: int,
    q: str,
    filter_by: str,
    filter_value: str,
    sort_by: str,
):
    user = db.query(User).filter(User.id == user_id).first()

    if user.system_role == 4:
        queryset = db.query(Project)

    elif user.system_role == 1:
        queryset = filter_by_tenant(db, Project, tenant_id)
    else:
        queryset = (
            filter_by_tenant(db, Project, tenant_id)
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .filter(ProjectUser.user_id == user_id)
        )

    queryset = queryset.options(
        selectinload(Project.project_controls)
        .selectinload(ProjectControl.control)
        .selectinload(Control.framework_versions),
        selectinload(Project.project_controls).selectinload(ProjectControl.assessment),
        selectinload(Project.project_controls)
        .selectinload(ProjectControl.exception)
        .selectinload(Exception.owner),
        selectinload(Project.project_controls)
        .selectinload(ProjectControl.exception)
        .selectinload(Exception.stakeholders),
        selectinload(Project.project_evaluations),
        selectinload(Project.risks),
        selectinload(Project.documents),
        selectinload(Project.audit_tests),
        selectinload(Project.project_group),
        selectinload(Project.project_admin),
    )
    if filter_by and filter_value:
        if filter_by in ("name", "description"):
            queryset = queryset.filter(
                func.lower(getattr(Project, filter_by)).contains(func.lower(filter_value))
            )
        elif filter_by in ("project_group",):
            queryset = queryset.join(
                ProjectGroup, Project.project_group_id == ProjectGroup.id
            ).filter(ProjectGroup.id == filter_value)
        else:
            queryset = queryset.filter(getattr(Project, filter_by) == filter_value)

    if sort_by:
        queryset = ordering_query(query=queryset, model=Project.__tablename__, order=sort_by)

    if q:
        queryset = queryset.filter(
            or_(
                func.lower(Project.name).contains(func.lower(q)),
                func.lower(Project.description).contains(func.lower(q)),
            )
        )

    return queryset.distinct()


async def get_project(db: Session, id: int, tenant_id: int, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if user.system_role == 1 or user.system_role == 4:
        queryset = filter_by_tenant(db, Project, tenant_id)
    else:
        queryset = (
            filter_by_tenant(db, Project, tenant_id)
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .filter(ProjectUser.user_id == user_id)
        )

    queryset = queryset.options(
        selectinload(Project.project_controls).selectinload(ProjectControl.control),
        # .selectinload(Control.framework_version),
        selectinload(Project.project_controls).selectinload(ProjectControl.assessment),
        selectinload(Project.project_controls)
        .selectinload(ProjectControl.exception)
        .selectinload(Exception.owner),
        selectinload(Project.project_controls)
        .selectinload(ProjectControl.exception)
        .selectinload(Exception.stakeholders),
        selectinload(Project.project_evaluations),
        selectinload(Project.risks),
        selectinload(Project.documents),
        selectinload(Project.audit_tests),
        selectinload(Project.project_group),
        selectinload(Project.project_admin),
    )
    return queryset.filter(Project.id == id).first()


def get_all_tenant_projects(db: Session, tenant_id: int):
    return filter_by_tenant(db, Project, tenant_id).all()


async def update_project(
    db: Session, id: int, project: UpdateProject, tenant_id: int, keywords: str, user_id: int
):
    existing_project = filter_by_tenant(db, Project, tenant_id).filter(Project.id == id)
    if not existing_project.first():
        return False
    # Get all users watching project overview for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_overview == True)
        .filter(UserWatching.project_id == existing_project.first().id)
        .all()
    )
    link = f"/projects/{id}"
    # send notifications
    changes = []
    for field in [
        "name",
        "description",
        "project_group_id",
        "project_admin_id",
        "status",
    ]:
        if (
            getattr(existing_project.first(), field) != getattr(project, field, None)
            and getattr(project, field, None) != None
        ):
            changes.append(f"Updated {field.replace('_', ' ')} to {getattr(project, field, None)}")
    all_changes = ".    ".join(changes)
    if all_changes != "":
        await manage_notifications(
            db,
            users_watching,
            "projects",
            all_changes,
            link,
            existing_project.first().id,
            existing_project.first().id,
        )
        # post history
        for change in changes:
            db.add(
                ProjectHistory(
                    project_id=existing_project.first().id, author_id=user_id, history=change
                )
            )
    project_dict = project.dict(exclude_unset=True)
    # Update costs
    cost_ids = project_dict.pop("cost_ids", None)
    if cost_ids is not None or []:
        # add costs
        for cost in cost_ids:
            # check if cost id exists on tenant
            existing_cost = db.query(Cost).filter(Cost.tenant_id == tenant_id).first()
            # if the cost exists
            if existing_cost is not None:
                new_cost_map = ProjectCost(project_id=id, cost_id=cost)
                try:
                    db.add(new_cost_map)
                    db.commit()
                except:
                    LOGGER.error("Could not add cost with this ID")
    existing_project.update(project_dict)

    # remove keywords not included
    await remove_old_keywords(db, keywords, id)
    # add keywords
    await add_keywords(db, keywords, id, tenant_id)

    db.commit()
    return True


async def delete_project(db: Session, id: int, tenant_id: int):
    existing_project = filter_by_tenant(db, Project, tenant_id).filter(Project.id == id)
    if not existing_project.first():
        return False
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.project_id == id).delete()
    # delete all history references
    db.query(ProjectHistory).filter(ProjectHistory.project_id == id).delete()
    # delete all document references
    db.query(ProjectDocument).filter(ProjectDocument.project_id == id).delete()
    users = db.query(ProjectUser).filter(ProjectUser.project_id == existing_project.first().id)
    users.delete()
    db.commit()
    # App Project
    db.query(AppProject).filter(AppProject.project_id == id).delete()
    # Service Provider Project
    db.query(ServiceProviderProject).filter(ServiceProviderProject.project_id == id).delete()
    db.commit()
    cap_poams = db.query(CapPoam).filter(CapPoam.project_id == existing_project.first().id)
    for cappoam in cap_poams:
        db.query(CapPoamHistory).filter(CapPoamHistory.cap_poam_id == cappoam.id).delete()
        db.query(CapPoamStakeHolder).filter(CapPoamStakeHolder.cap_poam_id == cappoam.id).delete()
        db.query(CapPoamProjectControl).filter(
            CapPoamProjectControl.cap_poam_id == cappoam.id
        ).delete()
        db.query(CapPoamTask).filter(CapPoamTask.cap_poam_id == cappoam.id).delete()
        db.query(CapPoamApprovalWorkflow).filter(
            CapPoamApprovalWorkflow.cap_poam_id == cappoam.id
        ).delete()
        db.query(CapPoamCost).filter(CapPoamCost.cap_poam_id == cappoam.id).delete()
    cap_poams.delete()
    db.commit()
    risks = db.query(Risk).filter(Risk.project_id == existing_project.first().id)
    for risk in risks:
        db.query(RiskStakeholder).filter(RiskStakeholder.risk_id == risk.id).delete()
        db.query(RiskDocument).filter(RiskDocument.risk_id == risk.id).delete()
        db.query(TaskRisk).filter(TaskRisk.risk_id == risk.id).delete()
        db.query(RiskHistory).filter(RiskHistory.risk_id == risk.id).delete()
        db.query(KeywordMapping).filter(KeywordMapping.risk_id == risk.id).delete()
        db.query(RiskApprovalWorkflow).filter(RiskApprovalWorkflow.risk_id == risk.id).delete()
        db.query(RiskCost).filter(RiskCost.risk_id == risk.id).delete()
    risks.delete()
    db.commit()
    audit_tests = db.query(AuditTest).filter(AuditTest.project_id == existing_project.first().id)
    for audit_test in audit_tests:
        db.query(AuditTestStakeHolder).filter(
            AuditTestStakeHolder.audit_test_id == audit_test.id
        ).delete()
        db.query(AuditTestDocument).filter(
            AuditTestDocument.audit_test_id == audit_test.id
        ).delete()
        db.query(TaskAuditTest).filter(TaskAuditTest.audit_test_id == audit_test.id).delete()
        db.query(AuditTestHistory).filter(AuditTestHistory.audit_test_id == audit_test.id).delete()
        db.query(KeywordMapping).filter(KeywordMapping.audit_test_id == audit_test.id).delete()
        db.query(AuditTestApprovalWorkflow).filter(
            AuditTestApprovalWorkflow.audit_test_id == audit_test.id
        ).delete()
        db.query(AuditTestInstance).filter(
            AuditTestInstance.audit_test_id == audit_test.id
        ).delete()
        db.query(AuditTestCost).filter(AuditTestCost.audit_test_id == audit_test.id).delete()
    audit_tests.delete()
    db.commit()
    tasks = db.query(Task).filter(Task.project_id == existing_project.first().id)
    for task in tasks:
        db.query(TaskHistory).filter(TaskHistory.task_id == task.id).delete()
        db.query(TaskResource).filter(TaskResource.task_id == task.id).delete()
        db.query(TaskChild).filter(TaskChild.parent_task_id == task.id).delete()
        db.query(TaskChild).filter(TaskChild.child_task_id == task.id).delete()
        db.query(ProjectTaskHistory).filter(ProjectTaskHistory.task_id == task.id).delete()
        db.query(TaskProjectControl).filter(TaskProjectControl.task_id == task.id).delete()
        db.query(TaskRisk).filter(TaskRisk.task_id == task.id).delete()
        db.query(KeywordMapping).filter(KeywordMapping.task_id == task.id).delete()
        db.query(TaskLink).filter(TaskLink.source_id == task.id).delete()
        db.query(TaskLink).filter(TaskLink.target_id == task.id).delete()
        db.query(TaskAuditTest).filter(TaskAuditTest.task_id == task.id).delete()
        db.query(TaskDocument).filter(TaskDocument.task_id == task.id).delete()
        db.query(TaskCost).filter(TaskCost.task_id == task.id).delete()
        db.query(TaskApprovalWorkflow).filter(TaskApprovalWorkflow.task_id == task.id).delete()
        # WorkflowTaskMapping
        db.query(WorkflowTaskMapping).filter(WorkflowTaskMapping.task_id == task.id).delete()
        # TaskStakeholder
        db.query(TaskStakeholder).filter(TaskStakeholder.task_id == task.id).delete()
        db.commit()
    tasks.delete()
    db.commit()
    project_controls = db.query(ProjectControl).filter(
        ProjectControl.project_id == existing_project.first().id
    )
    for project_control in project_controls:
        assessments = db.query(Assessment).filter(
            Assessment.project_control_id == project_control.id
        )
        for assess in assessments:
            db.query(AssessmentHistory).filter(
                AssessmentHistory.assessment_id == assess.id
            ).delete()
            # AssessmentApprovalWorkflow
            db.query(AssessmentApprovalWorkflow).filter(
                AssessmentApprovalWorkflow.assessment_id == assess.id
            ).delete()
            # AssessmentCost
            db.query(AssessmentCost).filter(AssessmentCost.assessment_id == assess.id).delete()
            # AssessmentDocument
            db.query(AssessmentDocument).filter(
                AssessmentDocument.assessment_id == assess.id
            ).delete()
            # AssessmentHistory
            db.query(AssessmentHistory).filter(
                AssessmentHistory.assessment_id == assess.id
            ).delete()
            # AssessmentInstance
            db.query(AssessmentInstance).filter(
                AssessmentInstance.assessment_id == assess.id
            ).delete()
            # KeywordMapping
            db.query(KeywordMapping).filter(KeywordMapping.assessment_id == assess.id).delete()
        assessments.delete()
        exceptions = (
            db.query(Exception).filter(Exception.project_control_id == project_control.id).all()
        )
        for exception in exceptions:
            db.query(ExceptionStakeholder).filter(
                ExceptionStakeholder.exception_id == exception.id
            ).delete()
            db.query(ExceptionDocument).filter(
                ExceptionDocument.exception_id == exception.id
            ).delete()
            db.query(ExceptionHistory).filter(
                ExceptionHistory.exception_id == exception.id
            ).delete()
            # ExceptionApprovalWorkflow
            db.query(ExceptionApprovalWorkflow).filter(
                ExceptionApprovalWorkflow.exception_id == exception.id
            ).delete()
            # ExceptionCost
            db.query(ExceptionCost).filter(ExceptionCost.exception_id == exception.id).delete()
            # ExceptionReview
            db.query(ExceptionReview).filter(ExceptionReview.exception_id == exception.id).delete()
            db.query(KeywordMapping).filter(KeywordMapping.exception_id == exception.id).delete()
        db.query(Exception).filter(Exception.project_control_id == project_control.id).delete()
        db.query(TaskProjectControl).filter(
            TaskProjectControl.project_control_id == project_control.id
        ).delete()
        db.query(ProjectControlHistory).filter(
            ProjectControlHistory.project_control_id == project_control.id
        ).delete()
        db.query(ProjectControlDocument).filter(
            ProjectControlDocument.project_control_id == project_control.id
        ).delete()
        db.query(ProjectControlCost).filter(
            ProjectControlCost.project_control_id == project_control.id
        ).delete()
        db.query(ProjectControlApprovalWorkflow).filter(
            ProjectControlApprovalWorkflow.project_control_id == project_control.id
        ).delete()
        db.query(KeywordMapping).filter(
            KeywordMapping.project_control_id == project_control.id
        ).delete()
        project_control_evidence = (
            db.query(ProjectControlEvidence)
            .filter(ProjectControlEvidence.project_control_id == project_control.id)
            .all()
        )
        evidence_ids = []
        for pce in project_control_evidence:
            evidence_ids.append(pce.evidence_id)

        db.query(ProjectControlEvidence).filter(
            ProjectControlEvidence.project_control_id == project_control.id
        ).delete()

        for id in evidence_ids:
            db.query(ProjectControlEvidence).filter(
                ProjectControlEvidence.evidence_id == id
            ).delete()
            db.query(Evidence).filter(Evidence.id == id).delete()

        # AWSProjectControl
        aws_project_control = (
            db.query(AWSControlProjectControl)
            .filter(AWSControlProjectControl.project_control_id == project_control.id)
            .all()
        )
        aws_control_ids = []
        for control in aws_project_control:
            aws_control_ids.append(control.aws_control_id)

        db.query(AWSControlProjectControl).filter(
            AWSControlProjectControl.project_control_id == project_control.id
        ).delete()

        for id in aws_control_ids:
            db.query(AWSControlProjectControl).filter(
                AWSControlProjectControl.aws_control_id == id
            ).delete()
            db.query(AWSControl).filter(AWSControl.id == id).delete()

        # Service Provider Project Control
        db.query(ServiceProviderProjectControl).filter(
            ServiceProviderProjectControl.project_control_id == project_control.id
        ).delete()
        # App Project Control
        db.query(AppProjectControl).filter(
            AppProjectControl.project_control_id == project_control.id
        ).delete()

    project_controls.delete()
    db.commit()
    project_evaluations = db.query(ProjectEvaluation).filter(
        ProjectEvaluation.project_id == existing_project.first().id
    )
    for eval in project_evaluations:
        db.query(ProjectEvaluationHistory).filter(
            ProjectEvaluationHistory.project_evaluation_id == eval.id
        ).delete()
        db.query(ProjectEvaluationDocument).filter(
            ProjectEvaluationDocument.project_evaluation_id == eval.id
        ).delete()
        # ProjectEvaluationCost
        db.query(ProjectEvaluationCost).filter(
            ProjectEvaluationCost.project_evaluation_id == eval.id
        ).delete()
        db.query(KeywordMapping).filter(KeywordMapping.project_evaluation_id == eval.id).delete()
        db.query(ProjectEvaluationApprovalWorkflow).filter(
            ProjectEvaluationApprovalWorkflow.project_evaluation_id == eval.id
        ).delete()
    project_evaluations.delete()
    db.commit()
    wbs = db.query(WBS).filter(WBS.project_id == existing_project.first().id)
    for w in wbs:
        db.query(WBSHistory).filter(WBSHistory.wbs_id == w.id).delete()
        db.query(WBSDocument).filter(WBSDocument.wbs_id == w.id).delete()
        db.query(KeywordMapping).filter(KeywordMapping.wbs_id == w.id).delete()
        # WBSCost
        db.query(WBSCost).filter(WBSCost.wbs_id == w.id).delete()
        # WBSApprovalWorkflow
        db.query(WBSApprovalWorkflow).filter(WBSApprovalWorkflow.wbs_id == w.id).delete()
        # Import Task
        db.query(ImportTask).filter(ImportTask.wbs_id == w.id).delete()
        wbs_tasks = db.query(Task).filter(Task.wbs_id == w.id).all()
        for task in wbs_tasks:
            db.query(KeywordMapping).filter(KeywordMapping.task_id == task.id).delete()
            db.query(Task).filter(Task.id == task.id).delete()
    wbs.delete()
    db.commit()
    project_users = db.query(ProjectUser).filter(
        ProjectUser.project_id == existing_project.first().id
    )
    for pu in project_users:
        db.query(ProjectUserHistory).filter(ProjectUserHistory.author_id == pu.user_id).delete()
        db.query(ProjectUserHistory).filter(ProjectUserHistory.author_id == pu.assigned_id).delete()
        db.commit()
    project_users.delete()
    db.commit()
    db.query(ProjectUserHistory).filter(
        ProjectUserHistory.project_id == existing_project.first().id
    ).delete()
    documents = db.query(Document).filter(Document.project_id == existing_project.first().id)
    for doc in documents:
        db.query(DocumentHistory).filter(DocumentHistory.document_id == doc.id).delete()
        db.query(KeywordMapping).filter(KeywordMapping.document_id == doc.id).delete()
        db.query(DocumentApprovalWorkflow).filter(
            DocumentApprovalWorkflow.document_id == doc.id
        ).delete()
    documents.delete()
    db.commit()
    db.query(AuditTest).filter(AuditTest.project_id == existing_project.first().id).delete()
    db.commit()
    db.query(UserNotifications).filter(
        UserNotifications.project_id == existing_project.first().id
    ).delete()
    db.commit()
    db.query(UserWatching).filter(UserWatching.project_id == existing_project.first().id).delete()
    db.commit()
    db.query(ProjectCost).filter(ProjectCost.project_id == existing_project.first().id).delete()
    db.commit()
    # delete all approval workflow references
    db.query(ProjectApprovalWorkflow).filter(ProjectApprovalWorkflow.project_id == id).delete()
    db.commit()
    # delete all features
    db.query(FeatureProject).filter(FeatureProject.project_id == id).delete()
    db.commit()
    # Workflow Flowchart
    db.query(WorkflowFlowchart).filter(WorkflowFlowchart.project_id == id).delete()
    db.commit()
    # Survey Model
    db.query(SurveyModel).filter(SurveyModel.project_id == id).delete()

    existing_project.delete(synchronize_session=False)
    db.commit()
    return True


async def add_control_to_project(
    db: Session,
    id: int,
    control_id: int,
    tenant_id: int,
    user_id: int,
    project_control: CreateProjectControl,
    keywords: str = None,
    assessment_confirmed: str = None,
):
    existing_project = filter_by_tenant(db, Project, tenant_id).filter(Project.id == id)
    if not existing_project.first():
        return NO_SUCH_PROJECT

    my_existing_project = existing_project.first()
    existing_control = db.query(Control).filter(Control.id == control_id)
    if not existing_control.first():
        return NO_SUCH_CONTROL

    existing_project_control = (
        db.query(ProjectControl)
        .filter(ProjectControl.project_id == id)
        .filter(ProjectControl.control_id == control_id)
    )
    if existing_project_control.first():
        return PROJECT_CONTROL_ALREADY_EXISTS

    my_existing_control = existing_control.first()

    new_project_control = Project(**project_control.dict(), tenant_id=tenant_id)

    db.add(new_project_control)
    db.commit()
    db.refresh(new_project_control)

    # Add history
    history = {
        "project_control_id": new_project_control.id,
        "author_id": user_id,
        "history": f"Added new project control {my_existing_control.name}",
    }
    new_history = ProjectControlHistory(**history)
    db.add(new_history)
    db.commit()
    # Create user notifications
    # Get all users watching project overview for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_controls == True)
        .filter(UserWatching.project_id == existing_project.first().id)
        .all()
    )
    link = f"/projects/{id}/controls/{new_project_control.id}"
    # Create user notifications
    await manage_notifications(
        db,
        users_watching,
        "projects",
        f"Added new project control {my_existing_control.name}",
        link,
        existing_project.first().id,
        existing_project.first().id,
    )

    assessment = {
        "name": f"Assess Control '{my_existing_control.name}' on Project '{my_existing_project.name}'",
        "description": f"Assessment of whether or not the constraints for Control '{my_existing_control.name}' have been met on Project '{my_existing_project.name}'",
        "project_control_id": new_project_control.id,
        "is_assessment_confirmed": "No",
        "tenant_id": tenant_id,
    }
    new_assessment = CreateAssessment(**assessment)
    new_assessment_resp = await create_assessment(db, new_assessment, user_id)
    new_project_control.assessment_id = new_assessment_resp.id
    db.commit()
    db.refresh(new_project_control)
    # add keywords
    await add_pc_keywords(db, keywords, new_project_control.id, tenant_id)
    return db.query(Project).filter(Project.id == id).first()


async def update_control_on_project(
    db: Session,
    project_control_id: int,
    tenant_id: int,
    project_control: UpdateProjectControl,
    keywords: str = None,
    assessment_confirmed: str = None,
    user_id: int = None,
):
    existing_project_control = db.query(ProjectControl).filter(
        ProjectControl.id == project_control_id
    )

    project_control_obj = existing_project_control.first()
    if not project_control_obj:
        return NO_SUCH_PROJECT_CONTROL

    project_control_dict = project_control.dict(exclude_unset=True)

    # ✅ Fix: Prevent empty update
    if not project_control_dict:
        LOGGER.warning("No valid fields provided for update")
        raise HTTPException(status_code=400, detail="No fields provided for update")

    # ✅ Fix: Cost handling
    cost_ids = project_control_dict.pop("cost_ids", None)
    if cost_ids:
        for cost in cost_ids:
            existing_cost = db.query(Cost).filter(Cost.tenant_id == tenant_id).first()
            if existing_cost:
                new_cost_map = ProjectControlCost(
                    project_control_id=project_control_id, cost_id=cost
                )
                try:
                    db.add(new_cost_map)
                    db.commit()
                except:
                    LOGGER.error("Could not add cost with this ID")

    # ✅ Fix: Correct dictionary value retrieval
    changes = []
    for field in [
        "mitigation_percentage",
        "control_family_id",
        "control_phase_id",
        "control_status_id",
        "control_class_id",
    ]:
        new_value = project_control_dict.get(field, None)
        if getattr(project_control_obj, field) != new_value and new_value is not None:
            changes.append(f"Updated {field.replace('_', ' ')} to {new_value}")

    # ✅ Optimize first() calls
    project_id = project_control_obj.project_id
    control_id = project_control_obj.id

    # Send notifications
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_controls == True)
        .filter(UserWatching.project_id == project_id)
        .all()
    )
    link = f"/projects/{project_id}/controls/{control_id}"
    all_changes = ".    ".join(changes)
    await manage_notifications(
        db, users_watching, "project_controls", all_changes, link, project_id, control_id
    )

    # ✅ Fix: Prevent empty update statement
    if project_control_dict:
        existing_project_control.update(project_control_dict)
        db.commit()

    # ✅ Update assessment
    existing_assessment = db.query(Assessment).filter(Assessment.project_control_id == control_id)
    existing_assessment.update({"is_assessment_confirmed": assessment_confirmed})
    db.commit()

    # ✅ Remove old and add new keywords
    await remove_old_pc_keywords(db, keywords, control_id)
    await add_pc_keywords(db, keywords, control_id, tenant_id)

    return existing_project_control.first()


async def remove_control_from_project(
    db: Session, id: int, project_control_id: int, tenant_id: int, user_id: int
):
    existing_project = db.query(Project).filter(Project.id == id)
    if not existing_project.first():
        return False, status.HTTP_404_NOT_FOUND, f"Project with id '{id}' does not exist"

    existing_project_control = db.query(ProjectControl).filter(
        ProjectControl.id == project_control_id
    )
    if not existing_project_control.first():
        return (
            False,
            status.HTTP_404_NOT_FOUND,
            f"Project control with id '{project_control_id}' does not exist",
        )
    # Create user notifications
    # Get all users watching project controls for this project
    # users_watching = (
    #     db.query(UserWatching)
    #     .filter(UserWatching.project_controls == True)
    #     .filter(UserWatching.project_id == existing_project.first().id)
    #     .all()
    # )
    # existing_control = (
    #     db.query(Control).filter(Control.id == existing_project_control.first().control_id).first()
    # )
    # # Create user notifications
    # await manage_notifications(
    #     db,
    #     users_watching,
    #     "project_controls",
    #     f"Removed {existing_control.name} from project",
    #     f"/projects/{id}",
    #     existing_project_control.first().id,
    #     id,
    # )
    existing_project_control_id = [obj.id for obj in existing_project_control.all()]

    # error_message = "Cannot remove control from the project as risks/audit tests/project evaluations/documents exist with this control. Please add to Exceptions instead."

    # if len(existing_project_control_exception) > 0:
    #     return False, status.HTTP_400_BAD_REQUEST, error_message

    existing_project_control_object = existing_project_control.first()
    existing_project_control_risks = db.query(Risk).filter(
        Risk.project_id == existing_project_control_object.project_id,
        Risk.project_control_id == existing_project_control_object.id,
    )

    # update risk to not reference project control
    for risk in existing_project_control_risks:
        risk.update(project_control_id == "")
        db.commit()

    # if len(existing_project_control_risks) > 0:
    #     return False, status.HTTP_400_BAD_REQUEST, error_message

    existing_project_control_audit_tests = db.query(AuditTest).filter(
        AuditTest.project_id == existing_project_control_object.project_id,
        AuditTest.project_control_id == existing_project_control_object.id,
    )

    for audit in existing_project_control_audit_tests:
        audit.update(project_control_id == "")
        db.commit()

    # if len(existing_project_control_audit_tests) > 0:
    #     return False, status.HTTP_400_BAD_REQUEST, error_message

    # delete all assessment history
    assessment_history_joins = db.query(AssessmentHistory).join(Assessment).join(ProjectControl)
    assessment_history_filter = assessment_history_joins.filter(
        Assessment.project_control_id == project_control_id
    )
    assessment_history_id_subquery = assessment_history_filter.with_entities(
        AssessmentHistory.id
    ).subquery()

    db.query(AssessmentHistory).filter(
        AssessmentHistory.id.in_(assessment_history_id_subquery)
    ).delete(synchronize_session=False)

    existing_project_control_assessment = db.query(Assessment).filter(
        Assessment.project_control_id.in_(existing_project_control_id)
    )

    existing_project_control_assessment.delete(synchronize_session=False)

    existing_project_control_task = db.query(TaskProjectControl).filter(
        TaskProjectControl.project_control_id.in_(existing_project_control_id)
    )

    # delete all history references
    db.query(ProjectControlHistory).filter(
        ProjectControlHistory.project_control_id == project_control_id
    ).delete()
    # delete all keyword references
    db.query(KeywordMapping).filter(
        KeywordMapping.project_control_id == project_control_id
    ).delete()
    # delete all document references
    db.query(ProjectControlDocument).filter(
        ProjectControlDocument.project_control_id == project_control_id
    ).delete()

    # delete all assessments
    db.query(Assessment).filter(Assessment.project_control_id == project_control_id).delete()

    # delete exception
    db.query(Exception).filter(Exception.project_control_id == project_control_id).delete()

    # delete all evidence linkages
    db.query(ProjectControlEvidence).filter(
        ProjectControlEvidence.project_control_id == project_control_id
    ).delete()

    db.commit()
    # delete all approval workflow references
    db.query(ProjectControlApprovalWorkflow).filter(
        ProjectControlApprovalWorkflow.project_control_id == project_control_id
    ).delete()
    existing_project_control_task.delete(synchronize_session=False)
    # try:
    existing_project_control.delete(synchronize_session=False)
    db.commit()
    return True, status.HTTP_200_OK, "Successfully removed control from project."
    # except Exception as e:
    # return "error_message {e}"


def get_available_controls_for_adding_to_project(db: Session, id: int, tenant_id: int):
    existing_project = filter_by_tenant(db, Project, tenant_id).filter(Project.id == id)
    if not existing_project.first():
        return -1

    controls_already_on_project = db.query(ProjectControl.control_id).filter(
        ProjectControl.project_id == id
    )
    available_controls = filter_by_tenant(db, Control, tenant_id).filter(
        ~Control.id.in_(controls_already_on_project)
    )
    return available_controls.options(
        selectinload(Control.framework_versions),
    ).all()


def get_project_controls_by_project_id(db: Session, project_id: int):
    return db.query(ProjectControl).filter(ProjectControl.project_id == project_id)


async def get_project_controls_dropdown_by_project_id(db: Session, project_id: int):
    results = (
        db.query(Control.name.label("label"), ProjectControl.id.label("id"))
        .select_from(ProjectControl, Control)
        .join(Control, ProjectControl.control_id == Control.id)
        .filter(ProjectControl.project_id == project_id)
        .group_by(Control.id)
        .group_by(ProjectControl.id)
        .all()
    )
    return results


def get_project_control_by_id(db: Session, project_control_id: int):
    project_control = (
        db.query(ProjectControl).filter(ProjectControl.id == project_control_id).first()
    )

    return project_control


def get_project_controls_by_project_id_by_framework_version_id(
    db: Session, project_id: int, framework_version_id: int
):
    added_controls = db.query(ProjectControl).filter(ProjectControl.project_id == project_id).all()
    framework_controls = (
        db.query(Control)
        .join(ControlFrameworkVersion, Control.id == ControlFrameworkVersion.control_id)
        .filter(ControlFrameworkVersion.framework_version_id == framework_version_id)
        .all()
    )
    controls = []
    for control in framework_controls:
        curControl = control
        curControl.used = False
        for added in added_controls:
            if curControl.id == added.control_id:
                curControl.used = True
        controls.append(curControl)
    return controls


def get_audit_tests_by_project_id(db: Session, project_id: int):
    return db.query(AuditTest).filter(AuditTest.project_id == project_id).all()


def get_risks_by_project_id(db: Session, project_id: int):
    return db.query(Risk).filter(Risk.project_id == project_id).all()


def get_assessments_by_project_id(db: Session, project_id: int):
    return (
        db.query(Assessment)
        .join(ProjectControl, ProjectControl.id == Assessment.project_control_id)
        .filter(ProjectControl.project_id == project_id)
        .all()
    )


def get_wbs_by_project_id(db: Session, project_id: int):
    return db.query(WBS).filter(WBS.project_id == project_id).all()


def get_evaluations_by_project_id(db: Session, project_id: int):
    return db.query(ProjectEvaluation).filter(ProjectEvaluation.project_id == project_id).all()


def create_exception_for_control_on_project(db: Session, id: int, control_id: int):
    existing_project = db.query(Project).filter(Project.id == id)
    if not existing_project.first():
        return -1
    my_existing_project = existing_project.first()

    existing_project_control = (
        db.query(ProjectControl)
        .filter(ProjectControl.project_id == id)
        .filter(ProjectControl.control_id == control_id)
    )
    if not existing_project_control.first():
        return -2
    my_existing_project_control = existing_project_control.first()

    new_exception = Exception(
        name=f"Exception for '{my_existing_project_control.control.name}' on Project '{my_existing_project.name}'",
        description=f"Indicates that an Exception is in place for Control '{my_existing_project_control.control.name}' on Project '{my_existing_project.name}'",
        project_control_id=my_existing_project_control.id,
    )

    db.commit()
    db.refresh(new_exception)

    return db.query(Project).filter(Project.id == id).first()


async def add_batch_project_controls_to_project(
    db: Session,
    project_id: int,
    project_controls: AddProjectControls,
    tenant_id: int,
    user_id: int,
):
    new_project_controls = []
    for project_control in project_controls.controls:
        new_project_control = ProjectControl(
            project_id=project_id,
            control_id=project_control.control_id,
            mitigation_percentage=0,
            # control_family_id=0,
            control_phase_id=1,
            # control_status_id=1,
            control_class_id=1,
        )
        db.add(new_project_control)
        db.commit()
        db.refresh(new_project_control)
        new_project_controls.append(new_project_control)
    # Create user notifications
    # Get all users watching project overview for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_controls == True)
        .filter(UserWatching.project_id == project_id)
        .all()
    )
    project = db.query(Project).filter(Project.id == project_id).first()
    # Create user notifications
    await manage_notifications(
        db,
        users_watching,
        "project_controls",
        f"Added {len(project_controls.controls)} new project controls",
        f"/projects/{new_project_control.project_id}/controls",
        project_id,
        new_project_control.id,
    )

    for control in new_project_controls:
        control_data = db.query(Control).filter(Control.id == control.control_id).first()

        assessment = {
            "project_control_id": control.id,
            "name": f"Assess Control '{control_data.name}' on Project '{project.name}'",
            "description": f"Assessment of whether or not the constraints for Control '{control_data.name}' have been met on Project '{project.name}'",
            "is_assessment_confirmed": "No",
            "tenant_id": tenant_id,
        }
        new_assessment = CreateAssessment(**assessment)
        new_assessment_resp = await create_assessment(db, new_assessment, user_id, tenant_id)
        control.assessment_id = new_assessment_resp.id
        db.commit()
        db.refresh(control)

    latest_controls = db.query(ProjectControl).filter(ProjectControl.project_id == project_id).all()
    return latest_controls


async def add_users_to_project(
    db: Session, id: int, project_users: AddProjectUsers, tenant_id: int, user_id: int
):
    new_project_users = []

    for project_user in project_users.users:
        new_project_user = ProjectUser(
            project_id=id,
            user_id=project_user.user_id,
            role_id=project_user.role_id,
        )
        new_project_users.append(new_project_user)
        user = db.query(User).filter(User.id == project_user.user_id).first()
        project = db.query(Project).filter(Project.id == id).first()
        role = db.query(Role).filter(Role.id == project_user.role_id).first()
        # Add history
        history = {
            "project_id": id,
            "author_id": user_id,
            "assigned_user_id": project_user.user_id,
            "role": role.name,
            "history": f"Added {user.email} as a {role.name} on {project.name}",
        }
        new_history = ProjectUserHistory(**history)
        db.add(new_history)
        db.commit()
        # Get all users watching project users for this project
        users_watching = (
            db.query(UserWatching)
            .filter(UserWatching.project_users == True)
            .filter(UserWatching.project_id == id)
            .all()
        )
        # Create user notifications
        await manage_notifications(
            db,
            users_watching,
            "project_users",
            f"Added {user.email} as a {role.name} on {project.name}",
            f"/projects/{id}/users",
            project.id,
            user.id,
        )

    db.add_all(new_project_users)
    db.commit()
    db.refresh(new_project_users)

    return new_project_users


async def remove_user_from_project(db: Session, id: int, user_id: int):
    existing_project_user = db.query(ProjectUser).filter(
        ProjectUser.user_id == user_id, ProjectUser.project_id == id
    )
    if not existing_project_user.first():
        return False, "Project with specified id doesn't contains User with specified id"

    user = db.query(User).filter(User.id == user_id).first()
    project = db.query(Project).filter(Project.id == id).first()
    role = db.query(Role).filter(Role.id == existing_project_user.first().role_id).first()
    # Add history
    history = {
        "project_id": id,
        "author_id": user_id,
        "assigned_user_id": user_id,
        "role": "",
        "history": f"Removed {user.email} from {role.name} on {project.name}",
    }
    new_history = ProjectUserHistory(**history)
    db.add(new_history)
    db.commit()
    # Get all users watching project users for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_users == True)
        .filter(UserWatching.project_id == id)
        .all()
    )
    # Create user notifications
    await manage_notifications(
        db,
        users_watching,
        "project_users",
        f"Removed {user.email} as a {role.name} on {project.name}",
        f"/projects/{id}/users",
        id,
        user.id,
    )
    existing_project_user.delete(synchronize_session=False)
    LOGGER.info(f"existing project user {existing_project_user}")
    db.commit()
    return True, "Successfully removed user from project"


async def change_user_role_in_project(
    db: Session, id: int, user_details: ChangeProjectUserRole, user_id: int
):
    existing_project_user = (
        db.query(ProjectUser)
        .filter(ProjectUser.user_id == user_details.user_id)
        .filter(ProjectUser.project_id == id)
        .first()
    )

    if not existing_project_user:
        return False, "User with spectified id does not exists in project"

    role = db.query(Role).filter(Role.id == user_details.role_id).first()
    if not role:
        return False, "Role does not exists"

    if existing_project_user.role_id == user_details.role_id:
        return False, "User already has this role"
    project = db.query(Project).filter(Project.id == id).first()
    user = db.query(User).filter(User.id == user_details.user_id).first()
    existing_project_user.role_id = user_details.role_id
    history = {
        "project_id": id,
        "author_id": user_id,
        "assigned_user_id": user_details.user_id,
        "role": role.name,
        "history": f"User {user.email} assigned as {role.name} on {project.name}",
    }
    new_history = ProjectUserHistory(**history)
    db.add(new_history)
    db.commit()
    # Get all users watching project users for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_users == True)
        .filter(UserWatching.project_id == id)
        .all()
    )
    # Create user notifications
    await manage_notifications(
        db,
        users_watching,
        "project_users",
        f"User {user.email} assigned as {role.name} on {project.name}",
        f"/projects/{id}/users",
        id,
        user.id,
    )
    return True, "Successfully changed user role"


def get_project_user_permission(db: Session, id: int, user_id: int):
    project_user = (
        db.query(ProjectUser)
        .filter(ProjectUser.project_id == id)
        .filter(ProjectUser.user_id == user_id)
        .first()
    )

    if not project_user:
        return False

    role = db.query(Role).filter(Role.id == project_user.role_id).first()
    permissions = (
        db.query(Permission)
        .join(PermissionRole, PermissionRole.permission_id == Permission.id)
        .filter(PermissionRole.role_id == role.id)
        .distinct()
        .all()
    )

    return {"role": role, "permission": permissions}


def get_project_associated_user(
    db: Session, id: int, q: str, filter_by: str, filter_value: str, sort_by: str, user
):
    existing_project = (
        filter_by_tenant(db, Project, user["tenant_id"]).filter(Project.id == id).first()
    )

    if not existing_project:
        return False

    queryset = (
        db.query(User, Role)
        .select_from(ProjectUser)
        .join(User, ProjectUser.user_id == User.id)
        .join(Role, ProjectUser.role_id == Role.id)
        .filter(ProjectUser.project_id == existing_project.id)
    )

    if filter_by and filter_value:
        if filter_by in ("username", "email"):
            queryset = queryset.filter(
                func.lower(getattr(User, filter_by)).contains(filter_value.lower())
            )
        else:
            queryset = queryset.filter(func.lower(getattr(User, filter_by)) == filter_value.lower())

    if sort_by:
        queryset = ordering_query(query=queryset, model=User.__tablename__, order=sort_by)

    if q:
        queryset = queryset.filter(
            func.lower(User.email).contains(func.lower(q)),
        )

    return queryset.distinct()


def get_project_pending_task(db: Session, user):
    user_object = db.query(User).filter(User.id == user["user_id"]).first()

    queryset = (
        db.query(
            Project.id.label("project_id"),
            Project.name.label("project_name"),
            func.count("*").label("task_pending_count"),
        )
        .select_from(Project)
        .join(Task, Project.id == Task.project_id)
        .filter(Task.task_status_id != 3)
        .group_by(Project.id, Project.name)
    )

    if user_object.is_superuser:
        pass
    if user_object.is_tenant_admin:
        queryset = queryset.filter(Project.tenant_id == user["tenant_id"])
    else:
        queryset = queryset.join(ProjectUser, ProjectUser.project_id == Project.id).filter(
            ProjectUser.user_id == user["user_id"]
        )

    return queryset.all()


def add_users_to_multiple_project(db: Session, project_users: AddProjectsUsers, tenant_id: int):
    new_project_users = []

    for project_user in project_users.users:
        new_project_user = ProjectUser(
            project_id=project_user.project_id,
            user_id=project_user.user_id,
            role_id=project_user.role_id,
        )
        new_project_users.append(new_project_user)

    db.add_all(new_project_users)
    db.commit()
    return new_project_users


def get_users_project(db: Session, user_id: int):
    queryset = (
        db.query(
            Project.id.label("id"),
            Project.name.label("name"),
            Project.description.label("description"),
            Role.name.label("role"),
        )
        .select_from(Project, Role)
        .join(ProjectUser, Project.id == ProjectUser.project_id)
        .join(Role, ProjectUser.role_id == Role.id)
        .filter(ProjectUser.user_id == user_id)
        .order_by(Project.id)
    ).all()
    queryset2 = (
        db.query(
            Project.id.label("id"),
            Project.name.label("name"),
            Project.description.label("description"),
        )
        .select_from(Project)
        .filter(Project.project_admin_id == user_id)
        .order_by(Project.id)
    ).all()
    new_arr = []
    for res in queryset2:
        obj = {"id": res[0], "name": res[1], "description": res[2], "role": "Project Administrator"}
        new_arr.append(obj)
    unique = []
    matches = 0
    for obj in new_arr:
        for query_obj in queryset:
            if obj["id"] == query_obj["id"]:
                matches = matches + 1
        if matches == 0:
            unique.append(obj)
        matches = 0
    result = queryset + unique
    return result


def get_project_frameworks(db: Session, project_id: int):
    frameworks = (
        db.query(
            Framework.id,
            Framework.name,
        )
        .select_from(Project, Control, ControlFrameworkVersion, FrameworkVersion, Framework)
        .join(ProjectControl, Project.id == ProjectControl.project_id)
        .join(Control, Control.id == ProjectControl.control_id)
        .join(ControlFrameworkVersion, Control.id == ControlFrameworkVersion.control_id)
        .join(FrameworkVersion, ControlFrameworkVersion.framework_version_id == FrameworkVersion.id)
        .join(Framework)
        .group_by(ControlFrameworkVersion.framework_version_id)
        .group_by(Framework.id)
        .group_by(Framework.name)
        .filter(ProjectControl.project_id == project_id)
        .all()
    )

    return frameworks


async def add_a_user_to_project(db: Session, id: int, user_id: int, role_id: int, author_id: int):
    new_project_user = {
        "project_id": id,
        "user_id": user_id,
        "role_id": role_id,
    }
    LOGGER.info(new_project_user)
    new_user = ProjectUser(**new_project_user)
    db.add(new_user)
    db.commit()
    LOGGER.info(new_user)
    # Add history
    user = db.query(User).filter(User.id == user_id).first()
    role = db.query(Role).filter(Role.id == role_id).first()
    project = db.query(Project).filter(Project.id == id).first()
    history = {
        "project_id": id,
        "author_id": author_id,
        "assigned_user_id": user_id,
        "role": role.name,
        "history": f"User {user.email} added as {role.name} to {project.name}",
    }
    new_history = ProjectUserHistory(**history)
    db.add(new_history)
    db.commit()
    # Get all users watching project users for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_users == True)
        .filter(UserWatching.project_id == id)
        .all()
    )
    # Create user notifications
    await manage_notifications(
        db,
        users_watching,
        "project_users",
        f"User {user.email} assigned as {role.name} on {project.name}",
        f"/projects/{id}/users",
        id,
        user.id,
    )
    return {"message": "Project user added"}
