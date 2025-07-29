import logging
from sqlalchemy import text
from sqlalchemy.orm.session import Session as SessionLocal
from fedrisk_api.db.models import ChatBotPrompt

LOGGER = logging.getLogger(__name__)

#### These utils are for populating the chat bot scripts with content and substituting Riskuity with Riskuity #####


#### Prompts and messages ####
PROMPTS_MESSAGES = [
    {
        "prompt": "frameworks",
        "message": "It looks like you need help with frameworks. If you have access to system administration you can import a framework and controls that belong to that framework from an excel spreadsheet. Frameworks, framework versions and controls are available for use on all projects in your account.",
    },
    {"prompt": "Hello", "message": "Hello!  What can I do for you today?"},
    {
        "prompt": "Audits",
        "message": "It appears you may need some help with audits.  Riskuity supports the entire audit lifecycle. Compliance frameworks, controls, assessments, risks, and audits are all easily managed within the project workflow. Visit the main project summary dashboard and select a project to begin.",
    },
    {
        "prompt": "Projects",
        "message": "It appears you may need some help with projects.  Riskuity manages all Governance Risk and Compliance activities at the project level. Visit the main project summary dashboard and create a new project to begin.",
    },
    {
        "prompt": "Risk",
        "message": "It appears you may need some help with risks.  Riskuity allows you to define and track all risks for your entire Governance Risk and Compliance program. Risk Dashboards, Risk Registers, and associated mitigation status are all managed by Riskuity. Visit the main project summary dashboard and select a project to begin managing risk.",
    },
    {
        "prompt": "Document",
        "message": "It appears you may need some help with documents.  Riskuity allows you to manage all documents for your entire Governance Risk and Compliance program. Multiple documents can be associated with each data type within Riskuity, including: Project Groups, Frameworks, Projects, Controls, Assessments, Risks, Audits, and WBS. Visit the main project summary dashboard, select a project, and select the tab you would like to associate a document with, to begin managing documents.",
    },
    {
        "prompt": "Risks",
        "message": "It appears you may need some help with risks.  Riskuity allows you to define and track all risks for your entire Governance Risk and Compliance program. Risk Dashboards, Risk Registers, and associated mitigation status are all managed by Riskuity. Visit the main project summary dashboard and select a project to begin managing risk.",
    },
    {
        "prompt": "Notifications",
        "message": "It appears you may need some help with notifications.  Riskuity allows you to manage notifications for your entire Governance Risk and Compliance program. You can choose to watch all activity for each data type within Riskuity and receive notifications when any updates are made. Notifications are stored in the notifications module.  You can also receive notifications via text message and email. Visit the main project summary dashboard and select a project to begin managing notifications. Visit the Notifications page to modify your notifications settings.",
    },
    {
        "prompt": "Alerts",
        "message": "It appears you may need some help with notifications.  Riskuity allows you to manage notifications for your entire Governance Risk and Compliance program. You can choose to watch all activity for each data type within Riskuity and receive notifications when any updates are made. Notifications are stored in the notifications module.  You can also receive notifications via text message and email. Visit the main project summary dashboard and select a project to begin managing notifications. Visit the Notifications page to modify your notifications settings.",
    },
    {"prompt": "Hi", "message": "Hello!  What can I do for you today?"},
    {
        "prompt": "User",
        "message": "It appears you may need some help with users.  Riskuity allows you to create all users and assign them the appropriate permissions to manage your entire Governance Risk and Compliance program. Users are assigned at the project level and only have access to information within projects they are assigned. Riskuity also allows you to assign a role to each user to define permissions at the project level. Visit the main project summary dashboard, select a project, and click the Users tab to begin managing users.",
    },
    {
        "prompt": "Evaluations",
        "message": "It appears you may need some help with evaluations.  Riskuity allows you to create evaluations for each project. Evaluations are observations about a project that are similar to an assessment, however, they don't map to a particular control. Visit the main project summary dashboard, select a project, and click the Evaluations tab to begin managing evaluations.",
    },
]


### Re-populate chat bot prompts ###
def repopulate_chat_bot(db: SessionLocal):
    # Delete all existing records
    db.query(ChatBotPrompt).delete()
    db.commit()

    # Reset the primary key sequence
    db.execute(text("ALTER SEQUENCE chat_bot_prompt_id_seq RESTART WITH 1"))
    db.commit()

    # Repopulate prompts
    for item in PROMPTS_MESSAGES:
        chatbot_prompt = ChatBotPrompt(prompt=item["prompt"], message=item["message"])
        db.add(chatbot_prompt)

    db.commit()

    return {"message": f"Re-created {len(PROMPTS_MESSAGES)} chat bot prompts"}
