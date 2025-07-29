import logging
import string
import random
import boto3
import uuid

from rich import print
from rich.console import Console
from rich.table import Table
from sqlalchemy import text
from sqlalchemy.orm.session import Session as SessionLocal
from typer import prompt

# from config.config import Settings
from fedrisk_api.endpoints import subscription
from fedrisk_api.db import risk_category as db_risk_category
from fedrisk_api.db import risk_impact as db_risk_impact
from fedrisk_api.db import risk_likelihood as db_risk_likelihood
from fedrisk_api.db import risk_mapping as db_risk_mapping
from fedrisk_api.db import risk_score as db_risk_score
from fedrisk_api.db import risk_status as db_risk_status
from fedrisk_api.db import task_status as db_task_status
from fedrisk_api.db import task as db_task
from fedrisk_api.db import feature as db_feature
from fedrisk_api.db.models import (
    ControlClass,
    ControlFamily,
    ControlPhase,
    ControlStatus,
    # Feature,
    Permission,
    PermissionRole,
    Project,
    ProjectGroup,
    Role,
    SystemRole,
    Task,
    Tenant,
    User,
    # TaskStatus,
    TaskCategory,
)

LOGGER = logging.getLogger(__name__)
# from fedrisk_api.endpoints import control_class

# All Model present in database
# Add model here if you want to create CRUD permission for Model
MODELS = [
    "assessment",
    "app",
    "approval_workflow",
    "approval_workflow_template",
    "audit_evidence",
    "audittest",
    "cappoam",
    "control",
    "controlclass",
    "controlfamily",
    "controlphase",
    "controlstatus",
    "cost",
    "document",
    "evidence",
    "exception",
    "framework",
    "framework_version",
    "frequency",
    "import_framework",
    "keyword",
    "project",
    "projectevaluation",
    "projectgroup",
    "projectuser",
    "risk",
    "riskcategory",
    "riskimpact",
    "risklikelihood",
    "riskmapping",
    "riskscore",
    "riskstatus",
    "role",
    "permission",
    "tenant",
    "projectcontrol",
    "service_provider",
    "survey_model",
    "survey_response",
    "survey_template",
    "task",
    "taskstatus",
    "taskcategory",
    "user",
    "wbs",
    "workflow_flowchart",
    "workflow_event",
    "workflow_template",
    "workflow_template_event",
]

# Type of System User
PROJECT_MANAGER = "Project Manager"
ANALYST = "Analyst"
AUDITOR = "Auditor"
SYSTEM_ADMINISTRATOR = "System Administrator"

ROLE_NAME_TO_KEY = {
    PROJECT_MANAGER: PROJECT_MANAGER,
    ANALYST: ANALYST,
    AUDITOR: AUDITOR,
    SYSTEM_ADMINISTRATOR: SYSTEM_ADMINISTRATOR,
}


CREATE_PERMISSION_PREFIX = "create_"
READ_PERMISSION_PREFIX = "view_"
UPDATE_PERMISSION_PREFIX = "update_"
DELETE_PERMISSION_PREFIX = "delete_"


# -------------------------- EXTRA PERMISSION INDEPENDENT OF MODELS ----------------------------

EXTRA_VIEW_PERMISSION = [
    "view_addablecontrols_project",
]
PROJECT_EXTRA_PERMISSIONS = [
    "addcontrol_project",
    "removecontrol_project",
    "adduser_project",
    "removeuser_project",
    "changeuserrole_project",
    "manage_project_feature",
]
EXTRA_DOCUMENT_PERMISSION = ["download_document"]

TENANT_EXTRA_PERMISSION = [
    "send_invitation_tenant",
    "manage_billing",
    "manage_system_feature",
    "view_api_keys",
    "manage_roles_permissions",
]

DASHBOARD_PERMISSION = [
    "view_summarydashboard",
    "view_governance_dashboard",
    "view_compliance_dashboard",
    "view_risk_dashboard",
    "view_tasks_dashboard",
    "view_system_administration",
    "view_subscription",
    "view_project_studio",
]

# SEARCH_PERMISSION = ["view_search"]

EXTRA_PERMISSIONS = (
    EXTRA_VIEW_PERMISSION
    + PROJECT_EXTRA_PERMISSIONS
    + EXTRA_DOCUMENT_PERMISSION
    + DASHBOARD_PERMISSION
    # + SEARCH_PERMISSION
    + TENANT_EXTRA_PERMISSION
)

# -------------------------------- PROJECT_MANAGER_PERMISSION --------------------------------

PROJECT_MANAGER_READ = [
    "assessment",
    "audittest",
    "control",
    "controlclass",
    "controlfamily",
    "controlphase",
    "controlstatus",
    "document",
    "exception",
    "framework",
    "frequency",
    "keyword",
    "project",
    "projectevaluation",
    "projectgroup",
    "risk",
    "riskcategory",
    "riskimpact",
    "risklikelihood",
    "riskmapping",
    "riskscore",
    "riskstatus",
    "task",
]

PROJECT_MANAGER_CREATE = [
    "assessment",
    "audittest",
    "document",
    "exception",
    "frequency",
    "keyword",
    "projectevaluation",
    "risk",
    "task",
]
PROJECT_MANAGER_UPDATE = PROJECT_MANAGER_CREATE + ["project"]
PROJECT_MANAGER_DELETE = PROJECT_MANAGER_CREATE
PROJECT_MANAGER_EXTRA = (
    EXTRA_VIEW_PERMISSION
    + PROJECT_EXTRA_PERMISSIONS
    + EXTRA_DOCUMENT_PERMISSION
    + DASHBOARD_PERMISSION
    # + SEARCH_PERMISSION
)

# -------------------------------- ANALYST_PERMISSION --------------------------------

