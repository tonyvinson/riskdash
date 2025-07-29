from typing import List

from pydantic import BaseModel


class DisplayRiskStatusMetrics(BaseModel):
    name: str
    count: int


class DisplayRiskCategoryMetrics(BaseModel):
    name: str
    count: int


class DisplayRiskScoreMetrics(BaseModel):
    name: str
    count: int


class DisplayRiskImpactMetrics(BaseModel):
    name: str
    count: int


class DisplayRiskMappingMetrics(BaseModel):
    name: str
    count: int


class DisplayRiskLikelihoodMetrics(BaseModel):
    name: str
    count: int


class DisplayRiskDashboardMetrics(BaseModel):
    project_name: str
    project_id: int
    risk_status: List[DisplayRiskStatusMetrics]
    risk_category: List[DisplayRiskCategoryMetrics]
    risk_score: List[DisplayRiskScoreMetrics]
    risk_impact: List[DisplayRiskImpactMetrics]
    risk_likelihood: List[DisplayRiskLikelihoodMetrics]
    risk_mapping: List[DisplayRiskMappingMetrics]
