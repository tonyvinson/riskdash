from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import Session
import logging
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

from fedrisk_api.db.enums import AuditTestStatus
from fedrisk_api.db.models import (
    AuditTest,
    AuditTestCost,
    AuditTestStakeHolder,
    AuditTestInstance,
    AuditTestApprovalWorkflow,
    Control,
    Cost,
    Framework,
    Project,
    # ProjectControl,
    User,
    AuditTestDocument,
    Keyword,
    KeywordMapping,
    Risk,
    TaskAuditTest,
    AuditTestHistory,
    # UserNotifications,
    UserWatching,
    UserNotificationSettings,
)
from fedrisk_api.schema.audit_test import (
    CreateAuditTest,
    UpdateAuditTest,
    CreateAuditTestInstance,
    UpdateAuditTestInstance,
)
from fedrisk_api.utils.utils import filter_by_tenant, filter_by_user_project_role, ordering_query

# from fedrisk_api.utils.email_util import send_watch_email
# from fedrisk_api.utils.sms_util import publish_notification

from fedrisk_api.db.util.notifications_utils import (
    notify_user,
    add_notification,
    manage_notifications,
)

AUDIT_TEST_STATUS = [member.value.lower() for member in AuditTestStatus]

LOGGER = logging.getLogger(__name__)


async def manage_stakeholders(db, stakeholder_ids, audit_test, project, link):
    """Helper function to handle stakeholder notifications and associations"""
    if not stakeholder_ids:
        return
    stakeholders = db.query(User).filter(User.id.in_(stakeholder_ids)).all()
    audit_test.stakeholders = stakeholders
    for stakeholder in stakeholders:
        await add_notification(
            db,
            stakeholder.id,
            "audit_test_stakeholder",
            audit_test.id,
            f"/projects/{project.id}/audit_tests/{audit_test.id}",
            f"You've been added as a stakeholder to {audit_test.name}",
            project.id,
        )
        await notify_user(
            stakeholder, f"You've been added as a stakeholder on {audit_test.name}", link, None
        )
    db.commit()


# Keyword Management Functions
async def add_keywords(db, keywords, audit_test_id, tenant_id):
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
                .filter_by(keyword_id=keyword.id, audit_test_id=audit_test_id)
                .first()
            ):
                db.add(KeywordMapping(keyword_id=keyword.id, audit_test_id=audit_test_id))
    db.commit()


