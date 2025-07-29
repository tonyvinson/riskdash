from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import Session
import logging

from fedrisk_api.db.enums import CapPoamStatus
from fedrisk_api.db.models import (
    AuditTest,
    CapPoam,
    CapPoamApprovalWorkflow,
    CapPoamCost,
    CapPoamStakeHolder,
    CapPoamProjectControl,
    CapPoamTask,
    Control,
    Project,
    User,
    CapPoamHistory,
    User,
    UserWatching,
    Project,
    ProjectControl,
)
from fedrisk_api.schema.cap_poam import CreateCapPoam, UpdateCapPoam
from fedrisk_api.utils.utils import filter_by_user_project_role

from fedrisk_api.db.util.notifications_utils import (
    notify_user,
    add_notification,
    manage_notifications,
)

cap_poam_STATUS = [member.value.lower() for member in CapPoamStatus]

LOGGER = logging.getLogger(__name__)


async def manage_stakeholders(db, stakeholder_ids, cap_poam, project, link):
    """Helper function to handle stakeholder notifications and associations"""
    if not stakeholder_ids:
        # check if stakeholder relationships exist and delete if they do
        db.query(CapPoamStakeHolder).filter(CapPoamStakeHolder.cap_poam_id == cap_poam.id).delete()
        db.commit()
        return
    # Remove any stakeholders not in list
    db.query(CapPoamStakeHolder).filter(~CapPoamStakeHolder.user_id.in_(stakeholder_ids)).delete()
    # check if stakeholder relationship already exists before adding
    stakeholders = db.query(User).filter(User.id.in_(stakeholder_ids)).all()
    new_stakeholders = []
    for stakeholder in stakeholders:
        exists = (
            db.query(CapPoamStakeHolder)
            .filter(CapPoamStakeHolder.cap_poam_id == cap_poam.id)
            .filter(CapPoamStakeHolder.user_id == stakeholder.id)
        )
        if exists.first() is None:
            db.add(CapPoamStakeHolder(cap_poam_id=cap_poam.id, user_id=stakeholder.id))
            new_stakeholders.append(stakeholder)
            db.commit()
    # cap_poam.stakeholders = stakeholders
    for stakeholder in new_stakeholders:
        await add_notification(
            db,
            stakeholder.id,
            "cap_poam_stakeholder",
            cap_poam.id,
            "/projects/{project.id}/cap_poams/{cap_poam.id}",
            f"You've been added as a stakeholder to {cap_poam.name}",
            project.id,
        )
        await notify_user(
            stakeholder, f"You've been added as a stakeholder on {cap_poam.name}", link, None
        )


async def manage_project_controls(db, project_control_ids, cap_poam):
    """Helper function to handle project control associations"""
    if not project_control_ids:
        # check if project control relationships exist and delete if they do
        db.query(CapPoamProjectControl).filter(
            CapPoamProjectControl.cap_poam_id == cap_poam.id
        ).delete()
        db.commit()
        return
    # Remove any project controls not in list
    db.query(CapPoamProjectControl).filter(
        ~CapPoamProjectControl.project_control_id.in_(project_control_ids)
    ).delete()
    project_controls = (
        db.query(ProjectControl).filter(ProjectControl.id.in_(project_control_ids)).all()
    )
    for pc in project_controls:
        exists = (
            db.query(CapPoamProjectControl)
            .filter(CapPoamProjectControl.cap_poam_id == cap_poam.id)
            .filter(CapPoamProjectControl.project_control_id == pc.id)
        )
        if exists.first() is None:
            db.add(CapPoamProjectControl(cap_poam_id=cap_poam.id, project_control_id=pc.id))
            db.commit()


