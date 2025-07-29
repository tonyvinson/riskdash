import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import feature as db_feature
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.feature import (
    CreateFeature,
    DisplayFeature,
    UpdateFeature,
    CreateFeatureProject,
    DisplayFeatureProject,
    UpdateFeatureProject,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_feature_permission,
    delete_feature_permission,
    update_feature_permission,
    view_feature_permission,
    create_feature_project_permission,
    delete_feature_project_permission,
    update_feature_project_permission,
    view_feature_project_permission,
)

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/features", tags=["features"])


@router.post("/", response_model=DisplayFeature, dependencies=[Depends(create_feature_permission)])
def create_feature(
    request: CreateFeature, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        feature = db_feature.create_feature(feature=request, db=db, tenant_id=user["tenant_id"])
    except IntegrityError as ie:
        LOGGER.exception("Create Feature Error. Invalid request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Feature with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)
    return feature


@router.get(
    "/",
    response_model=List[DisplayFeature],
    dependencies=[Depends(view_feature_permission)],
)
def get_all_features(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_feature.get_feature(
        db=db,
        tenant_id=user["tenant_id"],
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplayFeature,
    dependencies=[Depends(view_feature_permission)],
)
def get_feature_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_feature.get_feature_by_id(db=db, feature_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature with specified id does not exist",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_feature_permission)])
def update_feature_by_id(
    request: UpdateFeature, id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        queryset = db_feature.update_feature_by_id(
            feature=request, db=db, feature_id=id, tenant_id=user["tenant_id"]
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feature with specified id does not exist",
            )
        return {"detail": "Successfully updated Feature."}
    except IntegrityError as ie:
        LOGGER.exception("Get Feature Error - Invalid request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Feature with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_feature_permission)])
def delete_feature_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_feature.delete_feature_by_id(db=db, tenant_id=user["tenant_id"], feature_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature with specified id does not exists",
        )
    return {"detail": "Successfully deleted Feature."}


# FeatureProject
@router.post(
    "/feature_project",
    response_model=DisplayFeatureProject,
    dependencies=[Depends(create_feature_project_permission)],
)
def create_feature_project(
    request: CreateFeatureProject, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        feature_project = db_feature.create_feature_project(feature_project=request, db=db)
    except IntegrityError:
        LOGGER.exception("Create Feature Project Error. Invalid request")
    return feature_project


@router.get(
    "/feature_project/{project_id}",
    response_model=List,
    dependencies=[Depends(view_feature_project_permission)],
)
def get_feature_project_by_id(
    project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_feature.get_features_for_project(db=db, project_id=project_id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature Project with specified id does not exist",
        )
    return queryset


@router.put(
    "/feature_project/{project_id}/{feature_id}",
    dependencies=[Depends(update_feature_project_permission)],
)
def update_feature_project(
    project_id: int,
    feature_id: int,
    request: UpdateFeatureProject,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        updated = db_feature.update_feature_project(
            db=db, project_id=project_id, feature_id=feature_id, feature_project=request
        )
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="FeatureProject association does not exist",
            )
        return {"detail": "Successfully updated FeatureProject."}
    except IntegrityError as ie:
        LOGGER.exception("Update FeatureProject error")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = "FeatureProject already exists"
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/feature_project/{id}", dependencies=[Depends(delete_feature_project_permission)])
def delete_feature_project_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_feature.delete_feature_project_by_id(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feature Project with specified id does not exist",
        )
    return {"detail": "Successfully deleted Feature Project."}
