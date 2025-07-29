import logging

from sqlalchemy.orm import Session

from datetime import datetime

from fedrisk_api.db.models import (
    AuditTest,
    AuditTestStakeHolder,
    WorkflowEvent,
    WorkflowEventLog,
    Task,
    TaskStakeholder,
    User,
    Project,
    Risk,
    RiskStakeholder,
    WorkflowFlowchart,
)
from fedrisk_api.schema.workflow_event import (
    CreateWorkflowEvent,
    UpdateWorkflowEvent,
)

from fedrisk_api.utils.email_util import send_event_trigger_email

LOGGER = logging.getLogger(__name__)

# workflow_event
def create_workflow_event(db: Session, workflow_event: CreateWorkflowEvent, tenant_id: int):
    my_new_workflow_event_dict = workflow_event.dict()
    new_workflow_event = WorkflowEvent(**my_new_workflow_event_dict, tenant_id=tenant_id)
    db.add(new_workflow_event)
    db.commit()
    return new_workflow_event


def get_all_workflow_events_by_tenant_id(
    db: Session,
    tenant_id: int,
):
    queryset = db.query(WorkflowEvent).filter(WorkflowEvent.tenant_id == tenant_id).all()
    return queryset


def get_workflow_event_by_id(db: Session, workflow_event_id: int):
    queryset = db.query(WorkflowEvent).filter(WorkflowEvent.id == workflow_event_id).first()
    return queryset


def get_workflow_event_by_workflow_flowchart_node_id(db: Session, workflow_flowchart_node_id: int):
    queryset = (
        db.query(WorkflowEvent)
        .filter(WorkflowEvent.workflow_flowchart_node_id == workflow_flowchart_node_id)
        .all()
    )
    return queryset


def update_workflow_event_by_id(
    workflow_event: UpdateWorkflowEvent,
    db: Session,
    workflow_event_id: int,
):
    queryset = db.query(WorkflowEvent).filter(WorkflowEvent.id == workflow_event_id)

    if not queryset.first():
        return False

    queryset.update(workflow_event.dict(exclude_unset=True))
    db.commit()
    return True


def delete_workflow_event_by_id(db: Session, workflow_event_id: int):
    workflow_event = db.query(WorkflowEvent).filter(WorkflowEvent.id == workflow_event_id).first()

    if not workflow_event:
        return False

    db.delete(workflow_event)
    db.commit()
    return True


def get_config_value(config: dict, field_name: str, default=None):
    """
    Extracts the value for a given field name from a config dictionary.
    The config is expected to have a "fields" key which is a list of field objects.
    """
    for field_obj in config.get("fields", []):
        if field_obj.get("field") == field_name:
            return field_obj.get("value", default)
    return default


def evaluate_condition(condition: dict, task: Task) -> bool:
    # Map trigger field names to Task attributes
    field = condition["field"]
    operator = condition["operator"]
    expected_value = condition["value"]

    # You may need to adjust this mapping to match your Task model
    if field == "Priority":
        # assuming task.priority is a string (or convert as needed)
        task_value = task.priority
    elif field == "Status":
        # mapping "Status" to task_status_id, for example
        task_value = task.task_status_id
    elif field == "Category":
        task_value = task.task_category_id
    else:
        # default: try to get the attribute with lower-case field name
        task_value = getattr(task, field.lower(), None)

    # Evaluate based on the operator
    if operator == "Equals":
        return task_value == expected_value
    elif operator == "Does Not Equal":
        return task_value != expected_value
    else:
        # Add more operators as needed
        return False


