import logging

from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import (
    Document,
    DocumentApprovalWorkflow,
    AssessmentDocument,
    ExceptionDocument,
    AuditTestDocument,
    ControlDocument,
    ProjectDocument,
    RiskDocument,
    WBSDocument,
    TaskDocument,
    FrameworkDocument,
    FrameworkVersionDocument,
    ProjectControlDocument,
    ProjectEvaluationDocument,
    KeywordMapping,
    Keyword,
    DocumentHistory,
    UserWatching,
    # UserNotifications,
    UserNotificationSettings,
    User,
    Project,
)
from fedrisk_api.schema.document import CreateDocument, UpdateDocument
from fedrisk_api.utils.utils import filter_by_tenant, filter_by_user_project_role

# from fedrisk_api.utils.email_util import send_watch_email
# from fedrisk_api.utils.sms_util import publish_notification

LOGGER = logging.getLogger(__name__)

from fedrisk_api.db.util.notifications_utils import (
    notify_user,
    add_notification,
    manage_notifications,
)


# Keyword Management Functions
async def add_keywords(db, keywords, document_id, tenant_id):
    """Link keywords to document."""
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
                .filter_by(keyword_id=keyword.id, document_id=document_id)
                .first()
            ):
                db.add(KeywordMapping(keyword_id=keyword.id, document_id=document_id))
    db.commit()


async def remove_old_keywords(db, keywords, document_id):
    """Remove keywords from document that are not in the new list."""
    if not keywords:
        db.query(KeywordMapping).filter_by(document_id=document_id).delete()
        db.commit()
        return

    keywords_set = set(keywords.split(","))
    existing_keywords = (
        db.query(Keyword).join(KeywordMapping).filter_by(document_id=document_id).all()
    )

    for keyword in existing_keywords:
        if keyword.name not in keywords_set:
            mapping = (
                db.query(KeywordMapping)
                .filter_by(keyword_id=keyword.id, document_id=document_id)
                .first()
            )
            db.delete(mapping)
    db.commit()


