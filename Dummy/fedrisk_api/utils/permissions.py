from starlette.requests import Request

from datetime import datetime
from typing import Dict

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session, joinedload

from fedrisk_api.db.database import get_db
from fedrisk_api.db.models import *
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.service.payment_service import PaymentService
from config.config import Settings

from fedrisk_api.schema.subscription import ListSubscriptions
import logging

LOGGER = logging.getLogger(__name__)

# --------------------------------------- BASE PERMISSIONS --------------------------------


class BasePermission:
    def __init__(self, model, permission: str):
        self.model = model
        self.permission = permission

    def __call__(
        self,
        request: Request,
        db: Session = Depends(get_db),
        auth_user: Dict[str, str] = Depends(custom_auth),
    ):

        user = db.query(User).filter(User.email == auth_user.get("email")).first()

        if not user:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User not exists")

        if not user.is_active:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is Inactive")

        auth_user = {
            "user_id": user.id,
            "tenant_id": user.tenant_id,
            "is_superuser": user.is_superuser,
            "is_tenant_admin": user.is_tenant_admin,
            "system_role": user.system_role,
        }

        if self.has_permission(request, db, auth_user):
            return True
        return self.has_object_permission(db, auth_user, None)

    def has_permission(self, request, db, auth_user):
        LOGGER.info(f"self permission = {self.permission}")
        read_permission = db.query(
            db.query(ProjectUser)
            .join(Role, Role.id == ProjectUser.role_id)
            .join(PermissionRole, PermissionRole.role_id == Role.id)
            .join(Permission, Permission.id == PermissionRole.permission_id)
            .filter(Permission.perm_key == self.permission)
            .filter(ProjectUser.user_id == auth_user["user_id"])
            .exists()
        ).scalar()
        LOGGER.info(f"read permission = {read_permission}")
        return read_permission

    def has_object_permission(self, db, auth_user: Dict[str, str], id):
        return False


class SuperUserBasePermission(BasePermission):
    def has_permission(self, request, db, auth_user):
        return auth_user["is_superuser"]


class TenantAdminBasePermission(SuperUserBasePermission):
    def get_object_id(self, request):
        if "create" in self.permission:
            return request.query_params.get("id")
        return request.path_params.get("id")

    def has_permission(self, request, db, auth_user):
        if not super().has_permission(request, db, auth_user):
            if "subscription" not in self.permission:
                tenant = db.query(Tenant).filter(Tenant.id == auth_user["tenant_id"]).first()
                user = db.query(User).filter(User.id == auth_user["user_id"]).first()
                if not user.is_active:
                    raise HTTPException(
                        status_code=status.HTTP_406_NOT_ACCEPTABLE,
                        detail="The user does not have a license.",
                    )
                if not tenant.is_active:
                    # check subscription end
                    todays_date_time = datetime.now()
                    payment_client = PaymentService(config=Settings())
                    data = {
                        "customer": tenant.customer_id,
                        "status": "trialing",
                    }
                    payment_model = ListSubscriptions(**data)
                    trial = payment_client.list_subscriptions(payment_model)
                    if trial:
                        datetime_obj = datetime.fromtimestamp(trial.data[0].current_period_end)
                        if datetime_obj < todays_date_time:
                            raise HTTPException(
                                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                                detail="Subscription has reached its end date.",
                            )
            return auth_user["is_tenant_admin"]
        return True


class ProjectBasePermission(TenantAdminBasePermission):
    def has_object_permission(self, db, auth_user: Dict[str, str], id):
        project_exist = db.query(
            db.query(ProjectUser)
            .join(Role, Role.id == ProjectUser.role_id)
            .join(PermissionRole, PermissionRole.role_id == Role.id)
            .join(Permission, Permission.id == PermissionRole.permission_id)
            .filter(ProjectUser.user_id == auth_user["user_id"])
            .filter(ProjectUser.project_id == id)
            .filter(Permission.perm_key == self.permission)
            .exists()
        ).scalar()
        return project_exist

    def has_permission(self, request, db, auth_user):
        if not super().has_permission(request, db, auth_user):
            if self.permission == "create_project":
                return False
            elif self.permission == "view_project":
                return True
            elif request.method == "GET":
                return True
            else:
                id = self.get_object_id(request)
                return self.has_object_permission(db, auth_user, id)
        return True


