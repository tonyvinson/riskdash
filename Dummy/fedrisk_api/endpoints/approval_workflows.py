import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from typing import List

from fedrisk_api.db import approval_workflows as db_approval_workflow
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.approval_workflows import (
    CreateApprovalWorkflowUseTemplate,
    CreateApprovalWorkflow,
    DisplayApprovalWorkflow,
    UpdateApprovalWorkflow,
    CreateApprovalWorkflowTemplate,
    DisplayApprovalWorkflowTemplate,
    UpdateApprovalWorkflowTemplate,
    DisplayApproval,
    CreateApproval,
    UpdateApproval,
    DisplayApprovalStakeholder,
    CreateApprovalStakeholder,
    UpdateApprovalStakeholder,
    DisplayTaskApproval,
    CreateTaskApproval,
    UpdateTaskApproval,
    DisplayRiskApproval,
    CreateRiskApproval,
    UpdateRiskApproval,
    DisplayAuditTestApproval,
    CreateAuditTestApproval,
    UpdateAuditTestApproval,
    DisplayProjectEvaluationApproval,
    CreateProjectEvaluationApproval,
    UpdateProjectEvaluationApproval,
    DisplayAssessmentApproval,
    CreateAssessmentApproval,
    UpdateAssessmentApproval,
    DisplayExceptionApproval,
    CreateExceptionApproval,
    UpdateExceptionApproval,
    DisplayDocumentApproval,
    CreateDocumentApproval,
    UpdateDocumentApproval,
    DisplayCapPoamApproval,
    CreateCapPoamApproval,
    UpdateCapPoamApproval,
    CreateWBSApproval,
    DisplayWBSApproval,
    UpdateWBSApproval,
    CreateWorkflowFlowchartApproval,
    DisplayWorkflowFlowchartApproval,
    UpdateWorkflowFlowchartApproval,
    CreateProjectApproval,
    DisplayProjectApproval,
    UpdateProjectApproval,
    CreateProjectControlApproval,
    DisplayProjectControlApproval,
    UpdateProjectControlApproval,
)
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    create_approval_workflow,
    delete_approval_workflow,
    update_approval_workflow,
    view_approval_workflow,
)


router = APIRouter(prefix="/approval_workflows", tags=["approval_workflows"])
LOGGER = logging.getLogger(__name__)

############# Approval Workflows ##################

