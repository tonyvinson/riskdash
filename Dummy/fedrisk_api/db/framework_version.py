import logging

# from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import (
    # Assessment,
    Control,
    # Exception,
    Framework,
    FrameworkVersion,
    ControlFrameworkVersion,
    Project,
    ProjectControl,
    Keyword,
    KeywordMapping,
    ControlFrameworkVersion,
    FrameworkVersionDocument,
    # ProjectUser,
    # User,
)
from fedrisk_api.schema.framework_version import CreateFrameworkVersion, UpdateFrameworkVersion

# from fedrisk_api.schema.control import CreateControl

# from fedrisk_api.utils.utils import filter_by_tenant, ordering_query

LOGGER = logging.getLogger(__name__)

# Keyword Management Functions
def add_keywords(db, keywords, framework_version_id, tenant_id):
    """Link keywords to framework version."""
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
                .filter_by(keyword_id=keyword.id, framework_version_id=framework_version_id)
                .first()
            ):
                db.add(
                    KeywordMapping(keyword_id=keyword.id, framework_version_id=framework_version_id)
                )
    db.commit()


def remove_old_keywords(db, keywords, framework_version_id):
    """Remove keywords from framework version that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(framework_version_id=framework_version_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = (
        db.query(Keyword)
        .join(KeywordMapping)
        .filter_by(framework_version_id=framework_version_id)
        .all()
    )

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, framework_version_id=framework_version_id)
                .first()
            )
            db.delete(mapping)
    db.commit()


def create_framework_version(
    db: Session, framework_version: CreateFrameworkVersion, keywords: str, tenant_id: int
):
    new_framework_version = FrameworkVersion(**framework_version.dict())
    db.add(new_framework_version)
    db.commit()
    db.refresh(new_framework_version)
    # add keywords
    add_keywords(db, keywords, new_framework_version.id, tenant_id)
    return new_framework_version


def get_all_framework_versions(
    db: Session,
    # tenant_id: int,
    project_id: int = None,
    framework_id: int = None,
):
    queryset = db.query(FrameworkVersion).join(
        Framework, Framework.id == FrameworkVersion.framework_id
    )
    if project_id:
        queryset = (
            db.query(FrameworkVersion)
            .join(Framework, Framework.id == FrameworkVersion.framework_id)
            .join(
                ControlFrameworkVersion,
                FrameworkVersion.id == ControlFrameworkVersion.framework_version_id,
            )
            .join(Control, Control.id == ControlFrameworkVersion.control_id)
            .join(ProjectControl, ProjectControl.control_id == ControlFrameworkVersion.control_id)
            .join(Project, Project.id == ProjectControl.project_id)
            .filter(Project.id == project_id)
        )
    if framework_id:
        queryset = db.query(FrameworkVersion).filter(FrameworkVersion.framework_id == framework_id)
    LOGGER.info(queryset.distinct())
    return queryset.distinct()


def get_framework_version(db: Session, id: int):
    return (
        db.query(FrameworkVersion)
        .join(Framework, Framework.id == FrameworkVersion.framework_id)
        .filter(FrameworkVersion.id == id)
        # .options(
        # selectinload(FrameworkVersion.controls),
        # selectinload(Framework.controls).selectinload(Control.control_class),
        # selectinload(Framework.controls).selectinload(Control.control_status),
        # selectinload(Framework.controls).selectinload(Control.control_family),
        # selectinload(Framework.controls).selectinload(Control.control_phase),
        # )
        .first()
    )


def update_framework_version(
    db: Session, id: int, framework_version: UpdateFrameworkVersion, tenant_id: int, keywords: str
):
    existing_framework_version = db.query(FrameworkVersion).filter(FrameworkVersion.id == id)
    if not existing_framework_version.first():
        return False
    existing_framework_version.update(framework_version.dict(exclude_unset=True))
    # remove keywords not included
    remove_old_keywords(db, keywords, id)
    add_keywords(db, keywords, id, tenant_id)
    db.commit()
    return True


def delete_framework_version(db: Session, id: int):
    existing_framework_version = db.query(FrameworkVersion).filter(FrameworkVersion.id == id)
    if not existing_framework_version.first():
        return False

    # controls = db.query(Control).filter(Control.framework_version_id == id)

    # for control in controls:
    #     project_controls = db.query(ProjectControl).filter(ProjectControl.control_id == control.id)
    #     for project_control in project_controls:
    #         db.query(Assessment).filter(
    #             Assessment.project_control_id == project_control.id
    #         ).delete()
    #         db.query(Exception).filter(Exception.project_control_id == project_control.id).delete()
    #     project_controls.delete()
    # controls.delete()
    # delete all control references
    db.query(ControlFrameworkVersion).filter(
        ControlFrameworkVersion.framework_version_id == id
    ).delete()
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.framework_version_id == id).delete()
    # delete all document references
    db.query(FrameworkVersionDocument).filter(
        FrameworkVersionDocument.framework_version_id == id
    ).delete()
    existing_framework_version.delete(synchronize_session=False)
    db.commit()
    return True


# def search(
#     query: str,
#     db: Session,
#     tenant_id: int,
#     user_id: int,
#     offset: int = 0,
#     limit: int = 10,
# ):
#     lowercase_query = query.lower()
#     user = db.query(User).filter(User.id == user_id).first()

#     if user.is_superuser:
#         res = (
#             db.query(Framework)
#             .filter(
#                 or_(
#                     func.lower(Framework.name).contains(lowercase_query),
#                     func.lower(Framework.description).contains(lowercase_query),
#                     func.lower(Framework.keywords).contains(lowercase_query),
#                 )
#             )
#             .all()
#         )
#     elif user.is_tenant_admin:
#         res = (
#             filter_by_tenant(db, Framework, tenant_id)
#             .filter(
#                 or_(
#                     func.lower(Framework.name).contains(lowercase_query),
#                     func.lower(Framework.description).contains(lowercase_query),
#                     func.lower(Framework.keywords).contains(lowercase_query),
#                 )
#             )
#             .all()
#         )
#     else:
#         res = (
#             filter_by_tenant(db, Framework, tenant_id)
#             .join(Control, Control.framework_id == Framework.id)
#             .join(ProjectControl, ProjectControl.control_id == Control.id)
#             .join(ProjectUser, ProjectUser.project_id == ProjectControl.project_id)
#             .filter(ProjectUser.user_id == user_id)
#             .filter(
#                 or_(
#                     func.lower(Framework.name).contains(lowercase_query),
#                     func.lower(Framework.description).contains(lowercase_query),
#                     func.lower(Framework.keywords).contains(lowercase_query),
#                 )
#             )
#             .distinct()
#             .all()
#         )

#     if user.is_superuser:
#         count = (
#             db.query(Framework)
#             .filter(
#                 or_(
#                     func.lower(Framework.name).contains(lowercase_query),
#                     func.lower(Framework.description).contains(lowercase_query),
#                     func.lower(Framework.keywords).contains(lowercase_query),
#                 )
#             )
#             .count()
#         )
#     elif user.is_tenant_admin:
#         count = (
#             filter_by_tenant(db, Framework, tenant_id)
#             .filter(
#                 or_(
#                     func.lower(Framework.name).contains(lowercase_query),
#                     func.lower(Framework.description).contains(lowercase_query),
#                     func.lower(Framework.keywords).contains(lowercase_query),
#                 )
#             )
#             .count()
#         )
#     else:
#         count = (
#             filter_by_tenant(db, Framework, tenant_id)
#             .join(Control, Control.framework_id == Framework.id)
#             .join(ProjectControl, ProjectControl.control_id == Control.id)
#             .join(ProjectUser, ProjectUser.project_id == ProjectControl.project_id)
#             .filter(ProjectUser.user_id == user_id)
#             .filter(
#                 or_(
#                     func.lower(Framework.name).contains(lowercase_query),
#                     func.lower(Framework.description).contains(lowercase_query),
#                     func.lower(Framework.keywords).contains(lowercase_query),
#                 )
#             )
#             .distinct()
#             .count()
#         )
#     return count, res[offset : offset + limit]
