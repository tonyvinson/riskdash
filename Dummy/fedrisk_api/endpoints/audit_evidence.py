import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import audit_evidence as db_audit_evidence
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.audit_evidence import (
    CreateAuditEvidence,
    DisplayAuditEvidence,
    CreateAuditEvidenceReview,
    DisplayAuditEvidenceReview,
    CreateAuditEvidenceFilterApp,
    DisplayAuditEvidenceFilterApp,
    CreateAuditEvidenceFilterServiceProvider,
    DisplayAuditEvidenceFilterServiceProvider,
    CreateAuditEvidenceReviewProjectControl,
    DisplayAuditEvidenceReviewProjectControl,
    CreateAuditEvidenceFilterFramework,
    DisplayAuditEvidenceFilterFramework,
    CreateAuditEvidenceFilterProject,
    DisplayAuditEvidenceFilterProject,
    DisplayAuditEvidenceReviewDigSig,
    DisplayAuditEvidenceReviewProjContDigSig,
    CreateAuditEvidenceReviewDigSig,
    CreateAuditEvidenceReviewProjContDigSig,
    UpdateAuditEvidence,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_audit_evidence_permission,
    delete_audit_evidence_permission,
    update_audit_evidence_permission,
    view_audit_evidence_permission,
)

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/audit_evidence", tags=["audit_evidence"])