def evaluate_trigger_logic(logic: list, task: Task) -> bool:
    """
    Evaluate a list of trigger logic conditions against a task.
    The first condition's result is used as the initial value,
    then subsequent conditions are combined using the comparison operator.
    """
    if not logic:
        return True

    # Ensure the logic is sorted by weight if order matters
    sorted_logic = sorted(logic, key=lambda c: int(c.get("weight", 0)))

    # Evaluate the first condition
    result = evaluate_condition(sorted_logic[0], task)

    # Evaluate subsequent conditions with their comparison operator
    for condition in sorted_logic[1:]:
        comp = condition.get("comparison", {})
        # Determine the operator to combine with previous result (default to AND)
        comp_operator = comp.get("value", "AND")
        condition_result = evaluate_condition(condition, task)
        if comp_operator == "AND":
            result = result and condition_result
        elif comp_operator == "OR":
            result = result or condition_result
        else:
            # Default to AND if operator is unrecognized
            result = result and condition_result

    return result


def log_event(
    db: Session, event: WorkflowEvent, event_type: str, description: str, link: str = None
) -> WorkflowEventLog:
    new_log = WorkflowEventLog(
        workflow_event_id=event.id,
        event_type=event_type,
        event_description=description,
        link=link,
    )
    db.add(new_log)
    db.commit()
    return new_log


def process_task_event(
    db: Session, event: WorkflowEvent, project: Project, config: dict, stakeholder_user_ids: list
) -> WorkflowEventLog:
    # Extract values from config using the helper
    name = get_config_value(config, "name", "")
    title = name[:20]  # trim to 20 chars
    description_value = get_config_value(config, "description", "")
    owner_id = get_config_value(config, "owner_id")
    owner_user_id = db.query(User).filter(User.email == owner_id).first()
    due_date_value = get_config_value(config, "due_date")
    if due_date_value is not None:
        try:
            # Assuming due_date_value is a Unix timestamp in seconds.
            due_date = datetime.fromtimestamp(int(due_date_value)).date()
        except Exception as e:
            due_date = None
    else:
        due_date = None
    new_task = Task(
        title=title,
        name=name,
        description=description_value,
        assigned_to=owner_user_id.id,
        due_date=due_date,
        project_id=project.id,
        user_id=project.project_admin_id,
        tenant_id=project.tenant_id,
    )
    db.add(new_task)
    db.flush()  # Flush to assign new_task.id without ending the transaction

    added_task = db.query(Task).filter(Task.id == new_task.id).first()

    # Add stakeholders for the task
    for stakeholder in stakeholder_user_ids:
        new_stakeholder = TaskStakeholder(
            task_id=added_task.id,
            user_id=stakeholder,
        )
        db.add(new_stakeholder)
        db.flush()

    desc = f"Created a new task {added_task.name} with description {added_task.description}."
    link = f"/projects/{project.id}/tasks/{new_task.id}"
    event_log = log_event(db, event, "Create Task", desc, link)
    db.commit()  # Commit the whole transaction
    return event_log


def process_audit_test_event(
    db: Session, event: WorkflowEvent, project: Project, config: dict, stakeholder_user_ids: list
) -> WorkflowEventLog:
    name = get_config_value(config, "name", "")
    description_value = get_config_value(config, "description", "")
    tester_id = get_config_value(config, "owner_id")
    tester_user_id = db.query(User).filter(User.email == tester_id).first()

    new_audit_test = AuditTest(
        name=name,
        description=description_value,
        tester_id=tester_user_id.id,
        project_id=project.id,
        tenant_id=project.tenant_id,
    )
    db.add(new_audit_test)
    db.flush()  # Flush to assign an ID without committing
    added_audit_test = db.query(AuditTest).filter(AuditTest.id == new_audit_test.id).first()

    # Add stakeholders for the audit test
    for stakeholder in stakeholder_user_ids:
        new_stakeholder = AuditTestStakeHolder(
            audit_test_id=added_audit_test.id,
            user_id=stakeholder,
        )
        db.add(new_stakeholder)
        db.flush()

    description_text = f"Created a new audit test {added_audit_test.name} with description {added_audit_test.description}."
    link = f"/projects/{project.id}/audit_tests/{new_audit_test.id}"
    return log_event(db, event, "Create Audit Test", description_text, link)


