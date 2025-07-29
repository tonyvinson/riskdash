from sqlalchemy import func, or_
from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import ControlPhase
from fedrisk_api.schema.control_phase import CreateControlPhase, UpdateControlPhase
from fedrisk_api.utils.utils import ordering_query


def create_control_phase(db: Session, control_phase: CreateControlPhase, tenant_id: int):
    new_control_phase = ControlPhase(**control_phase.dict(), tenant_id=tenant_id)
    db.add(new_control_phase)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_control_phase)
    return new_control_phase


def get_all_control_phases(
    q: str, db: Session, tenant_id: int, filter_by: str, filter_value: str, sort_by: str
):
    queryset = db.query(ControlPhase).filter(
        or_(ControlPhase.tenant_id == tenant_id, ControlPhase.tenant_id == None)
    )

    if filter_by and filter_value:
        if filter_by in ("name", "description"):
            queryset = queryset.filter(
                func.lower(getattr(ControlPhase, filter_by)).contains(filter_value.lower())
            )
    elif q:
        queryset = queryset.filter(
            or_(
                func.lower(ControlPhase.name).contains(func.lower(q)),
                func.lower(ControlPhase.description).contains(func.lower(q)),
            )
        )

    if sort_by:
        queryset = ordering_query(query=queryset, order=sort_by)

    return queryset


def get_control_phase(db: Session, id: int, tenant_id: int):
    return (
        db.query(ControlPhase)
        .filter(or_(ControlPhase.tenant_id == tenant_id, ControlPhase.tenant_id == None))
        .filter(ControlPhase.id == id)
        .first()
    )


def update_control_phase(db: Session, id: int, control_phase: UpdateControlPhase, tenant_id: int):
    existing_control_phase = (
        db.query(ControlPhase)
        .filter(ControlPhase.id == id)
        .filter(ControlPhase.tenant_id == tenant_id)
    )
    if not existing_control_phase.first():
        return False
    existing_control_phase.update(control_phase.dict(exclude_unset=True))
    db.commit()
    return True


def delete_control_phase(db: Session, id: int, tenant_id: int):
    existing_control_phase = (
        db.query(ControlPhase)
        .filter(ControlPhase.id == id)
        .filter(ControlPhase.tenant_id == tenant_id)
    )
    if not existing_control_phase.first():
        return False

    existing_control_phase.delete(synchronize_session=False)
    db.commit()
    return True
