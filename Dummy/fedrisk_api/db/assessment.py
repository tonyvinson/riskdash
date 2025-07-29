import logging
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.orm.session import Session
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from fedrisk_api.db.models import (
    Assessment,
    Cost,
    ProjectControl,
    # ProjectUser,
    # User,
    Keyword,
    KeywordMapping,
    AssessmentCost,
    AssessmentHistory,
    AssessmentInstance,
    UserWatching,
    Project,
    # UserNotifications,
    # UserNotificationSettings,
)
from fedrisk_api.schema.assessment import (
    CreateAssessment,
    UpdateAssessment,
    CreateAssessmentInstance,
    UpdateAssessmentInstance,
)

from fedrisk_api.utils.utils import filter_by_tenant, filter_by_user_project_role

# from fedrisk_api.db import history as db_history

# from fedrisk_api.utils.email_util import send_watch_email
# from fedrisk_api.utils.sms_util import publish_notification

from fedrisk_api.db.util.notifications_utils import (
    # notify_user,
    # add_notification,
    manage_notifications,
)

LOGGER = logging.getLogger(__name__)

# Keyword Management Functions
async def add_keywords(db, keywords, assessment_id, tenant_id):
    """Link keywords to audit test."""
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
                .filter_by(keyword_id=keyword.id, assessment_id=assessment_id)
                .first()
            ):
                db.add(KeywordMapping(keyword_id=keyword.id, assessment_id=assessment_id))
    db.commit()


