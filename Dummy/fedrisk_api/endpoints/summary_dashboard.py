import math

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from fedrisk_api.db import summary_dashboard as db_summary_dashboard
from fedrisk_api.db.database import get_db
from fedrisk_api.db.models import (
    Control,
    Project,
    ProjectControl,
    ProjectUser,
    Risk,
    User,
)
from fedrisk_api.schema.summary_dashboard import (
    DisplayGovernance,
    FinalCompilanceDisplay,
    FinalDisplayRiskItems,
    FinalDisplayTask,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    view_compliance_permission,
    view_governanceprojects_permission,
    view_projecttasks_permission,
    view_riskitems_permission,
)
from fedrisk_api.utils.utils import filter_by_tenant

router = APIRouter(prefix="/summary_dashboards", tags=["summary_dashboards"])


@router.get(
    "/governance/",
    response_model=DisplayGovernance,
    dependencies=[Depends(view_governanceprojects_permission)],
)
def get_governance_projects(
    offset: int = 0,
    limit: int = 100,
    sort_by: str = "name",
    order_type: str = "desc",
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    final_response = {}
    response = []
    user_obj = db.query(User).filter(User.id == user["user_id"]).first()

    if user_obj.is_superuser:
        total = db.query(Project).count()
    elif user_obj.is_tenant_admin:
        total = filter_by_tenant(db, Project, user["tenant_id"]).count()
    else:
        total = (
            filter_by_tenant(db, Project, user["tenant_id"])
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .filter(ProjectUser.user_id == user["user_id"])
            .distinct()
            .count()
        )

    gov_projects = db_summary_dashboard.get_governance_projects(
        db, offset, limit, sort_by, order_type, user["tenant_id"], user["user_id"]
    )
    for project in gov_projects:
        total_risks = len(project.risks)
        total_audit_test = len(project.audit_tests)
        total_project_controls = len(project.project_controls)
        response.append(
            {
                "id": project.id,
                "name": project.name,
                "project_controls": project.project_controls,
                "total_project_controls": total_project_controls,
                "total_risks": total_risks,
                "total_audit_test": total_audit_test,
            }
        )

    final_response.update({"items": response, "total": len(response)})

    return final_response


@router.get(
    "/risk_items/",
    response_model=FinalDisplayRiskItems,
    dependencies=[Depends(view_riskitems_permission)],
)
def get_risk_items(
    offset: int = 0,
    limit: int = 100,
    sort_by: str = "name",
    order_type: str = "desc",
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    final_response = {}
    response = []
    total_risk_score = 0
    user_obj = db.query(User).filter(User.id == user["user_id"]).first()

    if user_obj.is_superuser:
        total = db.query(Project).count()
    elif user_obj.is_tenant_admin:
        total = filter_by_tenant(db, Project, user["tenant_id"]).count()
    else:
        total = (
            filter_by_tenant(db, Project, user["tenant_id"])
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .filter(ProjectUser.user_id == user["user_id"])
            .distinct()
            .count()
        )

    risk_items = db_summary_dashboard.get_risk_items(
        db, offset, limit, sort_by, order_type, user["tenant_id"], user["user_id"]
    )
    for project in risk_items:
        if project.risks:
            total_risks = len(project.risks)
            for risk in project.risks:
                total_risk_score += int(risk.risk_score.name)
            final_risk_score = int(total_risk_score) / total_risks
            total_risk_score = 0
        else:
            total_risks = 0
            final_risk_score = 0

        response.append(
            {
                "id": project.id,
                "name": project.name,
                "project_controls": project.project_controls,
                "total_risks": total_risks,
                "risk_score": final_risk_score,
            }
        )
    final_response.update({"items": response, "total": len(response)})

    return final_response


@router.get(
    "/compliance/",
    response_model=FinalCompilanceDisplay,
    dependencies=[Depends(view_compliance_permission)],
)
def get_compliance(
    offset: int = 0,
    limit: int = 100,
    sort_by: str = "name",
    order_type: str = "desc",
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    final_response = {}
    response = []

    user_obj = db.query(User).filter(User.id == user["user_id"]).first()

    if user_obj.is_superuser:
        total = db.query(Project).count()
    elif user_obj.is_tenant_admin:
        total = filter_by_tenant(db, Project, user["tenant_id"]).count()
    else:
        total = (
            filter_by_tenant(db, Project, user["tenant_id"])
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .filter(ProjectUser.user_id == user["user_id"])
            .distinct()
            .count()
        )

    compliance = db_summary_dashboard.get_compliance(
        db, offset, limit, sort_by, order_type, user["tenant_id"], user["user_id"]
    )
    for project in compliance:
        response.append(
            {
                "id": project.id,
                "name": project.name,
                "project_controls": project.project_controls,
                "audit_test_count": len(project.audit_tests),
            }
        )

    final_response.update({"items": response, "total": len(response)})
    return final_response


@router.get(
    "/tasks/", response_model=FinalDisplayTask, dependencies=[Depends(view_projecttasks_permission)]
)
def get_project_tasks(
    offset: int = 0,
    limit: int = 100,
    sort_by: str = "name",
    order_type: str = "desc",
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    final_response = {}
    response = []

    user_obj = db.query(User).filter(User.id == user["user_id"]).first()

    if user_obj.is_superuser:
        total = db.query(Project).count()
    elif user_obj.is_tenant_admin:
        total = filter_by_tenant(db, Project, user["tenant_id"]).count()
    else:
        total = (
            filter_by_tenant(db, Project, user["tenant_id"])
            .join(ProjectUser, ProjectUser.project_id == Project.id)
            .filter(ProjectUser.user_id == user["user_id"])
            .distinct()
            .count()
        )

    project_tasks = db_summary_dashboard.get_projects_tasks(
        db, offset, limit, sort_by, order_type, user["tenant_id"], user["user_id"]
    )
    for project in project_tasks:
        response.append(
            {
                "id": project.id,
                "name": project.name,
                "project_controls": project.project_controls,
                "total_tasks": 0,
            }
        )

    final_response.update({"items": response, "total": len(response)})

    return final_response


@router.get("/{project_id}")
def get_summary_chart_data_by_project(
    project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    chart_data = db_summary_dashboard.get_summary_chart_data_by_project(
        db=db, project_id=project_id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not chart_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with {project_id} do not exist",
        )
    return chart_data
