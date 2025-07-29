import logging

from sqlalchemy.orm.session import Session

import os

from fedrisk_api.db.models import (
    Approval,
    ApprovalStakeholder,
    ApprovalWorkflow,
    ApprovalWorkflowTemplate,
    ApprovalWorkflowHistory,
    ProjectControl,
    ProjectControlApprovalWorkflow,
    ProjectControlHistory,
    TaskApprovalWorkflow,
    RiskApprovalWorkflow,
    AuditTestApprovalWorkflow,
    AssessmentApprovalWorkflow,
    ExceptionApprovalWorkflow,
    DocumentApprovalWorkflow,
    CapPoamApprovalWorkflow,
    WBSApprovalWorkflow,
    WorkflowFlowchartApprovalWorkflow,
    ProjectApprovalWorkflow,
    ProjectEvaluationApprovalWorkflow,
    Project,
    ProjectApprovalWorkflow,
    ProjectHistory,
    Task,
    TaskApprovalWorkflow,
    TaskHistory,
    Risk,
    RiskApprovalWorkflow,
    RiskHistory,
    AuditTest,
    AuditTestApprovalWorkflow,
    AuditTestHistory,
    Assessment,
    AssessmentApprovalWorkflow,
    AssessmentHistory,
    Exception,
    ExceptionApprovalWorkflow,
    ExceptionHistory,
    Document,
    DocumentApprovalWorkflow,
    DocumentHistory,
    CapPoam,
    CapPoamApprovalWorkflow,
    CapPoamHistory,
    WBS,
    WBSApprovalWorkflow,
    WBSHistory,
    WorkflowFlowchart,
    WorkflowFlowchartApprovalWorkflow,
    WorkflowFlowchartHistory,
    ProjectEvaluation,
    ProjectEvaluationHistory,
    UserNotifications,
    UserNotificationSettings,
    User,
)
from fedrisk_api.db.project import ProjectControl
from fedrisk_api.schema.approval_workflows import (
    CreateApprovalWorkflowUseTemplate,
    CreateApprovalWorkflow,
    UpdateApprovalWorkflow,
    CreateApprovalWorkflowTemplate,
    UpdateApprovalWorkflowTemplate,
    CreateApproval,
    UpdateApproval,
    CreateApprovalStakeholder,
    UpdateApprovalStakeholder,
    CreateTaskApproval,
    UpdateTaskApproval,
    CreateRiskApproval,
    UpdateRiskApproval,
    CreateAuditTestApproval,
    UpdateAuditTestApproval,
    CreateAssessmentApproval,
    UpdateAssessmentApproval,
    CreateExceptionApproval,
    UpdateExceptionApproval,
    CreateCapPoamApproval,
    UpdateCapPoamApproval,
    CreateDocumentApproval,
    UpdateDocumentApproval,
    CreateProjectApproval,
    UpdateProjectApproval,
    CreateProjectEvaluationApproval,
    UpdateProjectEvaluationApproval,
    CreateWBSApproval,
    UpdateWBSApproval,
    CreateWorkflowFlowchartApproval,
    UpdateWorkflowFlowchartApproval,
    CreateProjectControlApproval,
    UpdateProjectControlApproval,
)

from fedrisk_api.schema.history import CreateApprovalWorkflowHistory

from fedrisk_api.utils.utils import filter_by_tenant

from fedrisk_api.db.util.notifications_utils import send_assigned_email, send_sms

from datetime import date

frontend_server_url = os.getenv("FRONTEND_SERVER_URL", "")

LOGGER = logging.getLogger(__name__)


# post approval workflow history
async def post_history(db: Session, workflow_history: CreateApprovalWorkflowHistory):
    workflow_history_data = workflow_history.dict(exclude_unset=True)
    new_workflow_history = ApprovalWorkflowHistory(**workflow_history_data)
    db.add(new_workflow_history)
    db.commit()
    return new_workflow_history


# Approval workflow template DB methods ##########
def get_all_approval_workflow_templates(db: Session, tenant_id: int, user_id: int):
    approval_workflow_templates = (
        db.query(ApprovalWorkflowTemplate)
        .filter(ApprovalWorkflowTemplate.tenant_id == tenant_id)
        .all()
    )

    return approval_workflow_templates


def get_approval_workflow_template(db: Session, id: int, tenant_id: int, user_id: int):
    approval_workflow = (
        db.query(ApprovalWorkflowTemplate).filter(ApprovalWorkflowTemplate.id == id).first()
    )

    return approval_workflow


async def create_approval_workflow_template(
    db: Session,
    approval_workflow_template: CreateApprovalWorkflowTemplate,
    user_id: int,
    tenant_id: int,
):
    new_approval_workflow_template = ApprovalWorkflowTemplate(
        **approval_workflow_template.dict(), tenant_id=tenant_id
    )
    db.add(new_approval_workflow_template)
    db.commit()
    return new_approval_workflow_template


async def update_approval_workflow_template(
    db: Session,
    approval_workflow_template: UpdateApprovalWorkflowTemplate,
    id: int,
    user_id: int,
    tenant_id: int,
):
    existing_query = db.query(ApprovalWorkflowTemplate).filter(ApprovalWorkflowTemplate.id == id)
    existing_obj = existing_query.first()
    if not existing_obj:
        return False

    update_data = approval_workflow_template.dict(exclude_unset=True)
    existing_query.update(update_data)
    db.commit()
    db.refresh(existing_obj)  # Refresh to get updated values
    return existing_obj


async def delete_approval_workflow_template(db: Session, id: int, tenant_id: int):
    existing_approval_workflow_template = db.query(ApprovalWorkflowTemplate).filter(
        ApprovalWorkflowTemplate.id == id
    )
    if not existing_approval_workflow_template.first():
        return False

    existing_approval_workflow_template.delete(synchronize_session=False)
    db.commit()
    return True


# Approval workflow DB methods ##########


def get_all_approval_workflows_project(db: Session, tenant_id: int, project_id: int, user_id: int):

    if project_id:
        approval_workflows = (
            db.query(ApprovalWorkflow)
            .join(
                TaskApprovalWorkflow,
                TaskApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
            )
            .join(Task, TaskApprovalWorkflow.task_id == Task.id)
            .join(
                RiskApprovalWorkflow,
                RiskApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
            )
            .join(Risk, Risk.id == RiskApprovalWorkflow.risk_id)
            .join(
                AuditTestApprovalWorkflow,
                AuditTestApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
            )
            .join(AuditTest, AuditTest.id == AuditTestApprovalWorkflow.audit_test_id)
            .join(
                AssessmentApprovalWorkflow,
                AssessmentApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
            )
            .join(Assessment, Assessment.id == AssessmentApprovalWorkflow.assessment_id)
            .join(ProjectControl, Assessment.project_control_id == ProjectControl.id)
            .join(
                ExceptionApprovalWorkflow,
                ExceptionApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
            )
            .join(Exception, Exception.id == ExceptionApprovalWorkflow.exception_id)
            .join(ProjectControl, Exception.project_control_id == ProjectControl.id)
            .join(
                DocumentApprovalWorkflow,
                DocumentApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
            )
            .join(Document, Document.id == DocumentApprovalWorkflow.document_id)
            .join(
                CapPoamApprovalWorkflow,
                CapPoamApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
            )
            .join(CapPoam, CapPoam.id == CapPoamApprovalWorkflow.cap_poam_id)
            .join(
                WBSApprovalWorkflow, WBSApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id
            )
            .join(WBS, WBS.id == WBSApprovalWorkflow.wbs_id)
            .join(
                WorkflowFlowchartApprovalWorkflow,
                WorkflowFlowchartApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
            )
            .join(
                WorkflowFlowchart,
                WorkflowFlowchart.id == WorkflowFlowchartApprovalWorkflow.workflow_flowchart_id,
            )
            .join(
                ProjectApprovalWorkflow,
                ProjectApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
            )
            .join(Project, Project.id == ProjectApprovalWorkflow.project_id)
            .join(
                ProjectEvaluationApprovalWorkflow,
                ProjectEvaluationApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
            )
            .join(
                ProjectEvaluation,
                ProjectEvaluation == ProjectEvaluationApprovalWorkflow.project_evaluation_id,
            )
            .filter(ApprovalWorkflow.tenant_id == tenant_id)
            .filter(ProjectControl.project_id == project_id)
            .filter(Task.project_id == project_id)
            .filter(Risk.project_id == project_id)
            .filter(AuditTest.project_id == project_id)
            .filter(Document.project_id == project_id)
            .filter(CapPoam.project_id == project_id)
            .filter(WBS.project_id == project_id)
            .filter(WorkflowFlowchart.project_id == project_id)
            .filter(Project.id == project_id)
            .filter(ProjectEvaluation.project_id == project_id)
            .all()
        )

        return approval_workflows


def get_all_approval_workflows_user(db: Session, user_id: int):
    approval_workflows = (
        db.query(ApprovalWorkflow).filter(ApprovalWorkflow.owner_id == user_id).all()
    )
    return approval_workflows


def get_approval_workflow(db: Session, id: int, tenant_id: int, user_id: int):
    approval_workflow = db.query(ApprovalWorkflow).filter(ApprovalWorkflow.id == id).first()

    return approval_workflow