ANALYST_READ = [
    "assessment",
    "audittest",
    "control",
    "controlclass",
    "controlfamily",
    "controlphase",
    "controlstatus",
    "document",
    "exception",
    "framework",
    "frequency",
    "keyword",
    "project",
    "projectevaluation",
    "projectgroup",
    "risk",
    "riskcategory",
    "riskimpact",
    "risklikelihood",
    "riskmapping",
    "riskscore",
    "riskstatus",
    "task",
]

ANALYST_CREATE = [
    "assessment",
    "audittest",
    "document",
    "exception",
    "frequency",
    "keyword",
    "projectevaluation",
    "risk",
    "task",
]
ANALYST_UPDATE = ANALYST_CREATE + ["project"]
ANALYST_DELETE = ANALYST_CREATE
ANALYST_EXTRA = (
    EXTRA_VIEW_PERMISSION
    + PROJECT_EXTRA_PERMISSIONS
    + EXTRA_DOCUMENT_PERMISSION
    + DASHBOARD_PERMISSION
    # + SEARCH_PERMISSION
)

# -------------------------------- AUDITOR_PERMISSION --------------------------------

AUDITOR_READ = [
    "assessment",
    "audittest",
    "control",
    "controlclass",
    "controlfamily",
    "controlphase",
    "controlstatus",
    "document",
    "exception",
    "framework",
    "frequency",
    "keyword",
    "project",
    "projectevaluation",
    "projectgroup",
    "risk",
    "riskcategory",
    "riskimpact",
    "risklikelihood",
    "riskmapping",
    "riskscore",
    "riskstatus",
    "task",
]
AUDITOR_CREATE = []
AUDITOR_UPDATE = []
AUDITOR_DELETE = []
AUDITOR_EXTRA = (
    EXTRA_VIEW_PERMISSION
    + EXTRA_DOCUMENT_PERMISSION
    + DASHBOARD_PERMISSION
    # + SEARCH_PERMISSION
)

# -------------------------------SYSTEM ADMINISTRATOR -----------------------------------------------------------

SYSTEM_ADMINISTRATOR_READ = MODELS

SYSTEM_ADMINISTRATOR_CREATE = MODELS
SYSTEM_ADMINISTRATOR_UPDATE = MODELS
SYSTEM_ADMINISTRATOR_DELETE = SYSTEM_ADMINISTRATOR_CREATE
SYSTEM_ADMINISTRATOR_EXTRA = (
    EXTRA_VIEW_PERMISSION
    + PROJECT_EXTRA_PERMISSIONS
    + EXTRA_DOCUMENT_PERMISSION
    + DASHBOARD_PERMISSION
    # + SEARCH_PERMISSION
    + TENANT_EXTRA_PERMISSION
)


# ------------------------------- ROLES AND PERMISSION MAPPING -------------------------------------------------

ROLES = {
    "PROJECT_MANAGER": {
        "C": PROJECT_MANAGER_CREATE,
        "R": PROJECT_MANAGER_READ,
        "U": PROJECT_MANAGER_UPDATE,
        "D": PROJECT_MANAGER_DELETE,
        "E": PROJECT_MANAGER_EXTRA,
    },
    "ANALYST": {
        "C": ANALYST_CREATE,
        "R": ANALYST_READ,
        "U": ANALYST_UPDATE,
        "D": ANALYST_DELETE,
        "E": ANALYST_EXTRA,
    },
    "AUDITOR": {
        "C": AUDITOR_CREATE,
        "R": AUDITOR_READ,
        "U": AUDITOR_UPDATE,
        "D": AUDITOR_DELETE,
        "E": AUDITOR_EXTRA,
    },
    "SYSTEM_ADMINISTRATOR": {
        "C": SYSTEM_ADMINISTRATOR_CREATE,
        "R": SYSTEM_ADMINISTRATOR_READ,
        "U": SYSTEM_ADMINISTRATOR_UPDATE,
        "D": SYSTEM_ADMINISTRATOR_DELETE,
        "E": SYSTEM_ADMINISTRATOR_EXTRA,
    },
}

# ------------------------------------------------------------------------------------------------------
CONTROLS_ATTRIBUTES = {
    "control_class": ["Unassigned", "Technical", "Operational", "Management"],
    "control_phase": ["Unassigned", "Procedural", "Technical", "Legal, Regulatory or Compliance"],
    "control_status": ["P0", "P1", "P2", "P3", "1", "2"],
    "control_family": [
        "Security & Privacy",
        "Asset Management",
        "Continuity & Disaster Recovery",
        "Capacity & Performance",
        "Change Management",
        "Cloud Security",
    ],
}

# ---------------------------------------------------------------------------------------------------------

TEST_RISK_LIKELIHOODS = (
    "Very Likely",
    "Likely",
    "Possible",
    "Unlikely",
    "Very Unlikely",
)

TEST_RISK_SCORES = (
    "10",
    "5",
    "1",
)

TEST_RISK_CATEGORIES = (
    "Access Management",
    "Environmental Resilience",
    "Monitoring",
    "Physical Security",
    "Policy & Procedure",
    "Sensitive Data Management",
    "Technical Vulnerability",
    "Third Party Management",
)

TEST_RISK_IMPACTS = (
    "Insignificant",
    "Minor",
    "Moderate",
    "Major",
    "Extreme",
)

TEST_RISK_MAPPINGS = (
    "Test Risk Mapping #1",
    "Test Risk Mapping #2",
    "Test Risk Mapping #3",
    "Test Risk Mapping #4",
)

TEST_RISK_STATUSES = (
    "Active",
    "On Hold",
    "Completed",
    "Cancelled",
)

TEST_TASK_STATUSES = (
    "In Progress",
    "Not Started",
    "Complete",
    "Cancelled",
)

