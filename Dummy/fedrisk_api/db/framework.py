import logging

from sqlalchemy import or_, func
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import (
    Assessment,
    Control,
    Exception,
    Framework,
    FrameworkVersion,
    ControlFrameworkVersion,
    Project,
    ProjectControl,
    Keyword,
    KeywordMapping,
    FrameworkDocument,
    FrameworkTenant,
    # ProjectUser,
    User,
)
from fedrisk_api.schema.framework import (
    CreateFramework,
    UpdateFramework,
    CreateFrameworkTenant,
    UpdateFrameworkTenant,
)
from fedrisk_api.utils.utils import filter_by_tenant  # , ordering_query

from sqlalchemy.exc import IntegrityError

LOGGER = logging.getLogger(__name__)


def add_keywords(db, keywords, framework_id, tenant_id):
    """Link keywords to framework."""
    if not keywords:
        return

    keyword_names = {k.strip().lower() for k in keywords.split(",") if k.strip()}

    for name in keyword_names:
        keyword = db.query(Keyword).filter_by(tenant_id=tenant_id, name=name).first()
        if not keyword:
            try:
                keyword = Keyword(name=name, tenant_id=tenant_id)
                db.add(keyword)
                db.flush()  # Get keyword.id before mapping
            except IntegrityError:
                db.rollback()
                keyword = db.query(Keyword).filter_by(tenant_id=tenant_id, name=name).first()

        # Add KeywordMapping if it doesn't exist
        if keyword:
            exists = (
                db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, framework_id=framework_id)
                .first()
            )
            if not exists:
                db.add(KeywordMapping(keyword_id=keyword.id, framework_id=framework_id))

    db.commit()