# Core CRUD Functions
async def create_cap_poam(db: Session, cap_poam: CreateCapPoam, tenant_id: int, user_id: int):
    project = db.query(Project).filter_by(id=cap_poam.project_id, tenant_id=tenant_id).first()
    if not project:
        return False

    cap_poam_data = cap_poam.dict()
    stakeholder_ids = cap_poam_data.pop("stakeholder_ids", None)
    project_control_ids = cap_poam_data.pop("project_control_ids", None)
    task_ids = cap_poam_data.pop("task_ids", None)
    new_cap_poam = CapPoam(**cap_poam_data)
    db.add(new_cap_poam)
    db.commit()
    db.refresh(new_cap_poam)

    # Update tasks
    if task_ids is not None:  # Fix condition
        # Add new costs
        for task in task_ids:
            new_task_map = CapPoamTask(cap_poam_id=new_cap_poam.id, task_id=task)
            db.add(new_task_map)

        db.commit()

    db.add(
        CapPoamHistory(
            cap_poam_id=new_cap_poam.id,
            author_id=user_id,
            history=f"Created new cap poam {new_cap_poam.name}",
        )
    )
    await add_notification(
        db,
        new_cap_poam.owner_id,
        "cap_poams",
        new_cap_poam.id,
        f"/projects/{project.id}/cap_poams/{new_cap_poam.id}",
        f"You've been assigned as an owner for cap poam {new_cap_poam.name}",
        project.id,
    )

    link = f"/projects/{project.id}/cap_poams/{new_cap_poam.id}"

    await manage_stakeholders(db, stakeholder_ids, new_cap_poam, project, link)
    await manage_project_controls(db, project_control_ids, new_cap_poam)
    # Get all users watching project cap poams for this project
    message = f"Created new cap poam {new_cap_poam.name}"
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_cap_poams == True)
        .filter(UserWatching.project_id == project.id)
        .all()
    )
    await manage_notifications(
        db, users_watching, "cap_poams", message, link, project.id, new_cap_poam.id
    )

    db.commit()
    return new_cap_poam


def get_cap_poams_by_project_id(db: Session, tenant_id: int, project_id: int, user_id: int):
    cap_poams = db.query(CapPoam).filter(CapPoam.project_id == project_id).all()
    return cap_poams


def get_cap_poam(db: Session, id: int, tenant_id: int, user_id: int):
    cap_poam = (
        filter_by_user_project_role(db=db, model=CapPoam, tenant_id=tenant_id, user_id=user_id)
        .options(
            selectinload(CapPoam.stakeholders),
            selectinload(CapPoam.project_controls),
        )
        .filter(CapPoam.id == id)
        .first()
    )
    return cap_poam


async def update_cap_poam(
    db: Session, id: int, cap_poam: UpdateCapPoam, tenant_id: int, user_id: int
):
    existing_cap_poam = db.query(CapPoam).filter(CapPoam.id == id)
    if not existing_cap_poam.first():
        return False

    cap_poam_data = cap_poam.dict(exclude_unset=True)
    stakeholder_ids = cap_poam_data.pop("stakeholder_ids", None)
    project_control_ids = cap_poam_data.pop("project_control_ids", None)

    # Update costs
    cost_ids = cap_poam_data.pop("cost_ids", None)
    if cost_ids is not None:  # Fix condition

        # Add new costs
        for cost in cost_ids:
            new_cost_map = CapPoamCost(cap_poam_id=id, cost_id=cost)
            db.add(new_cost_map)

        db.commit()

    # Update tasks
    task_ids = cap_poam_data.pop("task_ids", None)
    if task_ids is not None:  # Fix condition

        # Add new costs
        for task in task_ids:
            new_task_map = CapPoamTask(cap_poam_id=id, task_id=task)
            db.add(new_task_map)

        db.commit()

    update_cap_poam = UpdateCapPoam(**cap_poam_data)

    changes = []
    for field in [
        "name",
        "description",
        "comments",
        "due_date",
        "status",
        "criticality_rating",
        "owner_id",
    ]:
        if (
            getattr(existing_cap_poam.first(), field) != getattr(update_cap_poam, field, None)
            and getattr(update_cap_poam, field, None) is not None
        ):
            changes.append(
                f"Updated {field.replace('_', ' ')} to {getattr(update_cap_poam, field, None)}"
            )

    project = (
        db.query(Project)
        .filter_by(id=existing_cap_poam.first().project_id, tenant_id=tenant_id)
        .first()
    )
    link = f"/projects/{project.id}/cap_poams/{existing_cap_poam.first().id}"
    all_changes = ".    ".join(changes)
    if all_changes != "":
        users_watching = (
            db.query(UserWatching)
            .filter(UserWatching.project_cap_poams == True)
            .filter(UserWatching.project_id == project.id)
            .all()
        )
        await manage_notifications(
            db,
            users_watching,
            "cap_poams",
            all_changes,
            link,
            project.id,
            existing_cap_poam.first().id,
        )

        for change in changes:
            db.add(
                CapPoamHistory(
                    cap_poam_id=existing_cap_poam.first().id, author_id=user_id, history=change
                )
            )

    await manage_stakeholders(db, stakeholder_ids or [], existing_cap_poam.first(), project, link)
    await manage_project_controls(db, project_control_ids or [], existing_cap_poam.first())

    update_data = update_cap_poam.dict(exclude_unset=True)

    if update_data:
        existing_cap_poam.update(update_data)
        db.commit()
    else:
        LOGGER.warning("No valid fields to update, skipping UPDATE query.")

    return get_cap_poam(db=db, id=id, tenant_id=tenant_id, user_id=user_id)