async def create_approval_workflow(
    db: Session,
    approval_workflow: CreateApprovalWorkflow,
    user_id: int,
    tenant_id: int,
):
    new_approval_workflow = ApprovalWorkflow(**approval_workflow.dict(), tenant_id=tenant_id)
    db.add(new_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=new_approval_workflow.id,
        author_id=user_id,
        history=f"New approval workflow {approval_workflow.name} created.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    return new_approval_workflow


async def update_approval_workflow(
    db: Session,
    id: int,
    approval_workflow: UpdateApprovalWorkflow,
    user_id: int,
):
    # Retrieve the existing workflow once
    workflow_query = db.query(ApprovalWorkflow).filter(ApprovalWorkflow.id == id)
    existing_workflow = workflow_query.first()
    if not existing_workflow:
        return False

    # Get updated data (only fields provided)
    approval_workflow_data = approval_workflow.dict(exclude_unset=True)

    # Build a list of changes for history recording
    changes = []
    fields_to_check = ["name", "description", "status", "due_date", "is_private", "owner_id"]
    for field in fields_to_check:
        existing_value = getattr(existing_workflow, field)
        new_value = approval_workflow_data.get(field)
        if new_value is not None and existing_value != new_value:
            changes.append(f"Updated {field.replace('_', ' ')} to {new_value}")

    # Post history for each change
    for change in changes:
        history_obj = CreateApprovalWorkflowHistory(
            approval_workflow_id=id,
            author_id=user_id,
            history=change,
        )
        history = await post_history(db, history_obj)
        LOGGER.info(history)

    # Build a digest of all changes for notifications
    all_changes = ".    ".join(changes)
    if all_changes:
        full_link = frontend_server_url + f"/approval_workflows/{id}"

        # Notification for owner
        owner_id = existing_workflow.owner_id
        owner_notif = UserNotifications(
            user_id=owner_id,
            notification_data_type="approval_workflow",
            notification_data_id=id,
            notification_data_path=f"/approval_workflows/{id}",
            notification_message=all_changes,
        )
        db.add(owner_notif)
        # Retrieve owner's settings and send email/SMS if enabled.
        owner_notif_settings = (
            db.query(UserNotificationSettings).filter_by(user_id=owner_id).first()
        )
        if owner_notif_settings:
            owner = db.query(User).filter_by(id=owner_id).first()
            if owner_notif_settings.assigned_email:
                await send_assigned_email(
                    subject="Approval Workflow Updated",
                    email=owner.email,
                    message=f"{all_changes} Link: {full_link}",
                )
            if owner_notif_settings.assigned_sms:
                # Implement your sms sending function accordingly.
                await send_sms(owner.phone_no, f"{all_changes} Link: {full_link}")

        # Notifications for approvers
        approvers = db.query(Approval).filter(Approval.approval_workflow_id == id).all()
        for approver in approvers:
            notif = UserNotifications(
                user_id=approver.user_id,
                notification_data_type="approval_workflow",
                notification_data_id=id,
                notification_data_path=f"/approval_workflows/{id}",
                notification_message=all_changes,
            )
            db.add(notif)
            settings = (
                db.query(UserNotificationSettings).filter_by(user_id=approver.user_id).first()
            )
            if settings and settings.assigned_email:
                approver_user = db.query(User).filter_by(id=approver.user_id).first()
                await send_assigned_email(
                    subject="Approval Workflow Updated",
                    email=approver_user.email,
                    message=f"{all_changes} Link: {full_link}",
                )
            if settings and settings.assigned_sms:
                # Implement your sms sending function accordingly.
                await send_sms(approver_user.phone_no, f"{all_changes} Link: {full_link}")
        # Notifications for stakeholders
        stakeholders = db.query(ApprovalStakeholder).filter_by(approval_workflow_id=id).all()
        for stakeholder in stakeholders:
            notif = UserNotifications(
                user_id=stakeholder.user_id,
                notification_data_type="approval_workflow",
                notification_data_id=id,
                notification_data_path=f"/approval_workflows/{id}",
                notification_message=all_changes,
            )
            db.add(notif)
            settings = (
                db.query(UserNotificationSettings).filter_by(user_id=stakeholder.user_id).first()
            )
            if settings and settings.assigned_email:
                stakeholder_user = db.query(User).filter_by(id=stakeholder.user_id).first()
                await send_assigned_email(
                    subject="Approval Workflow Updated",
                    email=stakeholder_user.email,
                    message=f"{all_changes} Link: {full_link}",
                )
            if settings and settings.assigned_sms:
                # Implement your sms sending function accordingly.
                await send_sms(stakeholder_user.phone_no, f"{all_changes} Link: {full_link}")
        db.commit()  # Commit all notifications in a single transaction

    # Update the existing workflow with new data
    workflow_query.update(approval_workflow_data)
    db.commit()
    return workflow_query.first()


async def delete_approval_workflow(db: Session, id: int, user_id: int, tenant_id: int):
    existing_approval_workflow = filter_by_tenant(db, ApprovalWorkflow, tenant_id).filter(
        ApprovalWorkflow.id == id
    )
    if not existing_approval_workflow.first():
        return False

    my_existing_approval_workflow = existing_approval_workflow.first()

    all_changes = f"Approval workflow {my_existing_approval_workflow.name} deleted."

    full_link = frontend_server_url + f"/approval_workflows/{id}"

    # Notification for owner
    owner_id = my_existing_approval_workflow.owner_id
    owner_notif = UserNotifications(
        user_id=owner_id,
        notification_data_type="approval_workflow",
        notification_data_id=id,
        notification_data_path=f"/approval_workflows/{id}",
        notification_message=all_changes,
    )
    db.add(owner_notif)
    # Retrieve owner's settings and send email/SMS if enabled.
    owner_notif_settings = db.query(UserNotificationSettings).filter_by(user_id=owner_id).first()
    if owner_notif_settings:
        owner = db.query(User).filter_by(id=owner_id).first()
        if owner_notif_settings.assigned_email:
            await send_assigned_email(
                subject="Approval Workflow Deleted",
                email=owner.email,
                message=f"{all_changes} Link: {full_link}",
            )
        if owner_notif_settings.assigned_sms:
            # Implement your sms sending function accordingly.
            await send_sms(owner.phone_no, f"{all_changes} Link: {full_link}")

    # Notifications for approvers
    approvers = db.query(Approval).filter(Approval.approval_workflow_id == id).all()
    for approver in approvers:
        notif = UserNotifications(
            user_id=approver.user_id,
            notification_data_type="approval_workflow",
            notification_data_id=id,
            notification_data_path=f"/approval_workflows/{id}",
            notification_message=all_changes,
        )
        db.add(notif)
        settings = db.query(UserNotificationSettings).filter_by(user_id=approver.user_id).first()
        if settings and settings.assigned_email:
            approver_user = db.query(User).filter_by(id=approver.user_id).first()
            await send_assigned_email(
                subject="Approval Workflow Deleted",
                email=approver_user.email,
                message=f"{all_changes} Link: {full_link}",
            )
        if settings and settings.assigned_sms:
            # Implement your sms sending function accordingly.
            await send_sms(approver_user.phone_no, f"{all_changes} Link: {full_link}")
    # Notifications for stakeholders
    stakeholders = db.query(ApprovalStakeholder).filter_by(approval_workflow_id=id).all()
    for stakeholder in stakeholders:
        notif = UserNotifications(
            user_id=stakeholder.user_id,
            notification_data_type="approval_workflow",
            notification_data_id=id,
            notification_data_path=f"/approval_workflows/{id}",
            notification_message=all_changes,
        )
        db.add(notif)
        settings = db.query(UserNotificationSettings).filter_by(user_id=stakeholder.user_id).first()
        if settings and settings.assigned_email:
            stakeholder_user = db.query(User).filter_by(id=stakeholder.user_id).first()
            await send_assigned_email(
                subject="Approval Workflow Deleted",
                email=stakeholder_user.email,
                message=f"{all_changes} Link: {full_link}",
            )
        if settings and settings.assigned_sms:
            # Implement your sms sending function accordingly.
            await send_sms(stakeholder_user.phone_no, f"{all_changes} Link: {full_link}")
    db.commit()  # Commit all notifications in a single transaction

    # delete all associations
    db.query(TaskApprovalWorkflow).filter(TaskApprovalWorkflow.approval_workflow_id == id).delete()
    db.query(RiskApprovalWorkflow).filter(RiskApprovalWorkflow.approval_workflow_id == id).delete()
    db.query(AuditTestApprovalWorkflow).filter(
        AuditTestApprovalWorkflow.approval_workflow_id == id
    ).delete()
    db.query(AssessmentApprovalWorkflow).filter(
        AssessmentApprovalWorkflow.approval_workflow_id == id
    ).delete()
    db.query(ExceptionApprovalWorkflow).filter(
        ExceptionApprovalWorkflow.approval_workflow_id == id
    ).delete()
    db.query(DocumentApprovalWorkflow).filter(
        DocumentApprovalWorkflow.approval_workflow_id == id
    ).delete()
    db.query(ProjectApprovalWorkflow).filter(
        ProjectApprovalWorkflow.approval_workflow_id == id
    ).delete()
    db.query(ProjectControlApprovalWorkflow).filter(
        ProjectControlApprovalWorkflow.approval_workflow_id == id
    ).delete()
    db.query(WorkflowFlowchartApprovalWorkflow).filter(
        WorkflowFlowchartApprovalWorkflow.approval_workflow_id == id
    ).delete()
    db.query(WBSApprovalWorkflow).filter(WBSApprovalWorkflow.approval_workflow_id == id).delete()
    db.query(ProjectEvaluationApprovalWorkflow).filter(
        ProjectEvaluationApprovalWorkflow.approval_workflow_id == id
    ).delete()
    db.query(CapPoamApprovalWorkflow).filter(
        CapPoamApprovalWorkflow.approval_workflow_id == id
    ).delete()
    db.query(ApprovalWorkflowHistory).filter(
        ApprovalWorkflowHistory.approval_workflow_id == id
    ).delete()
    db.delete(my_existing_approval_workflow)
    db.commit()

    return True


async def create_approval_workflow_from_template(
    approval_workflow: CreateApprovalWorkflowUseTemplate,
    db: Session,
    user_id: int,
    tenant_id: int,
):
    # Get the workflow template from the database
    workflow_template = (
        db.query(ApprovalWorkflowTemplate)
        .filter(ApprovalWorkflowTemplate.id == approval_workflow.template_id)
        .first()
    )
    if workflow_template is None:
        return 0
    # get name, description, due_date, is_private, owner_id from template and
    approval_workflow_data = {
        "name": workflow_template.name,
        "description": workflow_template.description,
        "due_date": workflow_template.due_date,
        "is_private": workflow_template.is_private,
        "owner_id": workflow_template.owner_id,
    }
    # create new approval workflow
    new_approval_workflow = ApprovalWorkflow(**approval_workflow_data, tenant_id=tenant_id)

    db.add(new_approval_workflow)
    db.commit()
    db.flush()

    # create all approvals
    new_approvals = workflow_template.approvals
    for approval in new_approvals:
        LOGGER.info(f"approval {approval}")
        new_approval = CreateApproval(
            approval_workflow_id=new_approval_workflow.id,
            user_id=approval["id"],
            weight=approval["weight"],
        )
        await create_approval(db, new_approval, user_id)
    # create all stakeholders
    new_stakeholders = workflow_template.stakeholders
    for stakeholder in new_stakeholders:
        new_stakeholder = CreateApprovalStakeholder(
            approval_workflow_id=new_approval_workflow.id, user_id=stakeholder["id"]
        )
        await create_approval_stakeholder(db, new_stakeholder, user_id)
    # associate with type of object
    if approval_workflow.data_type == "projects":
        # associate with project
        new_assoc = CreateProjectApproval(
            project_id=approval_workflow.object_id, approval_workflow_id=new_approval_workflow.id
        )
        await create_project_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "audit_tests":
        # associate with audit_test
        new_assoc = CreateAuditTestApproval(
            audit_test_id=approval_workflow.object_id, approval_workflow_id=new_approval_workflow.id
        )
        await create_audit_test_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "assessments":
        # associate with assessment
        new_assoc = CreateAssessmentApproval(
            assessment_id=approval_workflow.object_id, approval_workflow_id=new_approval_workflow.id
        )
        await create_assessment_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "exceptions":
        # associate with exception
        new_assoc = CreateExceptionApproval(
            exception_id=approval_workflow.object_id, approval_workflow_id=new_approval_workflow.id
        )
        await create_exception_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "documents":
        # associate with document
        new_assoc = CreateDocumentApproval(
            document_id=approval_workflow.object_id, approval_workflow_id=new_approval_workflow.id
        )
        await create_document_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "tasks":
        # associate with task
        new_assoc = CreateTaskApproval(
            task_id=approval_workflow.object_id, approval_workflow_id=new_approval_workflow.id
        )
        await create_task_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "risks":
        # associate with risk
        new_assoc = CreateRiskApproval(
            risk_id=approval_workflow.object_id, approval_workflow_id=new_approval_workflow.id
        )
        await create_risk_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "project_evaluations":
        # associate with project evaluation
        new_assoc = CreateProjectEvaluationApproval(
            project_evaluation_id=approval_workflow.object_id,
            approval_workflow_id=new_approval_workflow.id,
        )
        await create_project_evaluation_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "projects":
        # associate with project
        new_assoc = CreateProjectApproval(
            project_id=approval_workflow.object_id, approval_workflow_id=new_approval_workflow.id
        )
        await create_project_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "cap_poams":
        # associate with CAP POAM
        new_assoc = CreateCapPoamApproval(
            cap_poam_id=approval_workflow.object_id, approval_workflow_id=new_approval_workflow.id
        )
        await create_cap_poam_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "project_controls":
        # associate with project control
        new_assoc = CreateProjectControlApproval(
            project_control_id=approval_workflow.object_id,
            approval_workflow_id=new_approval_workflow.id,
        )
        await create_project_control_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "workflow_flowcharts":
        # associate with workflow flowchart
        new_assoc = CreateWorkflowFlowchartApproval(
            workflow_flowchart_id=approval_workflow.object_id,
            approval_workflow_id=new_approval_workflow.id,
        )
        await create_workflow_flowchart_approval_workflow(db, new_assoc, user_id)
    if approval_workflow.data_type == "wbs":
        # associate with wbs
        new_assoc = CreateWBSApproval(
            wbs_id=approval_workflow.object_id, approval_workflow_id=new_approval_workflow.id
        )
        await create_workflow_flowchart_approval_workflow(db, new_assoc, user_id)
    return new_approval_workflow


async def check_due_date_approval_workflow_automate_status_rejected(
    db: Session,
    user_id: int,
):
    # Step 1: Find all workflows with past due date and not rejected
    workflows = (
        db.query(ApprovalWorkflow)
        .filter(ApprovalWorkflow.due_date < date.today())
        .filter(ApprovalWorkflow.status != "rejected")
        .all()
    )

    updated_count = 0

    for wf in workflows:
        wf.status = "rejected"
        updated_count += 1

        # Create history entry
        history_obj = CreateApprovalWorkflowHistory(
            approval_workflow_id=wf.id,
            author_id=user_id,
            history="Status automatically set to 'rejected' due to due date passing.",
        )
        db.add(ApprovalWorkflowHistory(**history_obj.dict()))

    db.commit()

    return f"Updated status to 'rejected' for {updated_count} approval workflows and logged history entries."


# Approval ######
def get_all_approvals_for_approval_workflow(db: Session, approval_workflow_id: int, user_id: int):
    approvals = (
        db.query(Approval).filter(Approval.approval_workflow_id == approval_workflow_id).all()
    )

    return approvals


def get_approval(db: Session, id: int, user_id: int):
    approval = db.query(Approval).filter(Approval.id == id).first()

    return approval


async def create_approval(
    db: Session,
    approval: CreateApproval,
    user_id: int,
):
    new_approval = Approval(**approval.dict())
    db.add(new_approval)
    db.commit()

    message = f"Approval added to approval workflow."
    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=approval.approval_workflow_id,
        author_id=user_id,
        history=message,
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    full_link = frontend_server_url + f"/approval_workflows/{approval.approval_workflow_id}"

    my_existing_approval_workflow = (
        db.query(ApprovalWorkflow)
        .filter(approval.approval_workflow_id == ApprovalWorkflow.id)
        .first()
    )
    # Notification for owner
    owner_id = my_existing_approval_workflow.owner_id
    owner_notif = UserNotifications(
        user_id=owner_id,
        notification_data_type="approval_workflow",
        notification_data_id=approval.approval_workflow_id,
        notification_data_path=f"/approval_workflows/{approval.approval_workflow_id}",
        notification_message=message,
    )
    db.add(owner_notif)
    # Retrieve owner's settings and send email/SMS if enabled.
    owner_notif_settings = db.query(UserNotificationSettings).filter_by(user_id=owner_id).first()
    if owner_notif_settings:
        owner = db.query(User).filter_by(id=owner_id).first()
        if owner_notif_settings.assigned_email:
            await send_assigned_email(
                subject="Approval Workflow Updated",
                email=owner.email,
                message=f"{message} Link: {full_link}",
            )
        if owner_notif_settings.assigned_sms:
            # Implement your sms sending function accordingly.
            await send_sms(owner.phone_no, f"{message} Link: {full_link}")

    # Notifications for approvers
    approvers = (
        db.query(Approval)
        .filter(Approval.approval_workflow_id == approval.approval_workflow_id)
        .all()
    )
    for approver in approvers:
        notif = UserNotifications(
            user_id=approver.user_id,
            notification_data_type="approval_workflow",
            notification_data_id=approval.approval_workflow_id,
            notification_data_path=f"/approval_workflows/{approval.approval_workflow_id}",
            notification_message=message,
        )
        db.add(notif)
        settings = db.query(UserNotificationSettings).filter_by(user_id=approver.user_id).first()
        if settings and settings.assigned_email:
            approver_user = db.query(User).filter_by(id=approver.user_id).first()
            await send_assigned_email(
                subject="Approval Workflow Updated",
                email=approver_user.email,
                message=f"{message} Link: {full_link}",
            )
        if settings and settings.assigned_sms:
            # Implement your sms sending function accordingly.
            await send_sms(approver_user.phone_no, f"{message} Link: {full_link}")
    # Notifications for stakeholders
    stakeholders = (
        db.query(ApprovalStakeholder)
        .filter_by(approval_workflow_id=my_existing_approval_workflow.id)
        .all()
    )
    for stakeholder in stakeholders:
        notif = UserNotifications(
            user_id=stakeholder.user_id,
            notification_data_type="approval_workflow",
            notification_data_id=approval.approval_workflow_id,
            notification_data_path=f"/approval_workflows/{approval.approval_workflow_id}",
            notification_message=message,
        )
        db.add(notif)
        settings = db.query(UserNotificationSettings).filter_by(user_id=stakeholder.user_id).first()
        if settings and settings.assigned_email:
            stakeholder_user = db.query(User).filter_by(id=stakeholder.user_id).first()
            await send_assigned_email(
                subject="Approval Workflow Updated",
                email=stakeholder_user.email,
                message=f"{message} Link: {full_link}",
            )
        if settings and settings.assigned_sms:
            # Implement your sms sending function accordingly.
            await send_sms(stakeholder_user.phone_no, f"{message} Link: {full_link}")

    return new_approval


async def update_approval(
    db: Session,
    id: int,
    approval: UpdateApproval,
    user_id: int,
):
    existing_approval = db.query(Approval).filter(Approval.id == id)
    if not existing_approval.first():
        return False

    approval_data = approval.dict(exclude_unset=True)

    # Build a list of changes for history recording
    changes = []
    fields_to_check = ["approval_workflow_id", "user_id", "status", "weight", "completed_date"]
    for field in fields_to_check:
        existing_value = getattr(existing_approval.first(), field)
        new_value = approval_data.get(field)
        if new_value is not None and existing_value != new_value:
            changes.append(f"Updated {field.replace('_', ' ')} to {new_value}")

    # Post history for each change
    for change in changes:
        history_obj = CreateApprovalWorkflowHistory(
            approval_workflow_id=id,
            author_id=user_id,
            history=change,
        )
        history = await post_history(db, history_obj)
        LOGGER.info(history)

    existing_workflow = (
        db.query(ApprovalWorkflow)
        .filter(ApprovalWorkflow.id == existing_approval.first().approval_workflow_id)
        .first()
    )
    # Build a digest of all changes for notifications
    all_changes = ".    ".join(changes)
    if all_changes:
        full_link = frontend_server_url + f"/approval_workflows/{id}"

        # Notification for owner
        owner_id = existing_workflow.owner_id
        owner_notif = UserNotifications(
            user_id=owner_id,
            notification_data_type="approval_workflow",
            notification_data_id=id,
            notification_data_path=f"/approval_workflows/{id}",
            notification_message=all_changes,
        )
        db.add(owner_notif)
        # Retrieve owner's settings and send email/SMS if enabled.
        owner_notif_settings = (
            db.query(UserNotificationSettings).filter_by(user_id=owner_id).first()
        )
        if owner_notif_settings:
            owner = db.query(User).filter_by(id=owner_id).first()
            if owner_notif_settings.assigned_email:
                await send_assigned_email(
                    subject="Approval Workflow Updated",
                    email=owner.email,
                    message=f"{all_changes} Link: {full_link}",
                )
            if owner_notif_settings.assigned_sms:
                # Implement your sms sending function accordingly.
                await send_sms(owner.phone_no, f"{all_changes} Link: {full_link}")

        # Notifications for approvers
        approvers = db.query(Approval).filter(Approval.approval_workflow_id == id).all()
        for approver in approvers:
            notif = UserNotifications(
                user_id=approver.user_id,
                notification_data_type="approval_workflow",
                notification_data_id=id,
                notification_data_path=f"/approval_workflows/{id}",
                notification_message=all_changes,
            )
            db.add(notif)
            settings = (
                db.query(UserNotificationSettings).filter_by(user_id=approver.user_id).first()
            )
            if settings and settings.assigned_email:
                approver_user = db.query(User).filter_by(id=approver.user_id).first()
                await send_assigned_email(
                    subject="Approval Workflow Updated",
                    email=approver_user.email,
                    message=f"{all_changes} Link: {full_link}",
                )
            if settings and settings.assigned_sms:
                # Implement your sms sending function accordingly.
                await send_sms(approver_user.phone_no, f"{all_changes} Link: {full_link}")
        # Notifications for stakeholders
        stakeholders = db.query(ApprovalStakeholder).filter_by(approval_workflow_id=id).all()
        for stakeholder in stakeholders:
            notif = UserNotifications(
                user_id=stakeholder.user_id,
                notification_data_type="approval_workflow",
                notification_data_id=id,
                notification_data_path=f"/approval_workflows/{id}",
                notification_message=all_changes,
            )
            db.add(notif)
            settings = (
                db.query(UserNotificationSettings).filter_by(user_id=stakeholder.user_id).first()
            )
            if settings and settings.assigned_email:
                stakeholder_user = db.query(User).filter_by(id=stakeholder.user_id).first()
                await send_assigned_email(
                    subject="Approval Workflow Updated",
                    email=stakeholder_user.email,
                    message=f"{all_changes} Link: {full_link}",
                )
            if settings and settings.assigned_sms:
                # Implement your sms sending function accordingly.
                await send_sms(stakeholder_user.phone_no, f"{all_changes} Link: {full_link}")
        db.commit()  # Commit all notifications in a single transaction

    existing_approval.update(approval_data)
    db.commit()
    return existing_approval.first()


async def delete_approval(db: Session, user_id: int, id: int):
    existing_approval = db.query(Approval).filter(Approval.id == id)
    if not existing_approval.first():
        return False

    my_existing_approval = existing_approval.first()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_approval.approval_workflow_id,
        author_id=user_id,
        history=f"Approval deleted from approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    all_changes = f"Approval deleted from approval workflow."

    full_link = frontend_server_url + f"/approval_workflows/{id}"

    existing_workflow = (
        db.query(ApprovalWorkflow)
        .filter(ApprovalWorkflow.id == my_existing_approval.approval_workflow_id)
        .first()
    )

    # Notification for owner
    owner_id = existing_workflow.owner_id
    owner_notif = UserNotifications(
        user_id=owner_id,
        notification_data_type="approval_workflow",
        notification_data_id=id,
        notification_data_path=f"/approval_workflows/{id}",
        notification_message=all_changes,
    )
    db.add(owner_notif)
    # Retrieve owner's settings and send email/SMS if enabled.
    owner_notif_settings = db.query(UserNotificationSettings).filter_by(user_id=owner_id).first()
    if owner_notif_settings:
        owner = db.query(User).filter_by(id=owner_id).first()
        if owner_notif_settings.assigned_email:
            await send_assigned_email(
                subject="Approval Workflow Updated",
                email=owner.email,
                message=f"{all_changes} Link: {full_link}",
            )
        if owner_notif_settings.assigned_sms:
            # Implement your sms sending function accordingly.
            await send_sms(owner.phone_no, f"{all_changes} Link: {full_link}")

    # Notifications for approvers
    approvers = db.query(Approval).filter(Approval.approval_workflow_id == id).all()
    for approver in approvers:
        notif = UserNotifications(
            user_id=approver.user_id,
            notification_data_type="approval_workflow",
            notification_data_id=id,
            notification_data_path=f"/approval_workflows/{id}",
            notification_message=all_changes,
        )
        db.add(notif)
        settings = db.query(UserNotificationSettings).filter_by(user_id=approver.user_id).first()
        if settings and settings.assigned_email:
            approver_user = db.query(User).filter_by(id=approver.user_id).first()
            await send_assigned_email(
                subject="Approval Workflow Updated",
                email=approver_user.email,
                message=f"{all_changes} Link: {full_link}",
            )
        if settings and settings.assigned_sms:
            # Implement your sms sending function accordingly.
            await send_sms(approver_user.phone_no, f"{all_changes} Link: {full_link}")
    # Notifications for stakeholders
    stakeholders = db.query(ApprovalStakeholder).filter_by(approval_workflow_id=id).all()
    for stakeholder in stakeholders:
        notif = UserNotifications(
            user_id=stakeholder.user_id,
            notification_data_type="approval_workflow",
            notification_data_id=id,
            notification_data_path=f"/approval_workflows/{id}",
            notification_message=all_changes,
        )
        db.add(notif)
        settings = db.query(UserNotificationSettings).filter_by(user_id=stakeholder.user_id).first()
        if settings and settings.assigned_email:
            stakeholder_user = db.query(User).filter_by(id=stakeholder.user_id).first()
            await send_assigned_email(
                subject="Approval Workflow Updated",
                email=stakeholder_user.email,
                message=f"{all_changes} Link: {full_link}",
            )
        if settings and settings.assigned_sms:
            # Implement your sms sending function accordingly.
            await send_sms(stakeholder_user.phone_no, f"{all_changes} Link: {full_link}")
    db.commit()  # Commit all notifications in a single transaction

    db.delete(my_existing_approval)
    db.commit()

    return True


# Approval Stakeholder ######
def get_all_approval_stakeholders_for_approval_workflow(
    db: Session, approval_workflow_id: int, user_id: int
):
    approval_stakeholders = (
        db.query(ApprovalStakeholder)
        .filter(ApprovalStakeholder.approval_workflow_id == approval_workflow_id)
        .all()
    )

    return approval_stakeholders


def get_approval_stakeholder(db: Session, id: int, user_id: int):
    approval = db.query(ApprovalStakeholder).filter(ApprovalStakeholder.id == id).first()

    return approval


async def create_approval_stakeholder(
    db: Session,
    approval_stakeholder: CreateApprovalStakeholder,
    user_id: int,
):
    new_approval_stakeholder = ApprovalStakeholder(**approval_stakeholder.dict())
    db.add(new_approval_stakeholder)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=approval_stakeholder.approval_workflow_id,
        author_id=user_id,
        history=f"Approval stakeholder added to approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Create User notification for added stakeholder
    # Notify the stakeholder who has been added if their settings are on for that

    return new_approval_stakeholder


async def update_approval_stakeholder(
    db: Session,
    id: int,
    approval_stakeholder: UpdateApprovalStakeholder,
    user_id: int,
):
    existing_approval_stakeholder = db.query(ApprovalStakeholder).filter(
        ApprovalStakeholder.id == id
    )
    if not existing_approval_stakeholder.first():
        return False

    approval_stakeholder_data = approval_stakeholder.dict(exclude_unset=True)

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=approval_stakeholder.approval_workflow_id,
        author_id=user_id,
        history=f"Approval stakeholder updated for approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    existing_approval_stakeholder.update(approval_stakeholder_data)
    db.commit()
    return existing_approval_stakeholder


async def delete_approval_stakeholder(db: Session, user_id: int, id: int):
    existing_approval_stakeholder = db.query(ApprovalStakeholder).filter(
        ApprovalStakeholder.id == id
    )
    if not existing_approval_stakeholder.first():
        return False

    my_existing_approval_stakeholder = existing_approval_stakeholder.first()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_approval_stakeholder.approval_workflow_id,
        author_id=user_id,
        history=f"Approval stakeholder deleted from approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Create User notification for deleted stakeholder
    # Notify the stakeholder who has been deleted if their settings are on for that

    db.delete(my_existing_approval_stakeholder)
    db.commit()

    return True


# Approval Workflow Task Association ######
def get_all_approval_workflows_for_task(db: Session, task_id: int, user_id: int):
    approval_workflows = (
        db.query(ApprovalWorkflow)
        .join(
            TaskApprovalWorkflow, TaskApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id
        )
        .filter(TaskApprovalWorkflow.task_id == task_id)
        .all()
    )

    return approval_workflows


async def create_task_approval_workflow(
    db: Session,
    task_approval_workflow: CreateTaskApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(TaskApprovalWorkflow).filter(
        TaskApprovalWorkflow.approval_workflow_id == task_approval_workflow.approval_workflow_id,
        TaskApprovalWorkflow.task_id == task_approval_workflow.task_id,
    )
    if existing_assoc.first():
        return False

    new_task_approval_workflow = TaskApprovalWorkflow(**task_approval_workflow.dict())
    db.add(new_task_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=task_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Task associated with approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for task history
    task_history = TaskHistory(
        comments="Task associated with approval workflow.",
        task_id=task_approval_workflow.task_id,
        updated_by_id=user_id,
    )
    db.add(task_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    return new_task_approval_workflow


async def update_task_approval_workflow(
    db: Session,
    id: int,
    task_approval_workflow: UpdateTaskApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(TaskApprovalWorkflow).filter(
        TaskApprovalWorkflow.approval_workflow_id == task_approval_workflow.approval_workflow_id,
        TaskApprovalWorkflow.task_id == task_approval_workflow.task_id,
    )
    if existing_assoc.first():
        return False

    # see if the relationship already exists
    existing_task_approval_workflow = (
        db.query(TaskApprovalWorkflow)
        .filter(
            task_approval_workflow.approval_workflow_id == TaskApprovalWorkflow.approval_workflow_id
        )
        .filter(TaskApprovalWorkflow.id == id)
    )
    if existing_task_approval_workflow.first():
        return False

    task_approval_workflow_data = task_approval_workflow.dict(exclude_unset=True)

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=task_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Task association updated for approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for task history
    task_history = TaskHistory(
        comments="Task association updated for approval workflow.",
        task_id=task_approval_workflow.task_id,
        updated_by_id=user_id,
    )
    db.add(task_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_task_approval_workflow.update(task_approval_workflow_data)
    db.commit()
    return existing_task_approval_workflow


async def delete_task_approval_workflow(db: Session, user_id: int, id: int):
    existing_task_approval_workflow = db.query(TaskApprovalWorkflow).filter(
        TaskApprovalWorkflow.id == id
    )
    if not existing_task_approval_workflow.first():
        return False

    my_existing_task_approval_workflow = existing_task_approval_workflow.first()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_task_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Task association deleted from approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for task history
    task_history = TaskHistory(
        comments="Task association deleted from approval workflow.",
        task_id=my_existing_task_approval_workflow.task_id,
        updated_by_id=user_id,
    )
    db.add(task_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_task_approval_workflow)
    db.commit()

    return True


# Approval Workflow Risk Association ######
def get_all_approval_workflows_for_risk(db: Session, risk_id: int, user_id: int):
    approval_workflows = (
        db.query(ApprovalWorkflow)
        .join(
            RiskApprovalWorkflow, RiskApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id
        )
        .filter(RiskApprovalWorkflow.risk_id == risk_id)
        .all()
    )

    return approval_workflows


async def create_risk_approval_workflow(
    db: Session,
    risk_approval_workflow: CreateRiskApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(RiskApprovalWorkflow).filter(
        RiskApprovalWorkflow.approval_workflow_id == risk_approval_workflow.approval_workflow_id,
        RiskApprovalWorkflow.risk_id == risk_approval_workflow.risk_id,
    )
    if existing_assoc.first():
        return False

    new_risk_approval_workflow = RiskApprovalWorkflow(**risk_approval_workflow.dict())
    db.add(new_risk_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=new_risk_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Risk associated with approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for risk history
    risk_history = RiskHistory(
        history="Risk associated with approval workflow.",
        risk_id=new_risk_approval_workflow.risk_id,
        author_id=user_id,
    )

    db.add(risk_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    return new_risk_approval_workflow


async def update_risk_approval_workflow(
    db: Session,
    id: int,
    risk_approval_workflow: UpdateRiskApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(RiskApprovalWorkflow).filter(
        RiskApprovalWorkflow.approval_workflow_id == risk_approval_workflow.approval_workflow_id,
        RiskApprovalWorkflow.risk_id == risk_approval_workflow.risk_id,
    )
    if existing_assoc.first():
        return False

    existing_risk_approval_workflow = db.query(RiskApprovalWorkflow).filter(
        RiskApprovalWorkflow.id == id
    )
    if not existing_risk_approval_workflow.first():
        return False

    risk_approval_workflow_data = risk_approval_workflow.dict(exclude_unset=True)

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=risk_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Risk association updated for approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for risk history
    risk_history = RiskHistory(
        history="Risk association updated for approval workflow.",
        risk_id=risk_approval_workflow.risk_id,
        author_id=user_id,
    )
    db.add(risk_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_risk_approval_workflow.update(risk_approval_workflow_data)
    db.commit()
    return existing_risk_approval_workflow


async def delete_risk_approval_workflow(db: Session, user_id: int, id: int):
    existing_risk_approval_workflow = db.query(RiskApprovalWorkflow).filter(
        RiskApprovalWorkflow.id == id
    )
    if not existing_risk_approval_workflow.first():
        return False

    my_existing_risk_approval_workflow = existing_risk_approval_workflow.first()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_risk_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Risk association deleted from approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for risk history
    risk_history = RiskHistory(
        history="Risk association deleted from approval workflow.",
        risk_id=my_existing_risk_approval_workflow.risk_id,
        author_id=user_id,
    )
    db.add(risk_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_risk_approval_workflow)
    db.commit()

    return True


# Approval Workflow Audit Test Association ######
def get_all_approval_workflows_for_audit_test(db: Session, audit_test_id: int, user_id: int):
    approval_workflows = (
        db.query(ApprovalWorkflow)
        .join(
            AuditTestApprovalWorkflow,
            AuditTestApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
        )
        .filter(AuditTestApprovalWorkflow.audit_test_id == audit_test_id)
        .all()
    )

    return approval_workflows


async def create_audit_test_approval_workflow(
    db: Session,
    audit_test_approval_workflow: CreateAuditTestApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(AuditTestApprovalWorkflow).filter(
        AuditTestApprovalWorkflow.approval_workflow_id
        == audit_test_approval_workflow.approval_workflow_id,
        AuditTestApprovalWorkflow.audit_test_id == audit_test_approval_workflow.audit_test_id,
    )
    if existing_assoc.first():
        return False

    new_audit_test_approval_workflow = AuditTestApprovalWorkflow(
        **audit_test_approval_workflow.dict()
    )
    db.add(new_audit_test_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=new_audit_test_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Audit test associated with approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for audit test history
    audit_test_history = AuditTestHistory(
        history="Audit test associated with approval workflow.",
        audit_test_id=new_audit_test_approval_workflow.audit_test_id,
        author_id=user_id,
    )
    db.add(audit_test_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    return new_audit_test_approval_workflow


async def update_audit_test_approval_workflow(
    db: Session,
    id: int,
    audit_test_approval_workflow: UpdateAuditTestApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(AuditTestApprovalWorkflow).filter(
        AuditTestApprovalWorkflow.approval_workflow_id
        == audit_test_approval_workflow.approval_workflow_id,
        AuditTestApprovalWorkflow.audit_test_id == audit_test_approval_workflow.audit_test_id,
    )
    if existing_assoc.first():
        return False

    existing_audit_test_approval_workflow = db.query(AuditTestApprovalWorkflow).filter(
        AuditTestApprovalWorkflow.id == id
    )
    if not existing_audit_test_approval_workflow.first():
        return False

    audit_test_approval_workflow_data = audit_test_approval_workflow.dict(exclude_unset=True)

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=audit_test_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Audit test association updated for approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for audit test history
    audit_test_history = AuditTestHistory(
        history="Audit test association updated for approval workflow.",
        audit_test_id=audit_test_approval_workflow.audit_test_id,
        author_id=user_id,
    )
    db.add(audit_test_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_audit_test_approval_workflow.update(audit_test_approval_workflow_data)
    db.commit()
    return existing_audit_test_approval_workflow


async def delete_audit_test_approval_workflow(db: Session, user_id: int, id: int):
    existing_audit_test_approval_workflow = db.query(AuditTestApprovalWorkflow).filter(
        AuditTestApprovalWorkflow.id == id
    )
    if not existing_audit_test_approval_workflow.first():
        return False

    my_existing_audit_test_approval_workflow = existing_audit_test_approval_workflow.first()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_audit_test_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Audit test association deleted from approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for audit test history
    audit_test_history = AuditTestHistory(
        history="Audit test association deleted from approval workflow.",
        audit_test_id=my_existing_audit_test_approval_workflow.audit_test_id,
        author_id=user_id,
    )
    db.add(audit_test_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_audit_test_approval_workflow)
    db.commit()

    return True


# Approval Workflow Project Evaluation Association ######
def get_all_approval_workflows_for_project_evaluation(
    db: Session, project_evaluation_id: int, user_id: int
):
    approval_project_evaluations = (
        db.query(ApprovalWorkflow)
        .join(
            ProjectEvaluationApprovalWorkflow,
            ProjectEvaluationApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
        )
        .filter(ProjectEvaluationApprovalWorkflow.project_evaluation_id == project_evaluation_id)
        .all()
    )

    return approval_project_evaluations


async def create_project_evaluation_approval_workflow(
    db: Session,
    project_evaluation_approval_workflow: CreateProjectEvaluationApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(ProjectEvaluationApprovalWorkflow).filter(
        ProjectEvaluationApprovalWorkflow.approval_workflow_id
        == project_evaluation_approval_workflow.approval_workflow_id,
        ProjectEvaluationApprovalWorkflow.project_evaluation_id
        == project_evaluation_approval_workflow.project_evaluation_id,
    )
    if existing_assoc.first():
        return False

    new_project_evaluation_approval_workflow = ProjectEvaluationApprovalWorkflow(
        **project_evaluation_approval_workflow.dict()
    )
    db.add(new_project_evaluation_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=project_evaluation_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Project evaluation associated with approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for project evaluation history
    proj_eval_history = ProjectEvaluationHistory(
        history="Audit test associated with approval workflow.",
        project_evaluation_id=new_project_evaluation_approval_workflow.project_evaluation_id,
        author_id=user_id,
    )

    db.add(proj_eval_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    return new_project_evaluation_approval_workflow


async def update_project_evaluation_approval_workflow(
    db: Session,
    id: int,
    project_evaluation_approval_workflow: UpdateProjectEvaluationApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(ProjectEvaluationApprovalWorkflow).filter(
        ProjectEvaluationApprovalWorkflow.approval_workflow_id
        == project_evaluation_approval_workflow.approval_workflow_id,
        ProjectEvaluationApprovalWorkflow.project_evaluation_id
        == project_evaluation_approval_workflow.project_evaluation_id,
    )
    if existing_assoc.first():
        return False

    existing_project_evaluation_approval_workflow = db.query(
        ProjectEvaluationApprovalWorkflow
    ).filter(ProjectEvaluationApprovalWorkflow.id == id)
    if not existing_project_evaluation_approval_workflow.first():
        return False

    project_evaluation_approval_workflow_data = project_evaluation_approval_workflow.dict(
        exclude_unset=True
    )

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=project_evaluation_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Project evaluation association updated for approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for project evaluation history
    proj_eval_history = ProjectEvaluationHistory(
        history="Project evaluation association updated for approval workflow.",
        project_evaluation_id=project_evaluation_approval_workflow.project_evaluation_id,
        author_id=user_id,
    )

    db.add(proj_eval_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_project_evaluation_approval_workflow.update(project_evaluation_approval_workflow_data)
    db.commit()
    return existing_project_evaluation_approval_workflow


async def delete_project_evaluation_approval_workflow(db: Session, user_id: int, id: int):
    existing_project_evaluation_approval_workflow = db.query(
        ProjectEvaluationApprovalWorkflow
    ).filter(ProjectEvaluationApprovalWorkflow.id == id)
    if not existing_project_evaluation_approval_workflow.first():
        return False

    my_existing_project_evaluation_approval_workflow = (
        existing_project_evaluation_approval_workflow.first()
    )

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_project_evaluation_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Project Evaluation association deleted from approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for project evaluation history
    proj_eval_history = ProjectEvaluationHistory(
        history="Project Evaluation association deleted from approval workflow.",
        project_evaluation_id=my_existing_project_evaluation_approval_workflow.project_evaluation_id,
        author_id=user_id,
    )

    db.add(proj_eval_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_project_evaluation_approval_workflow)
    db.commit()

    return True


# Approval Workflow Assessment Association ######
def get_all_approval_workflows_for_assessment(db: Session, assessment_id: int, user_id: int):
    approval_workflows = (
        db.query(ApprovalWorkflow)
        .join(
            AssessmentApprovalWorkflow,
            AssessmentApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
        )
        .filter(AssessmentApprovalWorkflow.assessment_id == assessment_id)
        .all()
    )

    return approval_workflows


async def create_assessment_approval_workflow(
    db: Session,
    assessment_approval_workflow: CreateAssessmentApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(AssessmentApprovalWorkflow).filter(
        AssessmentApprovalWorkflow.approval_workflow_id
        == assessment_approval_workflow.approval_workflow_id,
        AssessmentApprovalWorkflow.assessment_id == assessment_approval_workflow.assessment_id,
    )
    if existing_assoc.first():
        return False

    new_assessment_approval_workflow = AssessmentApprovalWorkflow(
        **assessment_approval_workflow.dict()
    )
    db.add(new_assessment_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=assessment_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Assessment associated with approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for assessment history
    assessment_history = AssessmentHistory(
        history="Assessment associated with approval workflow.",
        assessment_id=assessment_approval_workflow.assessment_id,
        author_id=user_id,
    )

    db.add(assessment_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    return new_assessment_approval_workflow


async def update_assessment_approval_workflow(
    db: Session,
    id: int,
    assessment_approval_workflow: UpdateAssessmentApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(AssessmentApprovalWorkflow).filter(
        AssessmentApprovalWorkflow.approval_workflow_id
        == assessment_approval_workflow.approval_workflow_id,
        AssessmentApprovalWorkflow.assessment_id == assessment_approval_workflow.assessment_id,
    )
    if existing_assoc.first():
        return False

    existing_assessment_approval_workflow = db.query(AssessmentApprovalWorkflow).filter(
        AssessmentApprovalWorkflow.id == id
    )
    if not existing_assessment_approval_workflow.first():
        return False

    assessment_approval_workflow_data = assessment_approval_workflow.dict(exclude_unset=True)

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=assessment_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Assessment association updated for approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for assessment history
    assessment_history = AssessmentHistory(
        history="Assessment association updated for approval workflow.",
        assessment_id=assessment_approval_workflow.assessment_id,
        author_id=user_id,
    )

    db.add(assessment_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_assessment_approval_workflow.update(assessment_approval_workflow_data)
    db.commit()
    return existing_assessment_approval_workflow


async def delete_assessment_approval_workflow(db: Session, user_id: int, id: int):
    existing_assessment_approval_workflow = db.query(AssessmentApprovalWorkflow).filter(
        AssessmentApprovalWorkflow.id == id
    )
    if not existing_assessment_approval_workflow.first():
        return False

    my_existing_assessment_approval_workflow = existing_assessment_approval_workflow.first()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_assessment_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Assessment association deleted from approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for assessment history
    assessment_history = AssessmentHistory(
        history="Assessment association deleted from approval workflow.",
        assessment_id=my_existing_assessment_approval_workflow.assessment_id,
        author_id=user_id,
    )

    db.add(assessment_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_assessment_approval_workflow)
    db.commit()

    return True


# Approval Workflow Exception Association ######
def get_all_approval_workflows_for_exception(db: Session, exception_id: int, user_id: int):
    approval_workflows = (
        db.query(ApprovalWorkflow)
        .join(
            ExceptionApprovalWorkflow,
            ExceptionApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
        )
        .filter(ExceptionApprovalWorkflow.exception_id == exception_id)
        .all()
    )

    return approval_workflows


async def create_exception_approval_workflow(
    db: Session,
    exception_approval_workflow: CreateExceptionApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(ExceptionApprovalWorkflow).filter(
        ExceptionApprovalWorkflow.approval_workflow_id
        == exception_approval_workflow.approval_workflow_id,
        ExceptionApprovalWorkflow.exception_id == exception_approval_workflow.exception_id,
    )
    if existing_assoc.first():
        return False

    new_exception_approval_workflow = ExceptionApprovalWorkflow(
        **exception_approval_workflow.dict()
    )
    db.add(new_exception_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=exception_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Exception associated with approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for exception history
    exception_history = ExceptionHistory(
        history="Exception associated with approval workflow.",
        exception_id=exception_approval_workflow.exception_id,
        author_id=user_id,
    )

    db.add(exception_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    return new_exception_approval_workflow


async def update_exception_approval_workflow(
    db: Session,
    id: int,
    exception_approval_workflow: UpdateExceptionApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(ExceptionApprovalWorkflow).filter(
        ExceptionApprovalWorkflow.approval_workflow_id
        == exception_approval_workflow.approval_workflow_id,
        ExceptionApprovalWorkflow.exception_id == exception_approval_workflow.exception_id,
    )
    if existing_assoc.first():
        return False

    existing_exception_approval_workflow = db.query(ExceptionApprovalWorkflow).filter(
        ExceptionApprovalWorkflow.id == id
    )
    if not existing_exception_approval_workflow.first():
        return False

    exception_approval_workflow_data = exception_approval_workflow.dict(exclude_unset=True)

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=exception_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Exception association updated for approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for exception history
    exception_history = ExceptionHistory(
        history="Exception association updated for approval workflow.",
        exception_id=exception_approval_workflow.exception_id,
        author_id=user_id,
    )

    db.add(exception_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_exception_approval_workflow.update(exception_approval_workflow_data)
    db.commit()
    return existing_exception_approval_workflow


async def delete_exception_approval_workflow(db: Session, user_id: int, id: int):
    existing_exception_approval_workflow = db.query(ExceptionApprovalWorkflow).filter(
        ExceptionApprovalWorkflow.id == id
    )
    if not existing_exception_approval_workflow.first():
        return False

    my_existing_exception_approval_workflow = existing_exception_approval_workflow.first()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_exception_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Exception association deleted from approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for exception history
    exception_history = ExceptionHistory(
        history="Exception association deleted from approval workflow.",
        exception_id=my_existing_exception_approval_workflow.exception_id,
        author_id=user_id,
    )

    db.add(exception_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_exception_approval_workflow)
    db.commit()

    return True


# Approval Workflow Document Association ######
def get_all_approval_workflows_for_document(db: Session, document_id: int, user_id: int):
    approval_workflows = (
        db.query(ApprovalWorkflow)
        .join(
            DocumentApprovalWorkflow,
            DocumentApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
        )
        .filter(DocumentApprovalWorkflow.document_id == document_id)
        .all()
    )

    return approval_workflows


async def create_document_approval_workflow(
    db: Session,
    document_approval_workflow: CreateDocumentApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(DocumentApprovalWorkflow).filter(
        DocumentApprovalWorkflow.approval_workflow_id
        == document_approval_workflow.approval_workflow_id,
        DocumentApprovalWorkflow.document_id == document_approval_workflow.document_id,
    )
    if existing_assoc.first():
        return False

    new_document_approval_workflow = DocumentApprovalWorkflow(**document_approval_workflow.dict())
    db.add(new_document_approval_workflow)
    db.commit()
    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=document_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Document associated with approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for document history
    document_history = DocumentHistory(
        history="Document associated with approval workflow.",
        document_id=document_approval_workflow.document_id,
        author_id=user_id,
    )
    db.add(**document_history.dict())
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    return new_document_approval_workflow


async def update_document_approval_workflow(
    db: Session,
    id: int,
    document_approval_workflow: UpdateDocumentApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(DocumentApprovalWorkflow).filter(
        DocumentApprovalWorkflow.approval_workflow_id
        == document_approval_workflow.approval_workflow_id,
        DocumentApprovalWorkflow.document_id == document_approval_workflow.document_id,
    )
    if existing_assoc.first():
        return False

    existing_document_approval_workflow = db.query(DocumentApprovalWorkflow).filter(
        DocumentApprovalWorkflow.id == id
    )
    if not existing_document_approval_workflow.first():
        return False

    document_approval_workflow_data = document_approval_workflow.dict(exclude_unset=True)

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=document_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Document association updated for approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for document history
    document_history = DocumentHistory(
        history="Document association updated for approval workflow.",
        document_id=document_approval_workflow.document_id,
        author_id=user_id,
    )

    db.add(document_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_document_approval_workflow.update(document_approval_workflow_data)
    db.commit()
    return existing_document_approval_workflow


async def delete_document_approval_workflow(db: Session, user_id: int, id: int):
    existing_document_approval_workflow = db.query(DocumentApprovalWorkflow).filter(
        DocumentApprovalWorkflow.id == id
    )
    if not existing_document_approval_workflow.first():
        return False

    my_existing_document_approval_workflow = existing_document_approval_workflow.first()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_document_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Document association deleted from approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for document history
    document_history = DocumentHistory(
        history="Document association deleted from approval workflow.",
        document_id=my_existing_document_approval_workflow.document_id,
        author_id=user_id,
    )

    db.add(document_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_document_approval_workflow)
    db.commit()

    return True


# Approval Workflow CapPoam Association ######
def get_all_approval_workflows_for_cap_poam(db: Session, cap_poam_id: int, user_id: int):
    approval_workflows = (
        db.query(ApprovalWorkflow)
        .join(
            CapPoamApprovalWorkflow,
            CapPoamApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
        )
        .filter(CapPoamApprovalWorkflow.cap_poam_id == cap_poam_id)
        .all()
    )

    return approval_workflows


async def create_cap_poam_approval_workflow(
    db: Session,
    cap_poam_approval_workflow: CreateCapPoamApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(CapPoamApprovalWorkflow).filter(
        CapPoamApprovalWorkflow.approval_workflow_id
        == cap_poam_approval_workflow.approval_workflow_id,
        CapPoamApprovalWorkflow.cap_poam_id == cap_poam_approval_workflow.cap_poam_id,
    )
    if existing_assoc.first():
        return False

    new_cap_poam_approval_workflow = CapPoamApprovalWorkflow(**cap_poam_approval_workflow.dict())
    db.add(new_cap_poam_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=cap_poam_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"CAP/POAM associated with approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for cap poam history
    cap_poam_history = CapPoamHistory(
        history="CAP/POAM associated with approval workflow.",
        cap_poam_id=cap_poam_approval_workflow.cap_poam_id,
        author_id=user_id,
    )

    db.add(cap_poam_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    return new_cap_poam_approval_workflow


async def update_cap_poam_approval_workflow(
    db: Session,
    id: int,
    cap_poam_approval_workflow: UpdateCapPoamApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(CapPoamApprovalWorkflow).filter(
        CapPoamApprovalWorkflow.approval_workflow_id
        == cap_poam_approval_workflow.approval_workflow_id,
        CapPoamApprovalWorkflow.cap_poam_id == cap_poam_approval_workflow.cap_poam_id,
    )
    if existing_assoc.first():
        return False

    existing_cap_poam_approval_workflow = db.query(CapPoamApprovalWorkflow).filter(
        CapPoamApprovalWorkflow.id == id
    )
    if not existing_cap_poam_approval_workflow.first():
        return False

    cap_poam_approval_workflow_data = cap_poam_approval_workflow.dict(exclude_unset=True)

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=cap_poam_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"CAP/POAM association updated for approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for cap poam history
    cap_poam_history = CapPoamHistory(
        history="CAP/POAM association updated for approval workflow.",
        cap_poam_id=cap_poam_approval_workflow.cap_poam_id,
        author_id=user_id,
    )

    db.add(cap_poam_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_cap_poam_approval_workflow.update(cap_poam_approval_workflow_data)
    db.commit()
    return existing_cap_poam_approval_workflow


async def delete_cap_poam_approval_workflow(db: Session, user_id: int, id: int):
    existing_cap_poam_approval_workflow = db.query(CapPoamApprovalWorkflow).filter(
        CapPoamApprovalWorkflow.id == id
    )
    if not existing_cap_poam_approval_workflow.first():
        return False

    my_existing_cap_poam_approval_workflow = existing_cap_poam_approval_workflow.first()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_cap_poam_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"CAP/POAM association deleted from approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for cap poam history
    cap_poam_history = CapPoamHistory(
        history="CAP/POAM association deleted from approval workflow.",
        cap_poam_id=my_existing_cap_poam_approval_workflow.cap_poam_id,
        author_id=user_id,
    )

    db.add(cap_poam_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_cap_poam_approval_workflow)
    db.commit()

    return True


# Approval Workflow WBS Association ######
def get_all_approval_workflows_for_wbs(db: Session, wbs_id: int, user_id: int):
    approval_workflows = (
        db.query(ApprovalWorkflow)
        .join(WBSApprovalWorkflow, WBSApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id)
        .filter(WBSApprovalWorkflow.wbs_id == wbs_id)
        .all()
    )

    return approval_workflows


async def create_wbs_approval_workflow(
    db: Session,
    wbs_approval_workflow: CreateWBSApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(WBSApprovalWorkflow).filter(
        WBSApprovalWorkflow.approval_workflow_id == wbs_approval_workflow.approval_workflow_id,
        WBSApprovalWorkflow.wbs_id == wbs_approval_workflow.wbs_id,
    )
    if existing_assoc.first():
        return False

    new_wbs_approval_workflow = WBSApprovalWorkflow(**wbs_approval_workflow.dict())
    db.add(new_wbs_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=wbs_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"WBS associated with approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for WBS history
    wbs_history = WBSHistory(
        history="WBS associated with approval workflow.",
        wbs_id=wbs_approval_workflow.wbs_id,
        author_id=user_id,
    )

    db.add(wbs_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    return new_wbs_approval_workflow


async def update_wbs_approval_workflow(
    db: Session,
    id: int,
    wbs_approval_workflow: UpdateWBSApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(WBSApprovalWorkflow).filter(
        WBSApprovalWorkflow.approval_workflow_id == wbs_approval_workflow.approval_workflow_id,
        WBSApprovalWorkflow.wbs_id == wbs_approval_workflow.wbs_id,
    )
    if existing_assoc.first():
        return False

    existing_wbs_approval_workflow = db.query(WBSApprovalWorkflow).filter(
        WBSApprovalWorkflow.id == id
    )
    if not existing_wbs_approval_workflow.first():
        return False

    wbs_approval_workflow_data = wbs_approval_workflow.dict(exclude_unset=True)

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=wbs_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"WBS association updated for approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for WBS history
    wbs_history = WBSHistory(
        history="WBS association updated for approval workflow.",
        wbs_id=wbs_approval_workflow.wbs_id,
        author_id=user_id,
    )

    db.add(wbs_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_wbs_approval_workflow.update(wbs_approval_workflow_data)
    db.commit()
    return existing_wbs_approval_workflow


async def delete_wbs_approval_workflow(db: Session, user_id: int, id: int):
    existing_wbs_approval_workflow = db.query(WBSApprovalWorkflow).filter(
        WBSApprovalWorkflow.id == id
    )
    if not existing_wbs_approval_workflow.first():
        return False

    my_existing_wbs_approval_workflow = existing_wbs_approval_workflow.first()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_wbs_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"WBS association deleted from approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for WBS history
    wbs_history = WBSHistory(
        history="WBS association deleted from approval workflow.",
        wbs_id=my_existing_wbs_approval_workflow.wbs_id,
        author_id=user_id,
    )

    db.add(wbs_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_wbs_approval_workflow)
    db.commit()

    return True


# Approval Workflow Workflow Flowchart Association ######
def get_all_approval_workflows_for_workflow_flowchart(
    db: Session, workflow_flowchart_id: int, user_id: int
):
    approval_workflows = (
        db.query(ApprovalWorkflow)
        .join(
            WorkflowFlowchartApprovalWorkflow,
            WorkflowFlowchartApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
        )
        .filter(WorkflowFlowchartApprovalWorkflow.workflow_flowchart_id == workflow_flowchart_id)
        .all()
    )

    return approval_workflows


async def create_workflow_flowchart_approval_workflow(
    db: Session,
    workflow_flowchart_approval_workflow: CreateWorkflowFlowchartApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(WorkflowFlowchartApprovalWorkflow).filter(
        WorkflowFlowchartApprovalWorkflow.approval_workflow_id
        == workflow_flowchart_approval_workflow.approval_workflow_id,
        WorkflowFlowchartApprovalWorkflow.workflow_flowchart_id
        == workflow_flowchart_approval_workflow.workflow_flowchart_id,
    )
    if existing_assoc.first():
        return False

    new_workflow_flowchart_approval_workflow = WorkflowFlowchartApprovalWorkflow(
        **workflow_flowchart_approval_workflow.dict()
    )
    db.add(new_workflow_flowchart_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=new_workflow_flowchart_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Workflow Flowchart associated with approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for Workflow Flowchart history
    workflow_flowchart_history = WorkflowFlowchartHistory(
        history="Workflow Flowchart associated with approval workflow.",
        workflow_flowchart_id=new_workflow_flowchart_approval_workflow.workflow_flowchart_id,
        author_id=user_id,
    )

    db.add(workflow_flowchart_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    return new_workflow_flowchart_approval_workflow


async def update_workflow_flowchart_approval_workflow(
    db: Session,
    id: int,
    workflow_flowchart_approval_workflow: UpdateWorkflowFlowchartApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(WorkflowFlowchartApprovalWorkflow).filter(
        WorkflowFlowchartApprovalWorkflow.approval_workflow_id
        == workflow_flowchart_approval_workflow.approval_workflow_id,
        WorkflowFlowchartApprovalWorkflow.workflow_flowchart_id
        == workflow_flowchart_approval_workflow.workflow_flowchart_id,
    )
    if existing_assoc.first():
        return False

    existing_workflow_flowchart_approval_workflow = db.query(
        WorkflowFlowchartApprovalWorkflow
    ).filter(WorkflowFlowchartApprovalWorkflow.id == id)
    if not existing_workflow_flowchart_approval_workflow.first():
        return False

    workflow_flowchart_approval_workflow_data = workflow_flowchart_approval_workflow.dict(
        exclude_unset=True
    )

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=workflow_flowchart_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Workflow flowchart association updated for approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for Workflow Flowchart history
    workflow_flowchart_history = WorkflowFlowchartHistory(
        history="Workflow flowchart association updated for approval workflow.",
        workflow_flowchart_id=workflow_flowchart_approval_workflow.workflow_flowchart_id,
        author_id=user_id,
    )

    db.add(workflow_flowchart_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_workflow_flowchart_approval_workflow.update(workflow_flowchart_approval_workflow_data)
    db.commit()
    return existing_workflow_flowchart_approval_workflow


async def delete_workflow_flowchart_approval_workflow(db: Session, user_id: int, id: int):
    existing_workflow_flowchart_approval_workflow = db.query(
        WorkflowFlowchartApprovalWorkflow
    ).filter(WorkflowFlowchartApprovalWorkflow.id == id)
    if not existing_workflow_flowchart_approval_workflow.first():
        return False

    my_existing_workflow_flowchart_approval_workflow = (
        existing_workflow_flowchart_approval_workflow.first()
    )

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_workflow_flowchart_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Workflow flowchart association deleted from approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for Workflow Flowchart history
    workflow_flowchart_history = WorkflowFlowchartHistory(
        history="Workflow flowchart association deleted from approval workflow.",
        workflow_flowchart_id=my_existing_workflow_flowchart_approval_workflow.workflow_flowchart_id,
        author_id=user_id,
    )

    db.add(workflow_flowchart_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_workflow_flowchart_approval_workflow)
    db.commit()

    return True


# Approval Workflow Project Association ######
def get_all_approval_workflows_for_project(db: Session, project_id: int, user_id: int):
    approval_workflows = (
        db.query(ApprovalWorkflow)
        .join(
            ProjectApprovalWorkflow,
            ProjectApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
        )
        .filter(ProjectApprovalWorkflow.project_id == project_id)
        .all()
    )

    return approval_workflows


async def create_project_approval_workflow(
    db: Session,
    project_approval_workflow: CreateProjectApproval,
    user_id: int,
):
    existing_assoc = db.query(ProjectApprovalWorkflow).filter(
        ProjectApprovalWorkflow.approval_workflow_id
        == project_approval_workflow.approval_workflow_id,
        ProjectApprovalWorkflow.project_id == project_approval_workflow.project_id,
    )
    if existing_assoc.first():
        return False

    new_project_approval_workflow = ProjectApprovalWorkflow(**project_approval_workflow.dict())
    db.add(new_project_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=new_project_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history="Project associated with approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    project_history = ProjectHistory(
        history="Project associated with approval workflow.",
        project_id=project_approval_workflow.project_id,
        author_id=user_id,
    )
    db.add(project_history)
    db.commit()

    return new_project_approval_workflow


async def update_project_approval_workflow(
    db: Session,
    id: int,
    project_approval_workflow: UpdateProjectApproval,
    user_id: int,
):
    existing_assoc = db.query(ProjectApprovalWorkflow).filter(
        ProjectApprovalWorkflow.approval_workflow_id
        == project_approval_workflow.approval_workflow_id,
        ProjectApprovalWorkflow.project_id == project_approval_workflow.project_id,
    )
    if existing_assoc.first():
        return False

    existing_project_approval_workflow = db.query(ProjectApprovalWorkflow).filter(
        ProjectApprovalWorkflow.id == id
    )
    if not existing_project_approval_workflow.first():
        return False

    project_approval_workflow_data = project_approval_workflow.dict(exclude_unset=True)

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=project_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Project association updated for approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for Project history
    project_history = ProjectHistory(
        history="Project association updated for approval workflow.",
        project_id=project_approval_workflow.project_id,
        author_id=user_id,
    )
    db.add(project_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_project_approval_workflow.update(project_approval_workflow_data)
    db.commit()
    return existing_project_approval_workflow


async def delete_project_approval_workflow(db: Session, user_id: int, id: int):
    existing_project_approval_workflow = db.query(ProjectApprovalWorkflow).filter(
        ProjectApprovalWorkflow.id == id
    )
    if not existing_project_approval_workflow.first():
        return False

    my_existing_project_approval_workflow = existing_project_approval_workflow.first()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_project_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Project association deleted from approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for Project history
    project_history = ProjectHistory(
        history="Project association updated for approval workflow.",
        project_id=my_existing_project_approval_workflow.project_id,
        author_id=user_id,
    )
    db.add(project_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_project_approval_workflow)
    db.commit()

    return True


# Approval Workflow Project Control Association ######
def get_all_approval_workflows_for_project_control(
    db: Session, project_control_id: int, user_id: int
):
    approval_workflows = (
        db.query(ApprovalWorkflow)
        .join(
            ProjectControlApprovalWorkflow,
            ProjectControlApprovalWorkflow.approval_workflow_id == ApprovalWorkflow.id,
        )
        .filter(ProjectControlApprovalWorkflow.project_control_id == project_control_id)
        .all()
    )

    return approval_workflows


async def create_project_control_approval_workflow(
    db: Session,
    project_control_approval_workflow: CreateProjectControlApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(ProjectControlApprovalWorkflow).filter(
        ProjectControlApprovalWorkflow.approval_workflow_id
        == project_control_approval_workflow.approval_workflow_id,
        ProjectControlApprovalWorkflow.project_control_id
        == project_control_approval_workflow.project_control_id,
    )
    if existing_assoc.first():
        return False

    new_project_control_approval_workflow = ProjectControlApprovalWorkflow(
        **project_control_approval_workflow.dict()
    )
    db.add(new_project_control_approval_workflow)
    db.commit()

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=new_project_control_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Project control associated with approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for Project Control history
    project_control_history = ProjectControlHistory(
        history="Project control associated with approval workflow.",
        project_control_id=new_project_control_approval_workflow.project_control_id,
        author_id=user_id,
    )
    db.add(project_control_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    return new_project_control_approval_workflow


async def update_project_control_approval_workflow(
    db: Session,
    id: int,
    project_control_approval_workflow: UpdateProjectControlApproval,
    user_id: int,
):
    # see if the relationship already exists
    existing_assoc = db.query(ProjectControlApprovalWorkflow).filter(
        ProjectControlApprovalWorkflow.approval_workflow_id
        == project_control_approval_workflow.approval_workflow_id,
        ProjectControlApprovalWorkflow.project_control_id
        == project_control_approval_workflow.project_control_id,
    )
    if existing_assoc.first():
        return False

    existing_project_control_approval_workflow = db.query(ProjectControlApprovalWorkflow).filter(
        ProjectControlApprovalWorkflow.id == id
    )
    if not existing_project_control_approval_workflow.first():
        return False

    project_control_approval_workflow_data = project_control_approval_workflow.dict(
        exclude_unset=True
    )

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=project_control_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Project control association updated for approval workflow.",
    )
    history = await post_history(db, history_obj)
    LOGGER.info(history)

    # Post history for Project Control history
    project_control_history = ProjectControlHistory(
        history="Project control association updated for approval workflow.",
        project_control_id=project_control_approval_workflow.project_control_id,
        author_id=user_id,
    )
    db.add(project_control_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    existing_project_control_approval_workflow.update(project_control_approval_workflow_data)
    db.commit()
    return existing_project_control_approval_workflow


async def delete_project_control_approval_workflow(db: Session, user_id: int, id: int):
    existing_project_control_approval_workflow = db.query(ProjectControlApprovalWorkflow).filter(
        ProjectControlApprovalWorkflow.id == id
    )
    if not existing_project_control_approval_workflow.first():
        return False

    my_existing_project_control_approval_workflow = (
        existing_project_control_approval_workflow.first()
    )

    # Post History
    history_obj = CreateApprovalWorkflowHistory(
        approval_workflow_id=my_existing_project_control_approval_workflow.approval_workflow_id,
        author_id=user_id,
        history=f"Project control association deleted from approval workflow.",
    )
    await post_history(db, history_obj)

    # Post history for Project Control history
    project_control_history = ProjectControlHistory(
        history="Project control association deleted from approval workflow.",
        project_control_id=my_existing_project_control_approval_workflow.project_control_id,
        author_id=user_id,
    )

    db.add(project_control_history)
    db.commit()

    # TODO: Notifications for users watching for updates
    # TODO: Notifications for approvers (approvals)
    # TODO: Notifications for stakeholders

    db.delete(my_existing_project_control_approval_workflow)
    db.commit()

    return True
