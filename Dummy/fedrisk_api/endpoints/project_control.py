import logging
from typing import List

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import project as db_project
from fedrisk_api.db.database import get_db
from fedrisk_api.db.project import (
    NO_SUCH_CONTROL,
    # NO_SUCH_CONTROL_CLASS,
    # NO_SUCH_CONTROL_FAMILY,
    # NO_SUCH_CONTROL_PHASE,
    # NO_SUCH_CONTROL_STATUS,
    NO_SUCH_PROJECT,
    NO_SUCH_PROJECT_CONTROL,
    PROJECT_CONTROL_ALREADY_EXISTS,
)
from fedrisk_api.schema.project import DisplayProject, DisplayProjectControl, UpdateProjectControl
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    addcontrol_project_permission,
    # removecontrol_project_permission,
    # update_project_permission,
    # view_project_permission,
)

from fedrisk_api.schema.project import (
    CreateProjectControl,
    UpdateProjectControl,
)

router = APIRouter(prefix="/project_controls", tags=["project_controls"])
LOGGER = logging.getLogger(__name__)

# Add control to the project
@router.post(
    "/{project_id}/{control_id}",
    response_model=DisplayProject,
    dependencies=[Depends(addcontrol_project_permission)],
)
async def add_control_to_project(
    project_id: int,
    control_id: int,
    project_control: CreateProjectControl,  # ✅ Corrected Pydantic model usage
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: Optional[str] = None,
    assessment_confirmed: Optional[str] = None,
):
    try:
        db_status = await db_project.add_control_to_project(
            db=db,
            id=project_id,
            control_id=control_id,
            tenant_id=user["tenant_id"],
            user_id=user["user_id"],
            project_control=project_control,
            keywords=keywords,
            assessment_confirmed=assessment_confirmed,
        )

        # ✅ Fix: Use project_id instead of id
        if db_status == NO_SUCH_PROJECT:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id '{project_id}' does not exist",
            )
        elif db_status == NO_SUCH_CONTROL:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Control with id '{control_id}' does not exist",
            )
        elif db_status == PROJECT_CONTROL_ALREADY_EXISTS:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Control with id '{control_id}' is already associated with project with id '{project_id}'",
            )

        # ✅ Ensure the response is serializable
        if hasattr(db_status, "__dict__"):
            return DisplayProject(**db_status.__dict__)
        elif isinstance(db_status, dict):
            return DisplayProject(**db_status)
        else:
            raise HTTPException(status_code=500, detail="Invalid response from database")

    except IntegrityError as ie:
        LOGGER.exception("Add Control To Project Error - Invalid Request")
        detail_message = str(ie)

        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = (
                f"Project with id '{project_id}' already contains Control with id '{control_id}'"
            )

        raise HTTPException(status_code=409, detail=detail_message)


# Get a single project control for a project with documents
@router.get(
    "/{project_control_id}",
    response_model=DisplayProjectControl,
)
def get_project_control_by_id(
    project_control_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    return db_project.get_project_control_by_id(db=db, project_control_id=project_control_id)


# Edit control attached to the project
@router.put(
    "/{project_control_id}",
    response_model=DisplayProjectControl,
    dependencies=[Depends(addcontrol_project_permission)],
)
async def update_project_control(
    project_control_id: int,
    project_control: UpdateProjectControl,  # Correct Pydantic model usage
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: Optional[str] = None,
    assessment_confirmed: Optional[str] = None,
):
    db_status = await db_project.update_control_on_project(
        db=db,
        project_control_id=project_control_id,
        tenant_id=user["tenant_id"],
        project_control=project_control,
        keywords=keywords,
        assessment_confirmed=assessment_confirmed,
        user_id=user["user_id"],
    )

    if db_status == NO_SUCH_PROJECT_CONTROL:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project control with id '{project_control_id}' does not exist",
        )

    # ✅ Fix: Convert SQLAlchemy model to a dict if necessary
    if hasattr(db_status, "__dict__"):  # If it's an object
        return DisplayProjectControl(**db_status.__dict__)  # Convert to Pydantic model
    elif isinstance(db_status, dict):  # If it's already a dict
        return DisplayProjectControl(**db_status)
    else:
        raise HTTPException(status_code=500, detail="Invalid response from database")
