from sqlalchemy import or_
from sqlalchemy.orm import Session

from fedrisk_api.db.models import (
    Control,
    Framework,
    FrameworkVersion,
    ControlFrameworkVersion,
    Project,
    ProjectControl,
    ProjectUser,
    User,
)


def get_project(db: Session, project_id: int, user):
    user_obj = db.query(User).filter(User.id == user["user_id"]).first()

    if not project_id:
        project = (
            db.query(Project)
            .filter(Project.tenant_id == user["tenant_id"])
            .order_by(Project.created_date.desc())
            .first()
        )
        if not project:
            project = db.query(Project).order_by(Project.last_updated_date.desc())

            if user_obj.is_superuser:
                return project.first()
            elif user_obj.is_tenant_admin:
                return project.filter(Project.tenant_id == user["tenant_id"]).first()
            else:
                return (
                    project.join(ProjectUser, ProjectUser.project_id == Project.id)
                    .filter(Project.tenant_id == user["tenant_id"])
                    .filter(ProjectUser.user_id == user["user_id"])
                    .first()
                )
    else:
        if user_obj.is_superuser:
            project = (
                db.query(Project)
                .filter(Project.id == project_id)
                .order_by(Project.last_updated_date.desc())
                .first()
            )
        elif user_obj.is_tenant_admin:
            project = (
                db.query(Project)
                .filter(Project.id == project_id)
                .filter(Project.tenant_id == user["tenant_id"])
                .order_by(Project.last_updated_date.desc())
                .first()
            )
        else:
            project = (
                db.query(Project)
                .join(ProjectUser, ProjectUser.project_id == Project.id)
                .filter(Project.tenant_id == user["tenant_id"])
                .filter(ProjectUser.user_id == user["user_id"])
                .filter(Project.id == project_id)
                .order_by(Project.last_updated_date.desc())
                .first()
            )
    return project


def get_framework(db: Session, framework_id: int, project_id: int, user):
    if not framework_id:
        framework = (
            db.query(Framework)
            .join(FrameworkVersion, FrameworkVersion.framework_id == Framework.id)
            .join(
                ControlFrameworkVersion,
                ControlFrameworkVersion.framework_version_id == FrameworkVersion.id,
            )
            .join(Control, Control.id == ControlFrameworkVersion.control_id)
            .join(ProjectControl, ProjectControl.project_id == project_id)
            .order_by(Framework.created_date.desc())
            .first()
        )
    else:
        framework = (
            db.query(Framework)
            .filter(Framework.id == framework_id)
            # .filter(or_(Framework.tenant_id == user["tenant_id"], Framework.tenant_id == None))
            .order_by(Framework.created_date.desc())
            .first()
        )
    return framework
