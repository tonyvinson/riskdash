import logging

from sqlalchemy.orm import Session

from fedrisk_api.db.models import Project, ProjectGroup
from fedrisk_api.schema.project_group import CreateProjectGroup, UpdateProjectGroup
from fedrisk_api.utils.utils import filter_by_tenant

LOGGER = logging.getLogger(__name__)


def create_project_group(project_group: CreateProjectGroup, db: Session, tenant_id: int):
    project_group = ProjectGroup(**project_group.dict(), tenant_id=tenant_id)
    db.add(project_group)
    db.commit()
    return project_group


def get_project_group(
    db: Session,
    tenant_id: int,
):
    queryset = filter_by_tenant(db=db, model=ProjectGroup, tenant_id=tenant_id).all()
    return queryset


def get_project_group_by_id(db: Session, project_group_id: int):
    queryset = db.query(ProjectGroup).filter(ProjectGroup.id == project_group_id).first()
    return queryset


def update_project_group_by_id(
    project_group: UpdateProjectGroup, db: Session, project_group_id: int, tenant_id: int
):
    queryset = filter_by_tenant(db=db, model=ProjectGroup, tenant_id=tenant_id).filter(
        ProjectGroup.id == project_group_id
    )

    if not queryset.first():
        return False

    queryset.update(project_group.dict(exclude_unset=True))
    db.commit()
    return True


def get_projects_by_group_id(db: Session, tenant_id: int, project_group_id: int):
    queryset = filter_by_tenant(db=db, model=Project, tenant_id=tenant_id)
    queryset = queryset.filter(Project.project_group_id == project_group_id).all()
    return queryset


def delete_project_group_by_id(db: Session, tenant_id: int, project_group_id: int):
    project_group = db.query(ProjectGroup).filter(ProjectGroup.id == project_group_id).first()

    if not project_group:
        return False

    project_group.projects = []
    db.delete(project_group)
    db.commit()
    return True
