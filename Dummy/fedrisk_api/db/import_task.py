import logging
import pandas as pd
from io import BytesIO

from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import ImportTask, User, Tenant
from fedrisk_api.schema.import_task import CreateImportTask
from fedrisk_api.utils.utils import filter_by_tenant

from fedrisk_api.s3 import S3Service

# from fedrisk_api.db import import_task as db_import_task

LOGGER = logging.getLogger(__name__)


def get_user_task_import(db: Session, user_id: int):
    user_details = db.query(User).filter(User.id == user_id).first()
    LOGGER.info(f"{user_details}")
    return user_details


def create_import_task(db: Session, task: CreateImportTask, file_content_type: str, tenant_id: int):
    task_dict = {**task.dict(), **{"file_content_type": file_content_type}}
    new_task_import = ImportTask(**task_dict, tenant_id=tenant_id)
    db.add(new_task_import)
    db.commit()
    db.refresh(new_task_import)
    return new_task_import


async def get_all_import_tasks_by_wbs(
    db: Session, tenant_id: int, wbs_id: int, user_id: int, project_id: int
):
    imports = []
    task_imports = (
        db.query(ImportTask)
        .filter(ImportTask.tenant_id == tenant_id)
        .filter(ImportTask.wbs_id == wbs_id)
        .all()
    )
    for task_import in task_imports:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        file_key = f"tasks/{task_import.id}-{task_import.name}"
        LOGGER.info(f"file key {file_key}")
        s3_service = S3Service()
        response = s3_service.get_object_tags(tenant.s3_bucket, file_key)
        # Extract tags from the response
        tags = response.get("TagSet", [])
        task_import_cur = db.query(ImportTask).filter(ImportTask.id == task_import.id)
        if task_import.imported is None:
            # check s3 tags
            if tags:
                # print("Tags for the object:")
                for tag in tags:
                    # print(f"Key: {tag['Key']}, Value: {tag['Value']}")
                    if tag["Key"] == "ScanResult":
                        scan_result = tag["Value"]
                        # Try to import
                        if scan_result == "Clean":
                            LOGGER.info("Scan result clean")
                            from fedrisk_api.db.util.import_task_utils import (
                                load_data_from_dataframe_tasks as load_data_from_dataframe_util,
                            )

                            # Try to import

                            # import file data using util
                            aws_import_file = await s3_service.get_file_object(
                                tenant.s3_bucket, file_key
                            )
                            my_data_frame = pd.read_excel(BytesIO(aws_import_file["Body"].read()))
                            task_control_num = await load_data_from_dataframe_util(
                                my_data_frame,
                                tenant_id,
                                True,
                                user_id,
                                project_id,
                                wbs_id,
                                task_import.id,
                            )
                            LOGGER.info(task_control_num)
                            if type(task_control_num) != list:
                                # if task_control_num.get("error") is not None:
                                task_import_cur.update(
                                    {
                                        "imported": False,
                                        "import_results": f"There was a problem importing your file. {task_control_num.get('error')}",
                                    }
                                )
                                db.commit()
                            else:
                                success_msg = f"Successfully loaded {task_control_num[0]} tasks."
                                LOGGER.info(f"{success_msg}")
                                task_import_cur.update(
                                    {
                                        "imported": True,
                                        "import_results": success_msg,
                                    }
                                )
                                db.commit()
                    elif scan_result == "Infected":
                        task_import_cur.update(
                            {
                                "imported": False,
                                "import_results": "Could not import task as file is infected",
                            }
                        )
                        db.commit()
                imports.append(task_import)
            else:
                print("No tags found for the object.")
                imports.append(task_import)
        else:
            imports.append(task_import)
    return imports


def get_import_task(db: Session, id: int, tenant_id: int):
    return db.query(ImportTask).filter_by(ImportTask.id == id).first()


def delete_import_task(db: Session, id: int, tenant_id: int):
    existing_import_task = filter_by_tenant(db, ImportTask, tenant_id).filter(ImportTask.id == id)
    if not existing_import_task.first():
        return False

    existing_import_task.delete(synchronize_session=False)
    db.commit()
    return True
