import logging

from sqlalchemy.orm import Session

from fedrisk_api.db.models import SurveyTemplate
from fedrisk_api.schema.survey_template import (
    CreateSurveyTemplate,
    UpdateSurveyTemplate,
)


LOGGER = logging.getLogger(__name__)


# survey_template
def create_survey_template(db: Session, survey_template: CreateSurveyTemplate, tenant_id: int):
    my_new_survey_template_dict = survey_template.dict()
    new_survey_template = SurveyTemplate(**my_new_survey_template_dict, tenant_id=tenant_id)
    db.add(new_survey_template)
    db.commit()
    return new_survey_template


def get_all_survey_templates_by_tenant_id(
    db: Session,
    tenant_id: int,
):
    queryset = db.query(SurveyTemplate).filter(SurveyTemplate.tenant_id == tenant_id).all()
    return queryset


def get_survey_template_by_id(db: Session, survey_template_id: int):
    queryset = db.query(SurveyTemplate).filter(SurveyTemplate.id == survey_template_id).first()
    return queryset


def update_survey_template_by_id(
    survey_template: UpdateSurveyTemplate,
    db: Session,
    survey_template_id: int,
):
    queryset = db.query(SurveyTemplate).filter(SurveyTemplate.id == survey_template_id)

    if not queryset.first():
        return False

    queryset.update(survey_template.dict(exclude_unset=True))
    db.commit()
    return True


def delete_survey_template_by_id(db: Session, survey_template_id: int):
    survey_template = (
        db.query(SurveyTemplate).filter(SurveyTemplate.id == survey_template_id).first()
    )

    if not survey_template:
        return False

    db.delete(survey_template)
    db.commit()
    return True
