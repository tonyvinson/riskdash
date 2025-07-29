import logging

from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import (
    Cost,
    Project,
    ProjectEvaluation,
    ProjectUser,
    User,
    ProjectEvaluationApprovalWorkflow,
    ProjectEvaluationCost,
    ProjectEvaluationDocument,
    # Document,
    KeywordMapping,
    Keyword,
    ProjectEvaluationHistory,
    UserWatching,
    # UserNotifications,
    # UserNotificationSettings,
)
from fedrisk_api.schema.project_evaluation import CreateProjectEvaluation, UpdateProjectEvaluation
from fedrisk_api.utils.utils import filter_by_tenant, filter_by_user_project_role

# from fedrisk_api.utils.email_util import send_watch_email
# from fedrisk_api.utils.sms_util import publish_notification

from fedrisk_api.db.util.notifications_utils import (
    # notify_user,
    # add_notification,
    manage_notifications,
)

LOGGER = logging.getLogger(__name__)

# Keyword Management Functions
async def add_keywords(db, keywords, project_evaluation_id, tenant_id):
    """Link keywords to project evaluation."""
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
                .filter_by(keyword_id=keyword.id, project_evaluation_id=project_evaluation_id)
                .first()
            ):
                db.add(
                    KeywordMapping(
                        keyword_id=keyword.id, project_evaluation_id=project_evaluation_id
                    )
                )
    db.commit()


