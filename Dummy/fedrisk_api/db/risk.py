import logging

from fastapi import HTTPException, status
from sqlalchemy import and_, case, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import Session
from sqlalchemy.exc import IntegrityError

from fedrisk_api.db.models import (
    Cost,
    Project,
    ProjectUser,
    Risk,
    RiskApprovalWorkflow,
    RiskCategory,
    RiskCost,
    RiskImpact,
    RiskLikelihood,
    RiskStakeholder,
    RiskStatus,
    User,
    TaskRisk,
    Task,
    # Document,
    RiskDocument,
    Keyword,
    KeywordMapping,
    RiskHistory,
    UserNotifications,
    UserWatching,
    # UserNotificationSettings,
)
from fedrisk_api.schema.risk import CreateRisk, UpdateRisk
from fedrisk_api.utils.utils import (
    filter_by_tenant,
    get_risk_mapping_metrics,
    get_risk_mapping_order,
    ordering_query,
)

# from fedrisk_api.utils.email_util import send_watch_email

# from fedrisk_api.utils.sms_util import publish_notification

from fedrisk_api.db.util.notifications_utils import (
    # notify_user,
    # add_notification,
    manage_notifications,
)

risk_mapping_metrics = get_risk_mapping_metrics()
risk_mapping_order = get_risk_mapping_order()

LOGGER = logging.getLogger(__name__)

RISK_ATTRIBUTES = {
    "risk_score": {"10", "5", "1"},
    "risk_status": {"Active", "On Hold", "Completed", "Cancelled"},
    "risk_category": {
        "Access Management",
        "Environmental Resilience",
        "Monitoring",
        "Physical Security",
        "Policy & Procedure",
        "Sensitive Data Management",
        "Technical Vulnerability",
        "Third Party Management",
    },
    "risk_impact": {"Insignificant", "Minor", "Moderate", "Major", "Extreme"},
    "risk_likelihood": {"Very Likely", "Likely", "Possible", "Unlikely", "Very Unlikely"},
}

# Keyword Management Functions
async def add_keywords(db, keywords, risk_id, tenant_id):
    """Link keywords to risk."""
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
                .filter_by(keyword_id=keyword.id, risk_id=risk_id)
                .first()
            ):
                db.add(KeywordMapping(keyword_id=keyword.id, risk_id=risk_id))
    db.commit()


