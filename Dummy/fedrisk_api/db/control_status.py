from sqlalchemy.orm.session import Session

from sqlalchemy import func, or_

from fedrisk_api.db.models import ControlStatus
from fedrisk_api.schema.control_status import CreateControlStatus, UpdateControlStatus

from fedrisk_api.utils.utils import ordering_query


def create_control_status(db: Session, control_status: CreateControlStatus):
    new_control_status = ControlStatus(**control_status.dict())
    db.add(new_control_status)
    db.commit()
    db.refresh(new_control_status)
    return new_control_status


def get_all_control_statuses(
    q: str,
    db: Session,
    tenant_id: int,
    # filter_by: str,
    # filter_value: str,
    sort_by: str,
):
    queryset = db.query(ControlStatus).filter(
        or_(ControlStatus.tenant_id == tenant_id, ControlStatus.tenant_id == None)
    )

    # if filter_by and filter_value:
    #     if filter_by in ("name", "description"):
    #         queryset = queryset.filter(
    #             func.lower(getattr(ControlStatus, filter_by)).contains(filter_value.lower())
    #         )
    if q:
        queryset = queryset.filter(
            or_(
                func.lower(ControlStatus.name).contains(func.lower(q)),
                func.lower(ControlStatus.description).contains(func.lower(q)),
            )
        )

    if sort_by:
        queryset = ordering_query(query=queryset, order=sort_by)

    return queryset


def get_control_status(db: Session, id: int):
    return db.query(ControlStatus).filter(ControlStatus.id == id).first()


def update_control_status(db: Session, id: int, control_status: UpdateControlStatus):
    existing_control_status = db.query(ControlStatus).filter(ControlStatus.id == id)
    if not existing_control_status.first():
        return False
    existing_control_status.update(control_status.dict(exclude_unset=True))
    db.commit()
    return True


def delete_control_status(db: Session, id: int):
    existing_control_status = db.query(ControlStatus).filter(ControlStatus.id == id)
    if not existing_control_status.first():
        return False

    existing_control_status.delete(synchronize_session=False)
    db.commit()
    return True