# POST a new approval workflow - approval_workflows
@router.post(
    "/", response_model=DisplayApprovalWorkflow, dependencies=[Depends(create_approval_workflow)]
)
async def create_approval_workflow_endpoint(
    request: CreateApprovalWorkflow,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_approval_workflow(
            db, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the approval workflow",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Approval Workflow Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing approval workflow - approval_workflows/{id}
@router.put(
    "/{id}",
    # response_model=DisplayApprovalWorkflow,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_approval_workflow_endpoint(
    request: UpdateApprovalWorkflow,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_approval_workflow(
            db, id, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the approval workflow",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update Approval Workflow Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows for a project - approval_workflows/projects/{project_id}
@router.get(
    "/projects/{project_id}",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_project_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    project_id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_project(
        db, user["tenant_id"], project_id, user["user_id"]
    )


# GET all approval workflows for a user - approval_workflows/
@router.get(
    "/user",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_user_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    return db_approval_workflow.get_all_approval_workflows_user(db, user["user_id"])


# GET one approval workflow by ID - approval_workflows/{id}
@router.get(
    "/{id}", response_model=DisplayApprovalWorkflow, dependencies=[Depends(view_approval_workflow)]
)
def get_approval_workflow_by_id_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_approval_workflow(db, id, user["tenant_id"], user["user_id"])


# Delete approval workflow
@router.delete("/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_workflow_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_approval_workflow(
        db=db, id=id, user_id=user["user_id"], tenant_id=user["tenant_id"]
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval Workflow with id {id} does not exist",
        )
    return {"detail": "Successfully deleted approval workflow."}


@router.post(
    "/use_template",
    response_model=DisplayApprovalWorkflow,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_approval_workflow_from_template(
    request: CreateApprovalWorkflowUseTemplate,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        approval_workflow_resp = await db_approval_workflow.create_approval_workflow_from_template(
            approval_workflow=request,
            db=db,
            user_id=user["user_id"],
            tenant_id=user["tenant_id"],
        )
    except IntegrityError as ie:
        LOGGER.exception("Create Approval Workflow from template Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return approval_workflow_resp


# an endpoint to check for approval workflows that are past their due date and push them to rejected if they are not approved and past their due date
@router.post(
    "/check_due_date/automated",
    dependencies=[Depends(create_approval_workflow)],
)
async def check_due_date_approval_workflow_automate_status(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        approval_workflow_resp = (
            await db_approval_workflow.check_due_date_approval_workflow_automate_status_rejected(
                db=db, user_id=user["user_id"]
            )
        )
    except IntegrityError as ie:
        LOGGER.exception("Update of Approval Workflow status Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return approval_workflow_resp


############# Approval Workflow Templates ##################

# POST a new approval workflow template - approval_workflows/templates
@router.post(
    "/templates",
    response_model=DisplayApprovalWorkflowTemplate,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_approval_workflow_template_endpoint(
    request: CreateApprovalWorkflowTemplate,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_approval_workflow_template(
            db, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the approval workflow template",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Approval Workflow Template Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing approval workflow template - approval_workflows/templates/{id}
@router.put(
    "/templates/{id}",
    response_model=DisplayApprovalWorkflowTemplate,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_approval_workflow_template_endpoint(
    request: UpdateApprovalWorkflowTemplate,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_approval_workflow_template(
            db, request, id, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the approval workflow template",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update Approval Workflow Template Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflow templates for a tenant - approval_workflows/templates
@router.get(
    "/templates/all",
    response_model=List[DisplayApprovalWorkflowTemplate],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflow_templates_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    return db_approval_workflow.get_all_approval_workflow_templates(
        db, user["tenant_id"], user["user_id"]
    )


# GET one approval workflow template by ID - approval_workflows/templates/{id}
@router.get(
    "/templates/{id}",
    response_model=DisplayApprovalWorkflowTemplate,
    dependencies=[Depends(view_approval_workflow)],
)
def get_approval_workflow_template_by_id_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_approval_workflow_template(
        db, id, user["tenant_id"], user["user_id"]
    )


# Delete approval workflow template
@router.delete("/templates/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_workflow_template_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_approval_workflow_template(
        db=db, id=id, tenant_id=user["tenant_id"]
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval Workflow Template with id {id} does not exist",
        )
    return {"detail": "Successfully deleted approval workflow template."}


############# Approvals ##################

# POST a new approval - approval_workflows/approval
@router.post(
    "/approvals",
    response_model=DisplayApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_approval_endpoint(
    request: CreateApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_approval(db, request, user["user_id"])
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing approval - approval_workflows/approval/{id}
@router.put(
    "/approvals/{id}",
    response_model=DisplayApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_approval_endpoint(
    request: UpdateApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_approval(db, id, request, user["user_id"])
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approvals for an approval workflow - approval_workflows/{id}/approvals
@router.get(
    "/{id}/approvals",
    response_model=List[DisplayApproval],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approvals_for_workflow_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approvals_for_approval_workflow(db, id, user["user_id"])


# GET one approval by ID - approval_workflows/templates/{id}
@router.get(
    "/approvals/{id}",
    response_model=DisplayApproval,
    dependencies=[Depends(view_approval_workflow)],
)
def get_approval_by_id_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_approval(db, id, user["user_id"])


# Delete approval for approval workflow
@router.delete("/approvals/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_approval(db=db, user_id=user["user_id"], id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval with id {id} does not exist",
        )
    return {"detail": "Successfully deleted approval."}


############# Approval Stakeholders ##################

# POST a new approval stakeholder - approval_workflows/stakeholder
@router.post(
    "/approval_stakeholders",
    response_model=DisplayApprovalStakeholder,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_approval_stakeholder_endpoint(
    request: CreateApprovalStakeholder,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_approval_stakeholder(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the approval stakeholder",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Approval Stakeholder Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing approval stakeholder - approval_workflows/stakeholder/{id}
@router.put(
    "/approval_stakeholders/{id}",
    response_model=DisplayApprovalStakeholder,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_approval_stakeholder_endpoint(
    request: UpdateApprovalStakeholder,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_approval_stakeholder(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the approval stakeholder",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update Approval Stakeholder Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval stakeholders for an approval workflow - approval_workflows/{id}/approval_stakeholders
@router.get(
    "/{id}/approval_stakeholders",
    response_model=List[DisplayApprovalStakeholder],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_stakeholders_for_workflow_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_stakeholders_for_approval_workflow(
        db, id, user["user_id"]
    )


# GET one approval stakeholder by ID - approval_workflows/approval_stakeholders/{id}
@router.get(
    "/approval_stakeholders/{id}",
    response_model=DisplayApprovalStakeholder,
    dependencies=[Depends(view_approval_workflow)],
)
def get_approval_stakeholder_by_id_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_approval_stakeholder(db, id, user["user_id"])


# Delete approval stakeholder for approval workflow
@router.delete("/approval_stakeholders/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_stakeholder_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_approval_stakeholder(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Approval stakeholder with id {id} does not exist",
        )
    return {"detail": "Successfully deleted approval stakeholder."}


############# Task Approvals ##################

# POST update a new task approval workflow mapping - approval_workflows/tasks
@router.post(
    "/tasks",
    response_model=DisplayTaskApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_task_approval_endpoint(
    request: CreateTaskApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_task_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the task approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Task Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing task approval association - approval_workflows/tasks/{id}
@router.put(
    "/tasks/{id}",
    response_model=DisplayTaskApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_task_approval_endpoint(
    request: UpdateTaskApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_task_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the task approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update Task Approval Workflow Association Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by task ID - approval_workflows/tasks/{id}/approval_workflows
@router.get(
    "/tasks/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_task_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_task(db, id, user["user_id"])


# Delete task association for approval workflow
@router.delete("/tasks/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_task_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_task_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted task association."}


############# Risk Approvals ##################

# POST a new risk approval workflow mapping - approval_workflows/risks
@router.post(
    "/risks",
    response_model=DisplayRiskApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_risk_approval_endpoint(
    request: CreateRiskApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_risk_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the risk approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Risk Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing risk approval association - approval_workflows/risks/{id}
@router.put(
    "/risks/{id}",
    response_model=DisplayRiskApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_risk_approval_endpoint(
    request: UpdateRiskApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_risk_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the risk approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update Risk Approval Workflow Association Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by risk ID - approval_workflows/risks/{id}/approval_workflows
@router.get(
    "/risks/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_risk_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_risk(db, id, user["user_id"])


# Delete risk association for approval workflow
@router.delete("/risks/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_risk_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_risk_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted risk association."}


############# Audit Test Approvals ##################

# POST a new audit test approval workflow mapping - approval_workflows/audit_tests
@router.post(
    "/audit_tests",
    response_model=DisplayAuditTestApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_audit_test_approval_endpoint(
    request: CreateAuditTestApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_audit_test_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the audit test approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Test Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing audit test approval association - approval_workflows/audit_tests/{id}
@router.put(
    "/audit_tests/{id}",
    response_model=DisplayAuditTestApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_audit_test_approval_endpoint(
    request: UpdateAuditTestApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_audit_test_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the audit test approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update Audit Test Approval Workflow Association Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by audit test ID - approval_workflows/audit_tests/{id}/approval_workflows
@router.get(
    "/audit_tests/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_audit_test_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_audit_test(db, id, user["user_id"])


# Delete audit test association for approval workflow
@router.delete("/audit_tests/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_audit_test_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_audit_test_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Audit Test association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted audit test association."}


############# Project Evaluation Approvals ##################

# POST a new project evaluation approval workflow mapping - approval_workflows/project_evaluations
@router.post(
    "/project_evaluations",
    response_model=DisplayProjectEvaluationApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_audit_test_approval_endpoint(
    request: CreateProjectEvaluationApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_project_evaluation_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the project evaluation approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Project Evaluation Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing project evaluation approval association - approval_workflows/project_evaluations/{id}
@router.put(
    "/project_evaluations/{id}",
    response_model=DisplayProjectEvaluationApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_project_evaluation_approval_endpoint(
    request: UpdateProjectEvaluationApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_project_evaluation_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the project evaluation approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception(
            "Update Project Evaluation Approval Workflow Association Error - Invalid Request"
        )
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by project evaluation ID - approval_workflows/project_evaluations/{id}/approval_workflows
@router.get(
    "/project_evaluations/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_project_evaluation_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_project_evaluation(
        db, id, user["user_id"]
    )


# Delete project evalaution association for approval workflow
@router.delete("/project_evaluations/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_project_evaluation_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_project_evaluation_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project Evaluation association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted project evaluation association."}


############# Assessment Approvals ##################

# POST a new assessment approval workflow mapping - approval_workflows/assessments
@router.post(
    "/assessments",
    response_model=DisplayAssessmentApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_assessment_approval_endpoint(
    request: CreateAssessmentApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_assessment_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the assessment approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Assessment Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing assessment approval association - approval_workflows/assessments/{id}
@router.put(
    "/assessments/{id}",
    response_model=DisplayAssessmentApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_assessment_approval_endpoint(
    request: UpdateAssessmentApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_assessment_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the assessment approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update Assessment Approval Workflow Association Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by assessment ID - approval_workflows/assessments/{id}/approval_workflows
@router.get(
    "/assessments/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_assessment_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_assessment(db, id, user["user_id"])


# Delete assessment association for approval workflow
@router.delete("/assessments/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_assessment_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_assessment_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Assessment association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted assessment association."}


############# Exception Approvals ##################

# POST a new exception approval workflow mapping - approval_workflows/exceptions
@router.post(
    "/exceptions",
    response_model=DisplayExceptionApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_exception_approval_endpoint(
    request: CreateExceptionApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_exception_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the exception approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Exception Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing exception approval association - approval_workflows/exceptions/{id}
@router.put(
    "/exceptions/{id}",
    response_model=DisplayExceptionApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_exception_approval_endpoint(
    request: UpdateExceptionApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_exception_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the exception approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update Exception Approval Workflow Association Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by exception ID - approval_workflows/exceptions/{id}/approval_workflows
@router.get(
    "/exceptions/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_exception_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_exception(db, id, user["user_id"])


# Delete exception association for approval workflow
@router.delete("/exceptions/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_exception_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_exception_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Exception association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted exception association."}


############# Document Approvals ##################

# POST a new document approval workflow mapping - approval_workflows/document
@router.post(
    "/documents",
    response_model=DisplayDocumentApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_document_approval_endpoint(
    request: CreateDocumentApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_document_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the document approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Document Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing document approval association - approval_workflows/document/{id}
@router.put(
    "/documents/{id}",
    response_model=DisplayDocumentApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_document_approval_endpoint(
    request: UpdateDocumentApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_document_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the document approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update Document Approval Workflow Association Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by document ID - approval_workflows/document/{id}/approval_workflows
@router.get(
    "/documents/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_document_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_document(db, id, user["user_id"])


# Delete document association for approval workflow
@router.delete("/documents/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_document_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_document_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted document association."}


############# CAP/POAM Approvals ##################

# POST a new cap_poam approval workflow mapping - approval_workflows/cap_poams
@router.post(
    "/cap_poams",
    response_model=DisplayCapPoamApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_cap_poam_approval_endpoint(
    request: CreateCapPoamApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_cap_poam_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the cap poam approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Cap Poam Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing CAP/POAM approval association - approval_workflows/cap_poams/{id}
@router.put(
    "/cap_poams/{id}",
    response_model=DisplayCapPoamApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_cap_poam_approval_endpoint(
    request: UpdateCapPoamApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_cap_poam_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the cap poam approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update CAP/POAM Approval Workflow Association Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by cap poam ID - approval_workflows/cap_poams/{id}/approval_workflows
@router.get(
    "/cap_poams/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_cap_poam_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_cap_poam(db, id, user["user_id"])


# Delete cap poam association for approval workflow
@router.delete("/cap_poams/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_cap_poam_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_cap_poam_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"CAP/POAM association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted CAP/POAM association."}


############# WBS Approvals ##################

# POST a new WBS approval workflow mapping - approval_workflows/wbs
@router.post(
    "/wbs",
    response_model=DisplayWBSApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_wbs_approval_endpoint(
    request: CreateWBSApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_wbs_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the WBS approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create WBS Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing WBS approval association - approval_workflows/wbs/{id}
@router.put(
    "/wbs/{id}",
    response_model=DisplayWBSApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_wbs_approval_endpoint(
    request: UpdateWBSApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_wbs_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the WBS approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update WBS Approval Workflow Association Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by WBS ID - approval_workflows/wbs/{id}/approval_workflows
@router.get(
    "/wbs/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_wbs_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_wbs(db, id, user["user_id"])


# Delete WBS association for approval workflow
@router.delete("/wbs/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_wbs_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_wbs_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"WBS association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted WBS association."}


############# Workflow Flowchart Approvals ##################

# POST a new workflow approval workflow mapping - approval_workflows/workflow_flowcharts
@router.post(
    "/workflow_flowcharts",
    response_model=DisplayWorkflowFlowchartApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_workflow_flowchart_approval_endpoint(
    request: CreateWorkflowFlowchartApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_workflow_flowchart_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the workflow flowchart approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Workflow Flowchart Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing workflow flowchart approval association - approval_workflows/workflow_flowcharts/{id}
@router.put(
    "/workflow_flowcharts/{id}",
    response_model=DisplayWorkflowFlowchartApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_workflow_flowchart_approval_endpoint(
    request: UpdateWorkflowFlowchartApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_workflow_flowchart_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the workflow flowchart approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception(
            "Update Workflow Flowchart Approval Workflow Association Error - Invalid Request"
        )
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by workflow flowchart ID - approval_workflows/workflow_flowcharts/{id}/approval_workflows
@router.get(
    "/workflow_flowcharts/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_workflow_flowchart_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_workflow_flowchart(
        db, id, user["user_id"]
    )


# Delete Workflow Flowchart association for approval workflow
@router.delete("/workflow_flowcharts/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_workflow_flowchart_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_workflow_flowchart_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workflow Flowchart association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted workflow flowchart association."}


############# Project Approvals ##################

# POST a new project approval workflow mapping - approval_workflows/project
@router.post(
    "/projects",
    response_model=DisplayProjectApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_project_approval_endpoint(
    request: CreateProjectApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_project_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the project approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Project Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing project approval association - approval_workflows/projects/{id}
@router.put(
    "/projects/{id}",
    response_model=DisplayProjectApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_project_approval_endpoint(
    request: UpdateProjectApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_project_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the project approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Update Project Approval Workflow Association Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by project ID - approval_workflows/projects/{id}/approval_workflows
@router.get(
    "/projects/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_project_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_project(db, id, user["user_id"])


# Delete project association for approval workflow
@router.delete("/projects/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_project_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_project_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted project association."}


############# Project Control Approvals ##################

# POST a new project control approval workflow mapping - approval_workflows/project_controls
@router.post(
    "/project_controls",
    response_model=DisplayProjectControlApproval,
    dependencies=[Depends(create_approval_workflow)],
)
async def create_project_control_approval_endpoint(
    request: CreateProjectControlApproval,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.create_project_control_approval_workflow(
            db, request, user["user_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the project control approval",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception("Create Project Control Approval Error - Invalid Request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# PUT update an existing project control approval association - approval_workflows/project_controls/{id}
@router.put(
    "/project_controls/{id}",
    response_model=DisplayProjectControlApproval,
    dependencies=[Depends(update_approval_workflow)],
)
async def update_project_control_approval_endpoint(
    request: UpdateProjectControlApproval,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        result = await db_approval_workflow.update_project_control_approval_workflow(
            db, id, request, user["user_id"], user["tenant_id"]
        )
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem updating the project control approval workflow association",
            )
        return result
    except IntegrityError as ie:
        LOGGER.exception(
            "Update Project Control Approval Workflow Association Error - Invalid Request"
        )
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET all approval workflows by project control ID - approval_workflows/project_controls/{id}/approval_workflows
@router.get(
    "/project_controls/{id}/approval_workflows",
    response_model=List[DisplayApprovalWorkflow],
    dependencies=[Depends(view_approval_workflow)],
)
def get_all_approval_workflows_for_project_control_endpoint(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    id: str = None,
):
    return db_approval_workflow.get_all_approval_workflows_for_project_control(
        db, id, user["user_id"]
    )


# Delete project control association for approval workflow
@router.delete("/project_controls/{id}", dependencies=[Depends(delete_approval_workflow)])
async def delete_approval_project_control_assoc_by_id_endpoint(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_approval_workflow.delete_project_control_approval_workflow(
        db=db, user_id=user["user_id"], id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project Control association with id {id} does not exist",
        )
    return {"detail": "Successfully deleted project control association."}
