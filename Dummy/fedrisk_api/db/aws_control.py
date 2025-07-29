import logging
import pandas as pd
from io import BytesIO
from sqlalchemy.orm import Session
from itertools import groupby

from sqlalchemy import Date, cast

from fedrisk_api.s3 import S3Service

from fedrisk_api.db.models import (
    AWSControl,
    ProjectControl,
    AWSControlProjectControl,
    Project,
    ImportAWSControls,
    Control,
    Tenant,
)
from fedrisk_api.schema.aws_control import (
    CreateAWSControl,
    UpdateAWSControl,
    CreateAWSControlProjControl,
    CreateImportAWSControl,
)
from fedrisk_api.utils.utils import filter_by_tenant


LOGGER = logging.getLogger(__name__)


def create_aws_control(aws_control: CreateAWSControl, db: Session):
    aws_control = AWSControl(**aws_control.dict())
    db.add(aws_control)
    db.commit()
    return aws_control


def create_aws_proj_control(aws_proj_control: CreateAWSControlProjControl, db: Session):
    aws_proj_control = AWSControlProjectControl(**aws_proj_control.dict())
    db.add(aws_proj_control)
    db.commit()
    return aws_proj_control


def get_aws_control(
    db: Session,
    tenant_id: int,
):
    queryset = (
        db.query(AWSControl)
        .join(AWSControlProjectControl, AWSControlProjectControl.aws_control_id == AWSControl.id)
        .join(ProjectControl, AWSControlProjectControl.project_control_id == ProjectControl.id)
        .join(Project, ProjectControl.project_id == Project.id)
        .filter(Project.tenant_id == tenant_id)
        .all()
    )
    return queryset


def get_aws_control_by_id(db: Session, aws_control_id: int):
    queryset = db.query(AWSControl).filter(AWSControl.id == aws_control_id).first()
    return queryset


def update_aws_control_by_id(
    aws_control: UpdateAWSControl, db: Session, aws_control_id: int, tenant_id: int
):
    queryset = filter_by_tenant(db=db, model=AWSControl, tenant_id=tenant_id).filter(
        AWSControl.id == aws_control_id
    )

    if not queryset.first():
        return False

    queryset.update(aws_control.dict(exclude_unset=True))
    db.commit()
    return True


def get_aws_controls_by_project_control_id(db: Session, project_control_id: int):
    daily_count = (
        db.query(
            cast(AWSControl.created, Date).label("date"),
            AWSControl.id,
            AWSControl.aws_id,
            AWSControl.aws_title,
            AWSControl.aws_control_status,
            AWSControl.aws_severity,
            AWSControl.aws_failed_checks,
            AWSControl.aws_unknown_checks,
            AWSControl.aws_not_available_checks,
            AWSControl.aws_passed_checks,
            AWSControl.aws_related_requirements,
            AWSControl.aws_custom_parameters,
            AWSControl.created,
            ProjectControl.id.label("project_control_id"),
            Control.name.label("control_name"),
        )
        .select_from(AWSControl, ProjectControl, Control)
        .join(AWSControlProjectControl, AWSControlProjectControl.aws_control_id == AWSControl.id)
        .join(ProjectControl, ProjectControl.id == AWSControlProjectControl.project_control_id)
        .join(Control, ProjectControl.control_id == Control.id)
        .group_by(AWSControl.id)
        .group_by(ProjectControl.id)
        .group_by(Control.id)
        .group_by(cast(AWSControl.created, Date))
        .filter(ProjectControl.id == project_control_id)
        .order_by(AWSControl.created.desc())
    )
    if not daily_count.first():
        return "No controls found"

    grouped = {k: list(g) for k, g in groupby(daily_count, lambda t: t.date)}

    first_group_key = (
        db.query(
            cast(AWSControl.created, Date).label("date"),
        )
        .select_from(AWSControl)
        .join(AWSControlProjectControl, AWSControlProjectControl.aws_control_id == AWSControl.id)
        .join(ProjectControl, ProjectControl.id == AWSControlProjectControl.project_control_id)
        .join(Control, ProjectControl.control_id == Control.id)
        .group_by(AWSControl.id)
        .group_by(cast(AWSControl.created, Date))
        .filter(ProjectControl.id == project_control_id)
        .order_by(AWSControl.created.desc())
        .first()
    )

    return grouped[first_group_key[0]]


def get_aws_controls_by_project_id(db: Session, project_id: int):
    daily_count = (
        db.query(
            AWSControlProjectControl.project_control_id,
            Control.name.label("control_name"),
            cast(AWSControl.created, Date).label("date"),
            AWSControl.id,
            AWSControl.aws_id,
            AWSControl.aws_title,
            AWSControl.aws_control_status,
            AWSControl.aws_severity,
            AWSControl.aws_failed_checks,
            AWSControl.aws_unknown_checks,
            AWSControl.aws_not_available_checks,
            AWSControl.aws_passed_checks,
            AWSControl.aws_related_requirements,
            AWSControl.aws_custom_parameters,
        )
        .select_from(AWSControlProjectControl, Control, AWSControl)
        .join(ProjectControl, AWSControlProjectControl.project_control_id == ProjectControl.id)
        .join(Control, ProjectControl.control_id == Control.id)
        .join(AWSControl, AWSControlProjectControl.aws_control_id == AWSControl.id)
        .filter(ProjectControl.project_id == project_id)
        .group_by(AWSControlProjectControl.project_control_id)
        .group_by(Control.name)
        .group_by(cast(AWSControl.created, Date))
        .group_by(AWSControl.id)
        .group_by(AWSControl.aws_id)
        .group_by(AWSControl.aws_title)
        .group_by(AWSControl.aws_control_status)
        .group_by(AWSControl.aws_severity)
        .group_by(AWSControl.aws_failed_checks)
        .group_by(AWSControl.aws_unknown_checks)
        .group_by(AWSControl.aws_not_available_checks)
        .group_by(AWSControl.aws_passed_checks)
        .group_by(AWSControl.aws_related_requirements)
        .group_by(AWSControl.aws_custom_parameters)
    )

    if not daily_count.first():
        return "No controls found"
    return daily_count.all()
    # grouped = {k: list(g) for k, g in groupby(daily_count.distinct(), lambda t: t.date)}

    # first_group_key = (
    #     db.query(
    #         cast(AWSControl.created, Date).label("date"),
    #     )
    #     .select_from(AWSControl)
    #     .join(AWSControlProjectControl, AWSControlProjectControl.aws_control_id == AWSControl.id)
    #     .join(ProjectControl, ProjectControl.id == AWSControlProjectControl.project_control_id)
    #     .join(Control, ProjectControl.control_id == Control.id)
    #     .group_by(AWSControl.id)
    #     .group_by(cast(AWSControl.created, Date))
    #     .filter(ProjectControl.project_id == project_id)
    #     .order_by(AWSControl.created.desc())
    #     .first()
    # )

    # return grouped[first_group_key[0]]


