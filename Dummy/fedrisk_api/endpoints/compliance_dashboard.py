from typing import Dict

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fedrisk_api.db.compliance_dashboard import (
    get_compliance_dashboard_metrics,
    get_compliance_dashboard_metrics_cap_poam,
    get_compliance_audit_test_by_month_for_year,
)
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.compliance_dashboard import (
    DisplayComplianceMetrics,
    DisplayComplianceMetricsCapPoam,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import view_compliance_dashboard

router = APIRouter(prefix="/dashboards/compliance", tags=["dashboards"])


@router.get(
    "/metrics",
    response_model=DisplayComplianceMetrics,
    dependencies=[Depends(view_compliance_dashboard)],
)
def get_compliance_matrics(
    project_id: int = None,
    framework_id: int = None,
    db: Session = Depends(get_db),
    user: Dict = Depends(custom_auth),
):
    response = get_compliance_dashboard_metrics(
        db=db, project_id=project_id, framework_id=framework_id, user=user
    )
    return response


@router.get(
    "/cap_poam/metrics",
    response_model=DisplayComplianceMetricsCapPoam,
    dependencies=[Depends(view_compliance_dashboard)],
)
def get_compliance_metrics_cap_poam(
    project_id: int = None,
    db: Session = Depends(get_db),
    user: Dict = Depends(custom_auth),
):
    response = get_compliance_dashboard_metrics_cap_poam(db=db, project_id=project_id, user=user)
    return response


@router.get(
    "/audit_test_by_month_for_year/metrics",
    dependencies=[Depends(view_compliance_dashboard)],
)
def get_audit_test_by_month_for_year(
    project_id: int = None,
    year: int = None,
    db: Session = Depends(get_db),
    user: Dict = Depends(custom_auth),
):
    response = get_compliance_audit_test_by_month_for_year(db=db, project_id=project_id, year=year)
    return response
