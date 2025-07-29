import logging

from sqlalchemy.orm import Session

from fedrisk_api.db.models import WorkflowTemplateEvent
from fedrisk_api.schema.workflow_template_event import (
    CreateWorkflowTemplateEvent,
    UpdateWorkflowTemplateEvent,
)


LOGGER = logging.getLogger(__name__)

# workflow_template_event
def create_workflow_template_event(
    db: Session, workflow_template_event: CreateWorkflowTemplateEvent, tenant_id: int
):
    my_new_workflow_template_event_dict = workflow_template_event.dict()
    new_workflow_template_event = WorkflowTemplateEvent(
        **my_new_workflow_template_event_dict, tenant_id=tenant_id
    )
    db.add(new_workflow_template_event)
    db.commit()
    return new_workflow_template_event


def get_all_workflow_template_events_by_tenant_id(
    db: Session,
    tenant_id: int,
):
    queryset = (
        db.query(WorkflowTemplateEvent).filter(WorkflowTemplateEvent.tenant_id == tenant_id).all()
    )
    return queryset


def get_workflow_template_event_by_id(db: Session, workflow_template_event_id: int):
    queryset = (
        db.query(WorkflowTemplateEvent)
        .filter(WorkflowTemplateEvent.id == workflow_template_event_id)
        .first()
    )
    return queryset


def get_workflow_template_event_by_workflow_template_node_id(
    db: Session, workflow_template_node_id: int
):
    queryset = (
        db.query(WorkflowTemplateEvent)
        .filter(WorkflowTemplateEvent.workflow_template_node_id == workflow_template_node_id)
        .all()
    )
    return queryset


def update_workflow_template_event_by_id(
    workflow_template_event: UpdateWorkflowTemplateEvent,
    db: Session,
    workflow_template_event_id: int,
):
    queryset = db.query(WorkflowTemplateEvent).filter(
        WorkflowTemplateEvent.id == workflow_template_event_id
    )

    if not queryset.first():
        return False

    queryset.update(workflow_template_event.dict(exclude_unset=True))
    db.commit()
    return True


def delete_workflow_template_event_by_id(db: Session, workflow_template_event_id: int):
    workflow_template_event = (
        db.query(WorkflowTemplateEvent)
        .filter(WorkflowTemplateEvent.id == workflow_template_event_id)
        .first()
    )

    if not workflow_template_event:
        return False

    db.delete(workflow_template_event)
    db.commit()
    return True
