from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from fedrisk_api.db.dashboard import get_project
from fedrisk_api.db.database import get_db
from fedrisk_api.db.models import (
    Risk,
    RiskCategory,
    RiskImpact,
    RiskLikelihood,
    RiskScore,
    RiskStatus,
)
from fedrisk_api.schema.risk_dashboard import DisplayRiskDashboardMetrics
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import view_risk_dashboard
from fedrisk_api.utils.utils import get_risk_mapping_metrics

router = APIRouter(prefix="/dashboards", tags=["dashboards"])

risk_mapping_metrics = get_risk_mapping_metrics()

RISK_ATTRIBUTES = {
    "risk_score": {"10", "5", "1"},
    "risk_status": {"Active", "On Hold", "Completed", "Cancelled"},
    "risk_category": {
        "Access Management",
        "Environmental Resilience",
        "Monitoring",
        "Physical Security",
        "Policy & Procedure",
        "Sensitive Data Management",
        "Technical Vulnerability",
        "Third Party Management",
    },
    "risk_impact": {"Insignificant", "Minor", "Moderate", "Major", "Extreme"},
    "risk_likelihood": {"Very Likely", "Likely", "Possible", "Unlikely", "Very Unlikely"},
}


@router.get(
    "/risk/metrics/",
    response_model=DisplayRiskDashboardMetrics,
    dependencies=[Depends(view_risk_dashboard)],
)
def get_risk_metrics(
    project_id: int = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    project = get_project(db, project_id=project_id, user=user)
    if not project:
        return DisplayRiskDashboardMetrics(
            project_name="",
            project_id=-1,
            risk_status=[],
            risk_category=[],
            risk_score=[],
            risk_impact=[],
            risk_likelihood=[],
            risk_mapping=[],
        )

    project_risk = db.query(Risk).filter(Risk.project_id == project.id).distinct().all()

    all_risks_ids = {risk.id for risk in project_risk}

    risk_status = (
        db.query(
            RiskStatus.name,
            func.count("*").label("count"),
        )
        .select_from(Risk)
        .join(RiskStatus, RiskStatus.id == Risk.risk_status_id)
        .filter(Risk.id.in_(all_risks_ids))
        .group_by(RiskStatus.name)
        .all()
    )

    risk_category = (
        db.query(
            RiskCategory.name,
            func.count("*").label("count"),
        )
        .select_from(Risk)
        .join(RiskCategory, RiskCategory.id == Risk.risk_category_id)
        .filter(Risk.id.in_(all_risks_ids))
        .group_by(RiskCategory.name)
        .all()
    )

    risk_score = (
        db.query(
            RiskScore.name,
            func.count("*").label("count"),
        )
        .select_from(Risk)
        .join(RiskScore, RiskScore.id == Risk.risk_score_id)
        .filter(Risk.id.in_(all_risks_ids))
        .group_by(RiskScore.name)
        .all()
    )

    risk_impact = (
        db.query(RiskImpact.name, func.count("*").label("count"))
        .select_from(Risk)
        .join(RiskImpact, RiskImpact.id == Risk.risk_impact_id)
        .filter(Risk.id.in_(all_risks_ids))
        .group_by(RiskImpact.name)
        .all()
    )

    risk_likelihood = (
        db.query(
            RiskLikelihood.name,
            func.count("*").label("count"),
        )
        .select_from(Risk)
        .join(RiskLikelihood, RiskLikelihood.id == Risk.current_likelihood_id)
        .filter(Risk.id.in_(all_risks_ids))
        .group_by(RiskLikelihood.name)
        .all()
    )

    default_mapping = [
        (risk_status, RISK_ATTRIBUTES["risk_status"].copy()),
        (risk_category, RISK_ATTRIBUTES["risk_category"].copy()),
        (risk_score, RISK_ATTRIBUTES["risk_score"].copy()),
        (risk_impact, RISK_ATTRIBUTES["risk_impact"].copy()),
        (risk_likelihood, RISK_ATTRIBUTES["risk_likelihood"].copy()),
    ]

    for risk_attr_value in default_mapping:
        missing_values = risk_attr_value[1] - {obj.name for obj in risk_attr_value[0]}
        for missing_value in missing_values:
            risk_attr_value[0].append({"name": missing_value, "count": 0})

    risks = (
        db.query(
            RiskLikelihood.name.label("current_likelihood"), RiskImpact.name.label("risk_impact")
        )
        .select_from(Risk)
        .join(RiskLikelihood, RiskLikelihood.id == Risk.current_likelihood_id)
        .join(RiskImpact, RiskImpact.id == Risk.risk_impact_id)
        .filter(Risk.id.in_(all_risks_ids))
        .all()
    )

    low_count = 0
    low_medium_count = 0
    medium_count = 0
    medium_high_count = 0
    high_count = 0
    for risk in risks:
        current_likelihood_name = "_".join(risk.current_likelihood.split(" "))
        risk_matrics_key = f"{current_likelihood_name}__{risk.risk_impact}".lower()
        for key, value in risk_mapping_metrics.items():
            for risk_matrics in set(value):
                if risk_matrics_key == risk_matrics:
                    if key == "low":
                        low_count += 1
                    elif key == "low_medium":
                        low_medium_count += 1
                    elif key == "medium":
                        medium_count += 1
                    elif key == "medium_high":
                        medium_high_count += 1
                    elif key == "high":
                        high_count += 1

    risk_mapping = [
        {"name": "Low", "count": low_count},
        {"name": "Low-Medium", "count": low_medium_count},
        {"name": "Medium", "count": medium_count},
        {"name": "Medium-High", "count": medium_high_count},
        {"name": "High", "count": high_count},
    ]

    return DisplayRiskDashboardMetrics(
        project_name=project.name,
        project_id=project.id,
        risk_status=risk_status,
        risk_category=risk_category,
        risk_score=risk_score,
        risk_impact=risk_impact,
        risk_likelihood=risk_likelihood,
        risk_mapping=risk_mapping,
    )