TEST_TASK_CATEGORIES = (
    "Projects",
    "Frameworks",
    "Controls",
    "Assessments",
    "Ad-hoc Assessments",
    "Project Evaluations",
    "Risks",
)


def create_or_get_role(db: SessionLocal, name: str):
    role = db.query(Role).filter(Role.name == name).first()
    if role:
        return role
    role = Role(name=name)
    db.add(role)
    db.flush()
    return role


def create_or_get_permission(db: SessionLocal, name: str, perm_key: str, category: str):
    permission = (
        db.query(Permission)
        .filter(Permission.name == name, Permission.perm_key == perm_key)
        .first()
    )
    if permission:
        return permission
    permission = Permission(name=name, perm_key=perm_key, category=category)
    db.add(permission)
    db.flush()
    return permission


def create_or_get_tenant(db: SessionLocal, name: str, is_active: bool):
    tenant = db.query(Tenant).filter(Tenant.name == name).first()
    if tenant:
        return tenant
    tenant = Tenant(name=name, is_active=True)
    db.add(tenant)
    db.flush()
    return tenant


def create_or_get_user(
    db: SessionLocal,
    email: str,
    is_active: bool,
    first_name: str,
    last_name: str,
    phone_no: str,
    is_superuser: bool,
    is_tenant_admin: bool,
    system_role: int,
    tenant_id: int,
    is_email_verified: bool = True,
    do_commit=True,
):
    user = db.query(User).filter(User.tenant_id == tenant_id, User.email == email)
    if user.first():
        return user.first()
    user = User(
        email=email,
        tenant_id=tenant_id,
        is_active=is_active,
        # system_role=system_role,
        first_name=first_name,
        last_name=last_name,
        phone_no=phone_no,
        is_superuser=is_superuser,
        is_tenant_admin=is_tenant_admin,
        is_email_verified=is_email_verified,
    )
    db.add(user)
    db.flush()
    if do_commit:
        db.commit()
    # add system role
    user_system_role = SystemRole(
        user_id=user.id,
        role_id=system_role,
    )
    db.add(user_system_role)
    db.commit()
    return user


def create_or_get_project(
    db: SessionLocal,
    name: str,
    description: str,
    tenant_id: int,
    project_group_id: int,
    project_admin_id: int,
):
    project = db.query(Project).filter(Project.name == name, Project.tenant_id == tenant_id).first()
    if project:
        return project
    project = Project(
        name=name,
        description=description,
        tenant_id=tenant_id,
        project_group_id=project_group_id,
        project_admin_id=project_admin_id,
    )
    db.add(project)
    db.flush()
    return project


def create_or_get_project_group(db: SessionLocal, name: str, description: str, tenant_id: int):
    project_group = db.query(ProjectGroup).filter(ProjectGroup.name == name).first()
    if project_group:
        return project_group
    project_group = ProjectGroup(name=name, description=description, tenant_id=tenant_id)
    db.add(project_group)
    db.flush()
    return project_group


def create_or_get_control_class(db: SessionLocal, name: str, description: str, tenant_id: int):
    control_class = db.query(ControlClass).filter(ControlClass.name == name).first()
    if control_class:
        return control_class
    control_class = ControlClass(name=name, description=description, tenant_id=tenant_id)
    db.add(control_class)
    db.flush()
    return control_class


def create_or_get_control_phase(db: SessionLocal, name: str, description: str, tenant_id: int):
    control_phase = db.query(ControlPhase).filter(ControlPhase.name == name).first()
    if control_phase:
        return control_phase
    control_phase = ControlPhase(name=name, description=description, tenant_id=tenant_id)
    db.add(control_phase)
    db.flush()
    return control_phase


def create_or_get_control_status(db: SessionLocal, name: str, description: str, tenant_id: int):
    control_status = db.query(ControlStatus).filter(ControlStatus.name == name).first()
    if control_status:
        return control_status
    control_status = ControlStatus(name=name, description=description, tenant_id=tenant_id)
    db.add(control_status)
    db.flush()


def create_or_get_control_family(db: SessionLocal, name: str, description: str, tenant_id: int):
    control_family = db.query(ControlFamily).filter(ControlFamily.name == name).first()
    if control_family:
        return control_family
    control_family = ControlFamily(name=name, description=description, tenant_id=tenant_id)
    db.add(control_family)
    db.flush()
    return control_family


def create_or_get_task_category(db: SessionLocal, name: str, description: str, tenant_id: int):
    task_category = db.query(TaskCategory).filter(TaskCategory.name == name).first()
    if task_category:
        return task_category
    task_category_obj = TaskCategory(name=name, description=description, tenant_id=tenant_id)
    db.add(task_category_obj)
    db.flush()
    return task_category_obj


