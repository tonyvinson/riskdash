import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, IntegrityError, ProgrammingError
from sqlalchemy.orm import Session

# from fastapi import BackgroundTasks

from fedrisk_api.db import project as db_project
from fedrisk_api.db.database import get_db
from fedrisk_api.db.models import ProjectUser, Role
from fedrisk_api.schema.control import DisplayControl
from fedrisk_api.schema.wbs import DisplayWBS
from fedrisk_api.schema.project import (
    AddProjectsUsers,
    AddProjectUsers,
    # AddProjectControl,
    AddProjectControls,
    ChangeProjectUserRole,
    CreateProject,
    DisplayProject,
    DisplayProjectUsers,
    ProjectPendingTasks,
    RemoveProjectUser,
    UpdateProject,
    DisplayProjectControl,
    DisplayProjectAuditTest,
    DisplayProjectRisk,
    DisplayProjectControlAssessment,
    DisplayProjectEvaluation,
)
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    addablecontrols_project_permission,
    adduser_project_permission,
    changerole_project_permission,
    create_project_permission,
    delete_project_permission,
    removecontrol_project_permission,
    removeuser_project_permission,
    update_project_permission,
    view_project_permission,
)
from fedrisk_api.utils.utils import (
    PaginateResponse,
    delete_documents_for_fedrisk_object,
    # get_modify_objects,
    pagination,
    verify_add_user_to_multiple_project,
    verify_add_user_to_project,
)

from fedrisk_api.db.util.encrypt_pii_utils import decrypt_user_fields

from fedrisk_api.schema.user import DisplayUser, DisplayRole

router = APIRouter(prefix="/projects", tags=["projects"])
LOGGER = logging.getLogger(__name__)

PROJECT_ADMIN_ROLE = "Project Administrator"


