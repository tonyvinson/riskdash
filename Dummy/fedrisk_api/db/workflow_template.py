import logging

from sqlalchemy.orm import Session

from fedrisk_api.db.models import WorkflowTemplate
from fedrisk_api.schema.workflow_template import (
    CreateWorkflowTemplate,
    UpdateWorkflowTemplate,
)


LOGGER = logging.getLogger(__name__)

# workflow_template
def create_workflow_template(
    db: Session, workflow_template: CreateWorkflowTemplate, tenant_id: int
):
    my_new_workflow_template_dict = workflow_template.dict()
    new_workflow_template = WorkflowTemplate(**my_new_workflow_template_dict, tenant_id=tenant_id)
    db.add(new_workflow_template)
    db.commit()
    return new_workflow_template


def get_all_workflow_templates_by_tenant_id(
    db: Session,
    tenant_id: int,
):
    queryset = db.query(WorkflowTemplate).filter(WorkflowTemplate.tenant_id == tenant_id).all()
    return queryset


def get_workflow_template_by_id(db: Session, workflow_template_id: int):
    queryset = (
        db.query(WorkflowTemplate).filter(WorkflowTemplate.id == workflow_template_id).first()
    )
    return queryset


def update_workflow_template_by_id(
    workflow_template: UpdateWorkflowTemplate,
    db: Session,
    workflow_template_id: int,
):
    queryset = db.query(WorkflowTemplate).filter(WorkflowTemplate.id == workflow_template_id)

    if not queryset.first():
        return False

    queryset.update(workflow_template.dict(exclude_unset=True))
    db.commit()
    return True


def delete_workflow_template_by_id(db: Session, workflow_template_id: int):
    workflow_template = (
        db.query(WorkflowTemplate).filter(WorkflowTemplate.id == workflow_template_id).first()
    )

    if not workflow_template:
        return False

    db.delete(workflow_template)
    db.commit()
    return True
