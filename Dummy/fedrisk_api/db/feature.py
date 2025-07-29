import logging

from sqlalchemy.orm import Session

from fedrisk_api.db.models import Feature, FeatureProject
from fedrisk_api.schema.feature import (
    CreateFeature,
    UpdateFeature,
    CreateFeatureProject,
    UpdateFeatureProject,
)
from fedrisk_api.utils.utils import filter_by_tenant

LOGGER = logging.getLogger(__name__)


# Feature
def create_feature(db: Session, feature: CreateFeature, tenant_id: int):
    my_new_feature_dict = feature.dict()
    feature = Feature(**my_new_feature_dict, tenant_id=tenant_id)
    db.add(feature)
    db.commit()
    return feature


def get_feature(
    db: Session,
    tenant_id: int,
):
    queryset = filter_by_tenant(db=db, model=Feature, tenant_id=tenant_id).all()
    return queryset


def get_feature_by_id(db: Session, feature_id: int):
    queryset = db.query(Feature).filter(Feature.id == feature_id).first()
    return queryset


def update_feature_by_id(feature: UpdateFeature, db: Session, feature_id: int, tenant_id: int):
    queryset = filter_by_tenant(db=db, model=Feature, tenant_id=tenant_id).filter(
        Feature.id == feature_id
    )

    if not queryset.first():
        return False

    queryset.update(feature.dict(exclude_unset=True))
    db.commit()
    return True


def delete_feature_by_id(db: Session, tenant_id: int, feature_id: int):
    feature = db.query(Feature).filter(Feature.id == feature_id).first()

    if not feature:
        return False

    db.delete(feature)
    db.commit()
    return True


# FeatureProject
def create_feature_project(feature_project: CreateFeatureProject, db: Session):
    feature_proj = FeatureProject(**feature_project.dict())
    db.add(feature_proj)
    db.commit()
    return feature_proj


def get_features_for_project(db: Session, project_id: int):
    # Outer join so we get all features, even if no FeatureProject entry
    features = (
        db.query(
            Feature.id,
            Feature.name,
            Feature.is_active.label("global_active"),
            FeatureProject.is_active.label("project_active"),
            FeatureProject.id.label("feature_project_id"),
            FeatureProject.project_id.label("project_id"),
        )
        .outerjoin(
            FeatureProject,
            (Feature.id == FeatureProject.feature_id) & (FeatureProject.project_id == project_id),
        )
        .filter(Feature.is_active == True)
        .all()
    )

    return [
        {
            "id": f.id,
            "name": f.name,
            "global_active": f.global_active,
            "project_active": f.project_active if f.project_active is not None else False,
            "feature_project_id": f.feature_project_id,  # ✅ add this so frontend can decide between PUT/POST
            "project_id": f.project_id,
        }
        for f in features
    ]


def update_feature_project(
    db: Session, project_id: int, feature_id: int, feature_project: UpdateFeatureProject
):
    queryset = db.query(FeatureProject).filter(
        FeatureProject.project_id == project_id, FeatureProject.feature_id == feature_id
    )
    if not queryset.first():
        return False

    queryset.update(feature_project.dict(exclude_unset=True))
    db.commit()
    return True


def delete_feature_project_by_id(db: Session, id: int):
    feature_project = db.query(FeatureProject).filter(Feature.id == id).first()

    if not feature_project:
        return False

    db.delete(feature_project)
    db.commit()
    return True