# --------------------------------------- PERMISSIONS CLASSES -------------------------------
class UserPermissionsChecker(BasePermission):
    pass


class PermissionChecker(ProjectBasePermission):
    def has_permission(self, request, db: Session, auth_user: Dict[str, str]):
        user_roles = (
            db.query(User, SystemRole)
            .options(joinedload(User.system_roles))
            .filter(User.id == auth_user["user_id"])
            .all()
        )
        for user, role in user_roles:
            LOGGER.info(user)
            LOGGER.info(role)
            LOGGER.info(self.permission)
            # check if role has permission to perform this action
            permission = (
                db.query(Permission)
                .join(PermissionRole, PermissionRole.permission_id == Permission.id)
                .filter(Permission.perm_key == self.permission)
                .filter(PermissionRole.role_id == role.role_id)
                .filter(PermissionRole.tenant_id == auth_user["tenant_id"])
                .first()
            )
            LOGGER.info(permission)
            if permission is not None:
                return True

        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted")


class TenantPermissionChecker(SuperUserBasePermission):
    def has_permission(self, request, db: Session, auth_user: Dict[str, str]):
        if not super().has_permission(request, db, auth_user):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Operation not permitted"
            )
        return True


# Framework permissions
create_framework_permission = PermissionChecker(Framework, "create_framework")
view_framework_permission = PermissionChecker(Framework, "view_framework")
update_framework_permission = PermissionChecker(Framework, "update_framework")
delete_framework_permission = PermissionChecker(Framework, "delete_framework")

# Assessment permissions
view_assessment_permission = PermissionChecker(Assessment, "view_assessment")
update_assessment_permission = PermissionChecker(Assessment, "update_assessment")
create_assessment_permission = PermissionChecker(Assessment, "create_assessment_permission")
delete_assessment_permission = PermissionChecker(Assessment, "delete_assessment_permission")

# AuditTest permissions
create_audittest_permission = PermissionChecker(AuditTest, "create_audittest")
view_audittest_permission = PermissionChecker(AuditTest, "view_audittest")
update_audittest_permission = PermissionChecker(AuditTest, "update_audittest")
delete_audittest_permission = PermissionChecker(AuditTest, "delete_audittest")

# Control permissions
create_control_permission = PermissionChecker(Control, "create_control")
view_control_permission = PermissionChecker(Control, "view_control")
update_control_permission = PermissionChecker(Control, "update_control")
delete_control_permission = PermissionChecker(Control, "delete_control")

# ControlClass permissions
create_controlclass_permission = PermissionChecker(ControlClass, "create_controlclass")
view_controlclass_permission = PermissionChecker(ControlClass, "view_controlclass")
update_controlclass_permission = PermissionChecker(ControlClass, "update_controlclass")
delete_controlclass_permission = PermissionChecker(ControlClass, "delete_controlclass")

# ControlFamily permissions
create_controlfamily_permission = PermissionChecker(ControlFamily, "create_controlfamily")
view_controlfamily_permission = PermissionChecker(ControlFamily, "view_controlfamily")
update_controlfamily_permission = PermissionChecker(ControlFamily, "update_controlfamily")
delete_controlfamily_permission = PermissionChecker(ControlFamily, "delete_controlfamily")

# ControlPhase permissions
create_controlphase_permission = PermissionChecker(ControlPhase, "create_controlphase")
view_controlphase_permission = PermissionChecker(ControlPhase, "view_controlphase")
update_controlphase_permission = PermissionChecker(ControlPhase, "update_controlphase")
delete_controlphase_permission = PermissionChecker(ControlPhase, "delete_controlphase")

