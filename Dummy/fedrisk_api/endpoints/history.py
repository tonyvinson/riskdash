import logging

from typing import List

# import requests

from fastapi import APIRouter, Depends, HTTPException, status

# from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import history as db_history
from fedrisk_api.db import project as db_project
from fedrisk_api.db import user as db_user
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.history import (
    DisplayApprovalWorkflowHistory,
    DisplayAssessmentHistory,
    DisplayAuditTestHistory,
    DisplayDocumentHistory,
    DisplayExceptionHistory,
    DisplayProjectControlHistory,
    DisplayProjectEvaluationHistory,
    DisplayProjectHistory,
    DisplayTaskHistory,
    DisplayRiskHistory,
    DisplayWBSHistory,
    CreateUserWatching,
    UpdateUserWatching,
    DisplayProjectUserHistory,
    DisplayCapPoamHistory,
    DisplayWorkflowFlowchartHistory,
)
from fedrisk_api.utils.authentication import custom_auth

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/history", tags=["history"])

# Assessments
@router.get(
    "/assessments/{id}",
    response_model=DisplayAssessmentHistory,
)
def get_assessment_history_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_history.get_assessment_history_by_id(db=db, assessment_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for assessment with specified id does not exist",
        )
    return queryset


@router.get(
    "/assessments/project/{project_id}",
    response_model=List[DisplayAssessmentHistory],
)
def get_all_assessment_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_assessment_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# Audit Tests
@router.get(
    "/audit_tests/{id}",
    response_model=DisplayAuditTestHistory,
)
def get_audit_test_history_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_history.get_audit_test_history_by_id(db=db, audit_test_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for audit test with specified id does not exist",
        )
    return queryset


@router.get(
    "/audit_tests/project/{project_id}",
    response_model=List[DisplayAuditTestHistory],
)
def get_all_audit_test_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_audit_test_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# Audit Tests
@router.get(
    "/cap_poams/{id}",
    response_model=DisplayCapPoamHistory,
)
def get_cap_poam_history_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_history.get_cap_poam_history_by_id(db=db, cap_poam_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for cap poam with specified id does not exist",
        )
    return queryset


@router.get(
    "/cap_poams/project/{project_id}",
    response_model=List[DisplayCapPoamHistory],
)
def get_all_cap_poam_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_cap_poam_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# Documents
@router.get(
    "/documents/{id}",
    response_model=DisplayDocumentHistory,
)
def get_document_history_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_history.get_document_history_by_id(db=db, document_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for document with specified id does not exist",
        )
    return queryset


@router.get(
    "/documents/project/{project_id}",
    # response_model=List[DisplayDocumentHistory],
)
def get_all_document_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_document_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    flattened = flatten(queryset)
    return flattened


# Exceptions
@router.get(
    "/exceptions/{id}",
    response_model=DisplayExceptionHistory,
)
def get_exception_history_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_history.get_exception_history_by_id(db=db, exception_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for exception with specified id does not exist",
        )
    return queryset


@router.get(
    "/exceptions/project/{project_id}",
    response_model=List[DisplayExceptionHistory],
)
def get_all_exception_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_exception_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# Project Controls
@router.get(
    "/project_controls/{id}",
    response_model=DisplayProjectControlHistory,
)
def get_project_control_history_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_history.get_project_control_history_by_id(db=db, project_control_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for project control with specified id does not exist",
        )
    return queryset


@router.get(
    "/project_controls/project/{project_id}",
    response_model=List[DisplayProjectControlHistory],
)
def get_all_project_control_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_project_control_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# Project Evaluations
@router.get(
    "/project_evaluations/{id}",
    response_model=DisplayProjectEvaluationHistory,
)
def get_project_evaluation_history_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_history.get_project_evaluation_history_by_id(db=db, project_evaluation_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for project evaluation with specified id does not exist",
        )
    return queryset


