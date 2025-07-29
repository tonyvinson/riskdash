# import sys
# print(sys.modules.get('logging'))
import logging

# print(dir(logging))
# test_logging.py
import logging.config

# print("Logging module functions:", dir(logging.config))
import os
from socket import gethostbyname, gethostname

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.config import Settings
from fedrisk_api.db.database import Base, get_db
from fedrisk_api.endpoints import (
    approval_workflows,
    assessment,
    audit_evidence,
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
    cost,
    digital_signature,
    document,
    evidence,
    exception,
    feature,
    framework,
    framework_version,
    governance_dashboard,
    help_section,
    history,
    import_framework,
    import_task,
    keyword,
    permissions,
    project,
    project_control,
    project_evaluation,
    project_group,
    reporting_dashboard,
    risk,
    risk_category,
    risk_dashboard,
    risk_impact,
    risk_likelihood,
    risk_mapping,
    risk_score,
    risk_status,
    role,
    service_provider,
    subscription,
    summary_dashboard,
    survey_model,
    survey_response,
    survey_template,
    task,
    task_category,
    task_status,
    tenant,
    user,
    user_notification,
    wbs,
    workflow_flowchart,
    workflow_event,
    workflow_event_log,
    workflow_template,
    workflow_template_event,
)


NUM_DEMO_FRAMEWORKS = 3
NUM_DEMO_CONTROLS_PER_FRAMEWORK = 4
CONSOLE_ONLY_LOGGING_CONFIG_FILE = "console_only_logging.conf"
CONSOLE_AND_FILE_LOGGING_CONFIG_FILE = "logging.conf"

LOGGER = logging.getLogger(__name__)


# async def cron_job_task():
#     while True:
#         try:
#             LOGGER.info("Cron job is running")
#         except Exception as e:
#             LOGGER.error(f"Error in cron job: {e}")

#         # Wait for 60 seconds before running the task again
#         await asyncio.sleep(60)


def create_tables():
    Base.metadata.create_all(bind=next(get_db()).get_bind())


def start_application():

    # Make sure there exists a
    allowed_origins_string = os.getenv("ALLOWED_ORIGINS", "")
    frontend_server_url = os.getenv("FRONTEND_SERVER_URL", "")
    LOGGER.warning(f"frontend server url {frontend_server_url}")

    if os.environ.get("AWS_EXECUTION_ENV"):
        logging_config_file = CONSOLE_ONLY_LOGGING_CONFIG_FILE
        if allowed_origins_string == "":
            allowed_origins_string += f"{gethostbyname(gethostname())}"
        else:
            allowed_origins_string += f",{gethostbyname(gethostname())}"
    else:
        logging_config_file = CONSOLE_AND_FILE_LOGGING_CONFIG_FILE
        os.makedirs("logs", exist_ok=True)

    logging.config.fileConfig(logging_config_file, disable_existing_loggers=False)

    LOGGER.warning(f"Allowed origins: {allowed_origins_string}")

    settings = Settings()
    if not settings.AWS_ACCESS_KEY_ID:
        raise ValueError("AWS_ACCESS_KEY_ID is not set")
    if not settings.AWS_SECRET_ACCESS_KEY:
        raise ValueError("AWS_SECRET_ACCESS_KEY is not set")
    if not settings.AWS_DEFAULT_REGION:
        raise ValueError("AWS_DEFAULT_REGION is not set")

    app = FastAPI(title=settings.PROJECT_TITLE, version=settings.PROJECT_VERSION)

    LOGGER.info("App has been created . . .")

    # LOGGER.info("Starting cron job")
    # asyncio.create_task(cron_job_task())

    app.include_router(approval_workflows.router)
    app.include_router(assessment.router)
    app.include_router(audit_evidence.router)
    app.include_router(audit_test.router)
    app.include_router(aws_control.router)
    app.include_router(cap_poam.router)
    app.include_router(chat_bot_prompt.router)
    app.include_router(compliance_dashboard.router)
    app.include_router(control.router)
    app.include_router(control_class.router)
    app.include_router(control_family.router)
    app.include_router(control_phase.router)
    app.include_router(control_status.router)
    app.include_router(cost.router)
    app.include_router(digital_signature.router)
    app.include_router(document.router)
    app.include_router(evidence.router)
    app.include_router(exception.router)
    app.include_router(feature.router)
    app.include_router(framework.router)
    app.include_router(framework_version.router)
    app.include_router(import_framework.router)
    app.include_router(import_task.router)
    app.include_router(governance_dashboard.router)
    app.include_router(help_section.router)
    app.include_router(history.router)
    app.include_router(keyword.router)
    app.include_router(permissions.router)
    app.include_router(project.router)
    app.include_router(project_control.router)
    app.include_router(project_evaluation.router)
    app.include_router(project_group.router)
    app.include_router(reporting_dashboard.router)
    app.include_router(risk.router)
    app.include_router(risk_dashboard.router)
    app.include_router(risk_category.router)
    app.include_router(risk_impact.router)
    app.include_router(risk_likelihood.router)
    app.include_router(risk_mapping.router)
    app.include_router(risk_score.router)
    app.include_router(risk_status.router)
    app.include_router(role.router)
    app.include_router(service_provider.router)
    app.include_router(subscription.router)
    app.include_router(summary_dashboard.router)
    app.include_router(survey_model.router)
    app.include_router(survey_response.router)
    app.include_router(survey_template.router)
    app.include_router(task.router)
    app.include_router(task_category.router)
    app.include_router(task_status.router)
    app.include_router(tenant.router)
    app.include_router(user.router)
    app.include_router(user_notification.router)
    app.include_router(wbs.router)
    app.include_router(workflow_flowchart.router)
    app.include_router(workflow_event.router)
    app.include_router(workflow_event_log.router)
    app.include_router(workflow_template.router)
    app.include_router(workflow_template_event.router)

    # TODO: Add any other needed origins
    allowed_origins = [
        next_origin.strip() for next_origin in str(allowed_origins_string).split(",")
    ]
    if frontend_server_url != "":
        allowed_origins.append(frontend_server_url)
        allowed_origins.append(frontend_server_url + "/")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    LOGGER.info("Creating tables . . .")
    create_tables()

    LOGGER.warning(f"Allowed Origins: {allowed_origins}")
    LOGGER.warning(f"frontend server url {frontend_server_url}")

    LOGGER.info("Application startup complete")

    return app


app = start_application()


@app.get("/", include_in_schema=False)
def index():
    return "You probably wanted the url '/docs' . . ."
