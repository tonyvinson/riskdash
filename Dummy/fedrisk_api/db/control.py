from sqlalchemy import func, or_
from sqlalchemy.orm.session import Session
import logging

from fedrisk_api.db.models import (
    Assessment,
    Control,
    ControlFrameworkVersion,
    ControlClass,
    ControlFamily,
    ControlPhase,
    ControlStatus,
    Exception,
    Framework,
    FrameworkVersion,
    ProjectControl,
    ProjectUser,
    Risk,
    # RiskStakeholder,
    User,
    # Document,
    ControlDocument,
    Keyword,
    KeywordMapping,
)
from fedrisk_api.schema.control import (
    CreateControl,
    CreateBatchControlsFrameworkVersion,
    UpdateControl,
)
from fedrisk_api.utils.utils import filter_by_tenant, ordering_query

LOGGER = logging.getLogger(__name__)

# Keyword Management Functions
def add_keywords(db, keywords, control_id, tenant_id):
    """Link keywords to control."""
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
                .filter_by(keyword_id=keyword.id, control_id=control_id)
                .first()
            ):
                db.add(KeywordMapping(keyword_id=keyword.id, control_id=control_id))
    db.commit()


async def remove_old_keywords(db, keywords, control_id):
    """Remove keywords from control that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(control_id=control_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = (
        db.query(Keyword).join(KeywordMapping).filter_by(control_id=control_id).all()
    )

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, audit_test_id=control_id)
                .first()
            )
            db.delete(mapping)
    db.commit()


def create_control(db: Session, control: CreateControl, keywords: str, tenant_id: int):
    control_data = control.dict()
    # if (control_data["framework_versions"]):
    framework_version_ids = control_data.pop("framework_versions", None)
    new_control = Control(**control_data, tenant_id=tenant_id)
    fvs = db.query(FrameworkVersion).filter(FrameworkVersion.id.in_(framework_version_ids)).all()
    new_control.framework_versions = fvs
    db.add(new_control)
    db.commit()
    db.refresh(new_control)
    # add keywords
    add_keywords(db, keywords, new_control.id, tenant_id)
    return new_control


# add a batch of controls to a framework version
def add_batch_controls_to_framework_version(
    db: Session, framework_version_id: int, controls: CreateBatchControlsFrameworkVersion
):
    for curcontrol in controls.controls:
        new_framework_version_control = ControlFrameworkVersion(
            control_id=curcontrol.control_id,
            framework_version_id=curcontrol.framework_version_id,
        )
        db.add(new_framework_version_control)
        db.commit()
        db.refresh(new_framework_version_control)

    updated_framework_version = (
        db.query(FrameworkVersion).filter(FrameworkVersion.id == framework_version_id).first()
    )
    # db.flush()
    return updated_framework_version


# add a single control to a framework version relationship
def add_single_control_to_framework_version_relationship(
    db: Session, framework_version_id: int, control_id: int
):
    new_framework_version_control = ControlFrameworkVersion(
        control_id=control_id,
        framework_version_id=framework_version_id,
    )
    db.add(new_framework_version_control)
    db.commit()
    db.refresh(new_framework_version_control)
    # db.flush()
    return new_framework_version_control


def get_all_controls(
    db: Session,
    tenant_id: int,
    project_id: int = None,
    q: str = None,
    filter_by: str = None,
    filter_value=None,
    sort_by: str = None,
):
    queryset = (
        db.query(Control)
        .filter(or_(Control.tenant_id == tenant_id, Control.tenant_id == None))
        .join(ControlFrameworkVersion, ControlFrameworkVersion.control_id == Control.id)
        .join(FrameworkVersion, FrameworkVersion.id == ControlFrameworkVersion.framework_version_id)
        # .options(
        # selectinload(Control.framework_version),
        # )
    )
    if project_id:
        queryset = queryset.join(ProjectControl, ProjectControl.control_id == Control.id).filter(
            ProjectControl.project_id == project_id
        )

    if filter_by and filter_value:
        if filter_by in ("name", "description", "keywords"):
            queryset = queryset.filter(
                func.lower(getattr(Control, filter_by)).contains(func.lower(filter_value))
            )
        elif filter_by == "control_class":
            queryset = queryset.filter(
                func.lower(ControlClass.name).contains(func.lower(filter_value))
            )
        elif filter_by == "control_status":
            queryset = queryset.filter(
                func.lower(ControlStatus.name).contains(func.lower(filter_value))
            )
        elif filter_by == "control_phase":
            queryset = queryset.filter(
                func.lower(ControlPhase.name).contains(func.lower(filter_value))
            )
        elif filter_by == "control_family":
            queryset = queryset.filter(
                func.lower(ControlFamily.name).contains(func.lower(filter_value))
            )
        elif filter_by == "framework_version":
            queryset = queryset.filter(ControlFrameworkVersion.framework_version_id == filter_value)
        else:
            queryset = queryset.filter(getattr(Control, filter_by) == filter_value)

    if sort_by:
        if "control_class" in sort_by:
            if sort_by[0] == "-":
                queryset = queryset.order_by(ControlClass.name.desc())
            else:
                queryset = queryset.order_by(ControlClass.name)
        elif "control_status" in sort_by:
            if sort_by[0] == "-":
                queryset = queryset.order_by(ControlStatus.name.desc())
            else:
                queryset = queryset.order_by(ControlStatus.name)
        elif "control_phase" in sort_by:
            if sort_by[0] == "-":
                queryset = queryset.order_by(ControlPhase.name.desc())
            else:
                queryset = queryset.order_by(ControlPhase.name)
        elif "control_family" in sort_by:
            if sort_by[0] == "-":
                queryset = queryset.order_by(ControlFamily.name.desc())
            else:
                queryset = queryset.order_by(ControlFamily.name)
        elif "framework_version" in sort_by:
            if sort_by[0] == "-":
                queryset = queryset.order_by(ControlFrameworkVersion.id.desc())
            else:
                queryset = queryset.order_by(ControlFrameworkVersion.id)
        else:
            queryset = ordering_query(query=queryset, model=Control.__tablename__, order=sort_by)

    if q:
        queryset = queryset.filter(
            or_(
                func.lower(Control.name).contains(func.lower(q)),
                func.lower(Control.description).contains(func.lower(q)),
            )
        )

    return queryset.distinct()


def get_control(db: Session, id: int, tenant_id: int):
    control = (
        db.query(Control)
        .filter(or_(Control.tenant_id == tenant_id, Control.tenant_id == None), Control.id == id)
        .first()
    )
    return control


async def update_control(
    db: Session, id: int, control: UpdateControl, keywords: str, tenant_id: int
):
    existing_control = filter_by_tenant(db, Control, tenant_id).filter(Control.id == id)
    if not existing_control.first():
        return False
    existing_control.update(control.dict(exclude_unset=True))
    db.commit()
    # remove keywords not included
    await remove_old_keywords(db, keywords, id)
    # add keywords
    await add_keywords(db, keywords, existing_control.first().id, tenant_id)
    return True


def delete_control(db: Session, id: int, tenant_id: int):
    # existing_control = filter_by_tenant(db, Control, tenant_id).filter(Control.id == id)
    # if not existing_control.first():
    #     return False

    existing_control = db.query(Control).filter(Control.id == id)
    if not existing_control.first():
        return False
    project_controls = db.query(ProjectControl).filter(
        ProjectControl.control_id == existing_control.first().id
    )
    for project_control in project_controls:
        # Delete the assessment object for this project control
        db.query(Assessment).filter(Assessment.project_control_id == project_control.id).delete()

        existing_exceptions = db.query(Exception).filter(
            Exception.project_control_id == project_control.id
        )
        for exception in existing_exceptions.all():
            exception.stakeholders = []
        existing_exceptions.delete(synchronize_session=False)

        existing_risks = db.query(Risk).filter(Risk.project_control_id == project_control.id)
        for next_risk in existing_risks.all():
            # additional_stakeholders = (
            #     db.query(RiskStakeholder)
            #     .filter(RiskStakeholder.risk_id == next_risk.id)
            #     .delete(synchronize_session=False)
            # )
            next_risk.stakeholders = []
            next_risk.project_control_id = None
        existing_risks.delete(synchronize_session=False)
    project_controls.delete()
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.control_id == id).delete()
    # delete all document references
    db.query(ControlDocument).filter(ControlDocument.control_id == id).delete()
    existing_control.delete(synchronize_session=False)
    db.commit()
    return True


def search(query: str, db: Session, tenant_id: int, user_id: int, offset: int = 0, limit: int = 10):
    lowercase_query = query.lower()

    user = db.query(User).filter(User.id == user_id).first()

    if user.is_superuser:
        res = (
            db.query(Control)
            .filter(
                or_(
                    func.lower(Control.name).contains(lowercase_query),
                    func.lower(Control.description).contains(lowercase_query),
                    func.lower(Control.keywords).contains(lowercase_query),
                )
            )
            .all()
        )
    elif user.is_tenant_admin:
        res = (
            filter_by_tenant(db, Control, tenant_id)
            .filter(
                or_(
                    func.lower(Control.name).contains(lowercase_query),
                    func.lower(Control.description).contains(lowercase_query),
                    func.lower(Control.keywords).contains(lowercase_query),
                )
            )
            .all()
        )
    else:
        res = (
            filter_by_tenant(db, Control, tenant_id)
            .join(ProjectControl, ProjectControl.control_id == Control.id)
            .join(ProjectUser, ProjectUser.project_id == ProjectControl.project_id)
            .filter(ProjectUser.user_id == user_id)
            .filter(
                or_(
                    func.lower(Control.name).contains(lowercase_query),
                    func.lower(Control.description).contains(lowercase_query),
                    func.lower(Control.keywords).contains(lowercase_query),
                )
            )
            .all()
        )

    if user.is_superuser:
        count = (
            db.query(Control)
            .filter(
                or_(
                    func.lower(Control.name).contains(lowercase_query),
                    func.lower(Control.description).contains(lowercase_query),
                    func.lower(Control.keywords).contains(lowercase_query),
                )
            )
            .count()
        )
    elif user.is_tenant_admin:
        count = (
            filter_by_tenant(db, Control, tenant_id)
            .filter(
                or_(
                    func.lower(Control.name).contains(lowercase_query),
                    func.lower(Control.description).contains(lowercase_query),
                    func.lower(Control.keywords).contains(lowercase_query),
                )
            )
            .count()
        )
    else:
        count = (
            filter_by_tenant(db, Control, tenant_id)
            .join(ProjectControl, ProjectControl.control_id == Control.id)
            .join(ProjectUser, ProjectUser.project_id == ProjectControl.project_id)
            .filter(ProjectUser.user_id == user_id)
            .filter(
                or_(
                    func.lower(Control.name).contains(lowercase_query),
                    func.lower(Control.description).contains(lowercase_query),
                    func.lower(Control.keywords).contains(lowercase_query),
                )
            )
            .distinct()
            .count()
        )

    return count, res[offset : offset + limit]
