from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import TaskCategory
from fedrisk_api.schema.task_category import CreateTaskCategory, UpdateTaskCategory


def create_task_category(db: Session, task_category: CreateTaskCategory, tenant_id: int):
    new_task_category = TaskCategory(**task_category.dict(), tenant_id=tenant_id)
    db.add(new_task_category)
    try:
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    db.refresh(new_task_category)
    return new_task_category


def get_all_task_categories(db: Session, tenant_id: int):
    return db.query(TaskCategory).filter(TaskCategory.tenant_id == tenant_id).all()


def get_task_category(db: Session, id: int):
    return db.query(TaskCategory).filter(TaskCategory.id == id).first()


def get_task_category_by_name(db: Session, name: str):
    return db.query(TaskCategory).filter(TaskCategory.name == name).first()


def update_task_category(db: Session, id: int, task_category: UpdateTaskCategory):
    existing_task_category = db.query(TaskCategory).filter(TaskCategory.id == id)
    if not existing_task_category.first():
        return 0
    existing_task_category.update(task_category.dict(exclude_unset=True))
    db.commit()
    return 1


def delete_task_category(db: Session, id: int):
    existing_task_category = db.query(TaskCategory).filter(TaskCategory.id == id)
    if not existing_task_category.first():
        return 0

    existing_task_category.delete(synchronize_session=False)
    db.commit()
    return 1
