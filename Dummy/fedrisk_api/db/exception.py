import logging

# import threading
import asyncio

from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import Session

import os

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from fedrisk_api.db.models import (
    Control,
    Cost,
    Exception,
    ExceptionApprovalWorkflow,
    ExceptionCost,
    ExceptionStakeholder,
    ProjectControl,
    Project,
    User,
    ExceptionDocument,
    ExceptionReview,
    Keyword,
    KeywordMapping,
    ExceptionHistory,
    UserNotificationSettings,
)
from fedrisk_api.db.project import ProjectControl
from fedrisk_api.schema.exception import (
    CreateException,
    UpdateException,
    CreateExceptionReview,
    UpdateExceptionReview,
)
from fedrisk_api.utils.utils import filter_by_tenant, filter_by_user_project_role

from fedrisk_api.utils.email_util import send_control_exception_email

frontend_server_url = os.getenv("FRONTEND_SERVER_URL", "")

LOGGER = logging.getLogger(__name__)

from fedrisk_api.db.util.notifications_utils import (
    notify_user,
    # add_notification,
    # manage_notifications,
)

# Keyword Management Functions
async def add_keywords(db, keywords, exception_id, tenant_id):
    """Link keywords to exception_id."""
    if not keywords:
        return
    keyword_names = set(keywords.split(","))
    for name in keyword_names:
        if name != "":
            keyword = db.query(Keyword).filter_by(tenant_id=tenant_id, name=name).first()
            if not keyword:
                keyword = Keyword(name=name, tenant_id=tenant_id)
                db.add(keyword)
                db.commit()
            if (
                not db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, exception_id=exception_id)
                .first()
            ):
                db.add(KeywordMapping(keyword_id=keyword.id, exception_id=exception_id))
    db.commit()