# ControlStatus permissions
create_controlstatus_permission = PermissionChecker(ControlStatus, "create_controlstatus")
view_controlstatus_permission = PermissionChecker(ControlStatus, "view_controlstatus")
update_controlstatus_permission = PermissionChecker(ControlStatus, "update_controlstatus")
delete_controlstatus_permission = PermissionChecker(ControlStatus, "delete_controlstatus")

# Document permissions
create_document_permission = PermissionChecker(Document, "create_document")
view_document_permission = PermissionChecker(Document, "view_document")
update_document_permission = PermissionChecker(Document, "update_document")
delete_document_permission = PermissionChecker(Document, "delete_document")
download_document_permission = PermissionChecker(Document, "download_document")

# Exception permissions
create_exception_permission = PermissionChecker(Exception, "create_exception")
view_exception_permission = PermissionChecker(Exception, "view_exception")
update_exception_permission = PermissionChecker(Exception, "update_exception")
delete_exception_permission = PermissionChecker(Exception, "delete_exception")

# Frequency permissions
create_frequency_permission = PermissionChecker(Frequency, "create_frequency")
view_frequency_permission = PermissionChecker(Frequency, "view_frequency")
update_frequency_permission = PermissionChecker(Frequency, "update_frequency")
delete_frequency_permission = PermissionChecker(Frequency, "delete_frequency")

# Keyword permissions
create_keyword_permission = PermissionChecker(Keyword, "create_keyword")
view_keyword_permission = PermissionChecker(Keyword, "view_keyword")
update_keyword_permission = PermissionChecker(Keyword, "update_keyword")
delete_keyword_permission = PermissionChecker(Keyword, "delete_keyword")

# Project permissions
create_project_permission = PermissionChecker(Project, "create_project")
view_project_permission = PermissionChecker(Project, "view_project")
update_project_permission = PermissionChecker(Project, "update_project")
delete_project_permission = PermissionChecker(Project, "delete_project")
addcontrol_project_permission = PermissionChecker(Project, "addcontrol_project")
removecontrol_project_permission = PermissionChecker(Project, "removecontrol_project")

addablecontrols_project_permission = PermissionChecker(Project, "view_addablecontrols_project")

adduser_project_permission = PermissionChecker(Project, "adduser_project")
removeuser_project_permission = PermissionChecker(Project, "removeuser_project")
changerole_project_permission = PermissionChecker(Project, "changeuserrole_project")


# ProjectEvaluation permissions
create_projectevaluation_permission = PermissionChecker(
    ProjectEvaluation, "create_projectevaluation"
)
view_projectevaluation_permission = PermissionChecker(ProjectEvaluation, "view_projectevaluation")
update_projectevaluation_permission = PermissionChecker(
    ProjectEvaluation, "update_projectevaluation"
)
delete_projectevaluation_permission = PermissionChecker(
    ProjectEvaluation, "delete_projectevaluation"
)

# Risk permissions
create_risk_permission = PermissionChecker(Risk, "create_risk")
view_risk_permission = PermissionChecker(Risk, "view_risk")
update_risk_permission = PermissionChecker(Risk, "update_risk")
delete_risk_permission = PermissionChecker(Risk, "delete_risk")

# RiskCategory permissions
create_riskcategory_permission = PermissionChecker(RiskCategory, "create_riskcategory")
view_riskcategory_permission = PermissionChecker(RiskCategory, "view_riskcategory")
update_riskcategory_permission = PermissionChecker(RiskCategory, "update_riskcategory")
delete_riskcategory_permission = PermissionChecker(RiskCategory, "delete_riskcategory")

# RiskImpact permissions
create_riskimpact_permission = PermissionChecker(RiskImpact, "create_riskimpact")
view_riskimpact_permission = PermissionChecker(RiskImpact, "view_riskimpact")
update_riskimpact_permission = PermissionChecker(RiskImpact, "update_riskimpact")
delete_riskimpact_permission = PermissionChecker(RiskImpact, "delete_riskimpact")

