import logging
import re
import pandas as pd
from sqlalchemy.exc import IntegrityError
from fedrisk_api.db import task as db_task
from fedrisk_api.db.database import get_db
from fedrisk_api.schema import task as schema_task
from fedrisk_api.db.models import User

LOGGER = logging.getLogger(__name__)

BAD_CHARS_TEXT = "!*&%^$#@{}+=<>"
ALLOWED_PRIORITIES = {"low", "medium", "high", "immediate"}


def clean_date(value):
    """Convert NaT values to None for database compatibility."""
    return None if pd.isna(value) else value


def sanitize_text(text):
    """Removes unwanted characters from text and handles None values safely."""
    if not isinstance(text, str):
        return ""
    return "".join(c for c in text if c not in BAD_CHARS_TEXT).strip()


def is_valid_email(email):
    """Validates email format."""
    return bool(re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email))


def truncate_text(value, max_length=30):
    """Ensures text does not exceed database column limits."""
    return value[:max_length] if isinstance(value, str) else value


async def get_user_id(db, value):
    """Retrieves user ID by email or name."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if is_valid_email(value):
        owner = db.query(User).filter(User.email == value).first()
    else:
        words = sanitize_text(value).split()
        if len(words) < 2:
            return None
        first_name, last_name = words[0], words[-1]
        owner = (
            db.query(User)
            .filter(User.first_name == first_name, User.last_name == last_name)
            .first()
        )
    return owner.id if owner else None


async def create_task(
    db,
    name,
    start_date,
    end_date,
    owner_id,
    is_superuser,
    tenant_id,
    project_id,
    wbs_id,
    import_id,
    priority,
):
    """Creates and returns a new task if it does not already exist."""
    existing_task = (
        db.query(db_task.Task)
        .filter_by(name=name.strip(), project_id=project_id, import_id=import_id)
        .first()
    )
    if existing_task:
        LOGGER.info(f"⚠️ Task '{name}' already exists. Skipping creation.")
        return existing_task
    new_task = schema_task.CreateTask(
        title=truncate_text(name, 30),
        name=truncate_text(name, 30),
        description=truncate_text(name, 100),
        actual_start_date=start_date,
        actual_end_date=end_date,
        due_date=end_date,
        owner=owner_id,
        user_id=owner_id,
        is_preloaded=True,
        is_global=is_superuser,
        project_id=project_id,
        wbs_id=wbs_id,
        import_id=import_id,
        priority=priority if priority in ALLOWED_PRIORITIES else "low",
    )
    return await db_task.create_task(
        db, new_task, tenant_id=tenant_id, keywords="import", user_id=owner_id
    )


async def update_task(
    db, id, tenant_id, task_link_targets, task_link_types, children, parents, owner_id
):
    """Updates and returns a task safely handling None values."""
    update_task_obj = schema_task.UpdateTask(
        task_link_targets=task_link_targets or [],
        task_link_types=task_link_types or [],
        children=children or [],
        parents=parents or [],
    )
    return await db_task.update_task(
        db=db, id=id, task=update_task_obj, tenant_id=tenant_id, keywords="import", user_id=owner_id
    )


async def load_data_from_dataframe_tasks(
    my_data_frame, tenant_id, is_superuser, user_id, project_id, wbs_id, import_id
):
    """Processes a DataFrame and loads tasks, links, and resources into the database."""
    try:
        db = next(get_db())
    except Exception as e:
        LOGGER.error(f"Database session error: {e}")
        return {"error": "Could not initialize database session"}
    num_tasks = 0
    parent_task_map = {}
    my_data_frame.sort_values(by=["Parent Task"], inplace=True, na_position="last")
    try:
        for _, row in my_data_frame.iterrows():
            task_name = sanitize_text(row.get("Task Name", ""))
            if not task_name:
                continue
            task_start_date, task_end_date = clean_date(row.get("Start Date")), clean_date(
                row.get("End Date")
            )
            if not task_start_date or not task_end_date:
                LOGGER.warning(f"Skipping task '{task_name}' due to missing start/end date.")
                continue
            task_owner = await get_user_id(db, row.get("Owner", "")) or user_id
            task_priority = sanitize_text(row.get("Priority", "low"))
            priority = task_priority if task_priority in ALLOWED_PRIORITIES else "low"
            new_task = await create_task(
                db,
                task_name,
                task_start_date,
                task_end_date,
                task_owner,
                is_superuser,
                tenant_id,
                project_id,
                wbs_id,
                import_id,
                priority,
            )
            db.commit()
            parent_task_map[task_name] = new_task.id
            num_tasks += 1
        LOGGER.debug(f"Task Map: {parent_task_map}")
        for _, row in my_data_frame.iterrows():
            task_name, parent_name = sanitize_text(row.get("Task Name", "")), sanitize_text(
                row.get("Parent Task", "")
            )
            if parent_name and task_name in parent_task_map and parent_name in parent_task_map:
                child_id, parent_id = parent_task_map[task_name], parent_task_map[parent_name]
                await update_task(db, child_id, tenant_id, None, None, None, [parent_id], user_id)
                await update_task(
                    db,
                    parent_id,
                    tenant_id,
                    [child_id],
                    ["finish_to_start"],
                    [child_id],
                    None,
                    user_id,
                )
    except IntegrityError as e:
        db.rollback()
        LOGGER.error(f"Database Integrity Error: {e}")
        return {"error": "Database Integrity Error - Possible duplicate entry"}
    except Exception as e:
        db.rollback()
        LOGGER.exception("Unexpected error occurred while processing the spreadsheet")
        return {"error": f"Unexpected error: {str(e)}"}
    return [num_tasks]
