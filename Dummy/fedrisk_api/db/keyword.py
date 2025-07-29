import logging
from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import (
    Keyword,
    KeywordMapping,
    # Document,
    # Assessment,
    # AuditTest,
    # Control,
    # Exception,
    # Framework,
    # FrameworkVersion,
    # Project,
    # ProjectControl,
    # ProjectEvaluation,
    # Risk,
    # Task,
    # WBS,
)
from fedrisk_api.schema.keyword import CreateKeyword, UpdateKeyword
from fedrisk_api.utils.utils import filter_by_tenant

# from sqlalchemy.orm import selectinload

LOGGER = logging.getLogger(__name__)


def create_keyword(db: Session, keyword: CreateKeyword, tenant_id: int):
    new_keyword = Keyword(**keyword.dict())
    # check if keyword exists on tenant
    keyword_exists = (
        db.query(Keyword)
        .filter(Keyword.name == new_keyword.name)
        .filter(Keyword.tenant_id == tenant_id)
    )
    if keyword_exists.first():
        return False
    else:
        new_keyword.tenant_id = tenant_id
        db.add(new_keyword)
        db.commit()
        db.refresh(new_keyword)
    return new_keyword


def get_keyword(
    db: Session,
    id: int,
    tenant_id: int,
):
    queryset = filter_by_tenant(db, Keyword, tenant_id)

    # queryset = queryset.options(
    #     selectinload(Keyword.documents),
    # )
    return queryset.filter(Keyword.id == id).first()


def get_all_keywords(
    db: Session,
    tenant_id: int,
):
    keywords = db.query(Keyword).filter(Keyword.tenant_id == tenant_id).all()

    if not keywords:
        return False
    return keywords


def update_keyword(
    db: Session,
    id: int,
    keyword: UpdateKeyword,
    # tenant_id: int,
):

    existing_keyword = db.query(Keyword).filter(Keyword.id == id)

    if not existing_keyword.first():
        return False

    existing_keyword.update(keyword.dict(exclude_unset=True))
    db.commit()
    db.flush()

    updated_keyword = db.query(Keyword).filter(Keyword.id == id).first()
    return updated_keyword


def delete_keyword(db: Session, id: int):
    existing_keyword = db.query(Keyword).filter(Keyword.id == id)
    if not existing_keyword.first():
        return False
    # delete all keyword references
    db.query(KeywordMapping).filter(KeywordMapping.keyword_id == id).delete()
    existing_keyword.delete(synchronize_session=False)
    # db.delete(existing_wbs)
    db.commit()
    return True
