from sqlalchemy import func, or_
from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import ControlFamily
from fedrisk_api.schema.control_family import CreateControlFamily, UpdateControlFamily
from fedrisk_api.utils.utils import ordering_query


def create_control_family(db: Session, control_family: CreateControlFamily, tenant_id: int):
    new_control_family = ControlFamily(**control_family.dict(), tenant_id=tenant_id)
    db.add(new_control_family)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_control_family)
    return new_control_family


def get_all_control_families(
    q: str, db: Session, tenant_id: int, filter_by: str, filter_value: str, sort_by: str
):
    queryset = db.query(ControlFamily).filter(
        or_(ControlFamily.tenant_id == tenant_id, ControlFamily.tenant_id == None)
    )

    if filter_by and filter_value:
        if filter_by in ("name", "description"):
            queryset = queryset.filter(
                func.lower(getattr(ControlFamily, filter_by)).contains(filter_value.lower())
            )
    elif q:
        queryset = queryset.filter(
            or_(
                func.lower(ControlFamily.name).contains(func.lower(q)),
                func.lower(ControlFamily.description).contains(func.lower(q)),
            )
        )

    if sort_by:
        queryset = ordering_query(query=queryset, order=sort_by)

    return queryset


def get_control_family(db: Session, id: int, tenant_id: int):
    return (
        db.query(ControlFamily)
        .filter(or_(ControlFamily.tenant_id == tenant_id, ControlFamily.tenant_id == None))
        .filter(ControlFamily.id == id)
        .first()
    )


def update_control_family(
    db: Session, id: int, control_family: UpdateControlFamily, tenant_id: int
):
    existing_control_family = (
        db.query(ControlFamily)
        .filter(ControlFamily.id == id)
        .filter(ControlFamily.tenant_id == tenant_id)
    )
    if not existing_control_family.first():
        return False
    existing_control_family.update(control_family.dict(exclude_unset=True))
    db.commit()
    return True


def delete_control_family(db: Session, id: int, tenant_id: int):
    existing_control_family = (
        db.query(ControlFamily)
        .filter(ControlFamily.id == id)
        .filter(ControlFamily.tenant_id == tenant_id)
    )
    if not existing_control_family.first():
        return False

    existing_control_family.delete(synchronize_session=False)
    db.commit()
    return True