@router.get(
    "/project_evaluations/project/{project_id}",
    response_model=List[DisplayProjectEvaluationHistory],
)
def get_all_project_evaluation_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_project_evaluation_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# Projects
@router.get(
    "/projects/{id}",
    response_model=DisplayProjectHistory,
)
def get_project_history_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_history.get_project_history_by_id(db=db, id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project history with specified id does not exist",
        )
    return queryset


@router.get(
    "/projects/project/{project_id}",
    response_model=List[DisplayProjectHistory],
)
def get_all_project_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_project_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# Tasks
@router.get(
    "/tasks/{id}",
    response_model=DisplayTaskHistory,
)
def get_task_history_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_history.get_task_history_by_id(db=db, task_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for task with specified id does not exist",
        )
    return queryset


@router.get(
    "/tasks/project/{project_id}",
    response_model=List[DisplayTaskHistory],
)
def get_all_task_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_task_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# Project Users
@router.get(
    "/project_users/project/{project_id}",
    response_model=List[DisplayProjectUserHistory],
)
def get_all_project_user_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_project_user_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# Risks
@router.get(
    "/risks/{id}",
    response_model=DisplayRiskHistory,
)
def get_risk_history_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_history.get_risk_history_by_id(db=db, risk_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for risk with specified id does not exist",
        )
    return queryset


@router.get(
    "/risks/project/{project_id}",
    response_model=List[DisplayRiskHistory],
)
def get_all_risk_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_risk_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# WBS
@router.get(
    "/wbs/{id}",
    response_model=DisplayWBSHistory,
)
def get_wbs_history_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_history.get_wbs_history_by_id(db=db, wbs_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for wbs with specified id does not exist",
        )
    return queryset


@router.get(
    "/wbs/project/{project_id}",
    response_model=List[DisplayWBSHistory],
)
def get_all_wbs_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_wbs_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# WorkflowFlowchart
@router.get(
    "/workflow_flowchart/{id}",
    response_model=DisplayWorkflowFlowchartHistory,
)
def get_workflow_flowchart_history_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_history.get_workflow_flowchart_history_by_id(db=db, workflow_flowchart=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for workflow_flowchart with specified id does not exist",
        )
    return queryset


@router.get(
    "/workflow_flowchart/project/{project_id}",
    response_model=List[DisplayWorkflowFlowchartHistory],
)
def get_all_workflow_flowchart_history_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_all_workflow_flowchart_history_by_project_id(
        db=db,
        project_id=project_id,
    )
    return queryset


# ApprovalWorkflow
@router.get(
    "/approval_workflows/{id}",
    response_model=List[DisplayApprovalWorkflowHistory],
)
def get_approval_workflow_history_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_history.get_approval_workflow_history_by_id(db=db, approval_workflow_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="History for approval workflow with specified id does not exist",
        )
    return queryset