async def create_document(
    db: Session,
    document: CreateDocument,
    fedrisk_object_type: str,
    fedrisk_object_id: str,
    file_content_type: str,
    tenant_id: int,
    keywords: str,
    user_id: int,
    project_id: int,
):
    document_dict = {**document.dict(), **{"file_content_type": file_content_type}}
    new_document = Document(**document_dict, tenant_id=tenant_id)
    db.add(new_document)
    db.flush()
    # db.commit()
    db.refresh(new_document)
    # Add history
    history = {
        "document_id": new_document.id,
        "author_id": user_id,
        "history": f"Created new document {new_document.title}",
    }
    new_history = DocumentHistory(**history)
    db.add(new_history)
    db.commit()

    # create notification for document owner
    await add_notification(
        db,
        new_document.owner_id,
        "documents",
        new_document.id,
        f"/documents/{new_document.id}",
        f"You've been assigned as an owner for document {new_document.title}",
        project_id,
    )

    # Send email and sms updates
    owner = db.query(User).filter_by(id=new_document.owner_id).first()
    owner_settings = (
        db.query(UserNotificationSettings).filter_by(user_id=new_document.owner_id).first()
    )
    link = f"/projects/documents/{new_document.id}"
    await notify_user(
        owner,
        f"You've been added as an owner on document {new_document.name}",
        link,
        owner_settings,
    )

    # add keywords
    await add_keywords(db, keywords, new_document.id, tenant_id)

    # add the relational references
    if fedrisk_object_type == "assessments":
        # add relational reference for assessment
        data = {"assessment_id": fedrisk_object_id, "document_id": new_document.id}
        new_assessment_doc = AssessmentDocument(**data)
        db.add(new_assessment_doc)
        db.commit()
        db.refresh(new_assessment_doc)

    elif fedrisk_object_type == "exceptions":
        data = {"exception_id": fedrisk_object_id, "document_id": new_document.id}
        new_exception_doc = ExceptionDocument(**data)
        db.add(new_exception_doc)
        db.commit()

    elif fedrisk_object_type == "audit_tests":
        data = {"audit_test_id": fedrisk_object_id, "document_id": new_document.id}
        new_at_doc = AuditTestDocument(**data)
        db.add(new_at_doc)
        db.commit()

    elif fedrisk_object_type == "controls":
        data = {"control_id": fedrisk_object_id, "document_id": new_document.id}
        new_control_doc = ControlDocument(**data)
        db.add(new_control_doc)
        db.commit()

    elif fedrisk_object_type == "frameworks":
        data = {"framework_id": fedrisk_object_id, "document_id": new_document.id}
        new_f_doc = FrameworkDocument(**data)
        db.add(new_f_doc)
        db.commit()

    elif fedrisk_object_type == "framework_versions":
        data = {"framework_version_id": fedrisk_object_id, "document_id": new_document.id}
        new_fv_doc = FrameworkVersionDocument(**data)
        db.add(new_fv_doc)
        db.commit()

    elif fedrisk_object_type == "projects":
        data = {"project_id": fedrisk_object_id, "document_id": new_document.id}
        new_proj_doc = ProjectDocument(**data)
        db.add(new_proj_doc)
        db.commit()
        # Get all users watching documents for this project
        users_watching = (
            db.query(UserWatching)
            .filter(UserWatching.project_documents == True)
            .filter(UserWatching.project_id == fedrisk_object_id)
            .all()
        )
        project = db.query(Project).filter(Project.id == fedrisk_object_id).first()
        message = f"Created new document {new_document.title}"
        await manage_notifications(
            db, users_watching, "documents", message, link, project.id, new_document.id
        )
    elif fedrisk_object_type == "project_controls":
        data = {"project_control_id": fedrisk_object_id, "document_id": new_document.id}
        new_proj_control_doc = ProjectControlDocument(**data)
        db.add(new_proj_control_doc)
        db.commit()

    elif fedrisk_object_type == "project_evaluations":
        data = {"project_evaluation_id": fedrisk_object_id, "document_id": new_document.id}
        new_proj_evaluation_doc = ProjectEvaluationDocument(**data)
        db.add(new_proj_evaluation_doc)
        db.commit()

    elif fedrisk_object_type == "risks":
        data = {"risk_id": fedrisk_object_id, "document_id": new_document.id}
        new_risk_doc = RiskDocument(**data)
        db.add(new_risk_doc)
        db.commit()

    elif fedrisk_object_type == "tasks":
        data = {"task_id": fedrisk_object_id, "document_id": new_document.id}
        new_task_doc = TaskDocument(**data)
        db.add(new_task_doc)
        db.commit()

    elif fedrisk_object_type == "wbs":
        data = {"wbs_id": fedrisk_object_id, "document_id": new_document.id}
        new_wbs_doc = WBSDocument(**data)
        db.add(new_wbs_doc)
        db.commit()

    return new_document


def get_all_documents(db: Session, tenant_id: int, user_id: int):
    queryset = filter_by_user_project_role(db, Document, user_id, tenant_id)
    return queryset.all()


def get_document(db: Session, id: int, tenant_id: int, user_id: int):
    queryset = filter_by_user_project_role(db, Document, user_id, tenant_id)
    # get document
    document = queryset.filter(Document.id == id).first()
    return document