def load_risk_attributes(db, verbose: bool = True):
    try:
        # Create some Risk Likelihood Values
        my_existing_risk_likelihoods = db_risk_likelihood.get_all_risk_likelihoods(db)
        if len(my_existing_risk_likelihoods) == 0:
            LOGGER.warning("No Risk Likelihoods in Database - creating demo data . . .")
            for next_likelihood_name in TEST_RISK_LIKELIHOODS:
                next_risk_likelihood = db_risk_likelihood.CreateRiskLikelihood(
                    name=next_likelihood_name, description="testing"
                )
                db_risk_likelihood.create_risk_likelihood(db, next_risk_likelihood)
        # Create some Risk Score Values
        my_existing_risk_scores = db_risk_score.get_all_risk_scores(db)
        if len(my_existing_risk_scores) == 0:
            LOGGER.warning("No Risk Scores in Database - creating demo data . . .")
            for next_score_name in TEST_RISK_SCORES:
                next_risk_score = db_risk_score.CreateRiskScore(
                    name=next_score_name, description="testing"
                )
                db_risk_score.create_risk_score(db, next_risk_score)
        # Create some Risk Impacts
        my_existing_risk_impacts = db_risk_impact.get_all_risk_impacts(db)
        if len(my_existing_risk_impacts) == 0:
            LOGGER.warning("No Risk Impacts in Database - creating demo data . . .")
            for next_impact_name in TEST_RISK_IMPACTS:
                next_risk_impact = db_risk_impact.CreateRiskImpact(
                    name=next_impact_name, description="testing"
                )
                db_risk_impact.create_risk_impact(db, next_risk_impact)
        # Create some Risk Mappings
        my_existing_risk_mappings = db_risk_mapping.get_all_risk_mappings(db)
        if len(my_existing_risk_mappings) == 0:
            LOGGER.warning("No Risk Mappings in Database - creating demo data . . .")
            for next_mapping_name in TEST_RISK_MAPPINGS:
                next_risk_mapping = db_risk_mapping.CreateRiskMapping(
                    name=next_mapping_name, description="testing"
                )
                db_risk_mapping.create_risk_mapping(db, next_risk_mapping)
        # Create some Risk Statuses
        my_existing_risk_statuses = db_risk_status.get_all_risk_statuses(db)
        if len(my_existing_risk_statuses) == 0:
            LOGGER.warning("No Risk Statuses in Database - creating demo data . . .")
            for next_status_name in TEST_RISK_STATUSES:
                next_risk_status = db_risk_status.CreateRiskStatus(
                    name=next_status_name, description="testing"
                )
                db_risk_status.create_risk_status(db, next_risk_status)
    except Exception as e:
        db.rollback()
        print(e)
        if verbose:
            print("[bold red]Failed[/bold red] Some error")
            print("[bold red]Rollback to Previous state [/bold red]")
        return -1


def load_risk_categories(db, verbose: bool = True):
    try:
        tenants_added = db.query(Tenant).all()
        for tenant in tenants_added:
            # Create some Risk Categories
            my_existing_risk_categories = db_risk_category.get_all_risk_categories(db, tenant.id)
            if len(my_existing_risk_categories) == 0:
                LOGGER.warning("No Risk Categories in Database - creating demo data . . .")
                for next_category_name in TEST_RISK_CATEGORIES:
                    next_risk_category = db_risk_category.CreateRiskCategory(
                        name=next_category_name, description="testing"
                    )
                    db_risk_category.create_risk_category(db, next_risk_category, tenant.id)
    except Exception as e:
        db.rollback()
        print(e)
        if verbose:
            print("[bold red]Failed[/bold red] Some error")
            print("[bold red]Rollback to Previous state [/bold red]")
        return -1


def load_controls_attributes(db, verbose: bool = True):
    try:
        for control_family in CONTROLS_ATTRIBUTES["control_family"]:
            create_or_get_control_family(
                db=db,
                name=control_family,
                description="control family description",
                tenant_id=1,
            )
        for control_status in CONTROLS_ATTRIBUTES["control_status"]:
            create_or_get_control_status(
                db=db,
                name=control_status,
                description="control status description",
                tenant_id=1,
            )
        for control_phase in CONTROLS_ATTRIBUTES["control_phase"]:
            create_or_get_control_phase(
                db=db,
                name=control_phase,
                description="control phase description",
                tenant_id=1,
            )
        for control_class in CONTROLS_ATTRIBUTES["control_class"]:
            create_or_get_control_class(
                db=db,
                name=control_class,
                description="control class description",
                tenant_id=1,
            )
        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        if verbose:
            print("[bold red]Failed[/bold red] Some error")
            print("[bold red]Rollback to Previous state [/bold red]")
        return -1


def load_task_categories(db, verbose: bool = True):
    try:
        for category in TEST_TASK_CATEGORIES:
            create_or_get_task_category(
                db=db,
                name=category,
                description="Category description",
                tenant_id=1,
            )

        db.commit()
    except Exception as e:
        db.rollback()
        print(e)
        if verbose:
            print("[bold red]Failed[/bold red] Some error")
            print("[bold red]Rollback to Previous state [/bold red]")
        return -1


def insert_default_features(db, verbose: bool = True):
    "Generate default features"
    try:
        # Create aws project feature
        my_existing_project_features = db_feature.get_feature(db, 1)
        if len(my_existing_project_features) == 0:
            LOGGER.warning("No Features in Database - creating demo data . . .")
            new_feature = db_feature.CreateFeature(name="aws_security_hub_imports", is_active=True)
            db_feature.create_feature(db, new_feature, 1)
            new_feature = db_feature.CreateFeature(name="evaluation_surveys", is_active=True)
            db_feature.create_feature(db, new_feature, 1)
    except Exception as e:
        db.rollback()
        print(e)
        if verbose:
            print("[bold red]Failed[/bold red] Some error")
            print("[bold red]Rollback to Previous state [/bold red]")
        return -1


def create_task_status(db, verbose: bool = True):
    try:
        # Create some Task Statuses
        tenants_added = db.query(Tenant).all()
        for tenant in tenants_added:
            my_existing_task_statuses = db_task_status.get_all_task_statuses(db, tenant.id)
            if len(my_existing_task_statuses) == 0:
                LOGGER.warning("No Task Statuses in Database - creating demo data . . .")
                for next_status_name in TEST_TASK_STATUSES:
                    next_task_status = db_task_status.CreateTaskStatus(
                        name=next_status_name, description="testing"
                    )
                    db_task_status.create_task_status(db, next_task_status, tenant.id)

    except Exception as e:
        db.rollback()
        print(e)
        if verbose:
            print("[bold red]Failed[/bold red] Some error")
            print("[bold red]Rollback to Previous state [/bold red]")
        return -1