async def remove_old_keywords(db, keywords, assessment_id):
    """Remove keywords from audit test that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(assessment_id=assessment_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = (
        db.query(Keyword).join(KeywordMapping).filter_by(assessment_id=assessment_id).all()
    )

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, assessment_id=assessment_id)
                .first()
            )
            db.delete(mapping)
    db.commit()


async def create_assessment(
    db: Session, assessment: CreateAssessment, user_id: int, tenant_id: int
):
    new_assessment = Assessment(**assessment.dict())
    db.add(new_assessment)
    db.commit()
    db.refresh(new_assessment)
    history = {
        "assessment_id": new_assessment.id,
        "author_id": user_id,
        "history": f"Created new assessment {new_assessment.name}",
    }
    new_history = AssessmentHistory(**history)
    db.add(new_history)
    db.commit()
    # project = (
    #     db.query(Project)
    #     .join(ProjectControl, Project.id == ProjectControl.project_id)
    #     .join(Assessment, Assessment.project_control_id == ProjectControl.id)
    #     .filter(Assessment.project_control_id == new_assessment.project_control_id)
    #     .first()
    # )
    # # Get all users watching project assessments for this project
    # users_watching = (
    #     db.query(UserWatching)
    #     .filter(UserWatching.project_assessments == True)
    #     .filter(UserWatching.project_id == project.id)
    #     .all()
    # )
    # message = f"Created new assessment {new_assessment.name} for {project.name}"
    # link = f"/projects/{project.id}/controls/{new_assessment.project_control_id}/assessments/{new_assessment.id}"
    # await manage_notifications(
    #     db, users_watching, "assessments", message, link, project.id, new_assessment.id
    # )
    return new_assessment


def get_all_assessments(db: Session, tenant_id: int, project_id: str):
    if project_id is None:
        assessments = (
            filter_by_tenant(db, Assessment, tenant_id)
            .options(
                selectinload(Assessment.project_control).selectinload(ProjectControl.project),
                selectinload(Assessment.project_control).selectinload(ProjectControl.control)
                # .selectinload(Control.framework),
            )
            .all()
        )
        return assessments
    if project_id != "":
        assessments = (
            filter_by_tenant(db, Assessment, tenant_id)
            .options(
                selectinload(Assessment.project_control).selectinload(ProjectControl.project),
                selectinload(Assessment.project_control).selectinload(ProjectControl.control)
                # .selectinload(Control.framework),
            )
            .filter(ProjectControl.project_id == project_id)
            .all()
        )
        return assessments


def get_assessment(db: Session, id: int, tenant_id: int):
    assessment = (
        db.query(Assessment)
        .filter(Assessment.id == id)
        .options(
            joinedload(Assessment.project_control).joinedload(ProjectControl.project),
            joinedload(Assessment.project_control).joinedload(ProjectControl.control)
            # .joinedload(Control.framework),
        )
        .first()
    )
    return assessment


async def update_assessment(
    db: Session, id: int, keywords: str, assessment: UpdateAssessment, tenant_id: int, user_id: int
):
    existing_assessment = db.query(Assessment).filter(Assessment.id == id)
    existing_assessment_obj = existing_assessment.first()
    if not existing_assessment_obj:
        return False

    assessment_data = assessment.dict(exclude_unset=True)
    cost_ids = assessment_data.pop("cost_ids", None)

    if cost_ids:  # Properly check if cost_ids is not None or empty
        for cost in cost_ids:
            existing_cost = (
                db.query(Cost).filter(Cost.id == cost, Cost.tenant_id == tenant_id).first()
            )
            if existing_cost:
                new_cost_map = AssessmentCost(assessment_id=id, cost_id=cost)
                try:
                    db.add(new_cost_map)
                    db.commit()
                except Exception as e:
                    LOGGER.error(f"Could not add cost with ID {cost}: {e}")

    # Get project
    project = (
        db.query(Project)
        .join(ProjectControl, Project.id == ProjectControl.project_id)
        .join(Assessment, Assessment.project_control_id == ProjectControl.id)
        .filter(Assessment.project_control_id == existing_assessment_obj.project_control_id)
        .first()
    )

    # Get users watching this project’s assessments
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_assessments == True, UserWatching.project_id == project.id)
        .all()
    )

    link = f"/projects/{project.id}/controls/{existing_assessment_obj.project_control_id}/assessments/{existing_assessment_obj.id}"

    # Track changes for history
    changes = []
    for field in ["name", "description", "status", "is_assessment_confirmed", "comments"]:
        new_value = getattr(assessment, field, None)
        if getattr(existing_assessment_obj, field) != new_value and new_value is not None:
            changes.append(f"Updated {field.replace('_', ' ')} to {new_value}")

    if changes:  # Only notify if there are actual changes
        all_changes = ".    ".join(changes)
        await manage_notifications(
            db,
            users_watching,
            "assessments",
            all_changes,
            link,
            project.id,
            existing_assessment_obj.id,
        )

    # Write changes to history
    for change in changes:
        db.add(
            AssessmentHistory(
                assessment_id=existing_assessment_obj.id, author_id=user_id, history=change
            )
        )

    # Update the assessment properly
    for key, value in assessment_data.items():
        setattr(existing_assessment_obj, key, value)

    db.commit()

    await remove_old_keywords(db, keywords, id)
    await add_keywords(db, keywords, id, tenant_id)

    return existing_assessment_obj


async def delete_assessment(db: Session, id: int, tenant_id: int):
    existing_assessment = filter_by_tenant(db, Assessment, tenant_id).filter(Assessment.id == id)
    if not existing_assessment.first():
        return False
    project = (
        db.query(Project)
        .join(ProjectControl, Project.id == ProjectControl.project_id)
        .join(Assessment, Assessment.project_control_id == ProjectControl.id)
        .filter(Assessment.project_control_id == existing_assessment.first().project_control_id)
        .first()
    )
    # Get all users watching project assessments for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_assessments == True)
        .filter(UserWatching.project_id == project.id)
        .all()
    )
    link = f"/projects/{project.id}/controls/{existing_assessment.first().project_control_id}/assessments/{existing_assessment.first().id}"
    message = f"Deleted assessment."
    await manage_notifications(
        db,
        users_watching,
        "assessments",
        message,
        link,
        project.id,
        existing_assessment.first().id,
    )
    # delete all history
    db.query(AssessmentHistory).filter(AssessmentHistory.assessment_id == id).delete()
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.assessment_id == id).delete()
    # delete all costs
    db.query(AssessmentCost).filter(AssessmentCost.assessment_id == id).delete()
    # delete all instances
    db.query(AssessmentInstance).filter(AssessmentInstance.assessment_id == id).delete()
    existing_assessment.delete(synchronize_session=False)
    db.commit()
    return True


def search(query: str, db: Session, tenant_id: int, user_id: int, offset: int = 0, limit: int = 10):
    lowercase_query = query.lower()
    res = (
        db.query(Assessment)
        .filter(
            or_(
                func.lower(Assessment.name).contains(lowercase_query),
                func.lower(Assessment.description).contains(lowercase_query),
                func.lower(Assessment.keywords).contains(lowercase_query),
            )
        )
        .all()
    )
    count = (
        db.query(Assessment)
        .filter(
            or_(
                func.lower(Assessment.name).contains(lowercase_query),
                func.lower(Assessment.description).contains(lowercase_query),
                func.lower(Assessment.keywords).contains(lowercase_query),
            )
        )
        .count()
    )


# DB methods for assessment_instance to CREATE, GET by id, GET all by assessment_id and DELETE by id
async def create_assessment_instance(db: Session, assessment_instance: CreateAssessmentInstance):

    assessment_instance_data = assessment_instance.dict()
    new_assessment_instance = AssessmentInstance(**assessment_instance_data)
    db.add(new_assessment_instance)
    db.commit()

    return new_assessment_instance


async def update_assessment_instance(
    db: Session, assessment_instance: UpdateAssessmentInstance, id: int
):
    existing_assessment_instance = db.query(AssessmentInstance).filter(AssessmentInstance.id == id)
    if not existing_assessment_instance.first():
        return False
    assessment_instance_data = assessment_instance.dict()
    update_assessment_instance = UpdateAssessmentInstance(**assessment_instance_data)

    existing_assessment_instance.update(update_assessment_instance.dict(exclude_unset=True))

    db.commit()
    return existing_assessment_instance.first()


def get_assessment_instance(db: Session, id: int, tenant_id: int, user_id: int):
    assessment_instance = (
        filter_by_user_project_role(
            db=db, model=AssessmentInstance, tenant_id=tenant_id, user_id=user_id
        )
        .options(
            selectinload(AssessmentInstance.assessment),
        )
        .filter(AssessmentInstance.id == id)
        .first()
    )
    LOGGER.info(assessment_instance)
    return assessment_instance


def get_assessment_instance_by_assessment_id(
    db: Session, assessment_id: int, tenant_id: int, user_id: int
):
    assessment_instances = (
        db.query(AssessmentInstance).filter(AssessmentInstance.assessment_id == assessment_id).all()
    )
    return assessment_instances


async def delete_assessment_instance(db: Session, id: int):
    existing_assessment_instance = db.query(AssessmentInstance).filter(AssessmentInstance.id == id)
    if not existing_assessment_instance.first():
        return False

    existing_assessment_instance.delete(synchronize_session=False)
    db.commit()
    return True


# creates audit test instances based on audit test definitions
async def create_assessment_instance_reoccurring(db: Session):
    daily_instances = 0
    weekly_instances = 0
    monthly_instances = 0
    quarterly_instances = 0
    annual_instances = 0
    # select all daily assessments that need to be created
    assessments_daily = (
        db.query(Assessment)
        .filter(Assessment.test_frequency == "daily")
        .filter(Assessment.start_date <= date.today())
        .filter(Assessment.end_date >= date.today())
        # .filter(Assessment.status == "on_going")
        .all()
    )
    for at in assessments_daily:
        # check if an audit test instance exists for the daily event
        assessment_instance = (
            db.query(AssessmentInstance)
            .filter(AssessmentInstance.assessment_id == at.id)
            .filter(Assessment.start_date <= date.today())
            .filter(AssessmentInstance.created_date == date.today())
        )
        # if it doesn't exist create one
        if not assessment_instance.first():
            db.add(AssessmentInstance(assessment_id=at.id, review_status="not_started"))
            db.commit()
            daily_instances += 1

    # select all weekly assessments that need to be created
    assessments_weekly = (
        db.query(Assessment)
        .filter(Assessment.test_frequency == "weekly")
        .filter(Assessment.start_date <= date.today())
        .filter(Assessment.end_date >= date.today())
        # .filter(Assessment.status == "on_going")
        .all()
    )
    for at in assessments_weekly:
        today = date.today()
        future_date = today + timedelta(days=7)
        # check if an audit test instance exists for the weekly event
        assessment_instance = (
            db.query(AssessmentInstance)
            .filter(AssessmentInstance.assessment_id == at.id)
            .filter(AssessmentInstance.created_date <= future_date)
        )
        # if it doesn't exist create one
        if not assessment_instance.first():
            db.add(AssessmentInstance(assessment_id=at.id, review_status="not_started"))
            db.commit()
            weekly_instances += 1

    # select all monthly assessments that need to be created
    assessments_monthly = (
        db.query(Assessment)
        .filter(Assessment.test_frequency == "monthly")
        .filter(Assessment.start_date <= date.today())
        .filter(Assessment.end_date >= date.today())
        # .filter(Assessment.status == "on_going")
        .all()
    )
    for at in assessments_monthly:
        today = date.today()
        future_date = today + relativedelta(months=1)
        # check if an audit test instance exists for the monthly event
        assessment_instance = (
            db.query(AssessmentInstance)
            .filter(AssessmentInstance.assessment_id == at.id)
            .filter(AssessmentInstance.created_date <= future_date)
        )
        # if it doesn't exist create one
        if not assessment_instance.first():
            db.add(AssessmentInstance(assessment_id=at.id, review_status="not_started"))
            db.commit()
            monthly_instances += 1
    # select all quarterly assessments that need to be created
    assessments_quarterly = (
        db.query(Assessment)
        .filter(Assessment.test_frequency == "quarterly")
        .filter(Assessment.start_date <= date.today())
        .filter(Assessment.end_date >= date.today())
        # .filter(Assessment.status == "on_going")
        .all()
    )
    for at in assessments_quarterly:
        today = date.today()
        future_date = today + relativedelta(months=3)
        # check if an audit test instance exists for the quarterly event
        assessment_instance = (
            db.query(AssessmentInstance)
            .filter(AssessmentInstance.assessment_id == at.id)
            .filter(AssessmentInstance.created_date <= future_date)
        )
        # if it doesn't exist create one
        if not assessment_instance.first():
            db.add(AssessmentInstance(assessment_id=at.id, review_status="not_started"))
            db.commit()
            quarterly_instances += 1
    # select all annual assessments that need to be created
    assessments_annually = (
        db.query(Assessment)
        .filter(Assessment.test_frequency == "annually")
        .filter(Assessment.start_date <= date.today())
        .filter(Assessment.end_date >= date.today())
        # .filter(Assessment.status == "on_going")
        .all()
    )
    for at in assessments_annually:
        today = date.today()
        future_date = today + relativedelta(months=12)
        LOGGER.info(future_date)
        # check if an audit test instance exists for the annual event
        assessment_instance = (
            db.query(AssessmentInstance)
            .filter(AssessmentInstance.assessment_id == at.id)
            .filter(AssessmentInstance.created_date <= future_date)
        )
        LOGGER.info(assessment_instance)
        # if it doesn't exist create one
        if not assessment_instance.first():
            db.add(AssessmentInstance(assessment_id=at.id, review_status="not_started"))
            db.commit()
            annual_instances += 1
    return f"Successfully created {daily_instances} assessment daily instances. Successfully created {weekly_instances} assessment weekly instances. Successfully created {monthly_instances} assessment monthly instances. Successfully created {quarterly_instances} assessment quarterly instances. Successfully created {annual_instances} assessment annual instances."


async def update_assessment_instance(
    db: Session, id: int, assessment_instance: UpdateAssessmentInstance
):
    existing_assessment_instance = db.query(AssessmentInstance).filter(AssessmentInstance.id == id)
    if not existing_assessment_instance.first():
        return False
    assessment_data_instance = assessment_instance.dict()
    update_assessment_instance = UpdateAssessmentInstance(**assessment_data_instance)

    existing_assessment_instance.update(update_assessment_instance.dict(exclude_unset=True))

    db.commit()
    return db.query(AssessmentInstance).filter(AssessmentInstance.id == id).first()