async def remove_old_keywords(db, keywords, audit_test_id):
    """Remove keywords from audit test that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(audit_test_id=audit_test_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = (
        db.query(Keyword).join(KeywordMapping).filter_by(audit_test_id=audit_test_id).all()
    )

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, audit_test_id=audit_test_id)
                .first()
            )
            db.delete(mapping)
    db.commit()


# Core CRUD Functions
async def create_audit_test(
    db: Session, keywords: str, audit_test: CreateAuditTest, tenant_id: int, user_id: int
):
    project = db.query(Project).filter_by(id=audit_test.project_id, tenant_id=tenant_id).first()
    if not project:
        return False

    audit_test_data = audit_test.dict()
    stakeholder_ids = audit_test_data.pop("stakeholder_ids", None)
    new_audit_test = AuditTest(**audit_test_data, tenant_id=tenant_id)
    db.add(new_audit_test)
    db.commit()
    db.refresh(new_audit_test)

    db.add(
        AuditTestHistory(
            audit_test_id=new_audit_test.id,
            author_id=user_id,
            history=f"Created new audit test {new_audit_test.name}",
        )
    )
    await add_notification(
        db,
        new_audit_test.tester_id,
        "audit_tests",
        new_audit_test.id,
        f"/projects/{audit_test.project_id}/audit_tests/{new_audit_test.id}",
        f"You've been assigned as a tester for audit test {new_audit_test.name}",
        project.id,
    )
    # Send email and sms updates to tester
    tester = db.query(User).filter_by(id=new_audit_test.tester_id).first()
    tester_settings = (
        db.query(UserNotificationSettings).filter_by(user_id=new_audit_test.tester_id).first()
    )
    link = f"/projects/{project.id}/audit_tests/{new_audit_test.id}"
    if tester is not None:
        await notify_user(
            tester,
            f"You've been added as a tester on audit test {new_audit_test.name}",
            link,
            tester_settings,
        )

    await add_keywords(db, keywords, new_audit_test.id, tenant_id)
    await manage_stakeholders(db, stakeholder_ids, new_audit_test, project, link)
    # Get all users watching project audit tests for this project
    message = f"Created new audit test {new_audit_test.name}"
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_audit_tests == True)
        .filter(UserWatching.project_id == project.id)
        .all()
    )
    await manage_notifications(
        db, users_watching, "audit_tests", message, link, project.id, new_audit_test.id
    )

    db.commit()
    return new_audit_test


def get_all_audit_tests(
    db: Session,
    tenant_id: int,
    user_id: int,
    project_id: int,
    framework_id: int,
    q,
    filter_by: str,
    filter_value: str,
    sort_by: str,
):
    # user = db.query(User).filter(User.id == user_id).first()

    queryset = filter_by_tenant(db, AuditTest, tenant_id)
    # if user.is_superuser:
    #     queryset = db.query(AuditTest)
    # elif user.is_tenant_admin:
    #     queryset = filter_by_tenant(db, AuditTest, tenant_id)
    # else:
    #     queryset = (
    #         filter_by_tenant(db, AuditTest, tenant_id)
    # .join(ProjectUser, ProjectUser.project_id == AuditTest.project_id)
    # .filter(ProjectUser.user_id == user_id)
    # )

    # queryset = (
    #     queryset.join(ProjectControl, ProjectControl.id == AuditTest.project_control_id)
    #     .join(Control, Control.id == ProjectControl.control_id)
    #     .options(
    #         selectinload(AuditTest.project_control),
    #         selectinload(AuditTest.project),
    #         selectinload(AuditTest.tester),
    #         selectinload(AuditTest.stakeholders),
    #     )
    # )

    if project_id:
        queryset = queryset.filter(AuditTest.project_id == project_id)

    if framework_id:
        queryset = queryset.filter(Framework.id == framework_id)

    if filter_by and filter_value:
        if filter_by == "control":
            queryset = queryset = queryset.filter(
                func.lower(Control.name).contains(filter_value.lower())
            )
        elif filter_by == "status":
            if filter_value.lower() in AUDIT_TEST_STATUS:
                filter_value = "_".join(filter_value.split(" ")).replace("-", "_")
                queryset = queryset.filter(AuditTest.status == filter_value.lower())
        else:
            queryset = queryset.filter(
                func.lower(getattr(AuditTest, filter_by)).contains(func.lower(filter_value))
            )
    elif q:
        queryset = queryset.filter(
            or_(
                func.lower(AuditTest.name).contains(func.lower(q)),
                func.lower(AuditTest.description).contains(func.lower(q)),
            )
        )

    if sort_by:
        if "control" in sort_by:
            if sort_by[0] == "-":
                queryset = queryset.order_by(Control.name.desc())
            else:
                queryset = queryset.order_by(Control.name)
        else:
            queryset = ordering_query(query=queryset, model=AuditTest.__tablename__, order=sort_by)

    return queryset.distinct()


def get_audit_test(db: Session, id: int, tenant_id: int, user_id: int):
    audit_test = (
        filter_by_user_project_role(db=db, model=AuditTest, tenant_id=tenant_id, user_id=user_id)
        .options(
            selectinload(AuditTest.project_control),
            selectinload(AuditTest.project),
            selectinload(AuditTest.tester),
            selectinload(AuditTest.stakeholders),
            selectinload(AuditTest.documents),
            selectinload(AuditTest.cap_poams),
        )
        .filter(AuditTest.id == id)
        .first()
    )
    return audit_test


async def update_audit_test(
    db: Session, id: int, keywords: str, audit_test: UpdateAuditTest, tenant_id: int, user_id: int
):
    existing_audit_test = filter_by_tenant(db, AuditTest, tenant_id).filter(AuditTest.id == id)
    if not existing_audit_test.first():
        return False
    audit_test_data = audit_test.dict(exclude_unset=True)
    stakeholder_ids = audit_test_data.pop("stakeholder_ids", None)
    # Update cost ids
    cost_ids = audit_test_data.pop("cost_ids", None)
    if cost_ids is not None or []:
        # add costs
        for cost in cost_ids:
            # check if cost id exists on tenant
            existing_cost = db.query(Cost).filter(Cost.tenant_id == tenant_id).first()
            # if the cost exists
            if existing_cost is not None:
                new_cost_map = AuditTestCost(audit_test_id=id, cost_id=cost)
                try:
                    db.add(new_cost_map)
                    db.commit()
                except:
                    LOGGER.error("Could not add cost with this ID")
    update_audit_test = UpdateAuditTest(**audit_test_data)

    changes = []
    for field in [
        "name",
        "description",
        "objective",
        "expected_results",
        "approximate_time_to_complete",
        "tester_id",
        "end_date",
        "status",
        "test_frequency",
        "last_test_date",
        "start_date",
    ]:
        if getattr(audit_test, field, None) is not None:
            if getattr(existing_audit_test.first(), field) != getattr(audit_test, field, None):
                changes.append(
                    f"Updated {field.replace('_', ' ')} to {getattr(audit_test, field, None)}"
                )
    project = (
        db.query(Project)
        .filter_by(id=existing_audit_test.first().project_id, tenant_id=tenant_id)
        .first()
    )
    link = f"/projects/{existing_audit_test.first().project_id}/audit_tests/{existing_audit_test.first().id}"
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_audit_tests == True)
        .filter(UserWatching.project_id == project.id)
        .all()
    )
    all_changes = ".    ".join(changes)
    if all_changes != "":
        await manage_notifications(
            db,
            users_watching,
            "audit_tests",
            all_changes,
            link,
            project.id,
            existing_audit_test.first().id,
        )
        for change in changes:
            db.add(
                AuditTestHistory(
                    audit_test_id=existing_audit_test.first().id, author_id=user_id, history=change
                )
            )
    await manage_stakeholders(db, stakeholder_ids, existing_audit_test.first(), project, link)
    existing_audit_test.update(update_audit_test.dict(exclude_unset=True))
    await remove_old_keywords(db, keywords, id)
    await add_keywords(db, keywords, id, tenant_id)

    db.commit()
    return get_audit_test(db=db, id=id, tenant_id=tenant_id, user_id=user_id)


async def delete_audit_test(db: Session, id: int, tenant_id: int):
    existing_audit_test = filter_by_tenant(db, AuditTest, tenant_id).filter(AuditTest.id == id)
    if not existing_audit_test.first():
        return False
    project = (
        db.query(Project)
        .join(AuditTest, AuditTest.project_id == Project.id)
        .filter(Project.id == existing_audit_test.first().project_id)
        .first()
    )
    await manage_notifications(
        db,
        db.query(UserWatching)
        .filter(UserWatching.project_audit_tests == True, UserWatching.project_id == project.id)
        .all(),
        "audit_tests",
        f"Deleted audit test {existing_audit_test.first().name}",
        f"/projects/{project.id}/audit_tests",
        project.id,
        existing_audit_test.first().id,
    )
    db.query(AuditTestStakeHolder).filter(
        AuditTestStakeHolder.audit_test_id == existing_audit_test.first().id
    ).delete()
    db.query(KeywordMapping).filter(KeywordMapping.audit_test_id == id).delete()
    db.query(AuditTestDocument).filter(AuditTestDocument.audit_test_id == id).delete()
    db.query(Risk).filter(Risk.audit_test_id == id).delete()
    db.query(TaskAuditTest).filter(TaskAuditTest.audit_test_id == id).delete()
    db.query(AuditTestHistory).filter(AuditTestHistory.audit_test_id == id).delete()
    db.query(AuditTestCost).filter(AuditTestCost.audit_test_id == id).delete()
    db.query(AuditTestApprovalWorkflow).filter(
        AuditTestApprovalWorkflow.audit_test_id == id
    ).delete()
    existing_audit_test.delete(synchronize_session=False)
    db.commit()
    return True


# DB methods for audit_test_instance to CREATE, GET by id, GET all by audit_test_id and DELETE by id
async def create_audit_test_instance(db: Session, audit_test_instance: CreateAuditTestInstance):

    audit_test_instance_data = audit_test_instance.dict()
    new_audit_test_instance = AuditTestInstance(**audit_test_instance_data)
    db.add(new_audit_test_instance)
    db.commit()

    return new_audit_test_instance


async def update_audit_test_instance(
    db: Session, audit_test_instance: UpdateAuditTestInstance, id: int
):
    existing_audit_test_instance = db.query(AuditTestInstance).filter(AuditTestInstance.id == id)
    if not existing_audit_test_instance.first():
        return False
    audit_test_instance_data = audit_test_instance.dict()
    update_audit_test_instance = UpdateAuditTestInstance(**audit_test_instance_data)

    existing_audit_test_instance.update(update_audit_test_instance.dict(exclude_unset=True))

    db.commit()
    return existing_audit_test_instance.first()


def get_audit_test_instance(db: Session, id: int, tenant_id: int, user_id: int):
    audit_test_instance = (
        filter_by_user_project_role(
            db=db, model=AuditTestInstance, tenant_id=tenant_id, user_id=user_id
        )
        .options(
            selectinload(AuditTestInstance.audit_test),
        )
        .filter(AuditTestInstance.id == id)
        .first()
    )
    LOGGER.info(audit_test_instance)
    return audit_test_instance


def get_audit_test_instance_by_audit_test_id(
    db: Session, audit_test_id: int, tenant_id: int, user_id: int
):
    audit_test_instances = (
        filter_by_user_project_role(
            db=db, model=AuditTestInstance, tenant_id=tenant_id, user_id=user_id
        )
        .options(
            selectinload(AuditTestInstance.audit_test),
        )
        .filter(AuditTestInstance.audit_test_id == audit_test_id)
        .order_by(AuditTestInstance.start_date)
        .all()
    )
    LOGGER.info(audit_test_instances)
    return audit_test_instances


async def delete_audit_test_instance(db: Session, id: int):
    existing_audit_test_instance = db.query(AuditTestInstance).filter(AuditTestInstance.id == id)
    if not existing_audit_test_instance.first():
        return False

    existing_audit_test_instance.delete(synchronize_session=False)
    db.commit()
    return True


# creates audit test instances based on audit test definitions
async def create_audit_test_instance_reoccurring(db: Session):
    daily_instances = 0
    weekly_instances = 0
    monthly_instances = 0
    quarterly_instances = 0
    annual_instances = 0
    # select all daily audit_tests that need to be created
    audit_tests_daily = (
        db.query(AuditTest)
        .filter(AuditTest.test_frequency == "daily")
        .filter(AuditTest.start_date <= date.today())
        .filter(AuditTest.end_date >= date.today())
        .filter(AuditTest.status == "on_going")
        .all()
    )
    for at in audit_tests_daily:
        # check if an audit test instance exists for the daily event
        audit_test_instance = (
            db.query(AuditTestInstance)
            .filter(AuditTestInstance.audit_test_id == at.id)
            .filter(AuditTest.start_date <= date.today())
            .filter(AuditTestInstance.start_date == date.today())
        )
        # if it doesn't exist create one
        if not audit_test_instance.first():
            db.add(
                AuditTestInstance(
                    audit_test_id=at.id, start_date=date.today(), status="not_started"
                )
            )
            db.commit()
            daily_instances += 1

    # select all weekly audit_tests that need to be created
    audit_tests_weekly = (
        db.query(AuditTest)
        .filter(AuditTest.test_frequency == "weekly")
        .filter(AuditTest.start_date <= date.today())
        .filter(AuditTest.end_date >= date.today())
        .filter(AuditTest.status == "on_going")
        .all()
    )
    for at in audit_tests_weekly:
        today = date.today()
        future_date = today + timedelta(days=7)
        # check if an audit test instance exists for the weekly event
        audit_test_instance = (
            db.query(AuditTestInstance)
            .filter(AuditTestInstance.audit_test_id == at.id)
            .filter(AuditTestInstance.start_date <= future_date)
        )
        # if it doesn't exist create one
        if not audit_test_instance.first():
            db.add(
                AuditTestInstance(
                    audit_test_id=at.id, start_date=date.today(), status="not_started"
                )
            )
            db.commit()
            weekly_instances += 1

    # select all monthly audit_tests that need to be created
    audit_tests_monthly = (
        db.query(AuditTest)
        .filter(AuditTest.test_frequency == "monthly")
        .filter(AuditTest.start_date <= date.today())
        .filter(AuditTest.end_date >= date.today())
        .filter(AuditTest.status == "on_going")
        .all()
    )
    for at in audit_tests_monthly:
        today = date.today()
        future_date = today + relativedelta(months=1)
        # check if an audit test instance exists for the monthly event
        audit_test_instance = (
            db.query(AuditTestInstance)
            .filter(AuditTestInstance.audit_test_id == at.id)
            .filter(AuditTestInstance.start_date <= future_date)
        )
        # if it doesn't exist create one
        if not audit_test_instance.first():
            db.add(
                AuditTestInstance(
                    audit_test_id=at.id, start_date=date.today(), status="not_started"
                )
            )
            db.commit()
            monthly_instances += 1
    # select all quarterly audit_tests that need to be created
    audit_tests_quarterly = (
        db.query(AuditTest)
        .filter(AuditTest.test_frequency == "quarterly")
        .filter(AuditTest.start_date <= date.today())
        .filter(AuditTest.end_date >= date.today())
        .filter(AuditTest.status == "on_going")
        .all()
    )
    for at in audit_tests_quarterly:
        today = date.today()
        future_date = today + relativedelta(months=3)
        # check if an audit test instance exists for the quarterly event
        audit_test_instance = (
            db.query(AuditTestInstance)
            .filter(AuditTestInstance.audit_test_id == at.id)
            .filter(AuditTestInstance.start_date <= future_date)
        )
        # if it doesn't exist create one
        if not audit_test_instance.first():
            db.add(
                AuditTestInstance(
                    audit_test_id=at.id, start_date=date.today(), status="not_started"
                )
            )
            db.commit()
            quarterly_instances += 1
    # select all annual audit_tests that need to be created
    audit_tests_annually = (
        db.query(AuditTest)
        .filter(AuditTest.test_frequency == "annually")
        .filter(AuditTest.start_date <= date.today())
        .filter(AuditTest.end_date >= date.today())
        .filter(AuditTest.status == "on_going")
        .all()
    )
    for at in audit_tests_annually:
        today = date.today()
        future_date = today + relativedelta(months=12)
        LOGGER.info(future_date)
        # check if an audit test instance exists for the annual event
        audit_test_instance = (
            db.query(AuditTestInstance)
            .filter(AuditTestInstance.audit_test_id == at.id)
            .filter(AuditTestInstance.start_date <= future_date)
        )
        LOGGER.info(audit_test_instance)
        # if it doesn't exist create one
        if not audit_test_instance.first():
            db.add(
                AuditTestInstance(
                    audit_test_id=at.id, start_date=date.today(), status="not_started"
                )
            )
            db.commit()
            annual_instances += 1
    return f"Successfully created {daily_instances} audit test daily instances. Successfully created {weekly_instances} audit test weekly instances. Successfully created {monthly_instances} audit test monthly instances. Successfully created {quarterly_instances} audit test quarterly instances. Successfully created {annual_instances} audit test annual instances."


async def update_audit_test_instance(
    db: Session, id: int, audit_test_instance: UpdateAuditTestInstance
):
    existing_audit_test_instance = db.query(AuditTestInstance).filter(AuditTestInstance.id == id)
    if not existing_audit_test_instance.first():
        return False
    audit_test_data_instance = audit_test_instance.dict()
    update_audit_test_instance = UpdateAuditTestInstance(**audit_test_data_instance)

    existing_audit_test_instance.update(update_audit_test_instance.dict(exclude_unset=True))

    db.commit()
    return db.query(AuditTestInstance).filter(AuditTestInstance.id == id).first()