async def update_document(
    db: Session,
    id: int,
    file_content_type: str,
    document: UpdateDocument,
    tenant_id: int,
    keywords: str,
    fedrisk_object_type: str,
    fedrisk_object_id: int,
    user_id: int,
):
    existing_document = filter_by_tenant(db, Document, tenant_id).filter(Document.id == id)
    if not existing_document.first():
        return False

    changes = []
    for field in [
        "name",
        "title",
        "description",
        "version",
    ]:
        if (
            getattr(existing_document.first(), field) != getattr(document, field, None)
            and getattr(document, field, None) != None
        ):
            changes.append(f"Updated {field.replace('_', ' ')} to {getattr(document, field, None)}")

    all_changes = ".    ".join(changes)
    if all_changes != "":
        for change in changes:
            db.add(
                DocumentHistory(
                    document_id=existing_document.first().id, author_id=user_id, history=change
                )
            )
    # document_dict = {**document.dict(exclude_unset=True), **{"file_content_type": file_content_type}}
    existing_document.update(document.dict(exclude_unset=True))
    db.commit()
    # remove previous relationship
    # delete all project control references
    db.query(ProjectControlDocument).filter(
        ProjectControlDocument.document_id == existing_document.first().id
    ).delete()
    # delete all project references
    db.query(ProjectDocument).filter(
        ProjectDocument.document_id == existing_document.first().id
    ).delete()
    # delete all audit tests references
    db.query(AuditTestDocument).filter(
        AuditTestDocument.document_id == existing_document.first().id
    ).delete()
    # delete all control references
    db.query(ControlDocument).filter(
        ControlDocument.document_id == existing_document.first().id
    ).delete()
    # delete all exception references
    db.query(ExceptionDocument).filter(
        ExceptionDocument.document_id == existing_document.first().id
    ).delete()
    # delete all control references
    db.query(ControlDocument).filter(
        ControlDocument.document_id == existing_document.first().id
    ).delete()
    # delete all framework references
    db.query(FrameworkDocument).filter(
        FrameworkDocument.document_id == existing_document.first().id
    ).delete()
    # delete all framework version references
    db.query(FrameworkVersionDocument).filter(
        FrameworkVersionDocument.document_id == existing_document.first().id
    ).delete()
    # delete all risk references
    db.query(RiskDocument).filter(RiskDocument.document_id == existing_document.first().id).delete()
    # delete all task references
    db.query(TaskDocument).filter(TaskDocument.document_id == existing_document.first().id).delete()
    # delete all wbs references
    db.query(WBSDocument).filter(WBSDocument.document_id == existing_document.first().id).delete()
    # delete all project evaluation references
    db.query(ProjectEvaluationDocument).filter(
        ProjectEvaluationDocument.document_id == existing_document.first().id
    ).delete()

    # add the relational reference
    if fedrisk_object_type == "assessments":
        # add relational reference for assessment
        data = {"assessment_id": fedrisk_object_id, "document_id": existing_document.first().id}
        new_assessment_doc = AssessmentDocument(**data)
        db.add(new_assessment_doc)
        db.commit()
        db.refresh(new_assessment_doc)
    elif fedrisk_object_type == "exceptions":
        data = {"exception_id": fedrisk_object_id, "document_id": existing_document.first().id}
        new_exception_doc = ExceptionDocument(**data)
        db.add(new_exception_doc)
        db.commit()

    elif fedrisk_object_type == "audit_tests":
        data = {"audit_test_id": fedrisk_object_id, "document_id": existing_document.first().id}
        new_at_doc = AuditTestDocument(**data)
        db.add(new_at_doc)
        db.commit()

    elif fedrisk_object_type == "controls":
        data = {"control_id": fedrisk_object_id, "document_id": existing_document.first().id}
        new_control_doc = ControlDocument(**data)
        db.add(new_control_doc)
        db.commit()

    elif fedrisk_object_type == "frameworks":
        data = {"framework_id": fedrisk_object_id, "document_id": existing_document.first().id}
        new_f_doc = FrameworkDocument(**data)
        db.add(new_f_doc)
        db.commit()

    elif fedrisk_object_type == "framework_versions":
        data = {
            "framework_version_id": fedrisk_object_id,
            "document_id": existing_document.first().id,
        }
        new_fv_doc = FrameworkVersionDocument(**data)
        db.add(new_fv_doc)
        db.commit()

    elif fedrisk_object_type == "projects":
        data = {"project_id": fedrisk_object_id, "document_id": existing_document.first().id}
        new_proj_doc = ProjectDocument(**data)
        db.add(new_proj_doc)
        db.commit()
        project = db.query(Project).filter(Project.id == fedrisk_object_id).first()
        # Get all users watching documents for this project
        users_watching = (
            db.query(UserWatching)
            .filter(UserWatching.project_documents == True)
            .filter(UserWatching.project_id == fedrisk_object_id)
            .all()
        )
        link = f"/documents/{existing_document.first().id}"
        await manage_notifications(
            db,
            users_watching,
            "project_documents",
            all_changes,
            link,
            project.id,
            existing_document.first().id,
        )

    elif fedrisk_object_type == "project_controls":
        data = {
            "project_control_id": fedrisk_object_id,
            "document_id": existing_document.first().id,
        }
        new_proj_control_doc = ProjectControlDocument(**data)
        db.add(new_proj_control_doc)
        db.commit()

    elif fedrisk_object_type == "project_evaluations":
        data = {
            "project_evaluation_id": fedrisk_object_id,
            "document_id": existing_document.first().id,
        }
        new_proj_evaluation_doc = ProjectEvaluationDocument(**data)
        db.add(new_proj_evaluation_doc)
        db.commit()

    elif fedrisk_object_type == "risks":
        data = {"risk_id": fedrisk_object_id, "document_id": existing_document.first().id}
        new_risk_doc = RiskDocument(**data)
        db.add(new_risk_doc)
        db.commit()

    elif fedrisk_object_type == "tasks":
        data = {"task_id": fedrisk_object_id, "document_id": existing_document.first().id}
        new_task_doc = TaskDocument(**data)
        db.add(new_task_doc)
        db.commit()

    elif fedrisk_object_type == "wbs":
        data = {"wbs_id": fedrisk_object_id, "document_id": existing_document.first().id}
        new_wbs_doc = WBSDocument(**data)
        db.add(new_wbs_doc)
        db.commit()
    # remove keywords not included
    await remove_old_keywords(db, keywords, id)
    # add keywords
    await add_keywords(db, keywords, id, tenant_id)
    return db.query(Document).filter(Document.id == id).first()