async def remove_old_keywords(db, keywords, risk_id):
    """Remove keywords from risk that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(risk_id=risk_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = db.query(Keyword).join(KeywordMapping).filter_by(risk_id=risk_id).all()

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping).filter_by(keyword_id=keyword.id, risk_id=risk_id).first()
            )
            db.delete(mapping)
    db.commit()


async def create_risk(db: Session, risk: CreateRisk, tenant_id: int, keywords: str, user_id: int):

    project = db.query(Project).filter(Project.id == risk.project_id).first()

    if not project.tenant_id == tenant_id:
        return False

    if risk.project_control_id:
        if not int(risk.project_control_id) in [
            project_control.id for project_control in project.project_controls
        ]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Control with id {risk.project_control_id} is not associated with "
                f"project with id {risk.project_id}",
            )
    if risk.audit_test_id:
        if not int(risk.audit_test_id) in [audit_test.id for audit_test in project.audit_tests]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"AuditTest with id {risk.audit_test_id} is not associated with "
                f"project with id {risk.project_id}",
            )

    risk_dict = risk.dict()
    stake_holder_ids = risk_dict.pop("additional_stakeholder_ids")
    new_risk = Risk(**risk_dict, tenant_id=tenant_id)
    db.add(new_risk)
    db.commit()
    db.refresh(new_risk)
    if stake_holder_ids:
        risk_stakeholders = db.query(User).filter(User.id.in_(stake_holder_ids)).all()
        new_risk.additional_stakeholders = risk_stakeholders
        # create notifications for stakeholders
        for stakeholder in stake_holder_ids:
            if stakeholder != 0:
                notification = {
                    "user_id": stakeholder,
                    "notification_data_type": "risk_stakeholder",
                    "notification_data_id": new_risk.id,
                    "notification_data_path": f"/projects/{project.id}/risks/{new_risk.id}",
                    "notification_message": f"You've been added as a stakeholder to {new_risk.name}",
                    "project_id": project.id,
                }
                new_notification = UserNotifications(**notification)
                db.add(new_notification)
                db.commit()
    db.add(new_risk)
    db.commit()
    # Add history
    history = {
        "risk_id": new_risk.id,
        "author_id": user_id,
        "history": f"Created a risk {new_risk.name}",
    }
    new_history = RiskHistory(**history)
    db.add(new_history)
    db.commit()
    # Get all users watching project risks for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_risks == True)
        .filter(UserWatching.project_id == project.id)
        .all()
    )
    await manage_notifications(
        db,
        users_watching,
        "risks",
        f"Created new risk {new_risk.name}",
        f"/projects/{project.id}/risks/{new_risk.id}",
        project.id,
        new_risk.id,
    )
    # add keywords
    await add_keywords(db, keywords, new_risk.id, tenant_id)
    return new_risk


def get_all_risks(
    tenant_id: int,
    project_id: int,
    db: Session,
    q: str = None,
    filter_by: str = None,
    filter_value: str = None,
    sort_by: str = "-created_date",
):
    queryset = (
        filter_by_tenant(db, Risk, tenant_id)
        .join(RiskStatus, RiskStatus.id == Risk.risk_status_id)
        .join(RiskCategory, RiskCategory.id == Risk.risk_category_id)
        .join(RiskImpact, RiskImpact.id == Risk.risk_impact_id)
        .join(RiskLikelihood, RiskLikelihood.id == Risk.current_likelihood_id)
        .join(Project, Project.id == Risk.project_id)
        .options(
            selectinload(Risk.project),
            selectinload(Risk.current_likelihood),
            selectinload(Risk.risk_score),
            selectinload(Risk.risk_category),
            selectinload(Risk.risk_impact),
            selectinload(Risk.risk_status),
            selectinload(Risk.project_control),
            selectinload(Risk.audit_test),
            selectinload(Risk.additional_stakeholders),
        )
    )
    if project_id:
        queryset = queryset.filter(Risk.project_id == project_id)

    if filter_by and filter_value:
        if filter_by == "risk_status":
            queryset = queryset.filter(
                func.lower(RiskStatus.name).contains(func.lower(filter_value))
            )
        elif filter_by == "risk_category":
            queryset = queryset.filter(
                func.lower(RiskCategory.name).contains(func.lower(filter_value))
            )
        elif filter_by == "risk_impact":
            queryset = queryset.filter(
                func.lower(RiskImpact.name).contains(func.lower(filter_value))
            )
        elif filter_by == "risk_mapping":
            filter_value = "_".join(map(lambda x: x.lower(), filter_value.split("-")))
            risk_mapping = risk_mapping_metrics.get(filter_value.lower(), None)
            if risk_mapping:
                conditions = []
                for mapping in risk_mapping:
                    risk_likelihood, risk_impact = mapping.split("__")
                    risk_impact_condition = RiskImpact.name == risk_impact.title()
                    risk_likelihood_condition = RiskLikelihood.name == " ".join(
                        map(lambda x: x.title(), risk_likelihood.split("_"))
                    )
                    conditions.append(and_(risk_impact_condition, risk_likelihood_condition))
                queryset = queryset.filter(or_(*conditions))
        elif filter_by == "project":
            queryset = queryset.filter(func.lower(Project.name).contains(func.lower(filter_value)))
        else:
            queryset = queryset.filter(
                func.lower(getattr(Risk, filter_by)).contains(func.lower(filter_value))
            )
    elif q:
        queryset = queryset.filter(
            or_(
                func.lower(Risk.name).contains(func.lower(q)),
                func.lower(Risk.description).contains(func.lower(q)),
                func.lower(Risk.keywords).contains(func.lower(q)),
            )
        )

    if sort_by:
        if "risk_status" in sort_by:
            if sort_by[0] == "-":
                queryset = queryset.order_by(RiskStatus.name.desc())
            else:
                queryset = queryset.order_by(RiskStatus.name)
        elif "risk_category" in sort_by:
            if sort_by[0] == "-":
                queryset = queryset.order_by(RiskCategory.name.desc())
            else:
                queryset = queryset.order_by(RiskCategory.name)
        elif "risk_impact" in sort_by:
            if sort_by[0] == "-":
                queryset = queryset.order_by(RiskImpact.name.desc())
            else:
                queryset = queryset.order_by(RiskImpact.name)
        elif "project" in sort_by:
            if sort_by[0] == "-":
                queryset = queryset.order_by(Project.name.desc())
            else:
                queryset = queryset.order_by(Project.name)
        elif "risk_mapping" in sort_by:
            order_list = []
            for key, risk_mapping in risk_mapping_metrics.items():
                key = risk_mapping_order.get(key)
                for mapping in risk_mapping:
                    risk_likelihood, risk_impact = mapping.split("__")
                    risk_impact_condition = RiskImpact.name == risk_impact.title()
                    risk_likelihood_condition = RiskLikelihood.name == " ".join(
                        map(lambda x: x.title(), risk_likelihood.split("_"))
                    )
                    order_list.append((and_(risk_impact_condition, risk_likelihood_condition), key))
            order_by_case = case(order_list)

            if sort_by[0] == "-":
                queryset = queryset.order_by(order_by_case.desc())
            else:
                queryset = queryset.order_by(order_by_case)

        else:
            queryset = ordering_query(query=queryset, model=Risk.__tablename__, order=sort_by)

    return queryset.distinct()


def get_all_risks_with_tasks_by_project(tenant_id: int, project_id: int, db: Session):
    risks = (
        db.query(Risk)
        .filter(Risk.project_id == project_id)
        .filter(Risk.tenant_id == tenant_id)
        .all()
    )

    for risk in risks:
        # Fetch tasks for the risk
        tasks = (
            db.query(Task.id.label("id"), Task.title.label("title"), Task.name.label("name"))
            .select_from(TaskRisk, Task)
            .join(Task, TaskRisk.task_id == Task.id)
            .filter(TaskRisk.risk_id == risk.id)
            .all()
        )
        risk.tasks = list(tasks)

        # Fetch likelihood and impact values
        risk_map_values = (
            db.query(
                RiskLikelihood.name.label("current_likelihood"),
                RiskImpact.name.label("risk_impact"),
            )
            .select_from(Risk)
            .join(RiskLikelihood, RiskLikelihood.id == Risk.current_likelihood_id)
            .join(RiskImpact, RiskImpact.id == Risk.risk_impact_id)
            .filter(Risk.id == risk.id)
            .first()
        )

        if not risk_map_values:
            risk.risk_mapping = "n/a"
            continue

        current_likelihood_name = "_".join(risk_map_values.current_likelihood.split(" "))
        risk_matrics_key = f"{current_likelihood_name}__{risk_map_values.risk_impact}".lower()

        risk_mapping = "n/a"
        for key, value in risk_mapping_metrics.items():
            if risk_matrics_key in set(value):
                risk_mapping = key
                break

        risk.risk_mapping = risk_mapping

    return risks


def get_risk(db: Session, id: int, tenant_id: int):
    risk = db.query(Risk).filter(Risk.id == id).filter(Risk.tenant_id == tenant_id).first()
    tasks = (
        db.query(Task.id.label("id"), Task.title.label("title"), Task.name.label("name"))
        .select_from(TaskRisk, Task)
        .join(Task, TaskRisk.task_id == Task.id)
        .filter(TaskRisk.risk_id == risk.id)
        .all()
    )
    tasksarr = []
    for task in tasks:
        tasksarr.append(task)
    risk.tasks = tasksarr
    risk_map_values = (
        db.query(
            RiskLikelihood.name.label("current_likelihood"), RiskImpact.name.label("risk_impact")
        )
        .select_from(Risk)
        .join(RiskLikelihood, RiskLikelihood.id == Risk.current_likelihood_id)
        .join(RiskImpact, RiskImpact.id == Risk.risk_impact_id)
        .filter(Risk.id == id)
    )
    if risk_map_values.first() is not None:
        risk_mapping = ""
        current_likelihood_name = "_".join(risk_map_values.first().current_likelihood.split(" "))
        if risk_map_values.first().risk_impact is not None:
            risk_matrics_key = (
                f"{current_likelihood_name}__{risk_map_values.first().risk_impact}".lower()
            )
            for key, value in risk_mapping_metrics.items():
                for risk_matrics in set(value):
                    if risk_matrics_key == risk_matrics:
                        risk_mapping = key
            risk.risk_mapping = risk_mapping
    return risk


async def update_risk(
    db: Session, id: int, risk: UpdateRisk, tenant_id: int, keywords: str, user_id: int
):
    existing_risk = filter_by_tenant(db, Risk, tenant_id).filter(Risk.id == id)
    if not existing_risk.first():
        return False

    risk_update_dict = risk.dict(exclude_unset=True)
    try:
        stake_holder_ids = risk_update_dict.pop("additional_stakeholder_ids")
    except KeyError as e:
        stake_holder_ids = None
    # Update costs
    cost_ids = risk_update_dict.pop("cost_ids", None)
    if cost_ids is not None or []:
        # add costs
        for cost in cost_ids:
            # check if cost id exists on tenant
            existing_cost = db.query(Cost).filter(Cost.tenant_id == tenant_id).first()
            # if the cost exists
            if existing_cost is not None:
                new_cost_map = RiskCost(risk_id=id, cost_id=cost)
                try:
                    db.add(new_cost_map)
                    db.commit()
                except:
                    LOGGER.error("Could not add cost with this ID")

    # get project
    project = db.query(Project).filter(Project.id == existing_risk.first().project_id).first()
    # Get changes and add notifications and history
    changes = []
    for field in [
        "name",
        "description",
        "project_control_id",
        "audit_test_id",
        "risk_status_id",
        "risk_impact_id",
        "risk_category_id",
        "risk_score_id",
        "current_likelihood_id",
        "comments",
        "additional_notes",
        "technology",
        "current_impact",
        "risk_assessment",
        "affected_assets",
        "owner_id",
        "owner_supervisor",
    ]:
        if getattr(risk, field, None) is not None:
            if getattr(existing_risk.first(), field) != getattr(risk, field, None):
                changes.append(f"Updated {field.replace('_', ' ')} to {getattr(risk, field, None)}")
    link = f"/projects/{project.id}/risks/{existing_risk.first().id}"
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_risks == True)
        .filter(UserWatching.project_id == project.id)
        .all()
    )
    all_changes = ".    ".join(changes)
    if all_changes != "":
        await manage_notifications(
            db,
            users_watching,
            "risks",
            all_changes,
            link,
            project.id,
            existing_risk.first().id,
        )
        for change in changes:
            try:
                new_record = RiskHistory(
                    risk_id=existing_risk.first().id, author_id=user_id, history=change
                )
                db.add(new_record)
                db.commit()
            except IntegrityError as e:
                print(f"IntegrityError occurred: {e}")
                db.rollback()
    if len(risk_update_dict) != 0:
        existing_risk.update(risk_update_dict)
    existing_risk = existing_risk.first()
    if stake_holder_ids:
        risk_stakeholders = db.query(User).filter(User.id.in_(stake_holder_ids)).all()
        existing_risk.additional_stakeholders = risk_stakeholders
    await remove_old_keywords(db, keywords, id)
    await add_keywords(db, keywords, id, tenant_id)
    db.commit()
    return existing_risk


async def delete_risk(db: Session, id: int, tenant_id: int):
    existing_risk = filter_by_tenant(db, Risk, tenant_id).filter(Risk.id == id)
    project = db.query(Project).filter(Project.id == existing_risk.first().project_id).first()
    if not existing_risk.first():
        return False
    # Get all users watching project risks for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_risks == True)
        .filter(UserWatching.project_id == project.id)
        .all()
    )
    await manage_notifications(
        db,
        users_watching,
        "risks",
        f"Deleted risk {existing_risk.first().name}",
        f"/projects/{project.id}/risks",
        project.id,
        existing_risk.first().id,
    )
    additional_stakeholders = db.query(RiskStakeholder).filter(
        RiskStakeholder.risk_id == existing_risk.first().id
    )
    additional_stakeholders.delete(synchronize_session=False)
    task_risks = db.query(TaskRisk).filter(TaskRisk.risk_id == existing_risk.first().id)
    task_risks.delete(synchronize_session=False)
    # delete all history references
    db.query(RiskHistory).filter(RiskHistory.risk_id == id).delete()
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.risk_id == id).delete()
    # delete all document references
    db.query(RiskDocument).filter(RiskDocument.risk_id == id).delete()
    # delete all cost references
    db.query(RiskCost).filter(RiskCost.risk_id == id).delete()
    # delete all approval workflow references
    db.query(RiskApprovalWorkflow).filter(RiskApprovalWorkflow.risk_id == id).delete()
    existing_risk.delete(synchronize_session=False)
    db.commit()
    return True


def search(query: str, db: Session, tenant_id: int, user_id: int, offset: int = 0, limit: int = 10):
    lowercase_query = query.lower()

    user = db.query(User).filter(User.id == user_id).first()

    if user.is_superuser:
        res = (
            db.query(Risk)
            .filter(
                or_(
                    func.lower(Risk.name).contains(lowercase_query),
                    func.lower(Risk.description).contains(lowercase_query),
                    func.lower(Risk.keywords).contains(lowercase_query),
                )
            )
            .all()
        )
    elif user.is_tenant_admin:
        res = (
            filter_by_tenant(db, Risk, tenant_id)
            .filter(
                or_(
                    func.lower(Risk.name).contains(lowercase_query),
                    func.lower(Risk.description).contains(lowercase_query),
                    func.lower(Risk.keywords).contains(lowercase_query),
                )
            )
            .all()
        )
    else:
        res = (
            filter_by_tenant(db, Risk, tenant_id)
            .join(ProjectUser, ProjectUser.id == Risk.project_id)
            .filter(ProjectUser.user_id == user_id)
            .filter(
                or_(
                    func.lower(Risk.name).contains(lowercase_query),
                    func.lower(Risk.description).contains(lowercase_query),
                    func.lower(Risk.keywords).contains(lowercase_query),
                )
            )
            .all()
        )

    if user.is_superuser:
        count = (
            db.query(Risk)
            .filter(
                or_(
                    func.lower(Risk.name).contains(lowercase_query),
                    func.lower(Risk.description).contains(lowercase_query),
                    func.lower(Risk.keywords).contains(lowercase_query),
                )
            )
            .count()
        )
    elif user.is_tenant_admin:
        count = (
            filter_by_tenant(db, Risk, tenant_id)
            .filter(
                or_(
                    func.lower(Risk.name).contains(lowercase_query),
                    func.lower(Risk.description).contains(lowercase_query),
                    func.lower(Risk.keywords).contains(lowercase_query),
                )
            )
            .distinct()
            .count()
        )
    else:
        count = (
            filter_by_tenant(db, Risk, tenant_id)
            .join(ProjectUser, ProjectUser.id == Risk.project_id)
            .filter(ProjectUser.user_id == user_id)
            .filter(
                or_(
                    func.lower(Risk.name).contains(lowercase_query),
                    func.lower(Risk.description).contains(lowercase_query),
                    func.lower(Risk.keywords).contains(lowercase_query),
                )
            )
            .distinct()
            .count()
        )

    return count, res[offset : offset + limit]