# RiskLikelihood permissions
create_risklikelihood_permission = PermissionChecker(RiskLikelihood, "create_risklikelihood")
view_risklikelihood_permission = PermissionChecker(RiskLikelihood, "view_risklikelihood")
update_risklikelihood_permission = PermissionChecker(RiskLikelihood, "update_risklikelihood")
delete_risklikelihood_permission = PermissionChecker(RiskLikelihood, "delete_risklikelihood")

# RiskMapping permissions
create_riskmapping_permission = PermissionChecker(RiskMapping, "create_riskmapping")
view_riskmapping_permission = PermissionChecker(RiskMapping, "view_riskmapping")
update_riskmapping_permission = PermissionChecker(RiskMapping, "update_riskmapping")
delete_riskmapping_permission = PermissionChecker(RiskMapping, "delete_riskmapping")

# RiskScore permissions
create_riskscore_permission = PermissionChecker(RiskScore, "create_riskscore")
view_riskscore_permission = PermissionChecker(RiskScore, "view_riskscore")
update_riskscore_permission = PermissionChecker(RiskScore, "update_riskscore")
delete_riskscore_permission = PermissionChecker(RiskScore, "delete_riskscore")

# RiskStatus permissions
create_riskstatus_permission = PermissionChecker(RiskStatus, "create_riskstatus")
view_riskstatus_permission = PermissionChecker(RiskStatus, "view_riskstatus")
update_riskstatus_permission = PermissionChecker(RiskStatus, "update_riskstatus")
delete_riskstatus_permission = PermissionChecker(RiskStatus, "delete_riskstatus")

# Role permissions
create_role_permission = PermissionChecker(Role, "create_role")
view_role_permission = PermissionChecker(Role, "view_role")
update_role_permission = PermissionChecker(Role, "update_role")
delete_role_permission = PermissionChecker(Role, "delete_role")

# Permission permissions
create_permission_permission = PermissionChecker(Permission, "create_permission")
view_permission_permission = PermissionChecker(Permission, "view_permission")
update_permission_permission = PermissionChecker(Permission, "update_permission")
delete_permission_permission = PermissionChecker(Permission, "delete_permission")

# Tenant permissions
create_tenant_permission = PermissionChecker(Tenant, "create_tenant")
view_tenant_permission = PermissionChecker(Tenant, "view_tenant")
update_tenant_permission = PermissionChecker(Tenant, "update_tenant")
delete_tenant_permission = PermissionChecker(Tenant, "delete_tenant")

# ProjectControl permissions
create_projectcontrol_permission = PermissionChecker(ProjectControl, "create_projectcontrol")
view_projectcontrol_permission = PermissionChecker(ProjectControl, "view_projectcontrol")
update_projectcontrol_permission = PermissionChecker(ProjectControl, "update_projectcontrol")
delete_projectcontrol_permission = PermissionChecker(ProjectControl, "delete_projectcontrol")

# summary_dashboard permissions
view_summarydashboard_permission = PermissionChecker(None, "view_summarydashboard")
view_governanceprojects_permission = PermissionChecker(None, "view_governanceprojects")
view_riskitems_permission = PermissionChecker(None, "view_riskitems")
view_compliance_permission = PermissionChecker(None, "view_compliance")
# view_pinprojects_permission = DashboardPermissionChecker(None, "view_pinprojects")
view_projecttasks_permission = PermissionChecker(None, "view_projecttasks")

# Task permissions
create_task_permission = PermissionChecker(Task, "create_task")
view_task_permission = PermissionChecker(Task, "view_task")
update_task_permission = PermissionChecker(Task, "update_task")
delete_task_permission = PermissionChecker(Task, "delete_task")

