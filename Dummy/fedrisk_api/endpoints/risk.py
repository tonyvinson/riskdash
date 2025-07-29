import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import risk as db_risk
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.risk import CreateRisk, DisplayRisk, UpdateRisk
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    create_risk_permission,
    delete_risk_permission,
    update_risk_permission,
    view_risk_permission,
)
from fedrisk_api.utils.utils import (
    PaginateResponse,
    delete_documents_for_fedrisk_object,
    pagination,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/risks", tags=["risks"])

# Create risk
@router.post("/", response_model=DisplayRisk, dependencies=[Depends(create_risk_permission)])
async def create_risk(
    request: CreateRisk,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        result = await db_risk.create_risk(
            db, request, user["tenant_id"], keywords, user["user_id"]
        )

        if not result:
            if not result:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"tenant with specified id does not have project with id {request.project_id}",
                )

        return result

    except IntegrityError as ie:
        LOGGER.exception("Create Risk Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all risks
@router.get(
    "/", response_model=PaginateResponse[DisplayRisk], dependencies=[Depends(view_risk_permission)]
)
def get_all_risks(
    project_id: int = None,
    q: str = None,
    filter_by: str = None,
    filter_value: str = None,
    sort_by: str = "-created_date",
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_risk.get_all_risks(
            user["tenant_id"], project_id, db, q, filter_by, filter_value, sort_by
        )
        return pagination(query=queryset, limit=limit, offset=offset)
    except DataError as e:
        LOGGER.exception("Get Risk Error - Invalid request")

        if "LIMIT must not be negative" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="LIMIT must not be negative",
            )
        elif "OFFSET must not be negative" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="OFFSET must not be negative",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Please provide correct filter_value"
            )
    except ProgrammingError:
        LOGGER.exception("Get Risk Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct sort_by field value",
        )
    except AttributeError:
        LOGGER.exception("Get Risk Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct filter_by field value",
        )


@router.get("/tasks/", response_model=List[DisplayRisk])
def get_all_risks_with_tasks_by_project(
    project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    risks = db_risk.get_all_risks_with_tasks_by_project(
        db=db, project_id=project_id, tenant_id=user["tenant_id"]
    )
    if not risks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No risks found",
        )

    return risks


# Read one risk
@router.get("/{id}", response_model=DisplayRisk)
def get_risk_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    risk = db_risk.get_risk(db=db, id=id, tenant_id=user["tenant_id"])
    if not risk:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk with id {id} does not exist",
        )

    return risk


# Update risk
@router.put("/{id}", response_model=DisplayRisk, dependencies=[Depends(update_risk_permission)])
async def update_risk_by_id(
    id: int,
    request: UpdateRisk,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        db_status = await db_risk.update_risk(
            db=db,
            id=id,
            risk=request,
            tenant_id=user["tenant_id"],
            keywords=keywords,
            user_id=user["user_id"],
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Risk with id {id} does not exist",
            )

        return db_status
    except IntegrityError as ie:
        LOGGER.exception("Update Risk Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Risk with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete risk
@router.delete("/{id}", dependencies=[Depends(delete_risk_permission)])
async def delete_risk_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    try:
        delete_documents_for_fedrisk_object(db=db, fedrisk_object_id=id, fedrisk_object_type="risk")
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while deleting associated documents",
        )

    db_status = await db_risk.delete_risk(db=db, id=id, tenant_id=user["tenant_id"])
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Risk with id {id} does not exist",
        )
    return {"detail": "Successfully deleted risk."}
