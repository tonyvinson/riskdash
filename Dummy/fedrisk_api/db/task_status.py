from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import TaskStatus
from fedrisk_api.schema.task_status import CreateTaskStatus, UpdateTaskStatus


def create_task_status(db: Session, task_status: CreateTaskStatus, tenant_id: int):
    new_task_status = TaskStatus(**task_status.dict(), tenant_id=tenant_id)
    db.add(new_task_status)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_task_status)
    return new_task_status


def get_all_task_statuses(db: Session, tenant_id: int):
    return db.query(TaskStatus).filter(TaskStatus.tenant_id == tenant_id).all()


def get_task_status(db: Session, id: int):
    return db.query(TaskStatus).filter(TaskStatus.id == id).first()


def get_task_status_by_name(db: Session, name: str):
    return db.query(TaskStatus).filter(TaskStatus.name == name).first()


def update_task_status(db: Session, id: int, task_status: UpdateTaskStatus):
    existing_task_status_query = db.query(TaskStatus).filter(TaskStatus.id == id)
    existing_task_status = existing_task_status_query.first()

    if not existing_task_status:
        return 0

    if existing_task_status.first().name in ["in_progress", "not_started", "complete", "canceled"]:
        return 0

    existing_task_status_query.update(task_status.dict(exclude_unset=True))
    db.commit()
    return 1


def delete_task_status(db: Session, id: int):
    existing_task_status = db.query(TaskStatus).filter(TaskStatus.id == id)
    if not existing_task_status.first():
        return 0

    if existing_task_status.first().name in ["in_progress", "not_started", "complete", "canceled"]:
        return 0

    existing_task_status.delete(synchronize_session=False)
    db.commit()
    return 1
