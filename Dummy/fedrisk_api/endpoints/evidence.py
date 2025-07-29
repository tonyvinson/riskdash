import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import evidence as db_evidence
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.evidence import (
    CreateEvidence,
    DisplayEvidence,
    UpdateEvidence,
    CreateProjectControlEvidence,
    CheckProjectControlOwner,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_evidence_permission,
    delete_evidence_permission,
    update_evidence_permission,
    view_evidence_permission,
)

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post(
    "/",
    response_model=DisplayEvidence,
    dependencies=[Depends(create_evidence_permission)],
)
def create_evidence(
    request: CreateEvidence, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        evidence = db_evidence.create_evidence(evidence=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Evidence Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return evidence


@router.get(
    "/{project_control_id}/all",
    response_model=List[DisplayEvidence],
    dependencies=[Depends(view_evidence_permission)],
)
def get_all_evidences(
    project_control_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_evidence.get_all_evidence_by_project_control_id(
        db=db,
        project_control_id=project_control_id,
    )
    return queryset


@router.get(
    "/{id}",
    response_model=DisplayEvidence,
    dependencies=[Depends(view_evidence_permission)],
)
def get_evidence_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_evidence.get_evidence_by_id(db=db, evidence_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence with specified id does not exist",
        )
    return queryset


@router.put("/{id}", dependencies=[Depends(update_evidence_permission)])
def update_evidence_by_id(
    request: UpdateEvidence,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_evidence.update_evidence_by_id(evidence=request, db=db, evidence_id=id)
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Evidence with specified id does not exist",
            )
        return {"detail": "Successfully updated Evidence."}
    except IntegrityError as ie:
        LOGGER.exception("Get Evidence Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.delete("/{id}", dependencies=[Depends(delete_evidence_permission)])
def delete_evidence_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_evidence.delete_evidence_by_id(db=db, evidence_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence with specified id does not exist",
        )
    return {"detail": "Successfully deleted Evidence."}


@router.post(
    "/project_control_evidence",
    response_model=DisplayEvidence,
    dependencies=[Depends(create_evidence_permission)],
)
def create_project_control_evidence(
    request: CreateProjectControlEvidence, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        evidence = db_evidence.create_project_control_evidence(pc_evidence=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Project Control Evidence Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return evidence


@router.put("/verify_project_control_owner/", dependencies=[Depends(update_evidence_permission)])
def verify_project_control_owner(
    request: CheckProjectControlOwner,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        response = db_evidence.check_project_control_owner(check=request, db=db)
        LOGGER.info(f"response {response}")
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="This project control is not owned by this tenant",
            )
        return {"detail": "Successfully verified owner of project control."}
    except IntegrityError as ie:
        LOGGER.exception("Verify owner of project control Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


@router.get("/project/{project_id}")
async def get_evidence_by_project_id(project_id: int, db: Session = Depends(get_db)):
    queryset = await db_evidence.get_evidence_by_project_id(db=db, project_id=project_id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence for project with specified id does not exist",
        )
    return queryset


@router.get("/app/{app_id}")
async def get_evidence_by_app_id(app_id: int, db: Session = Depends(get_db)):
    queryset = await db_evidence.get_evidence_by_app_id(db=db, app_id=app_id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Evidence for app with specified id does not exist",
        )
    return queryset


@router.get("/audit_evidence/{audit_evidence_id}")
async def get_evidence_by_audit_evidence_id(audit_evidence_id: int, db: Session = Depends(get_db)):
    queryset = await db_evidence.get_evidence_by_audit_evidence_id(
        db=db, audit_evidence_id=audit_evidence_id
    )
    if not queryset:
        return {"evidence": [], "message": "No evidence found."}
        # raise HTTPException(
        #     status_code=status.HTTP_404_NOT_FOUND,
        #     detail="Evidence for app and service provider with specified id does not exist",
        # )
    return queryset
