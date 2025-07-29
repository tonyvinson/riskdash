import logging

from sqlalchemy.orm import Session

from fedrisk_api.db.models import WorkflowEventLog
from fedrisk_api.schema.workflow_event_log import (
    CreateWorkflowEventLog,
    UpdateWorkflowEventLog,
)


LOGGER = logging.getLogger(__name__)

# workflow_event_log
def create_workflow_event_log(db: Session, workflow_event_log: CreateWorkflowEventLog):
    my_new_workflow_event_log_dict = workflow_event_log.dict()
    new_workflow_event_log = WorkflowEventLog(**my_new_workflow_event_log_dict)
    db.add(new_workflow_event_log)
    db.commit()
    return new_workflow_event_log


def get_all_workflow_event_logs_by_workflow_event_id(
    db: Session,
    workflow_event_id: int,
):
    queryset = (
        db.query(WorkflowEventLog)
        .filter(WorkflowEventLog.workflow_event_id == workflow_event_id)
        .all()
    )
    return queryset


def get_workflow_event_log_by_id(db: Session, workflow_event_log_id: int):
    queryset = (
        db.query(WorkflowEventLog).filter(WorkflowEventLog.id == workflow_event_log_id).first()
    )
    return queryset


def update_workflow_event_log_by_id(
    workflow_event_log: UpdateWorkflowEventLog,
    db: Session,
    workflow_event_log_id: int,
):
    queryset = db.query(WorkflowEventLog).filter(WorkflowEventLog.id == workflow_event_log_id)

    if not queryset.first():
        return False

    queryset.update(workflow_event_log.dict(exclude_unset=True))
    db.commit()
    return True


def delete_workflow_event_log_by_id(db: Session, workflow_event_log_id: int):
    workflow_event_log = (
        db.query(WorkflowEventLog).filter(WorkflowEventLog.id == workflow_event_log_id).first()
    )

    if not workflow_event_log:
        return False

    db.delete(workflow_event_log)
    db.commit()
    return True