async def remove_old_keywords(db, keywords, project_evaluation_id):
    """Remove keywords from project evaluation that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(project_evaluation_id=project_evaluation_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = (
        db.query(Keyword)
        .join(KeywordMapping)
        .filter_by(project_evaluation_id=project_evaluation_id)
        .all()
    )

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, project_evaluation_id=project_evaluation_id)
                .first()
            )
            db.delete(mapping)
    db.commit()


async def create_project_evaluation(
    db: Session,
    project_evaluation: CreateProjectEvaluation,
    tenant_id: int,
    keywords: str,
    user_id: int,
):
    project = db.query(Project).filter(Project.id == project_evaluation.project_id).first()
    if not project.tenant_id == tenant_id:
        return False
    new_project_evaluation = ProjectEvaluation(**project_evaluation.dict(), tenant_id=tenant_id)
    db.add(new_project_evaluation)
    db.commit()
    db.refresh(new_project_evaluation)
    # Add history
    history = {
        "project_evaluation_id": new_project_evaluation.id,
        "author_id": user_id,
        "history": f"Created new project evaluation {new_project_evaluation.name}",
    }
    new_history = ProjectEvaluationHistory(**history)
    db.add(new_history)
    db.commit()
    # Get all users watching project evaluations for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_evaluations == True)
        .filter(UserWatching.project_id == project.id)
        .all()
    )
    link = (
        f"/projects/{project_evaluation.project_id}/project_evaluations/{new_project_evaluation.id}"
    )
    message = f"Created new project evaluation {project_evaluation.name}"
    await manage_notifications(
        db,
        users_watching,
        "project_evaluations",
        message,
        link,
        project.id,
        new_project_evaluation.id,
    )

    # add keywords
    await add_keywords(db, keywords, new_project_evaluation.id, tenant_id)
    return new_project_evaluation


def get_all_project_evaluations(db: Session, tenant_id: int, user_id: int):
    queryset = filter_by_user_project_role(db, ProjectEvaluation, user_id, tenant_id)
    return queryset.options(selectinload(ProjectEvaluation.project)).all()


def get_project_evaluation(db: Session, id: int, tenant_id: int, user_id: int):
    queryset = filter_by_user_project_role(db, ProjectEvaluation, user_id, tenant_id)
    project_evaluation = (
        queryset.filter(ProjectEvaluation.id == id)
        .options(selectinload(ProjectEvaluation.project))
        .first()
    )
    return project_evaluation


async def update_project_evaluation(
    db: Session,
    id: int,
    project_evaluation: UpdateProjectEvaluation,
    tenant_id: int,
    keywords: str,
    user_id: int,
):
    existing_project_evaluation = db.query(ProjectEvaluation).filter(ProjectEvaluation.id == id)
    project = (
        db.query(Project).filter(Project.id == existing_project_evaluation.first().project_id)
    ).first()
    link = f"/projects/{project.id}/project_evaluations/{existing_project_evaluation.first().id}"
    if not existing_project_evaluation.first():
        return False
    # Add history
    changes = []
    for field in [
        "name",
        "description",
        "comments",
        "status",
    ]:
        if (
            getattr(existing_project_evaluation.first(), field)
            != getattr(project_evaluation, field, None)
            and getattr(project_evaluation, field, None) != None
        ):
            changes.append(
                f"Updated {field.replace('_', ' ')} to {getattr(project_evaluation, field, None)}"
            )
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
            "project_evaluations",
            all_changes,
            link,
            project.id,
            existing_project_evaluation.first().id,
        )
        for change in changes:
            db.add(
                ProjectEvaluationHistory(
                    project_evaluation_id=existing_project_evaluation.first().id,
                    author_id=user_id,
                    history=change,
                )
            )
    # remove keywords not included
    await remove_old_keywords(db, keywords, id)
    # add keywords
    await add_keywords(db, keywords, id, tenant_id)
    project_eval_dict = project_evaluation.dict(exclude_unset=True)
    # Update costs
    cost_ids = project_eval_dict.pop("cost_ids", None)
    if cost_ids is not None or []:
        # add costs
        for cost in cost_ids:
            # check if cost id exists on tenant
            existing_cost = db.query(Cost).filter(Cost.tenant_id == tenant_id).first()
            # if the cost exists
            if existing_cost is not None:
                new_cost_map = ProjectEvaluationCost(project_evaluation_id=id, cost_id=cost)
                try:
                    db.add(new_cost_map)
                    db.commit()
                except:
                    LOGGER.error("Could not add cost with this ID")
    existing_project_evaluation.update(project_eval_dict)
    db.commit()
    return existing_project_evaluation.first()


async def delete_project_evaluation(db: Session, id: int, tenant_id: int):
    existing_project_evaluation = filter_by_tenant(db, ProjectEvaluation, tenant_id).filter(
        ProjectEvaluation.id == id
    )
    if not existing_project_evaluation.first():
        return False
    project = (
        db.query(Project)
        .filter(Project.id == existing_project_evaluation.first().project_id)
        .first()
    )
    # Get all users watching project evaluations for this project
    users_watching = (
        db.query(UserWatching)
        .filter(UserWatching.project_evaluations == True)
        .filter(UserWatching.project_id == project.id)
        .all()
    )
    # send email and sms notifications
    await manage_notifications(
        db,
        users_watching,
        "project_evaluations",
        f"Deleted project evalution with id {existing_project_evaluation.first().id}.",
        f"/projects/{project.id}/project_evaluations",
        existing_project_evaluation.first().project_id,
        existing_project_evaluation.first().id,
    )
    # delete all history references
    db.query(ProjectEvaluationHistory).filter(
        ProjectEvaluationHistory.project_evaluation_id == id
    ).delete()
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.project_evaluation_id == id).delete()
    # delete all document references
    db.query(ProjectEvaluationDocument).filter(
        ProjectEvaluationDocument.project_evaluation_id == id
    ).delete()
    # delete all cost references
    db.query(ProjectEvaluationCost).filter(
        ProjectEvaluationCost.project_evaluation_id == id
    ).delete()
    # delete all approval workflow references
    db.query(ProjectEvaluationApprovalWorkflow).filter(
        ProjectEvaluationApprovalWorkflow.project_evaluation_id == id
    ).delete()
    existing_project_evaluation.delete(synchronize_session=False)
    db.commit()
    return True


def search(query: str, db: Session, tenant_id: int, user_id: int, offset: int = 0, limit: int = 10):
    lowercase_query = query.lower()

    user = db.query(User).filter(User.id == user_id).first()
    if user.is_superuser:
        res = (
            db.query(ProjectEvaluation)
            .filter(
                or_(
                    func.lower(ProjectEvaluation.name).contains(lowercase_query),
                    func.lower(ProjectEvaluation.description).contains(lowercase_query),
                    func.lower(ProjectEvaluation.keywords).contains(lowercase_query),
                )
            )
            .all()
        )
    elif user.is_tenant_admin:
        res = (
            filter_by_tenant(db, ProjectEvaluation, tenant_id)
            .filter(
                or_(
                    func.lower(ProjectEvaluation.name).contains(lowercase_query),
                    func.lower(ProjectEvaluation.description).contains(lowercase_query),
                    func.lower(ProjectEvaluation.keywords).contains(lowercase_query),
                )
            )
            .all()
        )
    else:
        res = (
            filter_by_tenant(db, ProjectEvaluation, tenant_id)
            .join(ProjectUser, ProjectUser.id == ProjectEvaluation.project_id)
            .filter(ProjectUser.user_id == user_id)
            .filter(
                or_(
                    func.lower(ProjectEvaluation.name).contains(lowercase_query),
                    func.lower(ProjectEvaluation.description).contains(lowercase_query),
                    func.lower(ProjectEvaluation.keywords).contains(lowercase_query),
                )
            )
            .distinct()
            .all()
        )

    if user.is_superuser:
        count = (
            db.query(ProjectEvaluation)
            .filter(
                or_(
                    func.lower(ProjectEvaluation.name).contains(lowercase_query),
                    func.lower(ProjectEvaluation.description).contains(lowercase_query),
                    func.lower(ProjectEvaluation.keywords).contains(lowercase_query),
                )
            )
            .count()
        )
    elif user.is_tenant_admin:
        count = (
            filter_by_tenant(db, ProjectEvaluation, tenant_id)
            .filter(
                or_(
                    func.lower(ProjectEvaluation.name).contains(lowercase_query),
                    func.lower(ProjectEvaluation.description).contains(lowercase_query),
                    func.lower(ProjectEvaluation.keywords).contains(lowercase_query),
                )
            )
            .count()
        )
    else:
        count = (
            filter_by_tenant(db, ProjectEvaluation, tenant_id)
            .join(ProjectUser, ProjectUser.id == ProjectEvaluation.project_id)
            .filter(ProjectUser.user_id == user_id)
            .filter(
                or_(
                    func.lower(ProjectEvaluation.name).contains(lowercase_query),
                    func.lower(ProjectEvaluation.description).contains(lowercase_query),
                    func.lower(ProjectEvaluation.keywords).contains(lowercase_query),
                )
            )
            .distinct()
            .count()
        )
    return count, res[offset : offset + limit]