def remove_old_keywords(db, keywords, framework_id):
    """Remove keywords from framework that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(framework_id=framework_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = (
        db.query(Keyword).join(KeywordMapping).filter_by(framework_id=framework_id).all()
    )

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, framework_id=framework_id)
                .first()
            )
            db.delete(mapping)
    db.commit()


def create_framework(db: Session, framework: CreateFramework, tenant_id: int, keywords: str):
    new_framework = Framework(**framework.dict())
    db.add(new_framework)
    db.commit()
    db.refresh(new_framework)
    # add framework tenant mapping
    new_frame_ten_map = {
        "tenant_id": tenant_id,
        "framework_id": new_framework.id,
        "is_enabled": True,
    }
    new_frame_ten_map_obj = FrameworkTenant(**new_frame_ten_map)
    db.add(new_frame_ten_map_obj)
    db.commit()
    # add keywords
    add_keywords(db, keywords, new_framework.id, tenant_id)
    return new_framework


def create_framework_map_tenant(db: Session, frame_ten_map: CreateFrameworkTenant):
    # add framework tenant mapping
    new_frame_ten_map_obj = FrameworkTenant(**frame_ten_map.dict())
    db.add(new_frame_ten_map_obj)
    db.commit()
    return new_frame_ten_map_obj


def get_all_frameworks(
    db: Session,
    tenant_id: int,
    project_id: int = None,
    is_global: bool = None,
    is_enabled: bool = None,
    # q: str = None,
    # filter_by: str = None,
    # filter_value=None,
    # sort_by: str = None,
):

    queryset = (
        db.query(Framework)
        .join(FrameworkTenant, Framework.id == FrameworkTenant.framework_id)
        .filter(FrameworkTenant.tenant_id == tenant_id)
        # .options(
        #     contains_eager(Framework.controls),
        #     # Control no longer has these attributes - that's only ProjectControl
        #     # selectinload(Framework.controls).selectinload(Control.control_class),
        #     # selectinload(Framework.controls).selectinload(Control.control_status),
        #     # selectinload(Framework.controls).selectinload(Control.control_family),
        #     # selectinload(Framework.controls).selectinload(Control.control_phase),
        # )
    )
    if project_id is not None:
        queryset = (
            queryset.join(FrameworkVersion, Framework.id == FrameworkVersion.framework_id)
            .join(
                ControlFrameworkVersion,
                ControlFrameworkVersion.framework_version_id == FrameworkVersion.id,
            )
            .join(Control, Control.id == ControlFrameworkVersion.control_id)
            .join(ProjectControl, ProjectControl.control_id == Control.id)
            .join(Project, Project.id == ProjectControl.project_id)
            .filter(Project.id == project_id)
        )
    if is_global is not None:
        queryset = queryset.filter(Framework.is_global == is_global)
    if is_enabled is not None:
        queryset = queryset.filter(FrameworkTenant.is_enabled == is_enabled)
    # if filter_by and filter_value:
    #     if filter_by in ("name", "description", "keywords"):
    #         queryset = queryset.filter(
    #             func.lower(getattr(Framework, filter_by)).contains(func.lower(filter_value))
    #         )
    #     else:
    #         queryset = queryset.filter(getattr(Framework, filter_by) == filter_value)

    # if sort_by:
    #     queryset = ordering_query(query=queryset, model=Framework.__tablename__, order=sort_by)

    # if q:
    #     queryset = queryset.filter(
    #         or_(
    #             func.lower(Framework.name).contains(func.lower(q)),
    #             func.lower(Framework.description).contains(func.lower(q)),
    #         )
    #     )

    return queryset.distinct()


def get_framework(db: Session, id: int, tenant_id: int):
    return (
        db.query(Framework)
        # .join(FrameworkTenant, Framework.id == FrameworkTenant.framework_id)
        .filter(Framework.id == id)
        # .filter(FrameworkTenant.id == tenant_id)
        .options(
            selectinload(Framework.framework_version),
            # selectinload(Framework.controls).selectinload(Control.control_class),
            # selectinload(Framework.controls).selectinload(Control.control_status),
            # selectinload(Framework.controls).selectinload(Control.control_family),
            # selectinload(Framework.controls).selectinload(Control.control_phase),
        ).first()
    )


def update_framework_map_tenant(db: Session, framework_tenant: UpdateFrameworkTenant):
    existing_frame_ten_map = (
        db.query(FrameworkTenant)
        .filter(FrameworkTenant.tenant_id == framework_tenant.tenant_id)
        .filter(FrameworkTenant.framework_id == framework_tenant.framework_id)
    )
    if not existing_frame_ten_map.first():
        return False
    existing_frame_ten_map.update(framework_tenant.dict(exclude_unset=True))
    db.commit()
    return existing_frame_ten_map.first()


def update_framework(
    db: Session, id: int, framework: UpdateFramework, tenant_id: int, keywords: str
):
    existing_framework = db.query(Framework).filter(Framework.id == id)
    if not existing_framework.first():
        return False
    # remove keywords not included
    remove_old_keywords(db, keywords, id)
    add_keywords(db, keywords, id, tenant_id)
    existing_framework.update(framework.dict(exclude_unset=True))
    db.commit()
    return existing_framework


def delete_framework(db: Session, id: int):
    existing_framework = (
        db.query(Framework)
        # .join(FrameworkTenant, Framework.id == FrameworkTenant.framework_id)
        # .filter(FrameworkTenant.tenant_id == tenant_id)
        .filter(Framework.id == id)
    )
    # filter_by_tenant(db, Framework, tenant_id).filter(Framework.id == id)
    if not existing_framework.first():
        return False

    framework_versions = db.query(FrameworkVersion).filter(FrameworkVersion.framework_id == id)

    for version in framework_versions:
        controls = db.query(ControlFrameworkVersion).filter(
            ControlFrameworkVersion.framework_version_id == version.id
        )
        for control in controls:
            project_controls = db.query(ProjectControl).filter(
                ProjectControl.control_id == control.id
            )
            for project_control in project_controls:
                # delete project control keyword mappings
                db.query(KeywordMapping).filter(
                    KeywordMapping.project_control_id == project_control.id
                ).delete()
                # delete assessment keyword mappings
                assessment = db.query(Assessment).filter(
                    Assessment.project_control_id == project_control.id
                )
                if assessment.first() is not None:
                    db.query(KeywordMapping).filter(
                        KeywordMapping.assessment_id == assessment.first().id
                    ).delete()
                    assessment.delete()
                # delete exception keyword mappings
                exception = db.query(Exception).filter(
                    Exception.project_control_id == project_control.id
                )
                if exception.first() is not None:
                    db.query(KeywordMapping).filter(
                        KeywordMapping.exception_id == exception.first().id
                    ).delete()
                    exception.delete()
            # delete project control keyword mappings
            project_controls.delete()
        # TODO: delete control keyword mappings
        controls.delete()
        # delete framework version keyword mappings
        db.query(KeywordMapping).filter(KeywordMapping.framework_version_id == version.id).delete()

    framework_versions.delete()
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.framework_id == id).delete()
    # delete all document references
    db.query(FrameworkDocument).filter(FrameworkDocument.framework_id == id).delete()
    # delete framework tenant reference
    db.query(FrameworkTenant).filter(FrameworkTenant.framework_id == id).delete()
    existing_framework.delete(synchronize_session=False)
    db.commit()
    return True


def search(
    query: str,
    db: Session,
    tenant_id: int,
    user_id: int,
    offset: int = 0,
    limit: int = 10,
):
    lowercase_query = query.lower()
    user = db.query(User).filter(User.id == user_id).first()

    if user.is_superuser:
        res = (
            db.query(Framework)
            .filter(
                or_(
                    func.lower(Framework.name).contains(lowercase_query),
                    func.lower(Framework.description).contains(lowercase_query),
                    func.lower(Framework.keywords).contains(lowercase_query),
                )
            )
            .all()
        )
    elif user.is_tenant_admin:
        res = (
            filter_by_tenant(db, Framework, tenant_id)
            .filter(
                or_(
                    func.lower(Framework.name).contains(lowercase_query),
                    func.lower(Framework.description).contains(lowercase_query),
                    func.lower(Framework.keywords).contains(lowercase_query),
                )
            )
            .all()
        )
    else:
        res = (
            filter_by_tenant(db, Framework, tenant_id)
            .join(Control, Control.framework_id == Framework.id)
            .join(ProjectControl, ProjectControl.control_id == Control.id)
            .join(ProjectUser, ProjectUser.project_id == ProjectControl.project_id)
            .filter(ProjectUser.user_id == user_id)
            .filter(
                or_(
                    func.lower(Framework.name).contains(lowercase_query),
                    func.lower(Framework.description).contains(lowercase_query),
                    func.lower(Framework.keywords).contains(lowercase_query),
                )
            )
            .distinct()
            .all()
        )

    if user.is_superuser:
        count = (
            db.query(Framework)
            .filter(
                or_(
                    func.lower(Framework.name).contains(lowercase_query),
                    func.lower(Framework.description).contains(lowercase_query),
                    func.lower(Framework.keywords).contains(lowercase_query),
                )
            )
            .count()
        )
    elif user.is_tenant_admin:
        count = (
            filter_by_tenant(db, Framework, tenant_id)
            .filter(
                or_(
                    func.lower(Framework.name).contains(lowercase_query),
                    func.lower(Framework.description).contains(lowercase_query),
                    func.lower(Framework.keywords).contains(lowercase_query),
                )
            )
            .count()
        )
    else:
        count = (
            filter_by_tenant(db, Framework, tenant_id)
            .join(Control, Control.framework_id == Framework.id)
            .join(ProjectControl, ProjectControl.control_id == Control.id)
            .join(ProjectUser, ProjectUser.project_id == ProjectControl.project_id)
            .filter(ProjectUser.user_id == user_id)
            .filter(
                or_(
                    func.lower(Framework.name).contains(lowercase_query),
                    func.lower(Framework.description).contains(lowercase_query),
                    func.lower(Framework.keywords).contains(lowercase_query),
                )
            )
            .distinct()
            .count()
        )
    return count, res[offset : offset + limit]