def delete_aws_control_by_id(db: Session, aws_control_id: int):
    aws_control = db.query(AWSControl).filter(AWSControl.id == aws_control_id).first()

    if not aws_control:
        return False

    # delete all mapping references
    db.query(AWSControlProjectControl).filter(
        AWSControlProjectControl.aws_control_id == id
    ).delete()
    db.delete(aws_control)
    db.commit()
    return True


def create_import_aws_control(
    db: Session, aws_controls: CreateImportAWSControl, file_content_type: str, tenant_id: int
):
    aws_controls_dict = {**aws_controls.dict(), **{"file_content_type": file_content_type}}
    new_aws_controls_import = ImportAWSControls(**aws_controls_dict, tenant_id=tenant_id)
    db.add(new_aws_controls_import)
    db.commit()
    db.refresh(new_aws_controls_import)
    return new_aws_controls_import


def get_all_import_aws_controls(db: Session, tenant_id: int):
    return filter_by_tenant(db, ImportAWSControls, tenant_id).all()


def get_import_aws_control(db: Session, id: int, tenant_id: int):
    return (
        filter_by_tenant(db, ImportAWSControls, tenant_id)
        .filter(ImportAWSControls.id == id)
        .first()
    )


def delete_import_aws_control(db: Session, id: int, tenant_id: int):
    existing_import_aws_controls = filter_by_tenant(db, ImportAWSControls, tenant_id).filter(
        ImportAWSControls.id == id
    )
    if not existing_import_aws_controls.first():
        return False

    existing_import_aws_controls.delete(synchronize_session=False)
    db.commit()
    return True


async def get_aws_controls_import(db: Session, tenant_id: int):
    imports = []
    aws_control_imports = (
        db.query(ImportAWSControls).filter(ImportAWSControls.tenant_id == tenant_id).all()
    )
    for aws_control_import in aws_control_imports:
        # check s3 tags
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        file_key = f"awscontrols/{aws_control_import.id}-{aws_control_import.name}"
        if aws_control_import.imported is None:
            # Try to import
            # try:
            s3_service = S3Service()
            response = s3_service.get_object_tags(tenant.s3_bucket, file_key)
            # Extract tags from the response
            tags = response.get("TagSet", [])
            aws_control_import_cur = db.query(ImportAWSControls).filter(
                ImportAWSControls.id == aws_control_import.id
            )
            if tags:
                # print("Tags for the object:")
                for tag in tags:
                    # print(f"Key: {tag['Key']}, Value: {tag['Value']}")
                    if tag["Key"] == "ScanResult":
                        scan_result = tag["Value"]
                        # Try to import
                        if scan_result == "Clean":
                            from fedrisk_api.db.util.import_aws_controls import (
                                load_aws_control_data_from_dataframe as load_aws_control_data_from_dataframe_s3,
                            )

                            aws_import_file = await s3_service.get_file_object(
                                tenant.s3_bucket, file_key
                            )
                            df = pd.read_csv(BytesIO(aws_import_file["Body"].read()))
                            aws_control_num = await load_aws_control_data_from_dataframe_s3(
                                df, aws_control_import.project_id
                            )
                            if type(aws_control_num) != list:
                                # if aws_control_num.get("error") is not None:
                                aws_control_import_cur.update(
                                    {
                                        "imported": False,
                                        "import_results": f"There was a problem importing your file. {aws_control_import_cur.get('error')}",
                                    }
                                )
                                db.commit()
                            else:
                                success_msg = f"Successfully loaded {aws_control_num[0]} aws controls. Successfully loaded {aws_control_num[1]} aws control to project control mappings."
                                LOGGER.info(f"{success_msg}")
                                LOGGER.info(f"aws_control_import_cur {aws_control_import_cur}")
                                aws_control_import_cur.update(
                                    {"imported": True, "import_results": success_msg}
                                )
                                db.commit()
                            # return "Imported"  # response added
                        elif scan_result == "Infected":
                            aws_control_import_cur.update(
                                {
                                    "imported": False,
                                    "import_results": "Could not import controls as file is infected",
                                }
                            )
                            db.commit()
                imports.append(aws_control_import)
            else:
                print("No tags found for the object.")
                imports.append(aws_control_import)
            # except Exception:
            #     LOGGER.exception("Could not find object with tags")
            #     raise AssertionError("Could not find object with tags")
        else:
            imports.append(aws_control_import)
    return imports
