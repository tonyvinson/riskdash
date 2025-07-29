from pathlib import Path

import pytest
from pydantic.error_wrappers import ValidationError

from config.config import Settings

REQUIRED_ENVIRONMENT_VARIABLES = [
    "FEDRISK_JWT_SECRET_KEY",
    "FRONTEND_SERVER_URL",
    "COGNITO_WEB_CLIENT_ID",
    "COGNITO_USER_POOL_ID",
    "COGNITO_ACCESS_KEY_ID",
    "COGNITO_SECRET_ACCESS_KEY",
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
]


# def test_settings_default_load_no_environment():
#     settings = None
#     with pytest.raises(ValidationError) as validation_error:
#         settings = Settings(_env_file=None)

#     missing_required_field_names = [
#         next_item["loc"][0] for next_item in validation_error.value.errors()
#     ]
#     print(missing_required_field_names)
#     assert len(missing_required_field_names) == len(REQUIRED_ENVIRONMENT_VARIABLES)
#     for next_required_environment_variable in REQUIRED_ENVIRONMENT_VARIABLES:
#         assert next_required_environment_variable in missing_required_field_names


def test_settings_default_load_using_environment_file():
    settings = None
    test_environment_file_path = Path(__file__).parent / "test_settings.env"
    settings = Settings(_env_file=test_environment_file_path)
    assert settings

    assert settings.COGNITO_ACCESS_KEY_ID != "test_cognito_access_key_id"
    assert settings.COGNITO_SECRET_ACCESS_KEY != "test_cognito_secret_access_key"
    assert settings.FRONTEND_SERVER_URL != "test_frontend_server_url"
    assert settings.FEDRISK_JWT_SECRET_KEY != "test_fedrisk_jwt_secret_key"
