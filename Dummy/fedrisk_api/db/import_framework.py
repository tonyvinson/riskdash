import logging
import pandas as pd
from io import BytesIO

from sqlalchemy.orm.session import Session

from fedrisk_api.db.models import ImportFramework, User, Tenant
from fedrisk_api.schema.import_framework import CreateImportFramework
from fedrisk_api.utils.utils import filter_by_tenant

from fedrisk_api.s3 import S3Service

# from fedrisk_api.db import import_framework as db_import_framework

LOGGER = logging.getLogger(__name__)


def get_user_framework_import(db: Session, user_id: int):
    user_details = db.query(User).filter(User.id == user_id).first()
    LOGGER.info(f"{user_details}")
    return user_details


def create_import_framework(
    db: Session, framework: CreateImportFramework, file_content_type: str, tenant_id: int
):
    framework_dict = {**framework.dict(), **{"file_content_type": file_content_type}}
    new_framework_import = ImportFramework(**framework_dict, tenant_id=tenant_id)
    db.add(new_framework_import)
    db.commit()
    db.refresh(new_framework_import)
    return new_framework_import


async def get_all_import_frameworks(db: Session, tenant_id: int):
    imports = []
    framework_imports = (
        db.query(ImportFramework).filter(ImportFramework.tenant_id == tenant_id).all()
    )
    for framework_import in framework_imports:
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        file_key = f"frameworks/{framework_import.id}-{framework_import.name}"
        LOGGER.info(f"file key {file_key}")
        s3_service = S3Service()
        response = s3_service.get_object_tags(tenant.s3_bucket, file_key)
        # Extract tags from the response
        tags = response.get("TagSet", [])
        framework_import_cur = db.query(ImportFramework).filter(
            ImportFramework.id == framework_import.id
        )
        if framework_import.imported is None:
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
                            from fedrisk_api.db.util.import_framework_utils import (
                                load_data_from_dataframe as load_data_from_dataframe_util,
                            )

                            # Try to import

                            # import file data using util
                            aws_import_file = await s3_service.get_file_object(
                                tenant.s3_bucket, file_key
                            )
                            my_data_frame = pd.read_excel(BytesIO(aws_import_file["Body"].read()))
                            framework_control_num = load_data_from_dataframe_util(
                                my_data_frame, tenant_id, True
                            )
                            if type(framework_control_num) != list:
                                # if framework_control_num.get("error") is not None:
                                framework_import_cur.update(
                                    {
                                        "imported": False,
                                        "import_results": f"There was a problem importing your file. {framework_control_num.get('error')}",
                                    }
                                )
                                db.commit()
                            else:
                                success_msg = f"Successfully loaded {framework_control_num[0]} frameworks. Successfully loaded {framework_control_num[1]} controls. Successfully loaded {framework_control_num[2]} framework_versions."
                                LOGGER.info(f"{success_msg}")
                                framework_import_cur.update(
                                    {
                                        "imported": True,
                                        "import_results": success_msg,
                                    }
                                )
                                db.commit()
                    elif scan_result == "Infected":
                        framework_import_cur.update(
                            {
                                "imported": False,
                                "import_results": "Could not import framework as file is infected",
                            }
                        )
                        db.commit()
                imports.append(framework_import)
            else:
                print("No tags found for the object.")
                imports.append(framework_import)
        else:
            imports.append(framework_import)
    return imports


def get_import_framework(db: Session, id: int, tenant_id: int):
    return db.query(ImportFramework).filter_by(ImportFramework.id == id).first()


def delete_import_framework(db: Session, id: int, tenant_id: int):
    existing_import_framework = filter_by_tenant(db, ImportFramework, tenant_id).filter(
        ImportFramework.id == id
    )
    if not existing_import_framework.first():
        return False

    existing_import_framework.delete(synchronize_session=False)
    db.commit()
    return True
