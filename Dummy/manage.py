import asyncio
import io
import logging
import os

import pandas as pd
import uvicorn
from rich import print
from typer import Typer

from config.config import Settings

from fedrisk_api.db.database import get_db
from fedrisk_api.db.models import Tenant
from fedrisk_api.db.util.data_creation_utils import clean_loaded_data as clean_loaded_data_util
from fedrisk_api.db.util.data_creation_utils import clean_permissions as clean_permissions_util
from fedrisk_api.db.util.data_creation_utils import clean_roles as clean_roles_util
from fedrisk_api.db.util.data_creation_utils import create_or_get_user as create_or_get_user_util
from fedrisk_api.db.util.data_creation_utils import (
    generate_roles_with_permissions as generate_roles_with_permissions_util,
)
from fedrisk_api.db.util.data_creation_utils import (
    remap_tenant_user_roles as remap_tenant_user_roles_util,
)

from fedrisk_api.db.util.data_creation_utils import (
    load_controls_attributes as load_controls_attributes_util,
)
from fedrisk_api.db.util.data_creation_utils import load_data as load_data_util
from fedrisk_api.db.util.data_creation_utils import remove_psi as remove_psi_util
from fedrisk_api.db.util.data_creation_utils import (
    create_tenant_s3_tags as create_tenant_s3_tags_util,
)
from fedrisk_api.db.util.import_framework_utils import (
    load_data_from_dataframe as load_data_from_dataframe_util,
)
from fedrisk_api.db.util.import_framework_utils import (
    remove_data_from_dataframe as remove_data_from_dataframe_util,
)

from fedrisk_api.db.util.import_aws_controls import (
    load_aws_control_data_from_dataframe as load_aws_control_data_from_dataframe_util,
)

from fedrisk_api.db.util.data_creation_utils import (
    create_tenant_s3_bucket as create_tenant_s3_bucket_util,
)

from fedrisk_api.db.util.data_creation_utils import (
    create_tenant_user_folder_s3 as create_tenant_user_folder_s3_util,
)

from fedrisk_api.db.util.data_creation_utils import (
    create_tenant_users_folders_s3 as create_tenant_users_folders_s3_util,
)

from fedrisk_api.db.util.data_creation_utils import (
    create_tenant_s3_lambda_trigger as create_tenant_s3_lambda_trigger_util,
)

from fedrisk_api.db.util.data_creation_utils import (
    create_task_status as load_task_status_util,
)

from fedrisk_api.db.util.data_creation_utils import (
    migrate_task_status as migrate_task_status_util,
)

from fedrisk_api.db.util.data_creation_utils import (
    load_task_categories as load_task_categories_util,
)

from fedrisk_api.db.util.data_creation_utils import (
    add_roles_permissions_for_tenant as add_roles_permissions_for_tenant_util,
)

from fedrisk_api.db.util.add_workflow_task_assoc_utils import (
    create_task_workflow_assoc as create_task_workflow_assoc_util,
)

from fedrisk_api.db.util.encrypt_pii_utils import (
    encrypt_user_data as encrypt_user_data_util,
    decrypt_user_data as decrypt_user_data_util,
    encrypt_user_by_id as encrypt_user_by_id_util,
    decrypt_user_by_id as decrypt_user_by_id_util,
    get_decrypted_user_display_by_id as get_decrypted_user_display_by_id_util,
)

from fedrisk_api.db.util.import_workflow_tasks import (
    safe_import_spreadsheet as safe_import_spreadsheet_util,
    import_workflow_flowchart_from_excel as import_workflow_flowchart_from_excel_util,
)

from fedrisk_api.db.util.chat_bot_utils import (
    repopulate_chat_bot as repopulate_chat_bot_util,
)

from fedrisk_api.db.util.help_support_utils import (
    repopulate_help_support as repopulate_help_support_util,
)

from fedrisk_api.db.util.webhook_api_key_utils import (
    update_tenant_webhook_api_key as update_tenant_webhook_api_key_util,
)

from fedrisk_api.utils.cognito import CognitoIdentityProviderWrapper

from fedrisk_api.utils.ses import EmailService

from fedrisk_api.utils.sns import SnsWrapper

# from fedrisk_api.endpoints import control_class

from config.config import Settings


LOGGER = logging.getLogger(__name__)

app = Typer()


# @app.command()
# def load_risk_attributes():
# with next(get_db()) as db:
# load_risk_attributes_util(db)


@app.command()
def load_controls_attributes():
    with next(get_db()) as db:
        load_controls_attributes_util(db)


@app.command()
def generate_roles_with_permissions():
    "Generate Roles and Permissions and Assign Permissions to Role"

    with next(get_db()) as db:
        generate_roles_with_permissions_util(db)


@app.command()
def clean_roles():
    with next(get_db()) as db:
        clean_roles_util(db)


@app.command()
def clean_permissions():
    with next(get_db()) as db:
        clean_permissions_util(db)