async def remove_old_keywords(db, keywords, exception_id):
    """Remove keywords from exception that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(exception_id=exception_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = (
        db.query(Keyword).join(KeywordMapping).filter_by(exception_id=exception_id).all()
    )

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, exception_id=exception_id)
                .first()
            )
            db.delete(mapping)
    db.commit()


async def send_email_notification(control_exception_data={}):
    # email_service = EmailService(config=Settings())
    await send_control_exception_email(control_exception_data=control_exception_data)


async def create_exception(
    db: Session, exception: CreateException, keywords: str, tenant_id: int, user_id: int
):
    target_project_control_id = exception.project_control_id
    existing_project_control = (
        db.query(ProjectControl).filter(ProjectControl.id == target_project_control_id).first()
    )

    if not existing_project_control:
        return -1

    # Prepare exception and history data
    my_new_exception_dict = exception.dict()
    stakeholder_ids = my_new_exception_dict.pop("stakeholder_ids", [])
    exception_name = (
        f"Exception for Control '{existing_project_control.control.name}' "
        f"on Project '{existing_project_control.project.name}'"
    )
    my_new_exception_dict["name"] = exception_name
    new_exception = Exception(**my_new_exception_dict, tenant_id=tenant_id)
    db.add(new_exception)
    db.commit()
    db.refresh(new_exception)

    # Add history
    history_entry = ExceptionHistory(
        exception_id=new_exception.id,
        author_id=user_id,
        history=f"Created new exception {exception_name}",
    )
    db.add(history_entry)

    # Link project control and exception
    existing_project_control.exception_id = new_exception.id
    db.commit()

    # Send email and sms updates to owner
    owner = db.query(User).filter_by(id=new_exception.owner_id).first()
    owner_settings = (
        db.query(UserNotificationSettings).filter_by(user_id=new_exception.owner_id).first()
    )
    project = (
        db.query(Project)
        .join(ProjectControl, Project.id == ProjectControl.project_id)
        .filter(new_exception.project_control_id == ProjectControl.id)
    ).first()
    link = f"/projects/{project.id}/controls/{new_exception.project_control_id}/exceptions/{new_exception.id}"
    if owner is not None:
        await notify_user(
            owner,
            f"You've been added as an owner on exception {new_exception.name}",
            link,
            owner_settings,
        )

    # Add stakeholders
    if stakeholder_ids:
        new_exception.stakeholders = db.query(User).filter(User.id.in_(stakeholder_ids)).all()

    # Send email and sms updates to stakeholders
    for stakeholder in stakeholder_ids:
        stake = db.query(User).filter_by(id=stakeholder).first()
        stake_settings = db.query(UserNotificationSettings).filter_by(user_id=stakeholder).first()
        if stake is not None:
            await notify_user(
                stake,
                f"You've been added as a stakeholder on exception {new_exception.name}",
                link,
                stake_settings,
            )
    # add keywords
    await add_keywords(db, keywords, new_exception.id, tenant_id)
    # db.commit()

    # Send email notification
    project_id = existing_project_control.project.id
    link = (
        f"{frontend_server_url}/{project_id}/controls/"
        f"{existing_project_control.id}/exceptions/{new_exception.id}"
    )
    emailstring = ", ".join(
        [user.email for user in db.query(User).filter(User.id.in_(stakeholder_ids)).all()]
    )

    owner = db.query(User).filter(User.id == exception.owner_id).first()
    if owner:
        emailstring += f", {owner.email}"

    if emailstring:
        control_exception_data = {"emails": emailstring, "hyperlink": link}
        asyncio.create_task(send_email_notification(control_exception_data))
        LOGGER.info("Send notification emails asynchronously")

    return new_exception


def get_all_exceptions(db: Session, tenant_id: int, project_id: int, user_id: int):
    if project_id:
        exceptions = (
            db.query(Exception)
            .join(ProjectControl, Exception.project_control_id == ProjectControl.id)
            .filter(Exception.tenant_id == tenant_id)
            .filter(ProjectControl.project_id == project_id)
            .all()
        )

        return exceptions

    queryset = filter_by_user_project_role(db, Exception, user_id, tenant_id)

    return queryset.options(
        selectinload(Exception.project_control)
        .selectinload(ProjectControl.control)
        .selectinload(Control.framework_versions),
        selectinload(Exception.project_control).selectinload(ProjectControl.assessment),
        selectinload(Exception.owner),
        selectinload(Exception.stakeholders),
    ).all()


def get_exception(db: Session, id: int, tenant_id: int, user_id: int):
    exception = (
        filter_by_user_project_role(db, Exception, user_id, tenant_id)
        .filter(Exception.id == id)
        .first()
    )

    return exception


async def update_exception(
    db: Session,
    id: int,
    exception: UpdateException,
    keywords: str,
    tenant_id: int,
    user_id: int,
):
    existing_exception = db.query(Exception).filter(Exception.id == id).first()
    if not existing_exception:
        return False

    exception_dict = exception.dict(exclude_unset=True)

    # Fetch project
    project = (
        db.query(Project)
        .join(ProjectControl, Project.id == ProjectControl.project_id)
        .filter(existing_exception.project_control_id == ProjectControl.id)
        .first()
    )

    link = f"/projects/{project.id}/controls/{existing_exception.project_control_id}/exceptions/{existing_exception.id}"

    # Handle stakeholders
    stakeholder_ids = exception_dict.pop("stakeholder_ids", None)
    if stakeholder_ids:
        existing_stakeholders = {
            s.user_id for s in db.query(ExceptionStakeholder).filter_by(exception_id=id).all()
        }

        new_stakeholders = set(stakeholder_ids) - existing_stakeholders
        for new_stakeholder_id in new_stakeholders:
            stake = db.query(User).filter_by(id=new_stakeholder_id).first()
            stake_settings = (
                db.query(UserNotificationSettings).filter_by(user_id=new_stakeholder_id).first()
            )
            if stake and stake_settings:
                await notify_user(
                    stake,
                    f"You've been added as a stakeholder on exception {existing_exception.name}",
                    link,
                    stake_settings,
                )

        # Update stakeholders
        existing_exception.stakeholders = db.query(User).filter(User.id.in_(stakeholder_ids)).all()
    # Update costs
    cost_ids = exception_dict.pop("cost_ids", None)
    if cost_ids is not None or []:
        # add costs
        for cost in cost_ids:
            # check if cost id exists on tenant
            existing_cost = db.query(Cost).filter(Cost.tenant_id == tenant_id).first()
            # if the cost exists
            if existing_cost is not None:
                new_cost_map = ExceptionCost(exception_id=id, cost_id=cost)
                try:
                    db.add(new_cost_map)
                    db.commit()
                except:
                    LOGGER.error("Could not add cost with this ID")
    # Track field changes
    changes = []
    for field, new_value in exception_dict.items():
        old_value = getattr(existing_exception, field, None)
        if new_value is not None and old_value != new_value:
            if field == "owner_id":
                owner = db.query(User).filter_by(id=new_value).first()
                owner_settings = (
                    db.query(UserNotificationSettings).filter_by(user_id=new_value).first()
                )
                if owner:
                    await notify_user(
                        owner,
                        f"You've been added as an owner on exception {existing_exception.name}",
                        link,
                        owner_settings,
                    )
            changes.append(f"Updated {field.replace('_', ' ')} to {new_value}")

    # Log changes in history
    for change in changes:
        db.add(ExceptionHistory(exception_id=id, author_id=user_id, history=change))

    # Apply updates
    if exception_dict:
        for key, value in exception_dict.items():
            setattr(existing_exception, key, value)

    # Update keywords
    await remove_old_keywords(db, keywords, id)
    await add_keywords(db, keywords, id, tenant_id)

    db.commit()
    return id


def delete_exception(db: Session, id: int, tenant_id: int):
    existing_exception = filter_by_tenant(db, Exception, tenant_id).filter(Exception.id == id)
    if not existing_exception.first():
        return False

    my_existing_exception = existing_exception.first()

    target_project_control_id = my_existing_exception.project_control_id
    LOGGER.warning(f"Target Project Control Id: {target_project_control_id} . . .")
    existing_project_control = db.query(ProjectControl).filter(
        ProjectControl.id == target_project_control_id
    )
    if not existing_project_control.first():
        return -1

    my_existing_project_control = existing_project_control.first()
    LOGGER.warning("About to set exception_id to None on existing_project_control . . .")
    my_existing_project_control.exception_id = None
    db.commit()
    db.refresh(my_existing_project_control)
    # delete all history
    db.query(ExceptionHistory).filter(ExceptionHistory.exception_id == id).delete()
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.exception_id == id).delete()
    # delete all document references
    db.query(ExceptionDocument).filter(ExceptionDocument.exception_id == id).delete()
    # delete all cost references
    db.query(ExceptionCost).filter(ExceptionCost.exception_id == id).delete()
    db.query(ExceptionStakeholder).filter(
        ExceptionStakeholder.exception_id == my_existing_exception.id
    ).delete(synchronize_session=False)
    db.query(ExceptionReview).filter(
        ExceptionReview.exception_id == my_existing_exception.id
    ).delete(synchronize_session=False)
    # delete all approval workflow references
    db.query(ExceptionApprovalWorkflow).filter(
        ExceptionApprovalWorkflow.exception_id == id
    ).delete()
    existing_exception.delete(synchronize_session=False)
    db.commit()

    return True


# DB methods for exception_review to CREATE, GET by id, GET all by audit_test_id and DELETE by id
async def create_exception_review(db: Session, exception_review: CreateExceptionReview):

    exception_review_data = exception_review.dict()
    new_exception_review = ExceptionReview(**exception_review_data)
    db.add(new_exception_review)
    db.commit()

    return new_exception_review


async def update_exception_review(db: Session, exception_review: UpdateExceptionReview, id: int):
    existing_exception_review = db.query(ExceptionReview).filter(ExceptionReview.id == id)
    if not existing_exception_review.first():
        return False
    exception_review_data = exception_review.dict()
    update_exception_review = UpdateExceptionReview(**exception_review_data)

    existing_exception_review.update(update_exception_review.dict(exclude_unset=True))

    db.commit()
    return existing_exception_review.first()


def get_exception_review(db: Session, id: int, tenant_id: int, user_id: int):
    exception_review = (
        filter_by_user_project_role(
            db=db, model=ExceptionReview, tenant_id=tenant_id, user_id=user_id
        )
        .options(
            selectinload(ExceptionReview.exception),
        )
        .filter(ExceptionReview.id == id)
        .first()
    )
    # LOGGER.info(exception_review)
    return exception_review


def get_exception_review_by_exception_id(
    db: Session, exception_id: int, tenant_id: int, user_id: int
):
    exception_reviews = (
        db.query(ExceptionReview).filter(ExceptionReview.exception_id == exception_id).all()
    )
    return exception_reviews


async def delete_exception_review(db: Session, id: int):
    existing_exception_review = db.query(ExceptionReview).filter(ExceptionReview.id == id)
    if not existing_exception_review.first():
        return False

    existing_exception_review.delete(synchronize_session=False)
    db.commit()
    return True


# creates audit test instances based on audit test definitions
async def create_exception_review_reoccurring(db: Session):
    daily_instances = 0
    weekly_instances = 0
    monthly_instances = 0
    quarterly_instances = 0
    # select all daily audit_tests that need to be created
    exceptions_daily = (
        db.query(Exception)
        .filter(Exception.review_frequency == "daily")
        .filter(Exception.start_date <= date.today())
        .filter(Exception.end_date >= date.today())
        .all()
    )
    for exception in exceptions_daily:
        # check if an exception review exists for the daily event
        exception_review = (
            db.query(ExceptionReview)
            .filter(ExceptionReview.exception_id == exception.id)
            .filter(ExceptionReview.created_date <= date.today())
        )
        # if it doesn't exist create one
        if not exception_review.first():
            db.add(ExceptionReview(exception_id=exception.id, review_status="not_started"))
            db.commit()
            daily_instances += 1
            today = date.today()
            future_date = today + timedelta(days=1)
            update_exception_obj = UpdateException(next_review_date=future_date)
            # update exception review date to date.today() + 1 day
            await update_exception(
                db,
                exception.id,
                update_exception_obj,
                None,
                exception.tenant_id,
                exception.owner_id,
            )

    # select all weekly audit_tests that need to be created
    exceptions_weekly = (
        db.query(Exception)
        .filter(Exception.review_frequency == "weekly")
        .filter(Exception.start_date <= date.today())
        .filter(Exception.end_date >= date.today())
        .all()
    )
    for exception in exceptions_weekly:
        today = date.today()
        future_date = today + timedelta(days=7)
        # check if an exception review exists for the weekly event
        exception_review = (
            db.query(ExceptionReview)
            .filter(ExceptionReview.exception_id == exception.id)
            .filter(ExceptionReview.created_date <= future_date)
        )
        # if it doesn't exist create one
        if not exception_review.first():
            db.add(ExceptionReview(exception_id=exception.id, review_status="not_started"))
            db.commit()
            weekly_instances += 1
            # update exception review date to future_date
            update_exception_obj = UpdateException(next_review_date=future_date)
            # update exception review date to future_date
            await update_exception(
                db,
                exception.id,
                update_exception_obj,
                None,
                exception.tenant_id,
                exception.owner_id,
            )

    # select all monthly exceptions that need to be created
    exceptions_monthly = (
        db.query(Exception)
        .filter(Exception.review_frequency == "monthly")
        .filter(Exception.start_date <= date.today())
        .filter(Exception.end_date >= date.today())
        .all()
    )
    for exception in exceptions_monthly:
        today = date.today()
        future_date = today + relativedelta(months=1)
        # check if an audit test instance exists for the monthly event
        exception_review = (
            db.query(ExceptionReview)
            .filter(ExceptionReview.exception_id == exception.id)
            .filter(ExceptionReview.created_date <= future_date)
        )
        # if it doesn't exist create one
        if not exception_review.first():
            db.add(ExceptionReview(exception_id=exception.id, review_status="not_started"))
            db.commit()
            monthly_instances += 1
            # update exception review date to future_date
            update_exception_obj = UpdateException(next_review_date=future_date)
            # update exception review date to future_date
            await update_exception(
                db,
                exception.id,
                update_exception_obj,
                None,
                exception.tenant_id,
                exception.owner_id,
            )
    # select all quarterly audit_tests that need to be created
    exceptions_quarterly = (
        db.query(Exception)
        .filter(Exception.review_frequency == "quarterly")
        .filter(Exception.start_date <= date.today())
        .filter(Exception.end_date >= date.today())
        .all()
    )
    for exception in exceptions_quarterly:
        today = date.today()
        future_date = today + relativedelta(months=3)
        # check if an audit test instance exists for the quarterly event
        exception_review = (
            db.query(ExceptionReview)
            .filter(ExceptionReview.exception_id == exception.id)
            .filter(ExceptionReview.created_date <= future_date)
        )
        # if it doesn't exist create one
        if not exception_review.first():
            db.add(ExceptionReview(exception_id=exception.id, review_status="not_started"))
            db.commit()
            quarterly_instances += 1
            # update exception review date to future_date
            update_exception_obj = UpdateException(next_review_date=future_date)
            # update exception review date to future_date
            await update_exception(
                db,
                exception.id,
                update_exception_obj,
                None,
                exception.tenant_id,
                exception.owner_id,
            )

    return f"Successfully created {daily_instances} exception review daily instances. Successfully created {weekly_instances} exception review weekly instances. Successfully created {monthly_instances} exception review monthly instances. Successfully created {quarterly_instances} exception review quarterly instances."


async def update_exception_review(db: Session, id: int, exception_review: UpdateExceptionReview):
    existing_exception_review = db.query(ExceptionReview).filter(ExceptionReview.id == id)
    if not existing_exception_review.first():
        return False
    audit_test_data_instance = exception_review.dict()
    update_exception_review = UpdateExceptionReview(**audit_test_data_instance)

    existing_exception_review.update(update_exception_review.dict(exclude_unset=True))

    db.commit()
    return db.query(ExceptionReview).filter(ExceptionReview.id == id).first()