# Create project
@router.post("/", response_model=DisplayProject, dependencies=[Depends(create_project_permission)])
async def create_project(
    request: CreateProject,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        response = await db_project.create_project(
            db,
            project=request,
            tenant_id=user["tenant_id"],
            keywords=keywords,
            user_id=user["user_id"],
        )
        return response

    except IntegrityError as ie:
        LOGGER.exception("Create Project Error - Invalid Request")
        detail_message = str(ie)
        print(f"\n\nDetail Message: {detail_message} . . .")
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Project with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Read all projects
@router.get(
    "/",
    response_model=PaginateResponse[DisplayProject],
    dependencies=[Depends(view_project_permission)],
)
def get_all_projects(
    q: str = None,
    filter_by: str = None,
    filter_value: str = None,
    offset: int = 0,
    limit: int = 10,
    sort_by: str = "name",
    get_role: bool = False,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        LOGGER.warning(f"User: {user}")
        queryset = db_project.get_all_projects(
            db,
            user["tenant_id"],
            user["user_id"],
            q=q,
            filter_by=filter_by,
            filter_value=filter_value,
            sort_by=sort_by,
        )
        response = pagination(query=queryset, offset=offset, limit=limit)
        # Adding user_role in project
        all_roles = {role.id: role.name for role in db.query(Role).all()}
        project_users = db.query(ProjectUser).filter(ProjectUser.user_id == user["user_id"]).all()

        if get_role:
            for project in response["items"]:
                for project_user in project_users:
                    if project_user.project_id == project.id:
                        setattr(project, "my_role", all_roles.get(project_user.role_id))
                        break
                else:
                    setattr(project, "my_role", None)
        return response
    except Exception:
        LOGGER.exception("List Project Error Invalid Request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Invalid value in Parameter"
        )


# Get all projects for tenant
@router.get(
    "/tenant/",
    dependencies=[Depends(view_project_permission)],
)
def get_all_projects_tenant(db: Session = Depends(get_db), user=Depends(custom_auth)):
    projects = db_project.get_all_tenant_projects(db, user["tenant_id"])
    # LOGGER.info(f"projects = {projects}")
    return projects


# Read one project
@router.get("/{id}", response_model=DisplayProject)
async def get_project_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):

    project = await db_project.get_project(
        db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {id} does not exist",
        )
    return project


@router.get("/get_user_projects/{user_id}")
def get_user_projects(user_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    response = db_project.get_users_project(
        db,
        user_id,
    )
    return response


@router.get("/get_project_frameworks/{project_id}")
def get_project_frameworks(
    project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    response = db_project.get_project_frameworks(
        db,
        project_id,
    )
    return response


# Update project
@router.put("/{id}", dependencies=[Depends(update_project_permission)])
async def update_project_by_id(
    id: int,
    request: UpdateProject,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        db_status = await db_project.update_project(
            db=db,
            id=id,
            project=request,
            tenant_id=user["tenant_id"],
            keywords=keywords,
            user_id=user["user_id"],
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project with id {id} does not exist",
            )

        return {"detail": "Successfully updated project."}
    except IntegrityError as ie:
        LOGGER.exception("Update Project Error - Invalid Request")
        detail_message = str(ie)
        if "duplicate" in detail_message or "UNIQUE" in detail_message:
            detail_message = f"Project with name '{request.name}' already exists"
        raise HTTPException(status_code=409, detail=detail_message)


# Delete project
@router.delete("/{id}", dependencies=[Depends(delete_project_permission)])
async def delete_project_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    try:
        await delete_documents_for_fedrisk_object(
            db=db, fedrisk_object_id=id, fedrisk_object_type="project"
        )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error while deleting associated documents",
        )
    db_status = await db_project.delete_project(db=db, id=id, tenant_id=user["tenant_id"])
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {id} does not exist",
        )
    return {"detail": "Successfully deleted project."}


# Delete project control
@router.delete(
    "/{id}/project_control/{project_control_id}",
    dependencies=[Depends(removecontrol_project_permission)],
)
async def remove_control_from_project(
    id: int, project_control_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_result, db_stats, db_message = await db_project.remove_control_from_project(
        db=db,
        id=id,
        project_control_id=project_control_id,
        tenant_id=user["tenant_id"],
        user_id=user["user_id"],
    )

    if not db_result:
        raise HTTPException(status_code=db_stats, detail=db_message)
    return {"detail": db_message}


# Get all Controls that can be added to the project
@router.get(
    "/{id}/addable_control/",
    response_model=List[DisplayControl],
    dependencies=[Depends(addablecontrols_project_permission)],
)
def get_all_addable_controls_for_project(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_result = db_project.get_available_controls_for_adding_to_project(
        db=db, id=id, tenant_id=user["tenant_id"]
    )
    if db_result == -1:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id '{id}' does not exist",
        )

    return db_result


# Get all project controls by project_id
@router.get(
    "/project_controls/{project_id}",
    response_model=PaginateResponse[DisplayProjectControl],
    dependencies=[Depends(addablecontrols_project_permission)],
)
def get_project_controls_by_project(
    project_id: int,
    q: str = None,
    filter_by: str = None,
    filter_value: str = None,
    sort_by: str = "-created_date",
    offset: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = db_project.get_project_controls_by_project_id(
        db=db,
        project_id=project_id,
    )
    response = pagination(query=queryset, offset=offset, limit=limit)
    return response


# Get all project controls by project_id
@router.get(
    "/project_controls_dropdown/{project_id}",
    # response_model=PaginateResponse[DisplayProjectControl],
    dependencies=[Depends(addablecontrols_project_permission)],
)
async def get_project_controls_dropdown_by_project(
    project_id: int,
    # q: str = None,
    # filter_by: str = None,
    # filter_value: str = None,
    # sort_by: str = "-created_date",
    # offset: int = 0,
    # limit: int = 10,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    queryset = await db_project.get_project_controls_dropdown_by_project_id(
        db=db,
        project_id=project_id,
    )
    # response = pagination(query=queryset, offset=offset, limit=limit)
    return queryset


# Get all controls for framework and any that have already been added to a project
@router.get(
    "/project_controls/{project_id}/framework_versions/{framework_version_id}",
    response_model=List[DisplayControl],
    dependencies=[Depends(addablecontrols_project_permission)],
)
def get_project_controls_by_project_id_by_framework_version_id(
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    project_id=int,
    framework_version_id=int,
):
    return db_project.get_project_controls_by_project_id_by_framework_version_id(
        db=db, project_id=project_id, framework_version_id=framework_version_id
    )


# Add endpoint that allows batch upload of controls to a project
@router.put(
    "/add_controls/{project_id}",
    response_model=List[DisplayProjectControl],
    # status_code=200,
    # dependencies=[Depends(adduser_project_permission)],
)
async def add_batch_controls_by_project_id(
    project_id: int,
    project_controls: AddProjectControls,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    project_controls_list = await db_project.add_batch_project_controls_to_project(
        db=db,
        project_id=project_id,
        project_controls=project_controls,
        tenant_id=user["tenant_id"],
        user_id=user["user_id"],
    )
    return project_controls_list


# Get all project audit tests by project_id
@router.get(
    "/audit_tests/{project_id}",
    response_model=List[DisplayProjectAuditTest],
    # dependencies=[Depends(addablecontrols_project_permission)],
)
def get_audit_tests_by_project(
    project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    return db_project.get_audit_tests_by_project_id(db=db, project_id=project_id)


# Get all project risks by project_id
@router.get(
    "/risks/{project_id}",
    response_model=List[DisplayProjectRisk],
    # dependencies=[Depends(addablecontrols_project_permission)],
)
def get_risks_by_project(project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    return db_project.get_risks_by_project_id(db=db, project_id=project_id)


# Get all project assessments by project_id
@router.get(
    "/assessments/{project_id}",
    response_model=List[DisplayProjectControlAssessment],
    # dependencies=[Depends(addablecontrols_project_permission)],
)
def get_assessments_by_project(
    project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    return db_project.get_assessments_by_project_id(db=db, project_id=project_id)


# Get all project wbs by project_id
@router.get(
    "/wbs/{project_id}",
    response_model=List[DisplayWBS],
    # dependencies=[Depends(addablecontrols_project_permission)],
)
def get_wbs_by_project(project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    return db_project.get_wbs_by_project_id(db=db, project_id=project_id)


# Get all project evaluations by project_id
@router.get(
    "/evaluations/{project_id}",
    response_model=List[DisplayProjectEvaluation],
    # dependencies=[Depends(addablecontrols_project_permission)],
)
def get_evaluations_by_project(
    project_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    return db_project.get_evaluations_by_project_id(db=db, project_id=project_id)


@router.put(
    "/{id}/add_users/",
    response_model=DisplayProjectUsers,
    status_code=200,
    dependencies=[Depends(adduser_project_permission)],
)
async def add_user_to_project(
    id: int,
    project_users: AddProjectUsers,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    status, status_code, message = verify_add_user_to_project(
        db=db, id=id, project_users=project_users, tenant_id=user["tenant_id"]
    )

    if not status:
        raise HTTPException(status_code=status_code, detail=message)

    project_users_list = await db_project.add_users_to_project(
        db=db,
        id=id,
        project_users=project_users,
        tenant_id=user.get("tenant_id"),
        user_id=user.get("user_id"),
    )
    return DisplayProjectUsers(users=project_users_list)


@router.delete("/{id}/remove-user/", dependencies=[Depends(removeuser_project_permission)])
async def remove_user_from_project(
    id: int, request: RemoveProjectUser, db: Session = Depends(get_db)
):
    db_status, message = await db_project.remove_user_from_project(
        db=db, id=id, user_id=request.user_id
    )
    if not db_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return {"detail": message}


@router.put("/{id}/change-role/", dependencies=[Depends(changerole_project_permission)])
async def change_user_role_in_project(
    id: int,
    request: ChangeProjectUserRole,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    db_status, message = await db_project.change_user_role_in_project(
        db=db, id=id, user_details=request, user_id=user["user_id"]
    )
    if not db_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=message)
    return {"detail": message}


@router.get("/{id}/user/{user_id}/permissions")
def get_project_user_permission(
    id: int, user_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    permissions = db_project.get_project_user_permission(db=db, id=id, user_id=user_id)
    if not permissions:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="permission not exists")
    return permissions


@router.get("/{id}/users")
def get_project_associated_user(
    id: int,
    q: str = None,
    filter_by: str = None,
    filter_value: str = None,
    offset: int = 0,
    limit: int = 10,
    sort_by: str = "email",
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_project.get_project_associated_user(
            db=db,
            id=id,
            q=q,
            filter_by=filter_by,
            filter_value=filter_value,
            sort_by=sort_by,
            user=user,
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project with specified id doesn't exist",
            )

        # Paginate the query
        paginated = pagination(query=queryset, limit=limit, offset=offset)

        # Decrypt user fields and convert to schemas
        items = []
        for user_obj, role_obj in paginated["items"]:
            decrypted_user_dict = decrypt_user_fields(user_obj)  # your custom decryption logic
            decrypted_user = DisplayUser(**decrypted_user_dict)
            role = DisplayRole(id=role_obj.id, name=role_obj.name)
            items.append({"user": decrypted_user, "role": role})

        return {
            "items": items,
            "total": paginated["total"],
            "limit": limit,
            "offset": offset,
        }
    except DataError as e:
        LOGGER.exception("Get Project Associated Users Error - Invalid request")
        if "LIMIT must not be negative" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="LIMIT must not be negative",
            )
        elif "OFFSET must not be negative" in str(e):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OFFSET must not be negative",
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Please provide correct filter_value",
            )
    except ProgrammingError:
        LOGGER.exception("Get Project Associated Users Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide correct sort_by field value",
        )
    except AttributeError:
        LOGGER.exception("Get Project Associated Users Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide correct filter_by field value",
        )


@router.get("/pending_project_task/", response_model=ProjectPendingTasks)
def get_project_pending_task(db: Session = Depends(get_db), user=Depends(custom_auth)):
    response = db_project.get_project_pending_task(db=db, user=user)
    return ProjectPendingTasks(items=response)


@router.put(
    "/add_users/",
    response_model=DisplayProjectUsers,
    status_code=status.HTTP_200_OK,
)
def add_users_to_multiple_project(
    projects_users: AddProjectsUsers,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    status, status_code, message = verify_add_user_to_multiple_project(
        db=db, project_users=projects_users, tenant_id=user["tenant_id"]
    )

    if not status:
        raise HTTPException(status_code=status_code, detail=message)

    project_users_list = db_project.add_users_to_multiple_project(
        db=db, project_users=projects_users, tenant_id=user.get("tenant_id")
    )
    return DisplayProjectUsers(users=project_users_list)


@router.put(
    "/{id}/add_a_user/{user_id}/{role_id}",
    # dependencies=[Depends(update_project_permission)]
)
async def add_a_user_to_project(
    id: int,
    user_id: int,
    role_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    author_id = user["user_id"]
    return await db_project.add_a_user_to_project(db, id, user_id, role_id, author_id)
