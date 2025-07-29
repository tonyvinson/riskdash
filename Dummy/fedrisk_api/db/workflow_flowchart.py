import logging

from sqlalchemy.orm import Session

from typing import List

from fedrisk_api.db.models import (
    WorkflowFlowchart,
    Cost,
    WorkflowFlowchartApprovalWorkflow,
    WorkflowFlowchartCost,
    WorkflowFlowchartHistory,
    WorkflowEvent,
    WorkflowTaskMapping,
    WorkflowTemplate,
    WorkflowTemplateEvent,
    UserWatching,
)

from fedrisk_api.schema.task import (
    CreateTask,
)


from fedrisk_api.schema.workflow_flowchart import (
    CreateWorkflowFlowchart,
    UpdateWorkflowFlowchart,
    CreateWorkflowProjectTemplate,
)

from fedrisk_api.db.util.notifications_utils import (
    # notify_user,
    # add_notification,
    manage_notifications,
)

from fedrisk_api.db import task as db_task

from datetime import datetime, timedelta

from fedrisk_api.db.util.add_workflow_task_assoc_utils import (
    create_task_workflow_assoc_for_workflow,
)

LOGGER = logging.getLogger(__name__)

# workflow_flowchart
async def create_workflow_flowchart(
    db: Session, workflow_flowchart: CreateWorkflowFlowchart, user_id: int
):
    my_new_workflow_flowchart_dict = workflow_flowchart.dict()
    new_workflow_flowchart = WorkflowFlowchart(**my_new_workflow_flowchart_dict)
    db.add(new_workflow_flowchart)
    db.commit()
    await create_task_workflow_assoc_for_workflow(db, new_workflow_flowchart.id)
    # db.refresh()
    # Add history
    history = {
        "workflow_flowchart_id": new_workflow_flowchart.id,
        "author_id": user_id,
        "history": f"Created new workflow flowchart {new_workflow_flowchart.name}",
    }
    new_history = WorkflowFlowchartHistory(**history)
    db.add(new_history)
    db.commit()
    # Get all users watching wbs for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_workflow_flowcharts == True)
        .filter(UserWatching.project_id == new_workflow_flowchart.project_id)
        .all()
    )
    message = f"Created new workflow flowchart {new_workflow_flowchart.name}"
    link = f"/projects/{new_workflow_flowchart.project_id}/workflows/{new_workflow_flowchart.id}"
    await manage_notifications(
        db,
        users_watching,
        "workflow_flowchart",
        message,
        link,
        new_workflow_flowchart.project_id,
        new_workflow_flowchart.id,
    )
    return new_workflow_flowchart


def get_all_workflow_flowcharts_by_project_id(
    db: Session,
    project_id: int,
):
    queryset = db.query(WorkflowFlowchart).filter(WorkflowFlowchart.project_id == project_id).all()
    return queryset


def get_workflow_flowchart_by_id(db: Session, workflow_flowchart_id: int):
    queryset = (
        db.query(WorkflowFlowchart).filter(WorkflowFlowchart.id == workflow_flowchart_id).first()
    )
    return queryset


async def update_workflow_flowchart_by_id(
    workflow_flowchart: UpdateWorkflowFlowchart,
    db: Session,
    workflow_flowchart_id: int,
    tenant_id: int,
    user_id: int,
):
    queryset = db.query(WorkflowFlowchart).filter(WorkflowFlowchart.id == workflow_flowchart_id)

    if not queryset.first():
        return False

    await create_task_workflow_assoc_for_workflow(db, workflow_flowchart_id)

    work_flow_dict = workflow_flowchart.dict(exclude_unset=True)
    # Update costs
    cost_ids = work_flow_dict.pop("cost_ids", None)
    if cost_ids is not None or []:
        # add costs
        for cost in cost_ids:
            # check if cost id exists on tenant
            existing_cost = db.query(Cost).filter(Cost.tenant_id == tenant_id).first()
            # if the cost exists
            if existing_cost is not None:
                new_cost_map = WorkflowFlowchartCost(
                    workflow_flowchart_id=workflow_flowchart_id, cost_id=cost
                )
                try:
                    db.add(new_cost_map)
                    db.commit()
                except:
                    LOGGER.error("Could not add cost with this ID")
    # get all changes
    # Get all users watching wbs for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_workflow_flowcharts == True)
        .filter(UserWatching.project_id == queryset.first().project_id)
        .all()
    )
    link = f"/projects/{queryset.first().project_id}/workflows/{queryset.first().id}"
    changes = []
    for field in [
        "name",
        "start_date",
        "end_date",
        "project_id",
        "status",
    ]:
        if getattr(workflow_flowchart, field, None) is not None:
            if getattr(queryset.first(), field) != getattr(workflow_flowchart, field, None):
                changes.append(
                    f"Updated {field.replace('_', ' ')} to {getattr(workflow_flowchart, field, None)}"
                )
    all_changes = ".    ".join(changes)
    if all_changes != "":
        await manage_notifications(
            db,
            users_watching,
            "workflow_flowcharts",
            all_changes,
            link,
            queryset.first().project_id,
            queryset.first().id,
        )
        # Add history
        for change in changes:
            db.add(
                WorkflowFlowchartHistory(
                    workflow_flowchart_id=queryset.first().id, author_id=user_id, history=change
                )
            )
    queryset.update(work_flow_dict)
    db.commit()
    return True