async def migrate_task_status(db, verbose: bool = True):
    # map existing status to new task status
    try:
        tenants_added = db.query(Tenant).all()
        for tenant in tenants_added:
            my_existing_task_statuses = db_task_status.get_all_task_statuses(db, tenant.id)
            print(f"{my_existing_task_statuses}")
            if len(my_existing_task_statuses) != 0:
                print("Task Statuses in Database - checking for existing task data . . .")
                my_existing_tasks_for_tenant = (
                    db.query(Task).filter(Task.tenant_id == tenant.id).all()
                )
                print(f"{my_existing_tasks_for_tenant}")
                if len(my_existing_tasks_for_tenant) != 0:
                    print(
                        f"There are tasks that exist for the tenant {len(my_existing_tasks_for_tenant)}"
                    )
                    for task_to_update in my_existing_tasks_for_tenant:
                        print(f"{str(task_to_update.status)}")
                        if task_to_update.status is not None:
                            status_value = str(task_to_update.status)
                            status_val = status_value.split(".")
                            value = status_val[1].replace("_", " ")
                            final_val = value.title()
                            print(f"final value {final_val}")
                            # get matching ID
                            try:
                                task_status = db_task_status.get_task_status_by_name(db, final_val)
                                print(f"task status {task_status}")
                                # update task
                                update_task = db_task.UpdateTask(task_status_id=task_status.id)
                                await db_task.update_task(
                                    db,
                                    task_to_update.id,
                                    update_task,
                                    tenant.id,
                                    task_to_update.assigned_to,
                                    "status id updated",
                                )
                                db.commit()
                            except Exception as e:
                                print(e)
    except Exception as e:
        db.rollback()
        print(e)
        if verbose:
            print("[bold red]Failed[/bold red] Some error")
            print("[bold red]Rollback to Previous state [/bold red]")
        return -1


def generate_roles_with_permissions(db, verbose: bool = True):
    "Generate Roles and Permissions and Assign Permissions to Role"

    try:
        # Create or get Role objects
        role_objs = {role: create_or_get_role(db=db, name=role) for role in ROLES.keys()}
        db.add_all(role_objs.values())
        db.commit()  # ✅ Commit roles
        if verbose:
            print("[bold green]✅ Roles Created[/bold green]")

        # Create permission objects for CRUD on models
        permissions = {}
        for model in MODELS:
            perm = {
                f"{CREATE_PERMISSION_PREFIX}{model}": create_or_get_permission(
                    db=db,
                    name=f"{CREATE_PERMISSION_PREFIX}{model}".replace("_", " ").title(),
                    perm_key=f"{CREATE_PERMISSION_PREFIX}{model}",
                    category="create",
                ),
                f"{READ_PERMISSION_PREFIX}{model}": create_or_get_permission(
                    db=db,
                    name=f"{READ_PERMISSION_PREFIX}{model}".replace("_", " ").title(),
                    perm_key=f"{READ_PERMISSION_PREFIX}{model}",
                    category="read",
                ),
                f"{UPDATE_PERMISSION_PREFIX}{model}": create_or_get_permission(
                    db=db,
                    name=f"{UPDATE_PERMISSION_PREFIX}{model}".replace("_", " ").title(),
                    perm_key=f"{UPDATE_PERMISSION_PREFIX}{model}",
                    category="update",
                ),
                f"{DELETE_PERMISSION_PREFIX}{model}": create_or_get_permission(
                    db=db,
                    name=f"{DELETE_PERMISSION_PREFIX}{model}".replace("_", " ").title(),
                    perm_key=f"{DELETE_PERMISSION_PREFIX}{model}",
                    category="delete",
                ),
            }
            permissions.update(perm)  # ✅ FIXED

        for extra_permission in EXTRA_PERMISSIONS:
            permissions[extra_permission] = create_or_get_permission(
                db=db,
                name=extra_permission.replace("_", " ").title(),
                perm_key=extra_permission,
                category="extra",
            )

        db.commit()  # ✅ Commit permissions
        if verbose:
            print("[bold green]✅ Permissions Created[/bold green]")

        # Link permissions to roles based on ROLES map
        for role_name, perms_by_type in ROLES.items():
            role = role_objs[role_name]

            for perm_type, keys in perms_by_type.items():
                for key in keys:
                    if perm_type == "E":
                        perm_key = key
                    else:
                        prefix = {
                            "C": CREATE_PERMISSION_PREFIX,
                            "R": READ_PERMISSION_PREFIX,
                            "U": UPDATE_PERMISSION_PREFIX,
                            "D": DELETE_PERMISSION_PREFIX,
                        }[perm_type]
                        perm_key = f"{prefix}{key}"

                    permission = permissions.get(perm_key)
                    if not permission:
                        print(f"⚠️ Permission not found: {perm_key}")
                        continue

                    # Check if already exists
                    existing = (
                        db.query(PermissionRole)
                        .filter_by(role_id=role.id, permission_id=permission.id)
                        .first()
                    )
                    if not existing:
                        db.add(
                            PermissionRole(
                                role_id=role.id, permission_id=permission.id, tenant_id=1
                            )
                        )  # or actual tenant

        db.commit()
        if verbose:
            print("[bold green]✅ Role-Permission mappings created[/bold green]")

    except Exception as e:
        db.rollback()
        print(f"[bold red]❌ Error:[/bold red] {e}")


