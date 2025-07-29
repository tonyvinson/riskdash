import logging
from fedrisk_api.db.models import WorkflowFlowchart, WorkflowTaskMapping

LOGGER = logging.getLogger(__name__)


def create_task_workflow_assoc(db):
    """Creates new task-workflow associations if they do not already exist."""
    # Get all workflow flowcharts
    workflow_flowcharts = db.query(WorkflowFlowchart).all()

    # Use a set to collect unique (task_id, workflow_id) pairs
    task_wf_ids = set()
    for wf in workflow_flowcharts:
        # Loop through node_data to get task nodes
        for node in wf.node_data:
            if node.get("category") in ("Parent", "Child"):
                # Save a tuple of (task_id, workflow_flowchart_id)
                task_wf_ids.add((node.get("key"), wf.id))

    # Check if an association already exists for each (task_id, workflow_id) pair
    for task_id, workflow_id in task_wf_ids:
        assoc_exists = (
            db.query(WorkflowTaskMapping)
            .filter(WorkflowTaskMapping.task_id == task_id)
            .filter(WorkflowTaskMapping.workflow_flowchart_id == workflow_id)
            .first()
        )
        if assoc_exists is None:
            # Create new association using keyword arguments
            new_assoc = WorkflowTaskMapping(
                task_id=task_id,
                workflow_flowchart_id=workflow_id,
            )
            db.add(new_assoc)
            db.commit()


async def create_task_workflow_assoc_for_workflow(db, workflow_id):
    """Creates new task-workflow associations if they do not already exist."""
    # Get the workflow flowchart by its ID
    workflow_flowchart = (
        db.query(WorkflowFlowchart).filter(WorkflowFlowchart.id == workflow_id).first()
    )
    if not workflow_flowchart:
        return

    # Use a set to collect unique (task_id, workflow_flowchart_id) pairs
    task_wf_ids = set()
    for node in workflow_flowchart.node_data:
        if node.get("category") in ("Parent", "Child"):
            task_wf_ids.add((node.get("key"), workflow_flowchart.id))

    # List to hold new associations to add
    new_assocs = []
    for task_id, wf_id in task_wf_ids:
        assoc_exists = (
            db.query(WorkflowTaskMapping)
            .filter(
                WorkflowTaskMapping.task_id == task_id,
                WorkflowTaskMapping.workflow_flowchart_id == wf_id,
            )
            .first()
        )
        if assoc_exists is None:
            new_assoc = WorkflowTaskMapping(
                task_id=task_id,
                workflow_flowchart_id=wf_id,
            )
            db.add(new_assoc)
            new_assocs.append(new_assoc)

    # If there are any new associations, commit them all at once
    if new_assocs:
        db.commit()