async def delete_cap_poam(db: Session, id: int, tenant_id: int):
    existing_cap_poam = db.query(CapPoam).filter(CapPoam.id == id)
    if not existing_cap_poam.first():
        return False
    project = (
        db.query(Project)
        .join(CapPoam, CapPoam.project_id == Project.id)
        .filter(Project.id == existing_cap_poam.first().project_id)
        .first()
    )
    manage_notifications(
        db,
        db.query(UserWatching)
        .filter(UserWatching.project_cap_poams == True, UserWatching.project_id == project.id)
        .all(),
        "cap_poams",
        f"Deleted cap poam {existing_cap_poam.first().name}",
        f"/projects/{project.id}/cap_poams",
        project.id,
        existing_cap_poam.first().id,
    )
    db.query(CapPoamStakeHolder).filter(
        CapPoamStakeHolder.cap_poam_id == existing_cap_poam.first().id
    ).delete()
    db.query(CapPoamProjectControl).filter(
        CapPoamProjectControl.cap_poam_id == existing_cap_poam.first().id
    ).delete()
    db.query(CapPoamHistory).filter(CapPoamHistory.cap_poam_id == id).delete()
    db.query(CapPoamCost).filter(CapPoamCost.cap_poam_id == id).delete()
    db.query(CapPoamTask).filter(CapPoamTask.cap_poam_id == id).delete()
    db.query(CapPoamApprovalWorkflow).filter(CapPoamApprovalWorkflow.cap_poam_id == id).delete()
    existing_cap_poam.delete(synchronize_session=False)
    db.commit()
    return True


def get_cap_poams_data_for_spreadsheet_by_project_id(
    db: Session, tenant_id: int, project_id: int, user_id: int
):
    cap_poams = (db.query(CapPoam).filter(CapPoam.project_id == project_id)).all()
    format_poams = []
    for cap_poam in cap_poams:
        # get audit test name
        audit_test_name = ""
        audit_test = db.query(AuditTest).filter(AuditTest.id == cap_poam.audit_test_id)
        if audit_test.first() is not None:
            audit_test_name = audit_test.first().name
        # get owner email
        owner = db.query(User).filter(User.id == cap_poam.owner_id).first()
        # get all stakeholder emails
        stakeholder_emails = ""
        stakeholders = (
            db.query(CapPoamStakeHolder, User)
            .join(User, User.id == CapPoamStakeHolder.user_id)
            .filter(CapPoamStakeHolder.cap_poam_id == cap_poam.id)
        ).all()
        for stake in stakeholders:
            stakeholder_emails += stake.User.email + ","

        # get project name
        project = db.query(Project).filter(Project.id == project_id).first()
        # get all project control names
        project_control_string = ""
        project_controls = (
            db.query(CapPoamProjectControl, ProjectControl, Control)
            .join(ProjectControl, ProjectControl.id == CapPoamProjectControl.project_control_id)
            .join(Control, Control.id == ProjectControl.control_id)
            .filter(CapPoamProjectControl.cap_poam_id == cap_poam.id)
        ).all()
        for pc in project_controls:
            project_control_string += pc.Control.name + ","

        new_cap = {
            "name": cap_poam.name,
            "owner_id": cap_poam.owner_id,
            "owner_email": owner.email,
            "audit_test_id": cap_poam.audit_test_id,
            "audit_test": audit_test_name,
            "description": cap_poam.description,
            "due_date": cap_poam.due_date,
            "status": cap_poam.status,
            "cap_poam_id": cap_poam.id,
            "project_id": cap_poam.project_id,
            "project": project.name,
            "user_defined_id": cap_poam.user_defined_id,
            "comments": cap_poam.comments,
            "criticality_rating": cap_poam.criticality_rating,
            "created_date": cap_poam.created_date,
            "stakeholders": stakeholder_emails,
            "controls": project_control_string,
        }
        format_poams.append(new_cap)

    return format_poams
