import logging
from sqlalchemy import text
from sqlalchemy.orm.session import Session as SessionLocal
from fedrisk_api.db.models import HelpSection

LOGGER = logging.getLogger(__name__)

#### These utils are for populating the help support with content and substituting Riskuity with Riskuity ####

#### Help Sections ####
HELP_SECTIONS = [
    {
        "title": "Getting Started",
        "divId": "getting-started",
        "body": "<strong>Riskuity</strong> allows you to manage frameworks, framework versions and associated controls. These frameworks and controls can then be used with a project. Riskuity allows you to import frameworks and controls from an excel spreadsheet in the <a href='/system-administration'>System Administration</a> area. Only users with the role of System Administrator can access this area. Riskuity provides framework versioning so controls can be mapped to a specific framework version.<br><br>Audit tests, risks, documents, project evaluations, control assessments, tasks, work breakdown structures and control exceptions can also be associated with a project. To create a new project please navigate to <a href='/'>Home</a> (Summary Dashboard) and click on the Start Project Wizard button in the upper left corner.<br><br>Multiple Work Breakdown Structues (WBS) can be used with a project. WBS allow you to define parent and child tasks. To view WBS related data please visit the <a href='/project-dashboard'>Project Studio</a><br><br>Riskuity provides valuable dashboards featuring visualizations of your projects and data. The dashboards can be opened from the side navigation menu.<br><br>Manage your profile by clicking on the top right icon with the person outline.<br><br>The <a href='/subscription'>Subscription</a> side navigation item allows you to manage your Riskuity subscription. You can also invite new users from this dashboard. Only users with the role System Administrator or Billing Administrator can access this.<br><br>Interact with the Riskuity virtual assistant by clicking on the top right icon that appears as a speech bubble.",
        "order": "1",
    },
    {
        "title": "System Administration",
        "divId": "system-administration",
        "body": "The <strong>System Administration</strong> area allows you to configure many features on the Riskuity platform.  Users are allowed to manage their subscription, import regulatory frameworks, manage keywords, define projects, manage organizations and groups, and manage control classes, phases, and families. You can also invite new users and deactivate existing user licenses.  Invoices and payments processing are also managed within this System Administration area.",
        "order": "2",
    },
    {
        "title": "Notifications Dashboard",
        "divId": "notifications-dashboard",
        "body": "This area provides a calendar view of all GRC activities associated with the user and their corresponding due dates. Calendar dates are populated with due dates associated with Tasks, Audits, Corrective Action Plans (CAP) and Plan of Action and Milestones (POA&amp;M). A tabular listing of all notifications is also displayed with the ability to click on each item and view the details.<p>There are 3 different types of notifications.</p><p>Notifications the user sees because he selected a &#39;watch&#39;&nbsp;feature&nbsp;within the application for a particular project data type (i.e., Controls, Evaluations, Risks, Audits).</p><p>Notifications the user sees because he was assigned a task, or selected as a stakeholder for a project data type (i.e., Tasks, Audits, Risks).</p><p>Notifications the user sees because there is an approaching deadline for a GRC activity (upcoming audit, upcoming task completion due deadline, upcoming CAP or POA&amp;M deadline).</p>",
        "order": "3",
    },
    {
        "title": "Governance Dashboard",
        "divId": "governance-dashboard",
        "body": "The <strong>Governance Dashboard</strong> provides a summary view of all controls applied to each project. This area also provides the count and a breakdown by type of the control classes, control families, control phases, control status, assessments, and exceptions for each project.  Additional information on the linked frameworks, as well as details related to each control, exception and assessment associated with the selected project are available in this area Riskuity.  Users are also able to quickly add frameworks, controls, assessments, and exceptions to a project from the Governance Dashboard.",
        "order": "4",
    },
    {
        "title": "Risk Dashboard",
        "divId": "risk-dashboard",
        "body": "The <strong>Risk Dashboard</strong> provides an overview of all risks for the selected project. Within this area users can view the risk mapping, risk score, risk category, risk impact, risk probability, and risk status summaries for each project.  The Risk Mapping chart provides a summary count of risks using a Low, Low-Medium, Medium, Medium-High, and High risk severity assignment range.  The Risk Category chart groups risks by their associated category and count.  Risk Impact captures the organizational impact and count for Extreme, Major, Minor, Moderate, and Insignificant risks.  The projected likelihood of each risk is also summarized under the  Risk Probability area using the Likely, Unlikely, Very Likely, Very Unlikely, and Possible risk probabilities.  Risk Status provides metrics on the number of risks that are Active, Cancelled, Completed, or On Hold.",
        "order": "5",
    },
    {
        "title": "Compliance Dashboard",
        "divId": "compliance-dashboard",
        "body": "The <strong>Compliance Dashboard</strong> provides an overview of all audits that were conducted for the selected project.  The count of compliance audits are viewable by month as well as by status.  Riskuity provides the following status indicators for each audit: Not Started, On Going, Complete, On Hold.",
        "order": "6",
    },
    {
        "title": "Search",
        "divId": "search-feature",
        "body": "Riskuity provides an integrated search feature that searches all API endpoints in the system and indexes keywords associations for each data type.  The search bar is located on the top left header of the application near the Riskuity logo.  To use the search feature, start typing the word you are searching for in the search field.  A dynamic list of all matching items within the Riskuity search database is returned as you type.  Select the item in the list that most closely matches the desired search term.  Riskuity will load the results for the selected item in the main screen.",
        "order": "7",
    },
    {
        "title": "Project Wizard",
        "divId": "project-wizard",
        "body": "<p>The <strong>Project Wizard</strong> provides an easy workflow to quickly get started with GRC audit, compliance, and risk tracking activities.  The wizard streamlines the process of creating a project, associating a regulatory framework, and applying controls.  To begin, select the Home option from the left navigation bar to access The Project Wizard.  It is located at the top of the screen underneath the Riskuity logo and search bar.  Select the Start Project Wizard button to open the Project Wizard.</p> <p>Once the screen opens, you will see the following sequence of steps at the top of the screen: 1. Define Project, 2. Define Governance, 3. Define Compliance Monitoring, 4. Define Risks, 5. Documents.</p> <p>Enter the new project name and associated details in the form fields listed in step 1, Define Project, and submit. </p> <p>Next on the 2. Define Governance Screen, select a framework, add the desired controls to the project and select Next. </p> <p>On the 3. Define Compliance screen, add any known audits that are applicable for the project, then select Next. </p> <p>On the 4. Risk screen, add any project risks for the project. </p> <p>On the 5. Documents screen, add any project level documents that are associated with the project. </p> <p>Please note that documents can also be added for each data type within the system.  For example, a document can be added as a supporting artifact for an audit, risk, control, evaluation, or a WBS item.  The Project Wizard can be accessed at any time to update information with any of the GRC data types. </p>",
        "order": "8",
    },
    {
        "title": "Tasks",
        "divId": "tasks-feature",
        "body": "<p>Riskuity provides the ability to create one or more tasks for a project and assign each task to a user for completion.  To add a task, go to the Notifications Dashboard and select the Add button under the Task header.  Enter the Task Name, Description, Due Date, Assigned To, and other required fields and submit.  The newly created task will be assigned to the project selected on the task creation screen.</p> <p>Tasks can be associated with any project data type within Riskuity.  Current Task associations include: Frameworks, Projects, Controls, Assessments, Ad-hoc Assessments, Project Evaluations, and Risks.</p> <p>The Task feature also provides the ability to set a Task’s status as Not Started, In Progress, or Complete.</p> <p>Additionally, a Task Priority can be set as Low, Medium, High, or Immediate.</p><p>Once a Task is assigned, associated users will receive notifications on the task completion status and any changes to the Task disposition. Users can update their notification preferences within the User Profile area of Riskuity.</p>",
        "order": "9",
    },
    {
        "title": "User Management",
        "divId": "user-management",
        "body": "<p>Riskuity is a role-based system that limits a user&rsquo;s ability to perform system functions based on the role assigned. &nbsp;Roles are assigned within the Project Workflow under the Users tab. &nbsp;To assign a user to a project, the user must have an active Riskuity license. &nbsp;If you are unsure of whether a user has an active license, please follow up with your Riskuity System Administrator. &nbsp;</p><p>To assign a user to a project, go to the Home area of Riskuity on the left navigation menu and select the desired project from the project dropdown list. &nbsp;Click on the project name to go into the project wizard for the selected project. &nbsp;Click on the Users tab. &nbsp;Click on the Add button.</p><p>Next select the user from the Users dropdown list and select the desired role for the user. &nbsp;</p><p>Below is an overview of the Riskuity roles and a brief description of each.</p><ul><li><strong>System Administrator</strong> &ndash; Has God privileges. &nbsp;Can execute and edit any page or feature within any project. &nbsp; Has full Create, Read, Update, Delete (CRUD) access to every component in the system. &nbsp;Creates new system users.</li><li><strong>Project Manager</strong> &ndash; Has CRUD access for new projects, edits existing projects, assigns new users to a Team, assigns user roles, approves any requests to join a project or receive notifications for a project, approves any workflows that require sign-off for a project (examples: adding a new governance framework, escalating a risk, creating an exception for compliance, etc.). &nbsp;Has CRUD for controls, assessments, frameworks, risks, and document upload.</li><li><strong>Project Administrator&nbsp;</strong>&ndash; Can execute and edit any page or feature within the assigned project. &nbsp;</li><li><strong>Billing Administrator</strong> &ndash; Has access to only perform management of the system subscription. &nbsp; This role can perform payment processing, view invoices, and change the subscription plan.</li><li><strong>Project Analyst&nbsp;</strong>&ndash; Primary user for conducting the bulk of the work in the system. &nbsp;Has CRUD capability for new projects, controls, assessments, frameworks, risks, document upload.</li><li><strong>Auditor&nbsp;</strong>&ndash; Read Only account.</li></ul></p>",
        "order": "10",
    },
]


### Re-populate help-support ###
def repopulate_help_support(db: SessionLocal):
    # Delete all existing records
    db.query(HelpSection).delete()
    db.commit()

    # Reset the primary key sequence
    db.execute(text("ALTER SEQUENCE help_section_id_seq RESTART WITH 1"))
    db.commit()

    # Repopulate prompts
    for item in HELP_SECTIONS:
        help_section = HelpSection(
            title=item["title"], divId=item["divId"], body=item["body"], order=item["order"]
        )
        db.add(help_section)

    db.commit()

    return {"message": f"Re-created {len(HELP_SECTIONS)} help sections"}