@app.command()
def add_roles_permissions_for_tenant(tenant_id: int):
    with next(get_db()) as db:
        add_roles_permissions_for_tenant_util(tenant_id, db)


@app.command()
def remap_user_roles_tenant(tenant_id: int):
    with next(get_db()) as db:
        remap_tenant_user_roles_util(db, tenant_id)


@app.command()
def load_data():
    with next(get_db()) as db:
        load_data_util(db)


@app.command()
def create_task_categories():
    with next(get_db()) as db:
        load_task_categories_util(db)


@app.command()
def remove_psi():
    with next(get_db()) as db:
        remove_psi_util(db)


@app.command()
def clean_loaded_data():
    with next(get_db()) as db:
        clean_loaded_data_util(db)


@app.command()
def create_wf_task_assoc():
    with next(get_db()) as db:
        create_task_workflow_assoc_util(db)


# encryption and decryption of PII
@app.command()
def encrypt_user_data():
    with next(get_db()) as db:
        encrypt_user_data_util(db)


@app.command()
def decrypt_user_data():
    with next(get_db()) as db:
        decrypt_user_data_util(db)


# encrypt_user_by_id
@app.command()
def encrypt_user_by_id(user_id: int):
    with next(get_db()) as db:
        encrypt_user_by_id_util(db, user_id)


# decrypt_user_by_id
@app.command()
def decrypt_user_by_id(user_id: int):
    with next(get_db()) as db:
        decrypt_user_by_id_util(db, user_id)


# get_decrypted_user_display_by_id
@app.command()
def get_decrypted_user_display_by_id(user_id: int):
    with next(get_db()) as db:
        get_decrypted_user_display_by_id_util(db, user_id)


# repopulate chat bot
@app.command()
def repopulate_chat_bot():
    with next(get_db()) as db:
        repopulate_chat_bot_util(db)


# repopulate help sections
@app.command()
def repopulate_help_sections():
    with next(get_db()) as db:
        repopulate_help_support_util(db)


# update_tenant_webhook_api_key_util
@app.command()
def update_tenant_webhook_api_key(tenant_id: int, webhook_api_key: str):
    with next(get_db()) as db:
        update_tenant_webhook_api_key_util(db, tenant_id, webhook_api_key)


@app.command()
def test(name: str):
    print(f"[bold green]Success[/bold green] {name}.")


@app.command()
def runserver(host: str = "127.0.0.1", port: int = 8000, reload: bool = False):
    try:
        uvicorn.run("main:app", host=host, port=port, reload=reload)
    except Exception as e:
        print(f"[bold red]Error while starting Server : {e}[bold /red]")


@app.command()
def runserver_ssl(
    host: str = "127.0.0.1",
    port: int = 8000,
    ssl_keyfile: str = None,
    ssl_certfile: str = None,
    reload: bool = False,
):
    if ssl_certfile is None or ssl_certfile is None:
        print("[bold red]SSL_KEYFILE OR SSL_CERTFILE NOT PROVIDED[bold /red]")
        return

    ssl_keyfile_path = os.path.exists(ssl_keyfile)
    ssl_certfile_path = os.path.exists(ssl_certfile)

    if ssl_keyfile_path:
        ssl_certfile = os.path.abspath(ssl_keyfile)
    else:
        print("[bold red]SSL_KEYFILE NOT EXIST[bold /red]")
        return

    if ssl_certfile_path:
        ssl_certfile = os.path.abspath(ssl_certfile)
    else:
        print("[bold red]SSL_CERTFILE NOT EXIST[bold /red]")
        return
    try:
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            ssl_keyfile=ssl_keyfile,
            ssl_certfile=ssl_certfile,
            reload=reload,
        )
    except Exception as e:
        print(f"[bold red]Please Provide Correct ssl_key or ssl_cert : {e}[bold /red]")


@app.command()
# def create_cognito_user(user_email: str, password: str, tenant_id: int, super_user: bool = False):
def create_cognito_user(
    user_email: str,
    password: str,
    phone_number: str,
    first_name: str,
    last_name: str,
    tenant_id: int,
    system_role: int,
):
    user = None
    with next(get_db()) as db:
        all_tenants = db.query(Tenant).all()
        tenant_ids = [tenant.id for tenant in all_tenants]
        if tenant_id not in tenant_ids:
            print(
                f"[bold red]Tenant with id: {tenant_id} does not exist. Please provide a valid tenant id.[bold /red]"
            )
            return

        try:
            user = create_or_get_user_util(
                db,
                user_email.lower(),
                is_active=True,
                system_role=system_role,
                first_name=first_name,
                last_name=last_name,
                phone_no=phone_number,
                # is_superuser=super_user,
                # is_tenant_admin=False,
                tenant_id=tenant_id,
                do_commit=True,
            )
        except Exception as exc:
            print(
                f"[bold red]Unable to locate or create user {user_email} in database - {str(exc)}[/bold red]"
            )
    if user:
        cognito_client = CognitoIdentityProviderWrapper()
        settings = Settings()
        print(f"attempting to create user in pool id {settings.COGNITO_USER_POOL_ID}")
        try:
            cognito_client.sign_up_user(
                user_email.lower(), password, phone_number, first_name, last_name
            )
            print(f"[bold green]User '{user_email}' created. [/bold green] ")
        except Exception as e:
            if "User already exists" in str(e):
                print(f"[bold green]User '{user_email}' is ready to roll! [/bold green] ")
                print(
                    f"[bold green]\tNote: User '{user_email}' already existed in cognito (password not changed).[bold /green]"
                )
            else:
                print(
                    f"[bold red]Unable to create Cognito User: '{user_email}' - {str(e)}.[bold /red]"
                )