# Governance_Dashboard permission
view_governance_dashboard = PermissionChecker(None, "view_governance_dashboard")

# Compliance Dashboard permission
view_compliance_dashboard = PermissionChecker(None, "view_compliance_dashboard")

# Risk Dashboard permission
view_risk_dashboard = PermissionChecker(None, "view_risk_dashboard")

# Project Group permission
create_project_group_permission = PermissionChecker(ProjectGroup, "create_projectgroup")
view_project_group_permission = PermissionChecker(ProjectGroup, "view_projectgroup")
update_project_group_permission = PermissionChecker(ProjectGroup, "update_projectgroup")
delete_project_group_permission = PermissionChecker(ProjectGroup, "delete_projectgroup")

# User Invitation Permission
send_invitation_tenant_permission = PermissionChecker(UserInvitation, "send_invitation_tenant")

view_subscription_permission = PermissionChecker(None, "view_subscription")
create_subscription_permission = PermissionChecker(None, "create_subscription")
update_subscription_permission = PermissionChecker(None, "update_subscription")
delete_subscription_permission = PermissionChecker(None, "delete_subscription")

# Import framework permissions
create_import_framework_permission = PermissionChecker(ImportFramework, "create_import_framework")
view_import_framework_permission = PermissionChecker(ImportFramework, "view_import_framework")
download_import_framework_permission = PermissionChecker(
    ImportFramework, "download_import_framework"
)
delete_import_framework_permission = PermissionChecker(ImportFramework, "delete_import_framework")

# Chat bot permissions
create_chat_bot_prompt_permission = PermissionChecker(ChatBotPrompt, "create_chat_bot_prompt")
delete_chat_bot_prompt_permission = PermissionChecker(ChatBotPrompt, "delete_chat_bot_prompt")
update_chat_bot_prompt_permission = PermissionChecker(ChatBotPrompt, "update_chat_bot_prompt")
view_chat_bot_prompt_permission = PermissionChecker(ChatBotPrompt, "view_chat_bot_prompt")

# Help section permissions
create_help_section_permission = PermissionChecker(HelpSection, "create_help_section")
delete_help_section_permission = PermissionChecker(HelpSection, "delete_help_section")
update_help_section_permission = PermissionChecker(HelpSection, "update_help_section")
view_help_section_permission = PermissionChecker(HelpSection, "view_help_section")


# Framework Version permissions
create_framework_version_permission = PermissionChecker(
    FrameworkVersion, "create_framework_version"
)
delete_framework_version_permission = PermissionChecker(
    FrameworkVersion, "delete_framework_version"
)
update_framework_version_permission = PermissionChecker(
    FrameworkVersion, "update_framework_version"
)
view_framework_version_permission = PermissionChecker(FrameworkVersion, "view_framework_version")

# WBS permissions
create_wbs_permission = PermissionChecker(WBS, "create_wbs")
delete_wbs_permission = PermissionChecker(WBS, "delete_wbs")
update_wbs_permission = PermissionChecker(WBS, "update_wbs")
view_wbs_permission = PermissionChecker(WBS, "view_wbs")

# AWS Control permission
create_aws_control_permission = PermissionChecker(AWSControl, "create_aws_control")
delete_aws_control_permission = PermissionChecker(AWSControl, "delete_aws_control")
update_aws_control_permission = PermissionChecker(AWSControl, "update_aws_control")
view_aws_control_permission = PermissionChecker(AWSControl, "view_aws_control")

# Feature permission
create_feature_permission = PermissionChecker(Feature, "create_feature_permission")
delete_feature_permission = PermissionChecker(Feature, "delete_feature_permission")
update_feature_permission = PermissionChecker(Feature, "update_feature_permission")
view_feature_permission = PermissionChecker(Feature, "view_feature_permission")

