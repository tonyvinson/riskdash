import logging
from typing import Optional, Union

from sqlalchemy.orm import Session

from fedrisk_api.db.models import SurveyResponse
from fedrisk_api.schema.survey_response import (
    CreateSurveyResponse,
    UpdateSurveyResponse,
)


LOGGER = logging.getLogger(__name__)


# survey_response
def create_survey_response(db: Session, survey_response: CreateSurveyResponse):
    my_new_survey_response_dict = survey_response.dict()
    new_survey_response = SurveyResponse(**my_new_survey_response_dict)
    db.add(new_survey_response)
    db.commit()
    return new_survey_response


def get_all_survey_responses_by_survey_id(
    db: Session,
    survey_model_id: int,
    test: Optional[bool] = None,
) -> Union[dict[bool, list[SurveyResponse]], list[SurveyResponse]]:

    query = db.query(SurveyResponse).filter(SurveyResponse.survey_model_id == survey_model_id)

    if test is not None:
        # Return only filtered list
        return query.filter(SurveyResponse.test == test).all()

    # No filter: return grouped results
    responses = query.all()

    grouped = {True: [], False: []}
    for response in responses:
        grouped[response.test].append(response)

    return grouped


def get_all_survey_responses_by_user_id(
    db: Session,
    user_id: int,
):
    queryset = db.query(SurveyResponse).filter(SurveyResponse.user_id == user_id).all()
    return queryset


def get_survey_response_by_id(db: Session, survey_response_id: int):
    queryset = db.query(SurveyResponse).filter(SurveyResponse.id == survey_response_id).first()
    return queryset


def update_survey_response_by_id(
    survey_response: UpdateSurveyResponse,
    db: Session,
    survey_response_id: int,
):
    queryset = db.query(SurveyResponse).filter(SurveyResponse.id == survey_response_id)

    if not queryset.first():
        return False

    queryset.update(survey_response.dict(exclude_unset=True))
    db.commit()
    return True


def delete_survey_response_by_id(db: Session, survey_response_id: int):
    survey_response = (
        db.query(SurveyResponse).filter(SurveyResponse.id == survey_response_id).first()
    )

    if not survey_response:
        return False

    db.delete(survey_response)
    db.commit()
    return True
