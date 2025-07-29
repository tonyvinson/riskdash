from sqlalchemy import func, or_
from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import ControlClass
from fedrisk_api.schema.control_class import CreateControlClass, UpdateControlClass
from fedrisk_api.utils.utils import ordering_query


def create_control_class(db: Session, control_class: CreateControlClass, tenant_id):
    new_control_class = ControlClass(**control_class.dict(), tenant_id=tenant_id)
    db.add(new_control_class)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_control_class)
    return new_control_class


def get_all_control_classes(
    q: str, db: Session, tenant_id: int, filter_by: str, filter_value: str, sort_by: str
):
    queryset = db.query(ControlClass).filter(
        or_(ControlClass.tenant_id == tenant_id, ControlClass.tenant_id == None)
    )

    if filter_by and filter_value:
        if filter_by in ("name", "description"):
            queryset = queryset.filter(
                func.lower(getattr(ControlClass, filter_by)).contains(filter_value.lower())
            )
    elif q:
        queryset = queryset.filter(
            or_(
                func.lower(ControlClass.name).contains(func.lower(q)),
                func.lower(ControlClass.description).contains(func.lower(q)),
            )
        )

    if sort_by:
        queryset = ordering_query(query=queryset, order=sort_by)

    return queryset


def get_control_class(db: Session, id: int, tenant_id: int):
    return (
        db.query(ControlClass)
        .filter(or_(ControlClass.tenant_id == tenant_id, ControlClass.tenant_id == None))
        .filter(ControlClass.id == id)
        .first()
    )


def update_control_class(db: Session, id: int, control_class: UpdateControlClass, tenant_id: int):
    existing_control_class = (
        db.query(ControlClass)
        .filter(ControlClass.id == id)
        .filter(ControlClass.tenant_id == tenant_id)
    )
    if not existing_control_class.first():
        return False
    existing_control_class.update(control_class.dict(exclude_unset=True))
    db.commit()
    return True


def delete_control_class(db: Session, id: int, tenant_id: int):
    existing_control_class = (
        db.query(ControlClass)
        .filter(ControlClass.id == id)
        .filter(ControlClass.tenant_id == tenant_id)
    )
    if not existing_control_class.first():
        return False

    existing_control_class.delete(synchronize_session=False)
    db.commit()
    return True