# Feature Project permission
create_feature_project_permission = PermissionChecker(
    FeatureProject, "create_feature_project_permission"
)
delete_feature_project_permission = PermissionChecker(
    FeatureProject, "delete_feature_project_permission"
)
update_feature_project_permission = PermissionChecker(
    FeatureProject, "update_feature_project_permission"
)
view_feature_project_permission = PermissionChecker(
    FeatureProject, "view_feature_project_permission"
)

# CapPoam permissions
create_cappoam_permission = PermissionChecker(CapPoam, "create_cappoam")
view_cappoam_permission = PermissionChecker(CapPoam, "view_cappoam")
update_cappoam_permission = PermissionChecker(CapPoam, "update_cappoam")
delete_cappoam_permission = PermissionChecker(CapPoam, "delete_cappoam")

# Workflow Flowchart permissions
create_workflow_flowchart_permission = PermissionChecker(
    WorkflowFlowchart, "create_workflow_flowchart"
)
view_workflow_flowchart_permission = PermissionChecker(WorkflowFlowchart, "view_workflow_flowchart")
update_workflow_flowchart_permission = PermissionChecker(
    WorkflowFlowchart, "update_workflow_flowchart"
)
delete_workflow_flowchart_permission = PermissionChecker(
    WorkflowFlowchart, "delete_workflow_flowchart"
)

# Workflow Event permissions
create_workflow_event_permission = PermissionChecker(WorkflowEvent, "create_workflow_event")
delete_workflow_event_permission = PermissionChecker(WorkflowEvent, "delete_workflow_event")
update_workflow_event_permission = PermissionChecker(WorkflowEvent, "update_workflow_event")
view_workflow_event_permission = PermissionChecker(WorkflowEvent, "view_workflow_event")

# Workflow Template permissions
create_workflow_template_permission = PermissionChecker(
    WorkflowTemplate, "create_workflow_template"
)
delete_workflow_template_permission = PermissionChecker(
    WorkflowTemplate, "delete_workflow_template"
)
update_workflow_template_permission = PermissionChecker(
    WorkflowTemplate, "update_workflow_template"
)
view_workflow_template_permission = PermissionChecker(WorkflowTemplate, "view_workflow_template")


# Task Status permissions
create_taskstatus_permission = PermissionChecker(TaskStatus, "create_taskstatus")
delete_taskstatus_permission = PermissionChecker(TaskStatus, "delete_taskstatus")
update_taskstatus_permission = PermissionChecker(TaskStatus, "update_taskstatus")
view_taskstatus_permission = PermissionChecker(TaskStatus, "view_taskstatus")

# Task Category permissions
create_taskcategory_permission = PermissionChecker(TaskCategory, "create_taskcategory")
delete_taskcategory_permission = PermissionChecker(TaskCategory, "delete_taskcategory")
update_taskcategory_permission = PermissionChecker(TaskCategory, "update_taskcategory")
view_taskcategory_permission = PermissionChecker(TaskCategory, "view_taskcategory")

# Cost permissions
create_cost_permission = PermissionChecker(Cost, "create_cost")
delete_cost_permission = PermissionChecker(Cost, "delete_cost")
update_cost_permission = PermissionChecker(Cost, "update_cost")
view_cost_permission = PermissionChecker(Cost, "view_cost")

# Task Category permissions
create_taskcategory_permission = PermissionChecker(TaskCategory, "create_taskcategory")
delete_taskcategory_permission = PermissionChecker(TaskCategory, "delete_taskcategory")
update_taskcategory_permission = PermissionChecker(TaskCategory, "update_taskcategory")
view_taskcategory_permission = PermissionChecker(TaskCategory, "view_taskcategory")

# Workflow template event permissions
create_workflow_template_event_permission = PermissionChecker(
    WorkflowTemplateEvent, "create_workflow_template_event"
)
delete_workflow_template_event_permission = PermissionChecker(
    WorkflowTemplateEvent, "delete_workflow_template_event"
)
update_workflow_template_event_permission = PermissionChecker(
    WorkflowTemplateEvent, "update_workflow_template_event"
)
view_workflow_template_event_permission = PermissionChecker(
    WorkflowTemplateEvent, "view_workflow_template_event"
)

