import os
import sys
from typing import Any, Generator
import logging

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from fedrisk_api.db.database import Base, get_db
from fedrisk_api.db.util.data_creation_utils import load_data as load_data_util
from fedrisk_api.endpoints import (
    assessment,
    audit_test,
    aws_control,
    cap_poam,
    chat_bot_prompt,
    compliance_dashboard,
    control,
    control_class,
    control_family,
    control_phase,
    control_status,
    document,
    exception,
    feature,
    framework,
    framework_version,
    governance_dashboard,
    help_section,
    history,
    import_framework,
    keyword,
    project,
    project_control,
    project_evaluation,
    project_group,
    reporting_dashboard,
    risk_category,
    risk_dashboard,
    risk_impact,
    risk_likelihood,
    risk_mapping,
    risk_score,
    risk_status,
    risk,
    role,
    summary_dashboard,
    task,
    tenant,
    user,
    user_notification,
    wbs,
)

# import sys

# sys.path.insert(0, "/project")

# sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# this is to include backend dir in sys.path so that we can import from db,main.py
LOGGER = logging.getLogger(__name__)
CONSOLE_ONLY_LOGGING_CONFIG_FILE = "console_only_logging.conf"


def start_application():
    logging_config_file = CONSOLE_ONLY_LOGGING_CONFIG_FILE
    logging.config.fileConfig(logging_config_file, disable_existing_loggers=False)
    app = FastAPI()
    app.include_router(audit_test.router)
    app.include_router(assessment.router)
    app.include_router(aws_control.router)
    app.include_router(cap_poam.router)
    app.include_router(chat_bot_prompt.router)
    app.include_router(compliance_dashboard.router)
    app.include_router(control.router)
    app.include_router(control_status.router)
    app.include_router(control_class.router)
    app.include_router(control_family.router)
    app.include_router(control_phase.router)
    app.include_router(document.router)
    app.include_router(exception.router)
    app.include_router(framework.router)
    app.include_router(framework_version.router)
    app.include_router(feature.router)
    app.include_router(governance_dashboard.router)
    app.include_router(help_section.router)
    app.include_router(history.router)
    app.include_router(import_framework.router)
    app.include_router(keyword.router)
    app.include_router(project.router)
    app.include_router(project_control.router)
    app.include_router(project_evaluation.router)
    app.include_router(project_group.router)
    app.include_router(reporting_dashboard.router)
    app.include_router(risk_category.router)
    app.include_router(risk_dashboard.router)
    app.include_router(risk_impact.router)
    app.include_router(risk_score.router)
    app.include_router(risk_likelihood.router)
    app.include_router(risk_status.router)
    app.include_router(risk_mapping.router)
    app.include_router(risk.router)
    app.include_router(role.router)
    app.include_router(summary_dashboard.router)
    app.include_router(task.router)
    app.include_router(tenant.router)
    app.include_router(user.router)
    app.include_router(user_notification.router)
    app.include_router(wbs.router)
    return app


SQLALCHEMY_DATABASE_URL = "sqlite:///./test_db.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
# Use connect_args parameter only with sqlite
SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def app() -> Generator[FastAPI, Any, None]:
    """
    Create a fresh database on each test case.
    """
    Base.metadata.create_all(engine)  # Create the tables.
    _app = start_application()
    yield _app
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def db_session(app: FastAPI) -> Generator[SessionTesting, Any, None]:
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionTesting(bind=connection)
    load_data_util(session)
    yield session  # use the session in tests.
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(app: FastAPI, db_session: SessionTesting) -> Generator[TestClient, Any, None]:
    """
    Create a new FastAPI TestClient that uses the `db_session` fixture to override
    the `get_db` dependency that is injected into routes.
    """

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