def process_risk_event(
    db: Session, event: WorkflowEvent, project: Project, config: dict, stakeholder_user_ids: list
) -> WorkflowEventLog:
    # Extract values using the helper function
    name = get_config_value(config, "name", "")
    description_value = get_config_value(config, "description", "")
    owner_id = get_config_value(config, "owner_id")
    owner_user_id = db.query(User).filter(User.email == owner_id).first()

    new_risk = Risk(
        name=name,
        description=description_value,
        owner_id=owner_user_id.id,
        project_id=project.id,
        tenant_id=project.tenant_id,
    )
    db.add(new_risk)
    db.flush()  # Flush to get new_risk.id
    added_risk = db.query(Risk).filter(Risk.id == new_risk.id).first()

    # Add stakeholders for the risk
    for stakeholder in stakeholder_user_ids:
        new_stakeholder = RiskStakeholder(
            risk_id=added_risk.id,
            user_id=stakeholder,
        )
        db.add(new_stakeholder)
        db.flush()

    description_text = (
        f"Created a new risk {added_risk.name} with description {added_risk.description}."
    )
    link = f"/projects/{project.id}/risks/{new_risk.id}"
    return log_event(db, event, "Create Risk", description_text, link)


async def process_email_event(db: Session, event: WorkflowEvent, config: dict) -> WorkflowEventLog:
    # Extract email configuration values from the nested fields
    email_subject = get_config_value(config, "email-subject", "No subject")
    email_body = get_config_value(config, "email-body", "No email body provided.")
    recipient_id = get_config_value(config, "recipient_id")
    internal_ccs = get_config_value(config, "internal_cc_recipient_list", [])
    external_ccs = get_config_value(config, "external_cc_recipient_list", [])

    # Prepare a new dictionary for sending the email
    email_data = {
        "recipient_id": recipient_id,
        "email-subject": email_subject,
        "email-body": email_body,
        "internal_cc_recipient_list": internal_ccs,
        "external_cc_recipient_list": external_ccs,
    }

    # Send the email asynchronously
    await send_event_trigger_email(email_data)

    description = f"Sent a new email with subject {email_subject} and body {email_body}."
    return log_event(db, event, "Send Email", description)


async def process_workflow_event_triggers(db: Session):
    # Query events that do not have any logs (i.e. not processed)
    all_workflow_events = (
        db.query(WorkflowEvent)
        .outerjoin(WorkflowEventLog)
        .filter(WorkflowEventLog.id == None)
        .all()
    )
    event_logs = []

    for event in all_workflow_events:
        task_id = event.workflow_flowchart_node_id

        # Get the associated project by joining WorkflowFlowchart and WorkflowEvent
        project = (
            db.query(Project)
            .join(WorkflowFlowchart, WorkflowFlowchart.project_id == Project.id)
            .join(WorkflowEvent, WorkflowEvent.workflow_flowchart_id == WorkflowFlowchart.id)
            .filter(WorkflowEvent.id == event.id)
            .first()
        )

        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            print(f"Task with id {task_id} not found for event {event.id}.")
            continue

        logic = event.trigger_logic  # List of conditions
        if evaluate_trigger_logic(logic, task):
            config = event.event_config
            # Retrieve stakeholder user IDs from emails in config
            stakeholder_user_ids = []
            for stakeholder in config.get("additional_stakeholder_ids", []):
                user = db.query(User).filter(User.email == stakeholder).first()
                if user:
                    stakeholder_user_ids.append(user.id)

            data_type = config.get("data_type")
            if data_type == "task":
                log = process_task_event(db, event, project, config, stakeholder_user_ids)
                event_logs.append(log)
            elif data_type == "audit_test":
                log = process_audit_test_event(db, event, project, config, stakeholder_user_ids)
                event_logs.append(log)
            elif data_type == "risk":
                log = process_risk_event(db, event, project, config, stakeholder_user_ids)
                event_logs.append(log)
            elif data_type == "email":
                log = await process_email_event(db, event, config)
                event_logs.append(log)
            else:
                print(f"Unknown data type {data_type} for event {event.id}")
        else:
            print(f"Event {event.id} conditions not met for task {task.id}.")

    return event_logs