def add_roles_permissions_for_tenant(tenant_id, db, verbose: bool = True):
    """
    Generate permissions and assign them to roles for a given tenant.
    """
    # Fetch all roles and permissions from DB
    role_objs = db.query(Role).all()
    permissions = {p.perm_key: p for p in db.query(Permission).all()}

    try:
        for role in role_objs:
            role_name = role.name

            print(f"✅ Processing role: {role_name}")
            role_permissions = []

            for perm_type, models_or_keys in ROLES[role_name].items():
                if perm_type == "E":
                    for key in models_or_keys:
                        perm_key = f"{key}"
                        permission = permissions.get(perm_key)
                        if not permission:
                            print(f"❌ Extra Permission not found: {key}")
                            continue
                        role_permissions.append(permission)
                else:
                    prefix = {
                        "C": CREATE_PERMISSION_PREFIX,
                        "R": READ_PERMISSION_PREFIX,
                        "U": UPDATE_PERMISSION_PREFIX,
                        "D": DELETE_PERMISSION_PREFIX,
                    }[perm_type]

                    for model in models_or_keys:
                        perm_key = f"{prefix}{model}"
                        permission = permissions.get(perm_key)
                        if not permission:
                            print(f"❌ Permission not found: {perm_key}")
                            continue
                        role_permissions.append(permission)

            # Assign via PermissionRole table if not already assigned
            for perm in role_permissions:
                exists = (
                    db.query(PermissionRole)
                    .filter_by(tenant_id=tenant_id, role_id=role.id, permission_id=perm.id)
                    .first()
                )

                if not exists:
                    db.add(
                        PermissionRole(
                            tenant_id=tenant_id,
                            role_id=role.id,
                            permission_id=perm.id,
                            enabled=True,
                        )
                    )

        db.commit()
        if verbose:
            print(f"🎉 Success: Assigned permissions for tenant {tenant_id}.")
    except Exception as e:
        db.rollback()
        print(f"❌ [Failed] Error: {e}")
        return -1


def clean_roles(db, verbose: bool = True):
    "Truncate Role Table"
    if verbose:
        print(
            f"[bold red]This Operation will Delete all data from {Role.__tablename__} and Dependent Tables [/bold red]"
        )
        confirmation = prompt("Are you sure ? [yes|no]")
        if confirmation == "yes":
            db.execute(text(f"TRUNCATE TABLE {Role.__tablename__} CASCADE"))
            db.commit()
            print(
                "[bold green]Success[/bold green] All roles and dependent on role  are Truncated."
            )
        else:
            print("Operation Terminated")

    else:
        db.execute(text(f"TRUNCATE TABLE {Role.__tablename__} CASCADE"))
        db.commit()


def clean_permissions(db, verbose: bool = True):
    "Truncate Permission Table"

    if verbose:
        print(
            f"[bold red]This Operation will Delete all data from {Permission.__tablename__} and Dependent Tables [/bold red]"
        )
        confirmation = prompt("Are you sure ? [yes|no]")
        if confirmation == "yes":
            db.execute(text(f"TRUNCATE TABLE {Permission.__tablename__} CASCADE"))
            db.commit()
            print(
                "[bold green]Success[/bold green] All Permissions and dependent on Permissions are Truncated."
            )
        else:
            print("Operation Terminated")
    else:
        db.execute(text(f"TRUNCATE TABLE {Permission.__tablename__} CASCADE"))
        db.commit()


TENANTS = {
    "TenantA": "tenant1.fedrisk.com",
    "TenantB": "tenant2.fedrisk.com",
    "TenantSuperUser": "tenantsuperuser.fedrisk.com",
}


USERS = [
    "userone",
    "usertwo",
    "userthree",
    "userfour",
    "userfive",
    "usersix",
    "superuser",
    "eric",
    "longevity",
    "rwolfapex",
]
PROJECT_NAME = [
    "NDTAC Motive 5",
    "Arkansas SSO Audit 2024",
    "ARDOT 2.0 042624",
    "PCI Assessment",
    "PSI Deliverables Tracking",
]

data_created = {}