# Approval Workflow permissions
update_approval_workflow = PermissionChecker(ApprovalWorkflow, "update_approval_workflow")
view_approval_workflow = PermissionChecker(ApprovalWorkflow, "view_approval_workflow")
create_approval_workflow = PermissionChecker(ApprovalWorkflow, "create_approval_workflow")
delete_approval_workflow = PermissionChecker(ApprovalWorkflow, "delete_approval_workflow")

# Survey Template Permissions
# create_survey_template_permission
create_survey_template_permission = PermissionChecker(SurveyTemplate, "create_survey_template")
# delete_survey_template_permission
delete_survey_template_permission = PermissionChecker(SurveyTemplate, "delete_survey_template")
# update_survey_template_permission
update_survey_template_permission = PermissionChecker(SurveyTemplate, "update_survey_template")
# view_survey_template_permission
view_survey_template_permission = PermissionChecker(SurveyTemplate, "view_survey_template")

# Survey Model Permissions
# create_survey_model_permission
create_survey_model_permission = PermissionChecker(SurveyModel, "create_survey_model")
# delete_survey_model_permission
delete_survey_model_permission = PermissionChecker(SurveyModel, "delete_survey_model")
# update_survey_model_permission
update_survey_model_permission = PermissionChecker(SurveyModel, "update_survey_model")
# view_survey_model_permission
view_survey_model_permission = PermissionChecker(SurveyModel, "view_survey_model")

# Survey Response Permissions
# create_survey_response_permission
create_survey_response_permission = PermissionChecker(SurveyResponse, "create_survey_response")
# delete_survey_response_permission
delete_survey_response_permission = PermissionChecker(SurveyResponse, "delete_survey_response")
# update_survey_response_permission
update_survey_response_permission = PermissionChecker(SurveyResponse, "update_survey_response")
# view_survey_response_permission
view_survey_response_permission = PermissionChecker(SurveyResponse, "view_survey_response")

# create_evidence_permission
create_evidence_permission = PermissionChecker(Evidence, "create_evidence")
# delete_evidence_permission
delete_evidence_permission = PermissionChecker(Evidence, "delete_evidence")
# update_evidence_permission
update_evidence_permission = PermissionChecker(Evidence, "update_evidence")
# view_evidence_permission
view_evidence_permission = PermissionChecker(Evidence, "view_evidence")

# create_digital_signature_permission
create_digital_signature_permission = PermissionChecker(
    DigitalSignature, "create_digital_signature"
)
# delete_digital_signature_permission
delete_digital_signature_permission = PermissionChecker(
    DigitalSignature, "delete_digital_signature"
)
# update_digital_signature_permission

# view_digital_signature_permission
view_digital_signature_permission = PermissionChecker(DigitalSignature, "view_digital_signature")

# create_service_provider_permission
create_service_provider_permission = PermissionChecker(ServiceProvider, "create_service_provider")
# delete_service_provider_permission
delete_service_provider_permission = PermissionChecker(ServiceProvider, "delete_service_provider")
# update_service_provider_permission
update_service_provider_permission = PermissionChecker(ServiceProvider, "update_service_provider")
# view_service_provider_permission
view_service_provider_permission = PermissionChecker(ServiceProvider, "view_service_provider")

# create_audit_evidence_permission
create_audit_evidence_permission = PermissionChecker(AuditEvidence, "create_audit_evidence")
# delete_audit_evidence_permission
delete_audit_evidence_permission = PermissionChecker(AuditEvidence, "delete_audit_evidence")
# update_audit_evidence_permission
update_audit_evidence_permission = PermissionChecker(AuditEvidence, "update_audit_evidence")
# view_audit_evidence_permission
view_audit_evidence_permission = PermissionChecker(AuditEvidence, "view_audit_evidence")
