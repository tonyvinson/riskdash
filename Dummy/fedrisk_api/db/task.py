import logging
from operator import or_

from sqlalchemy import case, func
from sqlalchemy.orm.session import Session

from sqlalchemy.orm import selectinload

from sqlalchemy.exc import IntegrityError

from collections import Counter

from fedrisk_api.db.enums import TaskCategory, TaskPriority
from fedrisk_api.db.models import (
    CapPoamTask,
    Cost,
    Project,
    ProjectUser,
    Task,
    TaskApprovalWorkflow,
    TaskHistory,
    User,
    WBS,
    Risk,
    AuditTest,
    Document,
    # TaskCategory,
    TaskChild,
    TaskCost,
    TaskAuditTest,
    TaskRisk,
    TaskStatus,
    TaskDocument,
    ProjectControl,
    TaskProjectControl,
    TaskStakeholder,
    Control,
    Keyword,
    KeywordMapping,
    ProjectTaskHistory,
    UserWatching,
    UserNotifications,
    UserNotificationSettings,
    TaskLink,
    TaskResource,
    WorkflowFlowchart,
    WorkflowTaskMapping,
)
from fedrisk_api.schema.task import CreateTask, UpdateTask
from fedrisk_api.utils.utils import filter_by_tenant, ordering_query

# from fedrisk_api.s3 import BUCKET_NAME, S3Service, get_profile_s3_key

from fedrisk_api.utils.email_util import send_watch_email

from fedrisk_api.utils.sms_util import publish_notification

from fedrisk_api.db.util.notifications_utils import (
    # notify_user,
    add_notification,
    manage_notifications,
)

# VALID_STATUS_VALUES = [member.value.lower() for member in TaskStatus]
VALID_PRIORITY_VALUES = [member.value.lower() for member in TaskPriority]
VALID_FEDRISK_OBJECT_TYPES = [member.value.lower() for member in TaskCategory]

LOGGER = logging.getLogger(__name__)


async def add_project_task_history(db, task_id, author_id, message):
    """Adds a history record for project tasks."""
    try:
        history = ProjectTaskHistory(task_id=task_id, author_id=author_id, history=message)
        db.add(history)
        db.commit()
    except IntegrityError as e:
        print(f"IntegrityError occurred: {e}")
        db.rollback()


async def handle_task_associations(db, task, risks, tests, attachments, project_controls):
    """Handles adding risks, tests, attachments, and controls to a task."""
    if risks:
        task.risks = db.query(Risk).filter(Risk.id.in_(risks)).all()
        db.commit()

    if tests:
        task.audit_tests = db.query(AuditTest).filter(AuditTest.id.in_(tests)).all()
        db.commit()

    if attachments:
        task.attachments = db.query(Document).filter(Document.id.in_(attachments)).all()
        db.commit()

    if project_controls:
        task.project_controls = (
            db.query(ProjectControl).filter(ProjectControl.id.in_(project_controls)).all()
        )
        db.commit()


async def handle_task_relations(db, task, children, parents):
    """Handles adding children and parent relationships to a task."""
    if children:
        for child_id in children:
            db.add(TaskChild(parent_task_id=task.id, child_task_id=child_id))
            db.commit()

    if parents:
        for parent_id in parents:
            db.add(TaskChild(parent_task_id=parent_id, child_task_id=task.id))
            db.commit()


async def handle_task_resources(db, task, resources):
    """Adds resources to a task."""
    resource_objs = [TaskResource(user_id=res, task_id=task.id, value=0) for res in resources or []]
    if resource_objs:
        db.bulk_save_objects(resource_objs)
        db.commit()


async def add_keywords(db, keywords, task_id, tenant_id):
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
            if (
                not db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, task_id=task_id)
                .first()
            ):
                db.add(KeywordMapping(keyword_id=keyword.id, task_id=task_id))
    db.commit()