def load_data(db, verbose: bool = True):
    try:
        user = db.query(db.query(User).exists()).scalar()
        if user:
            print("Data Already loaded")
            return

        tenants = [create_or_get_tenant(db=db, name=name, is_active=True) for name in TENANTS]

        if verbose:
            print("[bold green]Success[/bold green] Tenants Created.")

        # create tenant s3 bucket
        tenants_added = db.query(Tenant).all()

        # for tenant in tenants_added:
        #     create_tenant_s3_bucket(db, tenant.id)

        # settings = Settings()
        # create bucket tags
        # create_tenant_s3_tags(db, {settings.ENVIRONMENT})
        # if verbose:
        #     print("[bold green]Success[/bold green] Tenants S3 Buckets Created.")

        generate_roles_with_permissions(db, verbose=verbose)
        load_risk_attributes(db, verbose=verbose)
        load_risk_categories(db, verbose=verbose)
        load_controls_attributes(db, verbose=verbose)
        load_task_categories(db, verbose=verbose)
        insert_default_features(db, verbose=verbose)
        create_task_status(db, verbose=verbose)

        db.query(Role).order_by(Role.id.asc()).all()

        users = [
            create_or_get_user(
                db=db,
                email="projectadmin@gmail.com",
                is_active=True,
                first_name="Test",
                last_name="Test",
                phone_no="5555555555",
                is_superuser=False,
                is_tenant_admin=False,
                tenant_id=tenants[0].id,
                system_role=1,
            ),
            create_or_get_user(
                db=db,
                email="userthree@gmail.com",
                is_active=True,
                first_name="Test",
                last_name="Test",
                phone_no="5555555555",
                is_superuser=False,
                is_tenant_admin=False,
                tenant_id=tenants[0].id,
                system_role=1,
            ),
            create_or_get_user(
                db=db,
                email="userfour@gmail.com",
                is_active=True,
                first_name="Test",
                last_name="Test",
                phone_no="5555555555",
                is_superuser=False,
                is_tenant_admin=False,
                tenant_id=tenants[1].id,
                system_role=1,
            ),
            create_or_get_user(
                db=db,
                email="userfive@gmail.com",
                is_active=True,
                first_name="Test",
                last_name="Test",
                phone_no="5555555555",
                is_superuser=False,
                is_tenant_admin=False,
                tenant_id=tenants[1].id,
                system_role=1,
            ),
            create_or_get_user(
                db=db,
                email="superuser@gmail.com",
                is_active=True,
                first_name="Test",
                last_name="Test",
                phone_no="5555555555",
                is_superuser=True,
                is_tenant_admin=False,
                tenant_id=tenants[2].id,
                system_role=1,
            ),
            create_or_get_user(
                db=db,
                email="eric@longevityconsulting.com",
                is_active=True,
                first_name="Eric",
                last_name="Thompson",
                phone_no="5555555555",
                is_superuser=True,
                is_tenant_admin=True,
                tenant_id=tenants[0].id,
                system_role=4,
            ),
            create_or_get_user(
                db=db,
                email="eric1@longevityconsulting.com",
                is_active=True,
                first_name="Eric",
                last_name="Thompson",
                phone_no="5555555555",
                is_superuser=True,
                is_tenant_admin=True,
                tenant_id=tenants[1].id,
                system_role=4,
            ),
            create_or_get_user(
                db=db,
                email="richardwolf@gmail.com",
                is_active=True,
                first_name="Richard",
                last_name="Wolf",
                phone_no="5555555555",
                is_superuser=True,
                is_tenant_admin=True,
                tenant_id=tenants[0].id,
                system_role=4,
            ),
            create_or_get_user(
                db=db,
                email="sarah.vardy@longevityconsulting.com",
                is_active=True,
                first_name="Sarah",
                last_name="Vardy",
                phone_no="5555555555",
                is_superuser=True,
                is_tenant_admin=True,
                tenant_id=tenants[0].id,
                system_role=4,
            ),
        ]

        if verbose:
            print("[bold green]Success[/bold green] Users Created.")

        # create user s3 buckets

        for tenant in tenants_added:
            create_tenant_users_folders_s3(db, tenant.id)

        if verbose:
            print("[bold green]Success[/bold green] Tenants S3 Buckets Created.")

        # create stripe subscriptions
        tenant_id = 0
        userid = 1
        for user in users:
            if tenant_id != user.tenant_id:
                adduser = {"tenant_id": user.tenant_id, "user_id": userid}
                subscription.create_customer(db=db, user=adduser)
                tenant_id = user.tenant_id
                userid += 1

        project_groups = [
            create_or_get_project_group(
                db=db,
                name="Department of Education OESE",
                description="Department of Education OESE",
                tenant_id=tenants[0].id,
            ),
            create_or_get_project_group(
                db=db,
                name="USDA FPAC",
                description="USDA FPAC",
                tenant_id=tenants[0].id,
            ),
            create_or_get_project_group(
                db=db,
                name="Longevity",
                description="Longevity",
                tenant_id=tenants[0].id,
            ),
            create_or_get_project_group(
                db=db,
                name="Department of Transportation FTA TSO-20",
                description="Department of Transportation FTA TSO-20",
                tenant_id=tenants[0].id,
            ),
            create_or_get_project_group(
                db=db,
                name="USDA Forest Service",
                description="USDA Forest Service",
                tenant_id=tenants[0].id,
            ),
        ]

        [
            create_or_get_project(
                db=db,
                name="NDTAC Motive 5",
                description="NDTAC Motive 5",
                tenant_id=tenants[0].id,
                project_group_id=project_groups[0].id,
                project_admin_id=users[0].id,
            ),
            create_or_get_project(
                db=db,
                name="Arkansas SSO Audit 2024",
                description="Arkansas SSO Audit 2024",
                tenant_id=tenants[0].id,
                project_group_id=project_groups[3].id,
                project_admin_id=users[1].id,
            ),
            create_or_get_project(
                db=db,
                name="ARDOT 2.0 042624",
                description="ARDOT 2.0 042624",
                tenant_id=tenants[0].id,
                project_group_id=project_groups[3].id,
                project_admin_id=users[2].id,
            ),
            create_or_get_project(
                db=db,
                name="PCI Assessment",
                description="PCI Assessment",
                tenant_id=tenants[0].id,
                project_group_id=project_groups[2].id,
                project_admin_id=users[0].id,
            ),
            create_or_get_project(
                db=db,
                name="PSI Deliverables Tracking",
                description="PSI Deliverables Tracking",
                tenant_id=tenants[0].id,
                project_group_id=project_groups[4].id,
                project_admin_id=users[0].id,
            ),
        ]

        if verbose:
            print("[bold green]Success[/bold green] Projects Created.")

        db.commit()
        if verbose:
            print("[bold green]Success[/bold green] All Objects are created.")

        if verbose:
            print_tenant(tenants=tenants)
            print_user(users=users)
    except Exception as e:
        print("Exception Encountered!!")
        print(str(e))
        db.rollback()
        if verbose:
            print("[bold red]Failed[/bold red] Some error", e)
            print("[bold red]Rollback to Previous state [/bold red]")


# Removes PSI by obsfucating all personal data like email address, first name, last name and phone number
def remove_psi(db):
    # Select all users and obsfucate PSI
    users = db.query(User).all()
    for user in users:
        res = "".join(random.choices(string.ascii_letters, k=7))
        random_email = res + "@test.com"
        update_random_user = {
            "email": random_email,
            "first_name": res,
            "last_name": res,
            "phone_no": "+15551234567",
        }
        user_to_update = db.query(User).filter(User.id == user.id)
        user_to_update.update(update_random_user)
        db.commit()
    console = Console()
    console.print(f"Obsfucated all PSI")