# User watching endpoints
# POST for when a user elects to watch something
@router.post(
    "/user_watching",
    # response_model=DisplayUserWatching,
    # dependencies=[Depends(create_project_group_permission)]
)
def create_user_watching(
    request: CreateUserWatching, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    user_watching = db_history.create_user_watching(request, db)
    return user_watching


# GET to retrieve all content the user is watching for a project
@router.get(
    "/user_watching/{project_id}",
    # response_model=DisplayUserWatching,
)
def get_user_watching_by_project_id(
    project_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_history.get_user_watching_by_project_id(
        db=db,
        project_id=project_id,
    )
    # get all projects the user is watching
    return queryset


# helper function to flatten a list
def flatten(something):
    if isinstance(something, (list, tuple, set, range)):
        for sub in something:
            yield from flatten(sub)
    else:
        yield something


# helper function to help with adding project and user values to list for return
def return_list_with_proj_author(notifications, project_id, db, user):
    new_notifications = []
    for notification in notifications:
        cur_user = db_user.get_user_by_id(db, getattr(notification, "author_id"), user["tenant_id"])
        cur_project = db_project.get_project(db, project_id, user["tenant_id"], user["user_id"])
        new_object = {
            "id": getattr(notification, "id"),
            "history": getattr(notification, "history"),
            "updated": getattr(notification, "updated"),
            "project": {
                "id": getattr(cur_project, "id"),
                "name": getattr(cur_project, "name"),
            },
            "author": {
                "id": getattr(cur_user, "id"),
                "email": getattr(cur_user, "email"),
            },
        }
        new_notifications.append(new_object)
    return new_notifications


# GET to retrieve all content the user is watching for a project
@router.get(
    "/user_watching/all/{user_id}",
    # response_model=DisplayUserWatching,
)
def get_all_user_watching_by_user_id(
    user_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    projects = db_history.get_all_projects_user_is_watching(db=db, user_id=user["user_id"])
    all_notifications = []
    for project in projects:
        if project.project_assessments == True:
            assessment_history = get_all_assessment_history_by_project_id(
                project.project_id, db, user
            )
            # with_project = return_list_with_proj_author(assessment_history, cur_project, db, user)
            all_notifications.append(assessment_history)
        if project.project_audit_tests == True:
            audit_test_history = get_all_audit_test_history_by_project_id(
                project.project_id, db, user
            )
            # with_project = return_list_with_proj_author(audit_test_history, cur_project, db, user)
            all_notifications.append(audit_test_history)
        if project.project_documents == True:
            document_notifications = get_all_document_history_by_project_id(
                project.project_id, db, user
            )
            # with_project = return_list_with_proj_author(
            #     document_notifications, cur_project, db, user
            # )
            all_notifications.append(document_notifications)
        if project.project_controls == True:
            pc_notifications = get_all_project_control_history_by_project_id(
                project.project_id, db, user
            )
            # with_project = return_list_with_proj_author(pc_notifications, cur_project, db, user)
            all_notifications.append(pc_notifications)
        if project.project_evaluations == True:
            pe_notifications = get_all_project_evaluation_history_by_project_id(
                project.project_id, db, user
            )
            # with_project = return_list_with_proj_author(pe_notifications, cur_project, db, user)
            all_notifications.append(pe_notifications)
        if project.project_overview == True:
            project_notifications = get_all_project_history_by_project_id(
                project.project_id, db, user
            )
            with_project = return_list_with_proj_author(
                project_notifications, project.project_id, db, user
            )
            all_notifications.append(with_project)
        if project.project_tasks == True:
            pt_notifications = get_all_task_history_by_project_id(project.project_id, db, user)
            # with_project = return_list_with_proj_author(pt_notifications, cur_project, db, user)
            all_notifications.append(pt_notifications)
        if project.project_users == True:
            pu_notifications = get_all_project_user_history_by_project_id(
                project.project_id, db, user
            )
            # with_project = return_list_with_proj_author(pu_notifications, cur_project, db, user)
            all_notifications.append(pu_notifications)
        if project.project_risks == True:
            pr_notifications = get_all_risk_history_by_project_id(project.project_id, db, user)
            # with_project = return_list_with_proj_author(pr_notifications, cur_project, db, user)
            all_notifications.append(pr_notifications)
        if project.project_wbs == True:
            wbs_notifications = get_all_wbs_history_by_project_id(project.project_id, db, user)
            # with_project = return_list_with_proj_author(wbs_notifications, cur_project, db, user)
            all_notifications.append(wbs_notifications)
    # flatten notifications
    flattened_notifications = flatten(all_notifications)
    return flattened_notifications


# PUT to update what content types on a project a user is watching
@router.put("/user_watching/project/{project_id}")
def update_user_watching_by_project_id(
    project_id: int,
    request: UpdateUserWatching,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    updated_user_watching = db_history.update_user_watching_by_project_id(
        db=db, project_id=project_id, request=request
    )
    if not updated_user_watching:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User watching with id {id} does not exist",
        )
    return updated_user_watching
