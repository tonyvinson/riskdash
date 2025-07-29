import logging

# from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from fedrisk_api.db.models import HelpSection, User
from fedrisk_api.schema.help_section import CreateHelpSection, UpdateHelpSection, DisplayHelpSection

# from fedrisk_api.utils.utils import filter_by_tenant, ordering_query

LOGGER = logging.getLogger(__name__)


def create_help_section(help_section: CreateHelpSection, db: Session):
    help_section = HelpSection(**help_section.dict())
    db.add(help_section)
    db.commit()
    return help_section


def get_help_sections(
    db: Session,
):
    queryset = db.query(HelpSection).order_by(HelpSection.order).all()
    return queryset


def get_help_section_by_id(db: Session, help_section_id: int):
    queryset = db.query(HelpSection).filter(HelpSection.id == help_section_id).first()
    return queryset


def update_help_section_by_id(help_section: UpdateHelpSection, db: Session, help_section_id: int):
    queryset = db.query(HelpSection).filter(HelpSection.id == help_section_id)

    if not queryset.first():
        return False

    queryset.update(help_section.dict(exclude_unset=True))
    db.commit()
    return True


def delete_help_section_by_id(db: Session, help_section_id: int):
    help_section = db.query(HelpSection).filter(HelpSection.id == help_section_id).first()

    if not help_section:
        return False

    db.delete(help_section)
    db.commit()
    return True
