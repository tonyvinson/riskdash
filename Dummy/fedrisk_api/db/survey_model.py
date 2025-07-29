import logging

from sqlalchemy.orm import Session

from sqlalchemy import func

from fedrisk_api.db.models import SurveyModel, SurveyTemplate, SurveyResponse
from fedrisk_api.schema.survey_model import (
    CreateSurveyModel,
    UpdateSurveyModel,
    CreateSurveyProjectTemplate,
)


LOGGER = logging.getLogger(__name__)


# survey_model
def create_survey_model(db: Session, survey_model: CreateSurveyModel):
    my_new_survey_model_dict = survey_model.dict()
    new_survey_model = SurveyModel(**my_new_survey_model_dict)
    db.add(new_survey_model)
    db.commit()
    return new_survey_model


def get_all_survey_models_by_project_id(
    db: Session,
    project_id: int,
):
    survey_models = db.query(SurveyModel).filter(SurveyModel.project_id == project_id).all()
    # Fetch grouped counts for all relevant SurveyModel IDs
    model_ids = [sm.id for sm in survey_models]
    counts = (
        db.query(
            SurveyResponse.survey_model_id,
            SurveyResponse.test,
            func.count().label("count"),
        )
        .filter(SurveyResponse.survey_model_id.in_(model_ids))
        .group_by(SurveyResponse.survey_model_id, SurveyResponse.test)
        .all()
    )

    # Build a lookup for (survey_model_id) → test counts
    from collections import defaultdict

    test_count_map = defaultdict(lambda: {"test_true": 0, "test_false": 0})
    for model_id, test_value, count in counts:
        key = "test_true" if test_value else "test_false"
        test_count_map[model_id][key] = count

    # Annotate each SurveyModel with its test count
    for sm in survey_models:
        sm.test_counts = test_count_map.get(sm.id, {"test_true": 0, "test_false": 0})

    return survey_models


def get_survey_model_by_id(db: Session, survey_model_id: int):
    queryset = db.query(SurveyModel).filter(SurveyModel.id == survey_model_id).first()
    return queryset


def update_survey_model_by_id(
    survey_model: UpdateSurveyModel,
    db: Session,
    survey_model_id: int,
):
    queryset = db.query(SurveyModel).filter(SurveyModel.id == survey_model_id)

    if not queryset.first():
        return False

    queryset.update(survey_model.dict(exclude_unset=True))
    db.commit()
    return True


def delete_survey_model_by_id(db: Session, survey_model_id: int):
    survey_model = db.query(SurveyModel).filter(SurveyModel.id == survey_model_id).first()

    if not survey_model:
        return False
    # delete all survey responses
    db.query(SurveyResponse).filter(SurveyResponse.survey_model_id == survey_model_id).delete()
    db.delete(survey_model)
    db.commit()
    return True


async def create_survey_for_project_from_template(
    survey_template: CreateSurveyProjectTemplate, db: Session, user_id: int, tenant_id: int
):
    # Get the survey template from the database
    survey_template_db = (
        db.query(SurveyTemplate).filter(SurveyTemplate.id == survey_template.template_id).first()
    )
    if survey_template_db is None:
        return 0

    # Create Survey from template for project
    new_survey_obj = SurveyModel(
        name=survey_template_db.name,
        survey_json=survey_template_db.survey_json,
        project_id=survey_template.project_id,
    )
    db.add(new_survey_obj)
    db.commit()
    return new_survey_obj