async def remove_old_keywords(db, keywords, task_id):
    """Remove keywords from audit test that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(task_id=task_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = db.query(Keyword).join(KeywordMapping).filter_by(task_id=task_id).all()

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping).filter_by(keyword_id=keyword.id, task_id=task_id).first()
            )
            db.delete(mapping)
    db.commit()


async def send_assignment_notification(db, task, user_id):
    """Sends assignment notification to user based on their settings."""
    user_settings = (
        db.query(UserNotificationSettings)
        .filter(UserNotificationSettings.user_id == task.assigned_to)
        .first()
    )
    assigned_user = db.query(User).filter(User.id == task.assigned_to).first()
    project_link = f"/projects/{task.project_id}/tasks/{task.id}"
    if user_settings and assigned_user:
        if user_settings.assigned_email:
            email_content = {
                "subject": f"You've been assigned to task {task.name} on Fedrisk",
                "email": assigned_user.email,
                "message": f"Task {task.name} assigned to you. Link: {project_link}",
            }
            await send_watch_email(email_content)
        if user_settings.assigned_sms and assigned_user.phone_no:
            sms_content = {
                "phone_no": assigned_user.phone_no,
                "message": f"Task {task.name} assigned to you. Link: {project_link}",
            }
            await publish_notification(sms_content)


async def create_task(db: Session, task: CreateTask, tenant_id: int, keywords: str, user_id: int):
    if task.wbs_id == 0:
        del task.wbs_id
    if task.assigned_to == "":
        del task.assigned_to
    task_dict = task.dict()
    try:
        risks = task_dict.pop("risks")
    except KeyError:
        risks = None
    try:
        children = task_dict.pop("children")
    except KeyError:
        children = None
    try:
        parents = task_dict.pop("parents")
    except KeyError:
        parents = None
    try:
        attachments = task_dict.pop("attachments")
    except KeyError:
        attachments = None
    try:
        tests = task_dict.pop("audit_tests")
    except KeyError:
        tests = None
    try:
        project_controls = task_dict.pop("project_controls")
    except KeyError:
        project_controls = None
    # dhtmlx
    try:
        resources = task_dict.pop("resources")
    except KeyError:
        resources = None
    try:
        resources_value = task_dict.pop("resources_value")
    except KeyError:
        resources_value = None

    try:
        stake_holder_ids = task_dict.pop("additional_stakeholder_ids")
    except KeyError:
        stake_holder_ids = None

    new_task = Task(**task_dict, tenant_id=tenant_id)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    LOGGER.info(new_task)

    if stake_holder_ids:
        task_stakeholders = db.query(User).filter(User.id.in_(stake_holder_ids)).all()
        new_task.additional_stakeholders = task_stakeholders
        # create notifications for stakeholders
        for stakeholder in stake_holder_ids:
            if stakeholder != 0:
                notification = {
                    "user_id": stakeholder,
                    "notification_data_type": "task_stakeholder",
                    "notification_data_id": new_task.id,
                    "notification_data_path": f"/projects/{task.project_id}/tasks/{new_task.id}",
                    "notification_message": f"You've been added as a stakeholder to {new_task.name}",
                    "project_id": task.project_id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
    # Add history
    await add_project_task_history(db, new_task.id, user_id, f"Created new task {new_task.name}")

    # Get all users watching tasks for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_tasks == True)
        .filter(UserWatching.project_id == new_task.project_id)
        .all()
    )
    # project = db.query(Project).filter(Project.id == new_task.project_id).first()
    message = f"Created new task {new_task.name}"
    link = f"/projects/{new_task.project_id}/tasks/{new_task.id}"
    await manage_notifications(
        db, users_watching, "tasks", message, link, new_task.project_id, new_task.id
    )
    if new_task.assigned_to is not None:
        user_message = f"You have been assigned to a new task {new_task.name}"
        # add notification to DB
        await add_notification(
            db, new_task.assigned_to, "tasks", new_task.id, link, user_message, new_task.project_id
        )

    # Handle task associations and resources
    await handle_task_associations(db, new_task, risks, tests, attachments, project_controls)
    await handle_task_relations(db, new_task, children, parents)
    await handle_task_resources(db, new_task, resources)

    # Add keywords to task if present
    if keywords:
        await add_keywords(db, keywords, new_task.id, tenant_id)

    # Send notifications to assigned user
    await send_assignment_notification(db, new_task, user_id)

    return new_task


from sqlalchemy.orm import selectinload
from fedrisk_api.db.models import Task, User, WorkflowTaskMapping, WorkflowFlowchart


def get_task(db: Session, id: int, tenant_id: int, user_id):
    user = db.query(User).filter(User.id == user_id).first()
    queryset = db.query(Task)
    if user.system_role == 4:
        queryset = db.query(Task)
    elif user.is_tenant_admin:
        queryset = filter_by_tenant(db, Task, tenant_id)
    else:
        queryset = (
            filter_by_tenant(db, Task, tenant_id)
            .join(ProjectUser, ProjectUser.project_id == Task.project_id)
            .filter(ProjectUser.user_id == user_id)
        )
    return (
        # queryset.join(
        #     WorkflowTaskMapping, WorkflowTaskMapping.task_id == Task.id
        # ).join(
        #     WorkflowFlowchart, WorkflowFlowchart.id == WorkflowTaskMapping.workflow_flowchart_id
        # )
        # .filter(WorkflowFlowchart.status != "not_started")
        queryset.filter(Task.id == id)
        .options(selectinload(Task.children))
        .first()
    )


def get_all_tasks(
    db: Session,
    tenant_id: int,
    auth_user_id: int,
    project_id: int,
    wbs_id: int,
    user_id: int,
    due_date,
    filter_by: str,
    filter_value: str,
    sort_by: str,
    status: str,
    assigned_to: int,
):
    queryset = filter_by_tenant(db, Task, tenant_id)

    queryset = queryset.join(Project, Project.id == Task.project_id).join(
        User, Task.user_id == User.id
    )

    if project_id:
        queryset = queryset.filter(Project.id == project_id)
    if wbs_id:
        queryset = queryset.filter(Task.wbs_id == wbs_id)
    if user_id:
        queryset = queryset.filter(Task.user_id == user_id)
    if due_date:
        queryset = queryset.filter(Task.due_date == due_date)
    if assigned_to:
        queryset = queryset.filter(Task.assigned_to == assigned_to)

    if filter_by and filter_value:
        if filter_by == "project_name":
            queryset = queryset.filter(func.lower(Project.name).contains(filter_value.lower()))
        elif filter_by in ("name", "title"):
            queryset = queryset.filter(
                func.lower(getattr(Task, filter_by)).contains(filter_value.strip().lower())
            )
        elif filter_by == "owner":
            queryset = queryset.filter(
                func.lower(getattr(User, "email")).contains(filter_value.strip().lower())
            )
        elif filter_by == "status":
            filter_value = "_".join(filter_value.split(" ")).replace("-", "_")
            queryset = queryset.join(TaskStatus).filter(TaskStatus.name == filter_value.lower())
        elif filter_by == "priority":
            if filter_value.lower() in VALID_PRIORITY_VALUES:
                filter_value = "_".join(filter_value.split(" ")).replace("-", "_")
                queryset = queryset.filter(Task.priority == filter_value.lower())
        elif filter_by == "fedrisk_object_type":
            if filter_value.lower() in VALID_FEDRISK_OBJECT_TYPES:
                filter_value = "_".join(filter_value.split(" ")).replace("-", "_")
                queryset = queryset.filter(Task.fedrisk_object_type == filter_value.lower())
        else:
            queryset = queryset.filter(getattr(Task, filter_by) == filter_value)

    if sort_by:
        if "priority" in sort_by:
            order_by_case = case(
                [
                    (Task.priority == "low", 0),
                    (Task.priority == "medium", 1),
                    (Task.priority == "high", 2),
                    (Task.priority == "immediate", 3),
                ]
            )
            if sort_by.startswith("-"):
                queryset = queryset.order_by(order_by_case.desc())
            else:
                queryset = queryset.order_by(order_by_case)
        elif "project_name" in sort_by:
            if sort_by.startswith("-"):
                queryset = queryset.order_by(Project.name.desc())
            else:
                queryset = queryset.order_by(Project.name)
        elif "project_id" in sort_by:
            if sort_by.startswith("-"):
                queryset = queryset.order_by(Project.id.desc())
            else:
                queryset = queryset.order_by(Project.id)
        elif "owner" in sort_by:
            if sort_by.startswith("-"):
                queryset = queryset.order_by(User.email.desc())
            else:
                queryset = queryset.order_by(User.email)
        else:
            queryset = ordering_query(query=queryset, order=sort_by, model=Task.__tablename__)

    # Only filter by workflow status for tasks that are mapped.
    queryset = (
        queryset.outerjoin(WorkflowTaskMapping, WorkflowTaskMapping.task_id == Task.id)
        .outerjoin(
            WorkflowFlowchart, WorkflowFlowchart.id == WorkflowTaskMapping.workflow_flowchart_id
        )
        .filter(or_(WorkflowFlowchart.id == None, WorkflowFlowchart.status != "not_started"))
    )

    return queryset.distinct()


async def update_task(
    db: Session, id: int, task: UpdateTask, tenant_id: int, user_id: int, keywords: str
):
    LOGGER.info("updating task")
    existing_task = filter_by_tenant(db, Task, tenant_id).filter(Task.id == id)
    if not existing_task.first():
        return False
    if task.assigned_to is not None:
        if task.assigned_to.isdigit():
            assigned_to = db.query(User).filter(User.email == task.assigned_to).first()
            if assigned_to is not None:
                task.assigned_to = assigned_to.id
        else:
            assigned_to = db.query(User).filter(User.email == task.assigned_to).first()
            if assigned_to is not None:
                task.assigned_to = assigned_to.id
    if task.wbs_id == 0:
        del task.wbs_id
    if task.assigned_to == "":
        del task.assigned_to

    # Get all users watching tasks for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_tasks == True)
        .filter(UserWatching.project_id == existing_task.first().project_id)
        .all()
    )
    link = f"/projects/{existing_task.first().project_id}/tasks/{existing_task.first().id}"

    # Add notifications and history
    changes = []
    for field in [
        "title",
        "name",
        "description",
        "priority",
        "due_date",
        "task_status_id",
        "task_category_id",
        "wbs_id",
        "actual_start_date",
        "actual_end_date",
        "duration",
        "percent_complete",
        "milestone",
        "assigned_to",
        "estimated_loe",
        "actual_loe",
        "child_task_order",
        "category",
    ]:
        if getattr(task, field, None) is not None:
            if getattr(existing_task.first(), field) != getattr(task, field, None):
                changes.append(f"Updated {field.replace('_', ' ')} to {getattr(task, field, None)}")
    # LOGGER.info(f"changes {changes}")
    all_changes = ".    ".join(changes)
    if all_changes != "":
        await manage_notifications(
            db,
            users_watching,
            "tasks",
            all_changes,
            link,
            existing_task.first().project_id,
            existing_task.first().id,
        )
        for change in changes:
            try:
                db.add(
                    TaskHistory(
                        task_id=existing_task.first().id,
                        updated_by_id=user_id,
                        comments=change + task.comments,
                    )
                )
            except IntegrityError as e:
                print(f"IntegrityError occurred: {e}")
                db.rollback()
    old_status = {"name": None}

    if existing_task.first().task_status_id is not None:
        old_status = (
            db.query(TaskStatus)
            .filter(TaskStatus.id == existing_task.first().task_status_id)
            .first()
        )

    task_update_data = task.dict(exclude_unset=True)
    # update stakeholders
    try:
        stake_holder_ids = task_update_data.pop("additional_stakeholder_ids")
    except KeyError as e:
        stake_holder_ids = None
    if stake_holder_ids:
        task_stakeholders = db.query(User).filter(User.id.in_(stake_holder_ids)).all()
        existing_task.first().additional_stakeholders = task_stakeholders

    comments = (
        task_update_data.pop("comments") if "comments" in task_update_data else "updated task"
    )

    parents = task_update_data.pop("parents") if "parents" in task_update_data else []
    children = task_update_data.pop("children") if "children" in task_update_data else []
    risks = task_update_data.pop("risks") if "risks" in task_update_data else []
    project_controls = (
        task_update_data.pop("project_controls") if "project_controls" in task_update_data else []
    )
    attachments = task_update_data.pop("attachments") if "attachments" in task_update_data else []
    tests = task_update_data.pop("audit_tests") if "audit_tests" in task_update_data else []

    # dhtmlx
    task_link_targets = (
        task_update_data.pop("task_link_targets") if "task_link_targets" in task_update_data else []
    )
    task_link_types = (
        task_update_data.pop("task_link_types") if "task_link_types" in task_update_data else []
    )
    resources = task_update_data.pop("resources") if "resources" in task_update_data else []
    resources_value = (
        task_update_data.pop("resources_value") if "resources_value" in task_update_data else []
    )
    # Update costs
    cost_ids = task_update_data.pop("cost_ids", None)
    if cost_ids is not None or []:
        # add costs
        for cost in cost_ids:
            # check if cost id exists on tenant
            existing_cost = db.query(Cost).filter(Cost.tenant_id == tenant_id).first()
            # if the cost exists
            if existing_cost is not None:
                new_cost_map = TaskCost(task_id=id, cost_id=cost)
                try:
                    db.add(new_cost_map)
                    db.commit()
                except:
                    LOGGER.error("Could not add cost with this ID")

    for parent in parents:
        existing_parent_child = (
            db.query(TaskChild)
            .filter(TaskChild.parent_task_id == existing_task.first().id)
            .filter(TaskChild.parent_task_id == existing_task.first().id)
        )
        existing_parent_child.delete()
        data = {"parent_task_id": parent, "child_task_id": existing_task.first().id}
        new_parent_child = TaskChild(**data)
        db.add(new_parent_child)
        db.commit()

    if tests:
        existing_task.first().audit_tests = (
            db.query(AuditTest).filter(AuditTest.id.in_(tests)).all()
        )
        db.commit()

    if risks:
        existing_task.first().risks = db.query(Risk).filter(Risk.id.in_(risks)).all()
        db.commit()

    if attachments:
        existing_task.first().attachments = (
            db.query(Document).filter(Document.id.in_(attachments)).all()
        )
        db.commit()

    if project_controls:
        existing_task.first().project_controls = (
            db.query(ProjectControl).filter(ProjectControl.id.in_(project_controls)).all()
        )
        db.commit()

    for child in children:
        existing_child_parent = (
            db.query(TaskChild)
            .filter(TaskChild.child_task_id == child)
            .filter(TaskChild.parent_task_id == existing_task.first().id)
        )
        existing_child_parent.delete()
        data = {"parent_task_id": existing_task.first().id, "child_task_id": child}
        new_child_parent = TaskChild(**data)
        db.add(new_child_parent)
        db.commit()

    count = 0
    for target in task_link_targets:
        existing_targets = (
            db.query(TaskLink)
            .filter(TaskLink.source_id == target)
            .filter(TaskLink.target_id == existing_task.first().id)
        )
        if existing_targets.first() is None:
            # add the source and target
            new_task_link_obj = {
                "source_id": target,
                "target_id": existing_task.first().id,
                "type": task_link_types[count],
            }
            new_task_link = TaskLink(**new_task_link_obj)
            db.add(new_task_link)
            db.commit()
            count += 1
    resource_count = 0
    for resource in resources:
        # if resource does not exist insert
        resource_exists = (
            db.query(TaskResource)
            .filter(TaskResource.user_id == resource)
            .filter(TaskResource.task_id == id)
        )
        resource_obj = {
            "user_id": resource,
            "task_id": existing_task.first().id,
            "value": resources_value[resource_count],
        }
        new_res_obj = TaskResource(**resource_obj)
        if resource_exists.first() is None:
            db.add(new_res_obj)
            db.commit()
        # else update
        else:
            resource_exists.update(resource_obj)
            db.commit()
        resource_count += 1
    # get all existing resources
    existing_resources = db.query(TaskResource).filter(TaskResource.task_id == id).all()
    for exist in existing_resources:
        matches = 0
        for res in resources:
            if exist.user_id == res and exist.task_id == id:
                matches += 1
        if matches == 0:
            # delete task resource
            db.delete(exist)

    if task_update_data:
        existing_task.update(task_update_data)
    if existing_task.first().task_status_id is not None:
        new_status = (
            db.query(TaskStatus)
            .filter(TaskStatus.id == existing_task.first().task_status_id)
            .first()
        )
        old_status_name = old_status.name if old_status and hasattr(old_status, "name") else None
        new_status_name = new_status.name if new_status and hasattr(new_status, "name") else None
        if "task_status_id" in task_update_data or comments:
            task_history = TaskHistory(
                task_id=existing_task.first().id,
                old_status=old_status_name,
                new_status=new_status_name,
                updated_by_id=user_id,
                comments=comments,
            )
            db.add(task_history)
            db.commit()
    else:
        task_history = TaskHistory(
            task_id=existing_task.first().id,
            old_status=None,
            new_status=None,
            updated_by_id=user_id,
            comments=comments,
        )
        db.add(task_history)
        db.commit()
    await remove_old_keywords(db, keywords, id)
    await add_keywords(db, keywords, id, tenant_id)

    return existing_task.first()


def get_wbs_dhtmlx_tasks(db: Session, wbs_id: int, tenant_id: int, user_id):
    links = []
    resources = []
    # get project id
    wbs_query = db.query(WBS).filter(WBS.id == wbs_id).first()

    # get resources
    resources_query = (
        db.query(
            User.id.label("id"),
            User.email.label("text"),
        )
        .join(WBS, WBS.id == wbs_query.id)
        .join(Project, Project.id == WBS.project_id)
        .join(ProjectUser, ProjectUser.user_id == User.id)
    )
    if resources_query.first() is not None:
        for resource in resources_query:
            resource_obj = {
                "id": resource.id,
                "text": resource.text,
                # "unit": "hours/day",
                "parent": None,
            }
            resources.append(resource_obj)
    tasks_formatted = []
    # get all tasks
    tasks = (
        db.query(
            Task.actual_start_date.label("start_date"),
            Task.name.label("text"),
            Task.milestone.label("milestone"),
            Task.id.label("id"),
            Task.percent_complete.label("progress"),
            Task.duration.label("duration"),
            Task.project_id.label("project_id"),
        )
        .select_from(Task)
        .filter(Task.wbs_id == wbs_id)
    )
    # if no tasks return empty array
    if tasks.first() is None:
        return [{}]
    else:
        for task in tasks:
            # if tasks have children
            task_w_children = (
                db.query(
                    Task.actual_start_date.label("start_date"),
                    Task.name.label("text"),
                    Task.milestone.label("milestone"),
                    Task.id.label("id"),
                    Task.percent_complete.label("progress"),
                    Task.duration.label("duration"),
                    TaskChild.child_task_id.label("childTaskId"),
                    Task.project_id.label("project_id"),
                )
                .select_from(TaskChild)
                .join(Task, Task.id == TaskChild.parent_task_id)
                .filter(Task.id == task.id)
            )

            if task_w_children.first() is None:
                # check if task has a parent
                task_has_parent = (
                    db.query(
                        Task.actual_start_date.label("start_date"),
                        Task.name.label("text"),
                        Task.milestone.label("milestone"),
                        Task.id.label("id"),
                        Task.percent_complete.label("progress"),
                        Task.duration.label("duration"),
                        TaskChild.child_task_id.label("childTaskId"),
                        Task.project_id.label("project_id"),
                    )
                    .select_from(TaskChild)
                    .join(Task, Task.id == TaskChild.child_task_id)
                    .filter(Task.id == task.id)
                )
                if task_has_parent.first() is None:
                    # get links
                    links_query = (
                        db.query(
                            TaskLink.id.label("id"),
                            TaskLink.source_id.label("source"),
                            TaskLink.target_id.label("target"),
                            TaskLink.type.label("type"),
                        )
                        .filter(TaskLink.target_id == task.id)
                        .all()
                    )
                    owners = []
                    owner_query = db.query(
                        TaskResource.user_id.label("resource_id"), TaskResource.value.label("value")
                    ).filter(TaskResource.task_id == task.id)
                    if owner_query.first() is not None:
                        owners = owner_query.all()

                    date_formatted = "01-01-2024"
                    progress = 0
                    if task.progress is not None:
                        progress = task.progress / 100
                    duration = 1
                    if task.duration is not None:
                        duration = task.duration
                    if task.start_date is not None:
                        date_formatted = task.start_date.strftime("%d-%m-%Y")
                    milestone = False
                    if task.milestone is not None:
                        milestone = task.milestone
                    parent_task_obj = {
                        "id": task.id,
                        "text": task.text,
                        "progress": progress,
                        "start_date": date_formatted,
                        "duration": duration,
                        "owner": owners,
                        "parent": 0,
                    }
                    if links_query != []:
                        for link in links_query:
                            links.append(link)
                    tasks_formatted.append(parent_task_obj)
            if task_w_children.first() is not None:
                # get all the children
                children = []
                child_tasks = (
                    db.query(
                        TaskChild.child_task_id.label("child_task_id"),
                    )
                    .select_from(TaskChild)
                    .filter(TaskChild.parent_task_id == task.id)
                    .all()
                )
                for child in child_tasks:
                    # get links
                    links_query = (
                        db.query(
                            TaskLink.id.label("id"),
                            TaskLink.source_id.label("source"),
                            TaskLink.target_id.label("target"),
                            TaskLink.type.label("type"),
                        )
                        .filter(TaskLink.target_id == child.child_task_id)
                        .all()
                    )
                    if links_query != []:
                        for link in links_query:
                            links.append(link)
                    child_task = (
                        db.query(
                            Task.actual_start_date.label("start_date"),
                            Task.name.label("text"),
                            Task.milestone.label("milestone"),
                            Task.id.label("id"),
                            Task.percent_complete.label("progress"),
                            Task.duration.label("duration"),
                            Task.user_id.label("holder"),
                            Task.child_task_order.label("order"),
                            Task.project_id.label("project_id"),
                        )
                        .select_from(Task)
                        .filter(Task.id == child.child_task_id)
                        .first()
                    )
                    owners = []
                    owner_query = db.query(
                        TaskResource.user_id.label("resource_id"), TaskResource.value.label("value")
                    ).filter(TaskResource.task_id == child_task.id)
                    if owner_query.first() is not None:
                        owners = owner_query.all()
                    progress = 0
                    if child_task.progress is not None:
                        progress = child_task.progress / 100
                    duration = 1
                    if child_task.duration is not None:
                        duration = child_task.duration
                    # format date
                    date_formatted = "01-01-2024"
                    if child_task.start_date is not None:
                        date_formatted = child_task.start_date.strftime("%d-%m-%Y")
                    milestone = False
                    tasktype = "task"
                    if child_task.milestone is not None:
                        milestone = child_task.milestone
                    if milestone == True:
                        tasktype = "milestone"
                    child_task_obj = {
                        "id": child_task.id,
                        "text": child_task.text,
                        "type": tasktype,
                        "duration": duration,
                        "start_date": date_formatted,
                        "progress": progress,
                        "parent": task.id,
                        "owner": owners,
                    }
                    children.append(child_task_obj)
                # add parent and children
                progress = 0
                if task.progress is not None:
                    progress = task.progress / 100
                duration = 1
                if task.duration is not None:
                    duration = task.duration
                owners = []
                owner_query = db.query(
                    TaskResource.user_id.label("resource_id"), TaskResource.value.label("value")
                ).filter(TaskResource.task_id == task.id)
                if owner_query.first() is not None:
                    owners = owner_query.all()
                date_formatted = "01-01-2024"
                if task.start_date is not None:
                    date_formatted = task.start_date.strftime("%d-%m-%Y")
                tasktype = "task"
                milestone = False
                if task.milestone is not None:
                    milestone = task.milestone
                if milestone == True:
                    tasktype = "milestone"
                # add the parent task with children
                parent_task_obj = {
                    "id": task.id,
                    "text": task.text,
                    # "milestone": milestone,
                    "type": tasktype,
                    "progress": progress,
                    "start_date": date_formatted,
                    "duration": duration,
                    "parent": 0,
                    # "open": True,
                    "owner": owners,
                }
                # get links
                links_query = (
                    db.query(
                        TaskLink.id.label("id"),
                        TaskLink.source_id.label("source"),
                        TaskLink.target_id.label("target"),
                        TaskLink.type.label("type"),
                    )
                    .filter(TaskLink.target_id == task.id)
                    .all()
                )
                tasks_formatted.append(parent_task_obj)
                if links_query != []:
                    for link in links_query:
                        links.append(link)
                for c in children:
                    tasks_formatted.append(c)

    tasks_no_dupes = []
    for task in tasks_formatted:
        matched_tasks = []
        matches = 0
        for task_match in tasks_no_dupes:
            if task["id"] == task_match["id"]:
                matches += 1
                matched_tasks.append(task_match)
        if matches == 0:
            tasks_no_dupes.append(task)

    return {"data": tasks_no_dupes, "links": links, "resources": resources}


def get_wbs_child_tasks(db: Session, tasks: list):
    child_tasks = []

    for child in tasks:
        queryset = db.query(TaskChild).filter(TaskChild.parent_task_id == child.child_task_id)

        if queryset.first():
            child_tasks.extend(get_wbs_child_tasks(db, queryset.all()))

        if not queryset.first():
            child_task_query = (
                db.query(
                    Task.id.label("id"),
                    Task.title.label("title"),
                    Task.tenant_id.label("tenant_id"),
                    Task.user_id.label("user"),
                    Task.name.label("name"),
                    Task.description.label("description"),
                    Task.assigned_to.label("assigned"),
                    Task.project_id.label("project_id"),
                    Task.priority.label("priority"),
                    TaskStatus.name.label("status"),
                    Task.percent_complete.label("percent_complete"),
                    Task.due_date.label("due_date"),
                    Task.actual_start_date.label("actual_start_date"),
                    Task.actual_end_date.label("actual_end_date"),
                    Task.child_task_order.label("child_task_order"),
                )
                .join(TaskStatus, Task.task_status_id == TaskStatus.id)
                .filter(Task.id == child.child_task_id)
                .first()
            )

            if child_task_query:
                child_task = {
                    "id": child_task_query.id,
                    "title": child_task_query.title,
                    "tenant_id": child_task_query.tenant_id,
                    "name": child_task_query.name,
                    "description": child_task_query.description,
                    "user": child_task_query.user,
                    "project_id": child_task_query.project_id,
                    "priority": child_task_query.priority,
                    "status": child_task_query.status,
                    "percent_complete": child_task_query.percent_complete,
                    "due_date": child_task_query.due_date,
                    "actual_start_date": child_task_query.actual_start_date,
                    "actual_end_date": child_task_query.actual_end_date,
                    "child_task_order": child_task_query.child_task_order,
                    "parent_task_id": child.parent_task_id,
                    "children": get_wbs_child_tasks(db, queryset.all()),
                }
                child_tasks.append(child_task)

    return child_tasks


def get_wbs_tasks(db: Session, wbs_id: int, tenant_id: int, user_id):
    # get all tasks
    # for each task see if it has children
    # if it does get all the children
    tasksquery = (
        db.query(
            Task.id.label("id"),
            Task.title.label("title"),
            Task.tenant_id.label("tenant_id"),
            Task.name.label("name"),
            Task.user_id.label("user"),
            Task.description.label("description"),
            Task.assigned_to.label("assigned"),  # might have to join these in below
            Task.project_id.label("project_id"),  # ditto
            Task.priority.label("priority"),
            TaskStatus.name.label("status"),
            Task.percent_complete.label("percent_complete"),
            Task.due_date.label("due_date"),
            Task.actual_start_date.label("actual_start_date"),
            Task.actual_end_date.label("actual_end_date"),
            Task.child_task_order.label("child_task_order"),
        )
        .select_from(Task, TaskStatus)
        .join(Task, Task.task_status_id == TaskStatus.id)
        .filter(Task.wbs_id == wbs_id)
        .order_by(Task.child_task_order.asc())
    )

    LOGGER.info(tasksquery.all())

    if not tasksquery.first():
        return []
    tasks = tasksquery.all()
    tree_data = []
    task_tree = {
        "id": "",
        "title": "",
        "tenant_id": "",
        "name": "",
        "description": "",
        "user": "",
        "project_id": "",
        "priority": "",
        "status": "",
        "percent_complete": "",
        "due_date": "",
        "actual_start_date": "",
        "actual_end_date": "",
        "child_task_order": "",
        "children": [],
        "project": [],
        "risks": [],
        "audit_tests": [],
        "project_controls": [],
        # "task_history": [],
        "assigned": [],
        "assigned_pic": [],
        "parent_task_id": 0,
    }

    all_children = []

    # iterate through tasks
    for task in tasks:

        task_tree["id"] = task.id
        task_tree["title"] = task.title
        task_tree["tenant_id"] = task.tenant_id
        task_tree["name"] = task.name
        task_tree["user"] = task.user
        task_tree["description"] = task.description
        task_tree["assigned"] = task.assigned
        task_tree["project_id"] = task.project_id
        task_tree["priority"] = task.priority
        task_tree["status"] = task.status
        task_tree["percent_complete"] = task.percent_complete
        task_tree["due_date"] = task.due_date
        task_tree["actual_start_date"] = task.actual_start_date
        task_tree["actual_end_date"] = task.actual_end_date
        task_tree["child_task_order"] = task.child_task_order

        project_query = db.query(Project).filter(Project.id == task.project_id).first()
        risk_query = (
            db.query(TaskRisk, Risk)
            .join(Risk, TaskRisk.risk_id == Risk.id)
            .filter(TaskRisk.task_id == task.id)
            .all()
        )
        audit_test_query = (
            db.query(TaskAuditTest, AuditTest)
            .join(AuditTest, TaskAuditTest.audit_test_id == AuditTest.id)
            .filter(TaskAuditTest.task_id == task.id)
            .all()
        )
        project_control_query = (
            db.query(TaskProjectControl, ProjectControl, Control)
            .join(ProjectControl, TaskProjectControl.project_control_id == ProjectControl.id)
            .join(Control, Control.id == ProjectControl.control_id)
            .filter(TaskProjectControl.task_id == task.id)
            .all()
        )
        # history_query = db.query(TaskHistory).filter(TaskHistory.task_id == task.id).all()
        user_query = (
            db.query(
                User.id.label("id"),
                User.email.label("email"),
                User.first_name.label("first_name"),
                User.last_name.label("last_name"),
                User.profile_picture.label("profile_picture"),
            )
            .select_from(User)
            .filter(User.id == task.assigned)
            .first()
        )
        # LOGGER.info(f"user_query {user_query.first()}")
        # get s3 url for profile image
        # expire_time = 86400
        # s3_service = S3Service()
        profile_pic_assigned_to = ""
        # if not user_query.profile_picture:
        #     LOGGER.info("No profile picture")
        # else:
        #     profile_pic_assigned_to = s3_service.get_profile_picture_image_url(
        #         user_query.profile_picture, expire_time
        #     )

        task_tree["project"] = project_query
        task_tree["risks"] = risk_query
        task_tree["audit_tests"] = audit_test_query
        task_tree["project_controls"] = project_control_query
        # task_tree["task_history"] = history_query
        if user_query is not None:
            task_tree["assigned"] = user_query.email
        task_tree["assigned_pic"] = profile_pic_assigned_to

        # see if task has parent
        parentquery = db.query(TaskChild).filter(TaskChild.child_task_id == task.id)
        if parentquery.first():
            task_tree["parent_task_id"] = parentquery.first().parent_task_id
        if parentquery.first is None:
            task_tree["parent_task_id"] = task.id

        # child tasks

        queryset = db.query(TaskChild).filter(TaskChild.parent_task_id == task.id)

        child_tasks = []
        # if there are child tasks
        if queryset.all():
            child_tasks = get_wbs_child_tasks(db, queryset.all())
            for ct in child_tasks:
                all_children.append(ct)
            task_tree["children"] = child_tasks

        tree_data.append(task_tree)
        task_tree = {
            "id": "",
            "title": "",
            "name": "",
            "tenant_id": "",
            "description": "",
            "user": "",
            "project_id": "",
            "priority": "",
            "status": "",
            "percent_complete": "",
            "due_date": "",
            "actual_start_date": "",
            "actual_end_date": "",
            "child_task_order": "",
            "children": [],
            "project": [],
            "risks": [],
            "audit_tests": [],
            "project_controls": [],
            # "task_history": [],
            "assigned": [],
            "assigned_pic": [],
        }
        queryset = []
    # remove tasks if they match a child
    for c in all_children:
        for t in tree_data:
            if t["id"] == c["id"]:
                tree_data.remove(t)

    return tree_data


def get_tasks_wbs_chart_data(db: Session, project_id: int, tenant_id: int, user_id, wbs_id: int):
    # Query tasks based on WBS ID or Project ID
    base_query = db.query(
        TaskStatus.name.label("status"),
        Task.due_date,
        Task.actual_start_date,
        Task.actual_end_date,
    ).join(TaskStatus, Task.task_status_id == TaskStatus.id)

    tasks = (
        base_query.filter(Task.wbs_id == wbs_id).all()
        if wbs_id
        else base_query.filter(Task.project_id == project_id).all()
    )

    # Use Counter for efficient counting
    status_counter = Counter(task.status for task in tasks)

    completed = status_counter["Complete"]
    overdue = 0
    on_schedule = 0
    late = 0
    early = 0

    for task in tasks:
        if task.due_date and task.actual_start_date and task.actual_end_date:
            days_between_ends = (task.due_date - task.actual_end_date).days
            days_between_start_end = (task.due_date - task.actual_start_date).days

            late += days_between_ends <= 0
            early += days_between_ends > 0
            overdue += days_between_start_end <= 0
            on_schedule += days_between_start_end > 0

    return {
        "completed": completed,
        "overdue": overdue,
        "on_schedule": on_schedule,
        "late": late,
        "early": early,
    }


async def get_tasks_by_dates(
    db: Session, start_date: str, end_date: str, wbs_id: str, tenant_id: int, user_id: int
):
    tasksquery = db.query(Task).filter(Task.tenant_id == tenant_id)

    if start_date is not None:
        tasksquery = tasksquery.filter(Task.due_date >= start_date)

    if end_date is not None:
        tasksquery = tasksquery.filter(Task.due_date <= end_date)

    if wbs_id is not None:
        tasksquery = tasksquery.filter(Task.wbs_id == wbs_id)
    return tasksquery.all()


async def delete_task(db: Session, id: int):
    # delete all history references
    db.query(ProjectTaskHistory).filter(ProjectTaskHistory.task_id == id).delete()
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.task_id == id).delete()
    # delete all document references
    db.query(TaskDocument).filter(TaskDocument.task_id == id).delete()
    # delete all task link references
    db.query(TaskLink).filter(TaskLink.source_id == id).delete()
    db.query(TaskLink).filter(TaskLink.target_id == id).delete()
    # delete all task resources
    db.query(TaskResource).filter(TaskResource.task_id == id).delete()
    # delete all task costs
    db.query(TaskCost).filter(TaskCost.task_id == id).delete()
    # delete all cap poam links
    db.query(CapPoamTask).filter(CapPoamTask.task_id == id).delete()
    # delete all workflow flowchart mappings
    db.query(WorkflowTaskMapping).filter(WorkflowTaskMapping.task_id == id).delete()
    # delete all approval workflow references
    db.query(TaskApprovalWorkflow).filter(TaskApprovalWorkflow.task_id == id).delete()
    # delete task history
    task_history = db.query(TaskHistory).filter(TaskHistory.task_id == id).all()
    for history in task_history:
        db.query(TaskHistory).filter(TaskHistory.task_id == history.task_id).delete()
    # delete task audit test association
    task_audit_tests = db.query(TaskAuditTest).filter(TaskAuditTest.task_id == id).all()
    for test in task_audit_tests:
        db.query(TaskAuditTest).filter(TaskAuditTest.task_id == test.task_id).delete()
    # delete task parent association
    task_parents = db.query(TaskChild).filter(TaskChild.parent_task_id == id).all()
    for parent in task_parents:
        db.query(TaskChild).filter(TaskChild.parent_task_id == parent.parent_task_id).delete()
    # delete task child association
    task_children = db.query(TaskChild).filter(TaskChild.child_task_id == id).all()
    for child in task_children:
        db.query(TaskChild).filter(TaskChild.child_task_id == child.child_task_id).delete()
    # delete task document association
    task_documents = db.query(TaskDocument).filter(TaskDocument.task_id == id).all()
    for doc in task_documents:
        db.query(TaskDocument).filter(TaskDocument.task_id == doc.task_id).delete()
    # delete task project control association
    task_project_controls = (
        db.query(TaskProjectControl).filter(TaskProjectControl.task_id == id).all()
    )
    for control in task_project_controls:
        db.query(TaskProjectControl).filter(TaskProjectControl.task_id == control.task_id).delete()
    # delete task risk association
    task_risks = db.query(TaskRisk).filter(TaskRisk.task_id == id).all()
    for risk in task_risks:
        db.query(TaskRisk).filter(TaskRisk.task_id == risk.task_id).delete()
    # delete task additional stakeholders
    additional_stakeholders = db.query(TaskStakeholder).filter(TaskStakeholder.task_id == id)
    additional_stakeholders.delete(synchronize_session=False)
    # delete task
    existing_task = db.query(Task).filter(Task.id == id)
    if not existing_task.first():
        return False
    # Get all users watching tasks for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_tasks == True)
        .filter(UserWatching.project_id == existing_task.first().project_id)
        .all()
    )
    message = f"Deleted task {existing_task.first().name}"
    link = f"/projects/{existing_task.first().project_id}/tasks/{existing_task.first().id}"
    await manage_notifications(
        db,
        users_watching,
        "tasks",
        message,
        link,
        existing_task.first().project_id,
        existing_task.first().id,
    )
    existing_task.delete()

    db.commit()
    return True
