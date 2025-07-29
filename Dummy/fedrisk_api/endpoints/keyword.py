import logging

from fastapi import APIRouter, Depends, HTTPException, status

# from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session
from typing import List

from fedrisk_api.db import keyword as db_keyword
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.keyword import CreateKeyword, DisplayKeyword, UpdateKeyword
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    create_wbs_permission,
    delete_wbs_permission,
    update_wbs_permission,
    view_wbs_permission,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/keyword", tags=["keyword"])

# Create wbs
@router.post(
    "/",
    response_model=DisplayKeyword,
    # dependencies=[Depends(create_wbs_permission)]
)
def create_keyword(
    request: CreateKeyword,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    result = db_keyword.create_keyword(db, request, int(user["tenant_id"]))
    if not result:
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"There was a problem creating the keyword",
            )

    return result


# Read all keywords
@router.get(
    "/",  # response_model=List[DisplayKeyword]
)
def get_all_keywords(db: Session = Depends(get_db), user=Depends(custom_auth)):
    keywords = db_keyword.get_all_keywords(db, int(user["tenant_id"]))
    if not keywords:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No keywords found",
        )

    return keywords


# Read one keyword
@router.get("/{id}", response_model=DisplayKeyword)
def get_keyword_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    keyword = db_keyword.get_keyword(db, id, int(user["tenant_id"]))
    if not keyword:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Keyword with id {id} does not exist",
        )

    return keyword


# Update keyword
@router.put(
    "/{id}"
    # response_model=UpdateWBS
    # dependencies=[Depends(update_risk_permission)]
)
def update_keyword_by_id(
    id: int,
    request: UpdateKeyword,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    db_status = db_keyword.update_keyword(
        db=db,
        id=id,
        keyword=request,  # tenant_id=user["tenant_id"]
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Keyword with id {id} does not exist",
        )

    return db_status


# Delete wbs
@router.delete(
    "/{id}",
    # dependencies=[Depends(delete_risk_permission)]
)
def delete_keyword_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = db_keyword.delete_keyword(db=db, id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Keyword with id {id} does not exist",
        )
    return {"detail": "Successfully deleted keyword."}
