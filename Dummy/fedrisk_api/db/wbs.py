import logging
from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import (
    Cost,
    WBSCost,
    WBS,
    WBSDocument,
    Keyword,
    KeywordMapping,
    Task,
    TaskHistory,
    TaskChild,
    TaskProjectControl,
    TaskDocument,
    WBSApprovalWorkflow,
    WBSHistory,
    UserWatching,
)
from fedrisk_api.schema.wbs import CreateWBS, UpdateWBS

from fedrisk_api.db.util.notifications_utils import (
    # notify_user,
    # add_notification,
    manage_notifications,
)

LOGGER = logging.getLogger(__name__)

# Keyword Management Functions
async def add_keywords(db, keywords, wbs_id, tenant_id):
    """Link keywords to audit test."""
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
            if not db.query(KeywordMapping).filter_by(keyword_id=keyword.id, wbs_id=wbs_id).first():
                db.add(KeywordMapping(keyword_id=keyword.id, wbs_id=wbs_id))
    db.commit()


async def remove_old_keywords(db, keywords, wbs_id):
    """Remove keywords from audit test that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(wbs_id=wbs_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = db.query(Keyword).join(KeywordMapping).filter_by(wbs_id=wbs_id).all()

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping).filter_by(keyword_id=keyword.id, wbs_id=wbs_id).first()
            )
            db.delete(mapping)
    db.commit()


async def create_wbs(db: Session, wbs: CreateWBS, keywords: str, tenant_id: int, user_id: int):
    new_wbs = WBS(**wbs.dict())
    db.add(new_wbs)
    db.commit()
    db.refresh(new_wbs)
    # Add history
    history = {
        "wbs_id": new_wbs.id,
        "author_id": user_id,
        "history": f"Created new wbs {new_wbs.name}",
    }
    new_history = WBSHistory(**history)
    db.add(new_history)
    db.commit()
    # Get all users watching wbs for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_wbs == True)
        .filter(UserWatching.project_id == new_wbs.project_id)
        .all()
    )
    message = f"Created new wbs {new_wbs.name}"
    link = f"/projects/{new_wbs.project_id}/wbsstudio/{new_wbs.id}"
    await manage_notifications(
        db, users_watching, "wbs", message, link, new_wbs.project_id, new_wbs.id
    )
    # add keywords
    await add_keywords(db, keywords, new_wbs.id, tenant_id)
    return new_wbs


def get_all_project_wbs(
    db: Session,
    project_id: int,
):
    project_wbs = db.query(WBS).filter(WBS.project_id == project_id).all()

    return project_wbs


def get_wbs(
    db: Session,
    id: int,
):
    wbs = db.query(WBS).filter(WBS.id == id).first()
    if not wbs:
        return False
    return wbs


async def update_wbs(
    db: Session,
    id: int,
    wbs: UpdateWBS,
    tenant_id: int,
    keywords: str,
    user_id: int,
):

    existing_wbs = db.query(WBS).filter(WBS.id == id)

    if not existing_wbs.first():
        return False
    # Get all users watching wbs for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_wbs == True)
        .filter(UserWatching.project_id == existing_wbs.first().project_id)
        .all()
    )
    link = f"/projects/{existing_wbs.first().project_id}/wbsstudio/{existing_wbs.first().id}"

    # get all changes
    changes = []
    for field in [
        "name",
        "description",
        "project_id",
        "user_id",
    ]:
        if getattr(wbs, field, None) is not None:
            if getattr(existing_wbs.first(), field) != getattr(wbs, field, None):
                changes.append(f"Updated {field.replace('_', ' ')} to {getattr(wbs, field, None)}")
    all_changes = ".    ".join(changes)
    if all_changes != "":
        await manage_notifications(
            db,
            users_watching,
            "wbs",
            all_changes,
            link,
            existing_wbs.first().project_id,
            existing_wbs.first().id,
        )
        # Add history
        for change in changes:
            db.add(WBSHistory(wbs_id=existing_wbs.first().id, author_id=user_id, history=change))
    wbs_dict = wbs.dict(exclude_unset=True)
    # Update costs
    cost_ids = wbs_dict.pop("cost_ids", None)
    if cost_ids is not None or []:
        # add costs
        for cost in cost_ids:
            # check if cost id exists on tenant
            existing_cost = db.query(Cost).filter(Cost.tenant_id == tenant_id).first()
            # if the cost exists
            if existing_cost is not None:
                new_cost_map = WBSCost(wbs_id=id, cost_id=cost)
                try:
                    db.add(new_cost_map)
                    db.commit()
                except:
                    LOGGER.error("Could not add cost with this ID")
    existing_wbs.update(wbs_dict)
    db.commit()
    db.flush()
    # remove keywords not included
    await remove_old_keywords(db, keywords, id)
    await add_keywords(db, keywords, id, tenant_id)
    updated_wbs = db.query(WBS).filter(WBS.id == id).first()
    return updated_wbs


async def delete_wbs(db: Session, id: int):
    # delete all history references
    db.query(WBSHistory).filter(WBSHistory.wbs_id == id).delete()
    existing_wbs = db.query(WBS).filter(WBS.id == id)
    if not existing_wbs.first():
        return False
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.wbs_id == id).delete()
    # delete all document references
    db.query(WBSDocument).filter(WBSDocument.wbs_id == id).delete()
    # delete all cost references
    db.query(WBSCost).filter(WBSCost.wbs_id == id).delete()
    # delete all approval workflow references
    db.query(WBSApprovalWorkflow).filter(WBSApprovalWorkflow.wbs_id == id).delete()
    tasks = db.query(Task).filter(Task.wbs_id == id).all()
    for task in tasks:
        # delete all task history
        db.query(TaskHistory).filter(TaskHistory.task_id == task.id).delete()
        # delete all task children
        db.query(TaskChild).filter(TaskChild.child_task_id == task.id).delete()
        # delete all task project control refs
        db.query(TaskProjectControl).filter(TaskProjectControl.task_id == task.id).delete()
        # delete all document references
        db.query(TaskDocument).filter(TaskDocument.task_id == task.id).delete()
    # delete all task references
    db.query(Task).filter(Task.wbs_id == id).delete()
    # Get all users watching wbs for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_wbs == True)
        .filter(UserWatching.project_id == existing_wbs.first().project_id)
        .all()
    )
    message = f"Deleted {existing_wbs.first().name}"
    link = f"/projects/{existing_wbs.first().project_id}/wbsstudio/{existing_wbs.first().id}"
    await manage_notifications(
        db,
        users_watching,
        "wbs",
        message,
        link,
        existing_wbs.first().project_id,
        existing_wbs.first().id,
    )
    existing_wbs.delete(synchronize_session=False)
    # db.delete(existing_wbs)
    db.commit()
    return True
