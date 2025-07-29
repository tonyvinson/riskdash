import logging
from datetime import date
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import DataError, ProgrammingError
from sqlalchemy.orm import Session

from fedrisk_api.db import task as db_task
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.task import CreateTask, DisplayTask, UpdateTask, DisplayCalendarTask
from fedrisk_api.utils.authentication import custom_auth

from fedrisk_api.utils.permissions import (
    create_task_permission,
    update_task_permission,
    view_task_permission,
)

from fedrisk_api.utils.utils import (
    PaginateResponse,
    pagination,
)

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/task", response_model=DisplayTask, dependencies=[Depends(create_task_permission)])
async def create_task(
    request: CreateTask,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    # try:
    response = await db_task.create_task(
        db, request, int(user["tenant_id"]), keywords, int(user["user_id"])
    )
    return response
    # return response
    # except Exception as e:
    #     error = str(e)
    #     if "enum" in error:
    #         field_name = "enum"
    #         if "enum taskstatus" in error:
    #             field_name = "status"
    #         elif "enum taskpriority" in error:
    #             field_name = "priority"
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail=f"please provide valid {field_name} choice value.",
    #         )
    #     raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unable to create Task")


@router.get(
    "/", response_model=PaginateResponse[DisplayTask], dependencies=[Depends(view_task_permission)]
)
def get_all_task(
    offset: int = None,
    limit: int = None,
    user_id: int = None,
    project_id: int = None,
    wbs_id: int = None,
    due_date: date = None,
    filter_by: str = None,
    filter_value: str = None,
    sort_by: str = None,
    task_status: str = None,
    assigned_to: int = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = db_task.get_all_tasks(
            db=db,
            tenant_id=user["tenant_id"],
            auth_user_id=user["user_id"],
            user_id=user_id,
            project_id=project_id,
            wbs_id=wbs_id,
            due_date=due_date,
            assigned_to=assigned_to,
            filter_by=filter_by,
            filter_value=filter_value,
            sort_by=sort_by,
            status=task_status,
        )
        # LOGGER.info(queryset.all())
        return pagination(query=queryset, offset=offset, limit=limit)
        # return queryset.all()
    except DataError as e:
        LOGGER.exception("Get Task Error - Invalid request")

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
        LOGGER.exception("Get Task Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct sort_by field value",
        )
    except AttributeError:
        LOGGER.exception("Get Task Error - Invalid request")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Please provide correct filter_by field value",
        )


@router.get("/{id}", response_model=DisplayTask, dependencies=[Depends(view_task_permission)])
def get_task_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    task = db_task.get_task(db=db, id=id, tenant_id=user["tenant_id"], user_id=user["user_id"])
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with id {id} does not exist",
        )
    # task_history = db.query(TaskHistory).filter(TaskHistory.task_id == task.id).all()
    # result = (task.__dict__)
    # response = DisplayTask(**result, task_history=task_history)
    # response.project = task.project
    # response.user = task.user

    return task


@router.put("/{id}", response_model=DisplayTask, dependencies=[Depends(update_task_permission)])
async def update_task_by_id(
    id: int,
    request: UpdateTask,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
    keywords: str = None,
):
    try:
        db_status = await db_task.update_task(
            db=db,
            id=id,
            task=request,
            tenant_id=user["tenant_id"],
            user_id=user["user_id"],
            keywords=keywords,
        )
        if not db_status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task with id {id} does not exist",
            )

        return db_status
    except Exception as e:
        error = str(e)
        # if "enum" in error:
        # field_name = "enum"
        # if "enum taskstatus" in error:
        # field_name = "status"
        # raise HTTPException(
        # status_code=status.HTTP_400_BAD_REQUEST,
        # detail=f"please provide valid {field_name} choice value.",
        # )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error)

    # return db_status


@router.get("/wbs/{wbs_id}")
async def get_tasks_by_wbs_id(
    wbs_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    task_tree = db_task.get_wbs_tasks(
        db=db, wbs_id=wbs_id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not task_tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tasks with {wbs_id} do not exist",
        )
    return task_tree


@router.get("/dhwbsgantt/{wbs_id}")
async def get_tasks_by_wbs_dhtmlx_id(
    wbs_id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    task_tree = db_task.get_wbs_dhtmlx_tasks(
        db=db, wbs_id=wbs_id, tenant_id=user["tenant_id"], user_id=user["user_id"]
    )
    if not task_tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tasks with wbs id {wbs_id} do not exist",
        )
    return task_tree


@router.get("/charts/{project_id}")
def get_task_chart_data_by_project(
    project_id: int, wbs_id: int = None, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    task_tree = db_task.get_tasks_wbs_chart_data(
        db=db,
        project_id=project_id,
        wbs_id=wbs_id,
        tenant_id=user["tenant_id"],
        user_id=user["user_id"],
    )
    if not task_tree:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tasks with {project_id} do not exist",
        )
    return task_tree


@router.get("/start_end_date/", response_model=List[DisplayCalendarTask])
async def get_tasks_by_date_range(
    start_date: str = None,
    end_date: str = None,
    wbs_id: str = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    tasks = await db_task.get_tasks_by_dates(
        db=db,
        start_date=start_date,
        end_date=end_date,
        wbs_id=wbs_id,
        tenant_id=user["tenant_id"],
        user_id=user["user_id"],
    )
    if not tasks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No tasks found",
        )
    return tasks


# delete task
@router.delete("/{id}")
async def delete_task(id: int, db: Session = Depends(get_db), user: str = Depends(custom_auth)):
    response = await db_task.delete_task(id=id, db=db)
    if response:
        return {"detail": "Successfully deleted task"}

    LOGGER.error("Task does not exist")
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Task with specified id does not exists"
    )