def delete_workflow_flowchart_by_id(db: Session, workflow_flowchart_id: int):
    workflow_flowchart = (
        db.query(WorkflowFlowchart).filter(WorkflowFlowchart.id == workflow_flowchart_id).first()
    )

    if not workflow_flowchart:
        return False
    # delete all cost references
    db.query(WorkflowFlowchartCost).filter(
        WorkflowFlowchartCost.workflow_flowchart_id == workflow_flowchart_id
    ).delete()
    # delete all history references
    db.query(WorkflowFlowchartHistory).filter(
        WorkflowFlowchartHistory.workflow_flowchart_id == workflow_flowchart_id
    ).delete()
    # delete all WorkflowTaskMapping references
    db.query(WorkflowTaskMapping).filter(
        WorkflowTaskMapping.workflow_flowchart_id == workflow_flowchart_id
    ).delete()
    # delete all approval workflow references
    db.query(WorkflowFlowchartApprovalWorkflow).filter(
        WorkflowFlowchartApprovalWorkflow.workflow_flowchart_id == workflow_flowchart_id
    ).delete()
    db.delete(workflow_flowchart)
    db.commit()
    return True


async def create_workflow_flowchart_for_project_from_template(
    workflow_flowchart: CreateWorkflowProjectTemplate, db: Session, user_id: int, tenant_id: int
):
    # Get the workflow template from the database
    workflow_template = (
        db.query(WorkflowTemplate)
        .filter(WorkflowTemplate.id == workflow_flowchart.template_id)
        .first()
    )
    if workflow_template is None:
        return 0

    nodes = workflow_template.node_data
    links = workflow_template.link_data

    workflow_node_data = []
    key_mapping = {}  # Mapping from original template node key to new node key
    mappings = []

    # Process nodes and create tasks where necessary
    for node in nodes:
        if node["category"] == "Start":

            start_node = {
                "key": "start",
                "category": "Start",
                "loc": node["loc"],
                "text": node["text"],
            }
            workflow_node_data.append(start_node)
            key_mapping[node["key"]] = "start"
            # mappings.append({"old_key": node["key"], "new_key": node["key"]})

        elif node["category"] == "End":

            end_node = {"key": "end", "category": "End", "loc": node["loc"], "text": node["text"]}
            workflow_node_data.append(end_node)
            key_mapping[node["key"]] = "end"
            # mappings.append({"old_key": node["key"], "new_key": node["key"]})

        elif node["category"] == "Parent":
            new_task_obj = CreateTask(
                title=node["text"],
                name=node["text"],
                user_id=user_id,
                tenant_id=tenant_id,
                project_id=workflow_flowchart.project_id,
            )
            new_task = await db_task.create_task(db, new_task_obj, tenant_id, None, user_id)

            parent_node = {
                "key": new_task.id,  # New task id replaces the template key
                "category": "Parent",
                "loc": node["loc"],
                "text": node["text"],
            }
            workflow_node_data.append(parent_node)
            key_mapping[node["key"]] = new_task.id
            mappings.append({"old_key": node["key"], "new_key": new_task.id})

        elif node["category"] == "Child":

            new_task_obj = CreateTask(
                title=node["text"],
                name=node["text"],
                user_id=user_id,
                tenant_id=tenant_id,
                project_id=workflow_flowchart.project_id,
            )
            new_task = await db_task.create_task(db, new_task_obj, tenant_id, None, user_id)

            child_node = {
                "key": new_task.id,
                "category": "Child",
                "loc": node["loc"],
                "text": node["text"],
            }
            workflow_node_data.append(child_node)
            key_mapping[node["key"]] = new_task.id
            mappings.append({"old_key": node["key"], "new_key": new_task.id})

    # Now update links based on the new node keys
    workflow_link_data = []
    for link in links:
        new_from = key_mapping.get(link["from"], link["from"])
        new_to = key_mapping.get(link["to"], link["to"])
        new_link = {"from": new_from, "to": new_to, "key": link["key"]}
        if "text" in link:
            new_link["text"] = link["text"]
        workflow_link_data.append(new_link)

    # Calculate start_date and due_date (due_date is 30 days after start_date)
    today = datetime.utcnow()
    due_date = today + timedelta(days=30)

    # Instead of using the schema class, use the ORM model:
    new_project_workflow_obj = WorkflowFlowchart(
        name=workflow_template.name,
        node_data=workflow_node_data,
        link_data=workflow_link_data,
        project_id=workflow_flowchart.project_id,
        start_date=today,
        due_date=due_date,
    )
    db.add(new_project_workflow_obj)
    db.commit()
    await create_workflow_flowchart_events_for_project_from_template(
        workflow_flowchart.template_id, new_project_workflow_obj.id, mappings, db, tenant_id
    )
    await create_task_workflow_assoc_for_workflow(db, new_project_workflow_obj.id)
    return new_project_workflow_obj


# Add workflow events from template
async def create_workflow_flowchart_events_for_project_from_template(
    workflow_template_id: int,
    workflow_flowchart_id: int,
    mappings: List,
    db: Session,
    tenant_id: int,
):
    new_events = []
    # Loop through each mapping (only those with Parent/Child nodes should be present)
    for mapping in mappings:
        # Get template events corresponding to the old key from the template
        template_event_mappings = (
            db.query(WorkflowTemplateEvent)
            .filter(WorkflowTemplateEvent.workflow_template_node_id == mapping["old_key"])
            .filter(WorkflowTemplateEvent.workflow_template_id == workflow_template_id)
            .all()
        )
        # Create new events using the new key
        for template_event in template_event_mappings:
            new_event_obj = WorkflowEvent(
                name=template_event.name,
                workflow_flowchart_node_id=mapping["new_key"],  # Use new task id
                workflow_flowchart_id=workflow_flowchart_id,
                trigger_logic=template_event.trigger_logic,
                event_config=template_event.event_config,
                tenant_id=tenant_id,
            )
            new_events.append(new_event_obj)
    # Add all new events at once
    db.add_all(new_events)
    db.commit()
    return True