async def delete_document(db: Session, id: int, tenant_id: int):
    # existing_document = get_document(db=db, id=id, tenant_id=tenant_id, user_id=user_id)
    existing_document = filter_by_tenant(db, Document, tenant_id).filter(Document.id == id)
    if not existing_document:
        return False
    # if there is a project document reference
    project_doc_ref = db.query(ProjectDocument).filter(ProjectDocument.document_id == id)
    if project_doc_ref.first():
        # send email and sms notifications
        await manage_notifications(
            db,
            db.query(UserWatching)
            .filter(
                UserWatching.project_audit_tests == True,
                UserWatching.project_id == project_doc_ref.first().project_id,
            )
            .all(),
            "documents",
            f"Deleted document with id {project_doc_ref.first().id}.",
            f"/documents",
            project_doc_ref.first().project_id,
            project_doc_ref.first().id,
        )
    # delete all history references
    db.query(DocumentHistory).filter(DocumentHistory.document_id == id).delete()
    # delete all project control references
    db.query(ProjectControlDocument).filter(ProjectControlDocument.document_id == id).delete()
    # delete all project references
    db.query(ProjectDocument).filter(ProjectDocument.document_id == id).delete()
    # delete all audit tests references
    db.query(AuditTestDocument).filter(AuditTestDocument.document_id == id).delete()
    # delete all control references
    db.query(ControlDocument).filter(ControlDocument.document_id == id).delete()
    # delete all exception references
    db.query(ExceptionDocument).filter(ExceptionDocument.document_id == id).delete()
    # delete all control references
    db.query(ControlDocument).filter(ControlDocument.document_id == id).delete()
    # delete all framework references
    db.query(FrameworkDocument).filter(FrameworkDocument.document_id == id).delete()
    # delete all framework version references
    db.query(FrameworkVersionDocument).filter(FrameworkVersionDocument.document_id == id).delete()
    # delete all risk references
    db.query(RiskDocument).filter(RiskDocument.document_id == id).delete()
    # delete all task references
    db.query(TaskDocument).filter(TaskDocument.document_id == id).delete()
    # delete all wbs references
    db.query(WBSDocument).filter(WBSDocument.document_id == id).delete()
    # delete all project evaluation references
    db.query(ProjectEvaluationDocument).filter(ProjectEvaluationDocument.document_id == id).delete()
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.document_id == id).delete()
    # delete all approval workflow references
    db.query(DocumentApprovalWorkflow).filter(DocumentApprovalWorkflow.document_id == id).delete()
    existing_document.delete(synchronize_session=False)
    db.commit()
    return True