def clean_loaded_data(db, verbose: bool = True):
    for project in PROJECT_NAME:
        project = db.query(Project).filter(Project.name == project).first()
        if project:
            db.delete(project)
    db.commit()
    if verbose:
        print("[bold green]Success[/bold green] Projects Deleted.")
    for user in USERS:
        user = db.query(User).filter(User.email == user).first()
        if user:
            db.query(Task).filter(Task.user_id == user.id).delete()
            db.delete(user)
    db.commit()
    if verbose:
        print("[bold green]Success[/bold green] Users Deleted.")
    db.commit()

    db.query(Tenant).filter(Tenant.name.in_(TENANTS.values())).delete()

    if verbose:
        print("[bold green]Success[/bold green] Tenant Deleted.")
    db.commit()


def print_tenant(tenants):
    table = Table(title="Tenant")
    table.add_column("ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Tenant Name", justify="center", style="cyan", no_wrap=True)

    for tenant in tenants:
        table.add_row(str(tenant.id), str(tenant.name))
    console = Console()
    console.print(table)


def print_user(users):
    table = Table(title="Users")
    table.add_column("ID", justify="center", style="cyan", no_wrap=True)
    table.add_column("Email Address", justify="center", style="cyan", no_wrap=True)
    table.add_column("Tenant_id", justify="center", style="cyan", no_wrap=True)
    table.add_column("is_superuser", justify="center", style="cyan", no_wrap=True)
    table.add_column("is_tenant_admin", justify="center", style="cyan", no_wrap=True)

    for user in users:
        table.add_row(
            str(user.id),
            str(user.email),
            str(user.tenant_id),
            # str(user.is_superuser),
            str(user.is_tenant_admin),
        )
    console = Console()
    console.print(table)


def create_tenant_s3_lambda_trigger(function_name, bucket_name):
    # lambda_client = boto3.client("lambda")
    s3_client = boto3.client("s3")

    # add lambda function permissions
    # response = lambda_client.add_permission(
    #     FunctionName=function_name,
    #     StatementId='1',
    #     Action='lambda:InvokeFunction',
    #     Principal='s3.amazonaws.com',
    #     SourceArn='arn:aws:lambda:us-east-1:513177828614:function:FedriskClamAVS3ScanTag',
    #     SourceAccount='513177828614'
    # )

    # Get the Lambda function ARN
    # response = lambda_client.get_function(FunctionName=function_name)
    # function_arn = response["Configuration"]["FunctionArn"]

    # Add the S3 trigger to the Lambda function
    s3_client.put_bucket_notification_configuration(
        Bucket=bucket_name,
        NotificationConfiguration={
            "LambdaFunctionConfigurations": [
                {
                    "LambdaFunctionArn": "arn:aws:lambda:us-east-1:513177828614:function:FedriskClamAVS3ScanTag",
                    "Events": ["s3:ObjectCreated:*"],
                }
            ]
        },
    )


def create_s3_bucket_with_folders(bucket_name, folder_structure):
    """Creates an S3 bucket with the specified folder structure.

    Args:
        bucket_name: The name of the S3 bucket to create.
        folder_structure: A dictionary representing the folder structure.
                          Keys are folder names, and values are optional subfolders (dictionaries).
    """

    s3 = boto3.client("s3")

    # Create the bucket if it doesn't exist
    try:
        s3.create_bucket(Bucket=bucket_name)
    except s3.exceptions.BucketAlreadyOwnedByYou:
        print(f"Bucket '{bucket_name}' already exists.")

    # Create the folder structure
    for folder_name, subfolders in folder_structure.items():
        if subfolders:
            # Recursively create subfolders
            create_s3_bucket_with_folders(bucket_name, subfolders)
        else:
            # Create an empty object to represent the folder
            s3.put_object(Bucket=bucket_name, Key=f"{folder_name}/")


def create_tenant_s3_bucket(db, tenant_id):
    # bucket name for tenant
    bucket_name = f"fedrisk-tenant{tenant_id}-{str(uuid.uuid4())}"
    folder_structure = {
        "frameworks": {},
        "documents": {},
        "awscontrols": {},
        "tasks": {},
    }
    create_s3_bucket_with_folders(bucket_name, folder_structure)
    # create db reference
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id)
    tenant.update(
        {
            "s3_bucket": bucket_name,
        }
    )
    db.commit()


def create_tenant_user_folder_s3(db, user_id, tenant_id):
    s3 = boto3.client("s3")
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    directory_name = f"user{user_id}-{str(uuid.uuid4())}/"
    # Create a "directory" by uploading an empty object
    response = s3.put_object(Bucket=tenant.s3_bucket, Key=directory_name)

    # Check the response
    if response["ResponseMetadata"]["HTTPStatusCode"] == 200:
        user = db.query(User).filter(User.id == user_id)
        user.update(
            {
                "s3_bucket": directory_name,
            }
        )
        db.commit()
        print(f'Directory "{directory_name}" created successfully in bucket "{tenant.s3_bucket}".')
    else:
        print(f"Failed to create directory. Response: {response}")


def create_tenant_users_folders_s3(db, tenant_id):
    users = db.query(User).filter(User.tenant_id == tenant_id).all()
    for user in users:
        create_tenant_user_folder_s3(db, user.id, tenant_id)
    print(f"Buckets created for users on tenant")


def create_tenant_s3_tags(db, environment):
    s3 = boto3.client("s3")
    tenants = db.query(Tenant).all()
    for tenant in tenants:
        # Tag S3 Bucket
        response = s3.put_bucket_tagging(
            Bucket=tenant.s3_bucket,
            Tagging={"TagSet": [{"Key": "environment", "Value": environment}]},
        )
        LOGGER.info(response)
    print(f"Tags added to buckets for environment")


def remap_tenant_user_roles(db: SessionLocal, tenant_id: int):
    users = db.query(User).filter(User.tenant_id == tenant_id).all()
    for user in users:
        # get system role and insert into system_role table
        system_role_map = SystemRole(user_id=user.id, role_id=user.system_role, enabled=True)
        db.add(system_role_map)
        db.commit()
    return "System user roles mapped for tenant"