@app.command()
def import_framework_spreadsheets(tenant_id: int, is_superuser: bool):
    spreadsheet_files = [
        "notebooks/01-24-CFR-674_Import.xlsx",
        "notebooks/10-24-800_53_R5_Import.xlsx",
    ]
    frameworks = 0
    controls = 0
    framework_versions = 0
    for file in spreadsheet_files:
        my_data_frame = pd.read_excel(file)
        framework_control_num = load_data_from_dataframe_util(
            my_data_frame, tenant_id, is_superuser
        )
        frameworks += framework_control_num[0]
        controls += framework_control_num[1]
        framework_versions += framework_control_num[2]
    print(f"[bold green]Successfully loaded {frameworks} frameworks[/bold green].")
    print(f"[bold green]Successfully loaded {controls} controls[/bold green].")
    print(f"[bold green]Successfully loaded {framework_versions} framework versions[/bold green].")


@app.command()
def import_aws_controls(project_id: int):
    spreadsheet_file = "notebooks/NIST-800-53.csv"
    my_data_frame = pd.read_csv(spreadsheet_file)
    aws_control_num = load_aws_control_data_from_dataframe_util(my_data_frame, project_id)
    print(f"[bold green]Successfully loaded {aws_control_num[0]} aws controls[/bold green].")
    print(
        f"[bold green]Successfully loaded {aws_control_num[1]} aws control to project control mappings[/bold green]."
    )


@app.command()
def remove_import_framework_spreadsheet():
    spreadsheet_file = "notebooks/CFR49_Part674_Framework_Import.xlsx"
    my_data_frame = pd.read_excel(spreadsheet_file)
    framework_control_num = remove_data_from_dataframe_util(my_data_frame)
    print(f"[bold green]Successfully removed {framework_control_num[0]} frameworks[/bold green].")
    print(f"[bold green]Successfully removed {framework_control_num[1]} controls[/bold green].")


@app.command()
def import_workflow_data(filepath: str, user_id: int, tenant_id: int, project_id: int):
    """
    Import a workflow flowchart from an Excel spreadsheet after scanning it for suspicious content.
    """
    print(f"Scanning {filepath} for malicious content...")

    if safe_import_spreadsheet_util(filepath) is True:
        print("✅ Spreadsheet is safe. Proceeding with import...")

        with next(get_db()) as db:
            import_workflow_flowchart_from_excel_util(filepath, db, user_id, tenant_id, project_id)

        print("🚀 Import completed successfully.")
    else:
        print("❌ Suspicious content detected. Import aborted.")


@app.command()
def send_test_email():
    EmailService().send_email(
        to_email="sarah.vardy@longevityconsulting.com",
        subject="This is a test",
        message="Hi Developer\nIs Python SDK work complete or not?",
    )
    return {"message": "Mail Sent"}


@app.command()
def send_test_sms():
    SnsWrapper().publish_text_message(phone_number="+12513495597", message="Testing")
    return {"message": "Text message sent"}


@app.command()
def create_tenant_s3_bucket(tenant_id: int):
    with next(get_db()) as db:
        create_tenant_s3_bucket_util(db, tenant_id)


@app.command()
def create_tenant_user_s3_folder(user_id: int, tenant_id: int):
    with next(get_db()) as db:
        create_tenant_user_folder_s3_util(db, user_id, tenant_id)


@app.command()
def create_tenant_users_s3_folders(tenant_id: int):
    with next(get_db()) as db:
        create_tenant_users_folders_s3_util(db, tenant_id)


@app.command()
def create_tenant_s3_lambda_trigger(lambda_function: str, s3_bucket: str):
    create_tenant_s3_lambda_trigger_util(lambda_function, s3_bucket)


# Use this command to create bucket tags for an environment after using the sh db_tunnel.sh
@app.command()
def create_tenant_s3_bucket_tags(environment: str):
    with next(get_db()) as db:
        create_tenant_s3_tags_util(db, environment)


@app.command()
def create_task_statuses():
    with next(get_db()) as db:
        load_task_status_util(db, True)


@app.command()
def migrate_task_statuses():
    with next(get_db()) as db:
        asyncio.run(migrate_task_status_util(db, True))  # ✅ Runs the async function properly


if __name__ == "__main__":
    app()