############ Audit audit_evidence ############
# POST create new Audit audit_evidence
@router.post(
    "/",
    response_model=DisplayAuditEvidence,
    dependencies=[Depends(create_audit_evidence_permission)],
)
async def create_audit_evidence(
    request: CreateAuditEvidence, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        evidence = await db_audit_evidence.create_audit_evidence(
            evidence=request, db=db, tenant_id=user["tenant_id"]
        )
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Evidence Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return evidence


# PUT update Audit audit_evidence
@router.put("/{id}", dependencies=[Depends(update_audit_evidence_permission)])
def update_audit_evidence_by_id(
    request: UpdateAuditEvidence,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_audit_evidence.update_audit_evidence_by_id(
            evidence=request, db=db, evidence_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Audit Evidence with specified id does not exist",
            )
        return {"detail": "Successfully updated Audit Evidence."}
    except IntegrityError as ie:
        LOGGER.exception("Get Audit Evidence Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET ALL Audit audit_evidence by tenant ID
@router.get(
    "/all",
    response_model=List[DisplayAuditEvidence],
    dependencies=[Depends(view_audit_evidence_permission)],
)
def get_all_audit_evidence(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_audit_evidence.get_all_audit_evidence_by_tenant_id(
        db=db,
        tenant_id=user["tenant_id"],
    )
    return queryset


# GET Audit audit_evidence by ID
@router.get(
    "/{id}",
    response_model=DisplayAuditEvidence,
    dependencies=[Depends(view_audit_evidence_permission)],
)
def get_audit_evidence_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = db_audit_evidence.get_audit_evidence_by_id(db=db, audit_evidence_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence with specified id does not exist",
        )
    return queryset


@router.get(
    "/machine_readable/{id}",
    # response_model=DisplayAuditEvidence,
    dependencies=[Depends(view_audit_evidence_permission)],
)
async def get_audit_evidence_machine_readable_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = await db_audit_evidence.get_audit_evidence_machine_readable_by_id(
        db=db, audit_evidence_id=id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence with specified id does not exist",
        )
    return queryset


# DELETE delete Audit audit_evidence by ID
@router.delete("/{id}", dependencies=[Depends(delete_audit_evidence_permission)])
def delete_audit_evidence_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_audit_evidence.delete_audit_evidence_by_id(db=db, audit_evidence_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence with specified id does not exist",
        )
    return {"detail": "Successfully deleted Audit Evidence."}


############ Audit audit_evidence Review ############
# POST create new Audit audit_evidence Review
@router.post(
    "/review",
    response_model=DisplayAuditEvidenceReview,
    dependencies=[Depends(create_audit_evidence_permission)],
)
async def create_audit_evidence_review(
    request: CreateAuditEvidenceReview, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        evidence = await db_audit_evidence.create_audit_evidence_review(evidence=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Evidence Review Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return evidence


# GET Audit audit_evidence Review by ID
@router.get(
    "/review/{id}",
    response_model=DisplayAuditEvidenceReview,
    dependencies=[Depends(view_audit_evidence_permission)],
)
def get_audit_evidence_review_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_audit_evidence.get_audit_evidence_review_by_id(db=db, audit_evidence_review_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Review with specified id does not exist",
        )
    return queryset


# DELETE delete Audit audit_evidence Review by ID
@router.delete("/review/{id}", dependencies=[Depends(delete_audit_evidence_permission)])
def delete_audit_evidence_review_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_audit_evidence.delete_audit_evidence_review_by_id(
        db=db, audit_evidence_review_id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Review with specified id does not exist",
        )
    return {"detail": "Successfully deleted Audit Evidence Review."}


############ Audit audit_evidence Review Project Control ############
# POST create new Audit audit_evidence Review Project Control
@router.post(
    "/review_project_control",
    response_model=DisplayAuditEvidenceReviewProjectControl,
    dependencies=[Depends(create_audit_evidence_permission)],
)
def create_audit_evidence_review_proj_cont(
    request: CreateAuditEvidenceReviewProjectControl,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        evidence = db_audit_evidence.create_audit_evidence_review_project_control(
            evidence=request, db=db
        )
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Evidence Review Project Control Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return evidence


# GET Audit audit_evidence Review Project Control by ID
@router.get(
    "/review_project_control/{id}",
    response_model=DisplayAuditEvidenceReviewProjectControl,
    dependencies=[Depends(view_audit_evidence_permission)],
)
def get_audit_evidence_review_proj_cont_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_audit_evidence.get_audit_evidence_review_project_control_by_id(
        db=db, audit_evidence_review_project_control_id=id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Review Project Control with specified id does not exist",
        )
    return queryset


# DELETE delete Audit audit_evidence Review Project Control by ID
@router.delete(
    "/review_project_control/{id}", dependencies=[Depends(delete_audit_evidence_permission)]
)
def delete_audit_evidence_review_proj_cont_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_audit_evidence.delete_audit_evidence_review_project_control_by_id(
        db=db, audit_evidence_review_project_control_id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Review Project Control with specified id does not exist",
        )
    return {"detail": "Successfully deleted Audit Evidence Review Project Control."}


############ Audit audit_evidence Filter App ############
# POST create new Audit audit_evidence Filter App
@router.post(
    "/filter_app",
    response_model=DisplayAuditEvidenceFilterApp,
    dependencies=[Depends(create_audit_evidence_permission)],
)
def create_audit_evidence_filter_app(
    request: CreateAuditEvidenceFilterApp, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        evidence = db_audit_evidence.create_audit_evidence_filter_app(evidence=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Evidence Filter App Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return evidence


# GET Audit audit_evidence Filter App by ID
@router.get(
    "/filter_app/{id}",
    response_model=DisplayAuditEvidenceFilterApp,
    dependencies=[Depends(view_audit_evidence_permission)],
)
def get_audit_evidence_filter_app_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_audit_evidence.get_audit_evidence_filter_app_by_id(
        db=db, audit_evidence_filter_app_id=id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Filter App with specified id does not exist",
        )
    return queryset


# DELETE delete Audit audit_evidence Filter App by ID
@router.delete("/filter_app/{id}", dependencies=[Depends(delete_audit_evidence_permission)])
def delete_audit_evidence_filter_app_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_audit_evidence.delete_audit_evidence_filter_app_by_id(
        db=db, audit_evidence_filter_app_id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Filter App with specified id does not exist",
        )
    return {"detail": "Successfully deleted Audit Evidence Filter App."}


############ Audit audit_evidence Filter Service Provider ############
# POST create new Audit audit_evidence Filter Service Provider
@router.post(
    "/filter_service_provider",
    response_model=DisplayAuditEvidenceFilterServiceProvider,
    dependencies=[Depends(create_audit_evidence_permission)],
)
def create_audit_evidence_filter_sp(
    request: CreateAuditEvidenceFilterServiceProvider,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        evidence = db_audit_evidence.create_audit_evidence_filter_sp(evidence=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Evidence Filter Service Provider Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return evidence


# GET Audit audit_evidence Filter Service Provider by ID
@router.get(
    "/filter_service_provider/{id}",
    response_model=DisplayAuditEvidenceFilterServiceProvider,
    dependencies=[Depends(view_audit_evidence_permission)],
)
def get_audit_evidence_filter_sp_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_audit_evidence.get_audit_evidence_filter_sp_by_id(
        db=db, audit_evidence_filter_sp_id=id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Filter Service Provider with specified id does not exist",
        )
    return queryset


# DELETE delete Audit audit_evidence Filter Service Provider by ID
@router.delete(
    "/filter_service_provider/{id}", dependencies=[Depends(delete_audit_evidence_permission)]
)
def delete_audit_evidence_filter_sp_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_audit_evidence.delete_audit_evidence_filter_sp_by_id(
        db=db, audit_evidence_filter_sp_id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Filter Service Provider with specified id does not exist",
        )
    return {"detail": "Successfully deleted Audit Evidence Filter Service Provider."}


############ Audit audit_evidence Filter Project ############
# POST create new Audit audit_evidence Filter Project
@router.post(
    "/filter_project",
    response_model=DisplayAuditEvidenceFilterProject,
    dependencies=[Depends(create_audit_evidence_permission)],
)
def create_audit_evidence_filter_project(
    request: CreateAuditEvidenceFilterProject,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        evidence = db_audit_evidence.create_audit_evidence_filter_project(evidence=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Evidence Filter Project Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return evidence


# GET Audit audit_evidence Filter Project by ID
@router.get(
    "/filter_project/{id}",
    response_model=DisplayAuditEvidenceFilterProject,
    dependencies=[Depends(view_audit_evidence_permission)],
)
def get_audit_evidence_filter_project_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_audit_evidence.get_audit_evidence_filter_project_by_id(
        db=db, audit_evidence_filter_pr_id=id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Filter Project with specified id does not exist",
        )
    return queryset


# DELETE delete Audit audit_evidence Filter Project by ID
@router.delete("/filter_project/{id}", dependencies=[Depends(delete_audit_evidence_permission)])
def delete_audit_evidence_filter_project_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_audit_evidence.delete_audit_evidence_filter_project_by_id(
        db=db, audit_evidence_filter_pr_id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Filter Project with specified id does not exist",
        )
    return {"detail": "Successfully deleted Audit Evidence Filter Project."}


############ Audit audit_evidence Filter Framework ############
# POST create new Audit audit_evidence Filter Framework
@router.post(
    "/filter_framework",
    response_model=DisplayAuditEvidenceFilterFramework,
    dependencies=[Depends(create_audit_evidence_permission)],
)
def create_audit_evidence_filter_framework(
    request: CreateAuditEvidenceFilterFramework,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        evidence = db_audit_evidence.create_audit_evidence_filter_framework(evidence=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Evidence Filter Framework Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return evidence


# GET Audit audit_evidence Filter Framework by ID
@router.get(
    "/filter_framework/{id}",
    response_model=DisplayAuditEvidenceFilterFramework,
    dependencies=[Depends(view_audit_evidence_permission)],
)
def get_audit_evidence_filter_framework_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_audit_evidence.get_audit_evidence_filter_framework_by_id(
        db=db, audit_evidence_filter_fr_id=id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Filter Framework with specified id does not exist",
        )
    return queryset


# DELETE delete Audit audit_evidence Filter Framework by ID
@router.delete("/filter_framework/{id}", dependencies=[Depends(delete_audit_evidence_permission)])
def delete_audit_evidence_filter_framework_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_audit_evidence.delete_audit_evidence_filter_framework_by_id(
        db=db, audit_evidence_filter_fr_id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Filter Framework with specified id does not exist",
        )
    return {"detail": "Successfully deleted Audit Evidence Filter Framework."}


############ Audit Evidence Review Digital Signature ############
# POST create new Audit Evidence Review Digital Signature
@router.post(
    "/audit_evidence_review_dig_sig",
    response_model=DisplayAuditEvidenceReviewDigSig,
    dependencies=[Depends(create_audit_evidence_permission)],
)
def create_audit_evidence_review_dig_sig(
    request: CreateAuditEvidenceReviewDigSig,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        evidence = db_audit_evidence.create_audit_evidence_review_dig_sig(evidence=request, db=db)
    except IntegrityError as ie:
        LOGGER.exception("Create Audit Evidence Review Digital Signature Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return evidence


# GET Audit Evidence Review Digital Signature by review ID
@router.get(
    "/audit_evidence_review_dig_sig/{audit_evidence_review_id}",
    response_model=DisplayAuditEvidenceReviewDigSig,
    dependencies=[Depends(view_audit_evidence_permission)],
)
def get_audit_evidence_review_dig_sig_by_id(
    audit_evidence_review_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_audit_evidence.get_audit_evidence_review_dig_sig_by_id(
        db=db, audit_evidence_review_id=audit_evidence_review_id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Review Digital Signature with specified id does not exist",
        )
    return queryset


# DELETE Audit Evidence Review Digital Signature by ID
@router.delete(
    "/audit_evidence_review_dig_sig/{id}",
    dependencies=[Depends(delete_audit_evidence_permission)],
)
def delete_audit_evidence_review_dig_sig_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_audit_evidence.delete_audit_evidence_review_dig_sig_by_id(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Review Digital Signature with specified id does not exist",
        )
    return {"detail": "Successfully deleted Audit Evidence Review Digital Signature."}


############ Audit Evidence Review Project Control Digital Signature ############
# POST create new Audit Evidence Review Project Control Digital Signature
@router.post(
    "/audit_evidence_review_pc_dig_sig",
    response_model=DisplayAuditEvidenceReviewProjContDigSig,
    dependencies=[Depends(create_audit_evidence_permission)],
)
def create_audit_evidence_review_pc_dig_sig(
    request: CreateAuditEvidenceReviewProjContDigSig,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        evidence = db_audit_evidence.create_audit_evidence_review_proj_cont_dig_sig(
            evidence=request, db=db
        )
    except IntegrityError as ie:
        LOGGER.exception(
            "Create Audit Evidence Review Project Control Digital Signature Error. Invalid request"
        )
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return evidence


# GET Audit Evidence Review Project Control Digital Signature by review ID
@router.get(
    "/audit_evidence_review_pc_dig_sig/{project_control_id}",
    response_model=DisplayAuditEvidenceReviewProjContDigSig,
    dependencies=[Depends(view_audit_evidence_permission)],
)
def get_audit_evidence_review_pc_dig_sig_by_id(
    project_control_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = db_audit_evidence.get_audit_evidence_review_proj_cont_dig_sig_by_id(
        db=db, project_control_id=project_control_id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Review Project Control Digital Signature with specified id does not exist",
        )
    return queryset


# DELETE Audit Evidence Review Digital Signature by ID
@router.delete(
    "/audit_evidence_review_pc_dig_sig/{id}",
    dependencies=[Depends(delete_audit_evidence_permission)],
)
def delete_audit_evidence_review_pc_dig_sig_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = db_audit_evidence.delete_audit_evidence_review_proj_cont_dig_sig_by_id(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Audit Evidence Review Project Control Digital Signature with specified id does not exist",
        )
    return {
        "detail": "Successfully deleted Audit Evidence Review Project Control Digital Signature."
    }
