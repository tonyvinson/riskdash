import logging
import pandas as pd
from fedrisk_api.db import aws_control as db_aws_control
from fedrisk_api.db.database import get_db
from fedrisk_api.db.models import (
    AWSControl,
    ProjectControl,
    Control,
    FrameworkVersion,
    Framework,
    ControlFrameworkVersion,
)
from fedrisk_api.schema import aws_control as schema_aws_control
from sqlalchemy.orm import Session

LOGGER = logging.getLogger(__name__)


async def load_aws_control_data_from_dataframe(my_data_frame, project_id):
    db = next(get_db())
    num_aws_controls = 0
    num_aws_proj_cont_mappings = 0
    related_requirements = []
    try:
        for row in my_data_frame.iterrows():
            my_next_aws_control_aws_id = str(row[1]["ID"])
            my_next_aws_control_from_db = (
                db.query(AWSControl).filter(AWSControl.aws_id == my_next_aws_control_aws_id).first()
            )
            if not my_next_aws_control_from_db:
                next_aws_control = schema_aws_control.CreateAWSControl(
                    aws_id=my_next_aws_control_aws_id,
                    aws_title=row[1]["Title"],
                    aws_control_status=row[1]["Control Status"],
                    aws_severity=row[1]["Severity"],
                    aws_failed_checks=row[1]["Failed checks"],
                    aws_unknown_checks=row[1]["Unknown checks"],
                    aws_not_available_checks=row[1]["Not available checks"],
                    aws_passed_checks=row[1]["Passed checks"],
                    aws_related_requirements=row[1]["Related requirements"],
                    aws_custom_parameters=row[1]["Custom parameters"],
                )
                response = db_aws_control.create_aws_control(next_aws_control, db)
                db.commit()
                related_requirements.append(
                    {"id": response.id, "requirements": row[1]["Related requirements"]}
                )
                num_aws_controls += 1
    except Exception as e:
        LOGGER.exception("There was a problem processing this request")
        return {"error": f"{e}"}
    # create mapping to existing project controls
    project_controls = (
        db.query(ProjectControl, Control, FrameworkVersion, Framework)
        .join(Control, ProjectControl.control_id == Control.id)
        .join(ControlFrameworkVersion, ControlFrameworkVersion.control_id == Control.id)
        .join(
            FrameworkVersion,
            FrameworkVersion.id == ControlFrameworkVersion.framework_version_id,
        )
        .join(Framework, FrameworkVersion.framework_id == Framework.id)
        .filter(ProjectControl.project_id == project_id)
    ).all()
    try:
        for pc in project_controls:
            pc_str = str(pc)
            pc_split = pc_str.split(",")
            pc_split_id = pc_split[0].split(":")
            pc_split_control_name = pc_split[5].split(":")
            control_name = str(pc_split_control_name[1])
            trim_space_from_front = control_name.lstrip()
            split_cn = trim_space_from_front.split(" ")
            control_match = str(split_cn[0])
            # match the control with the requirement
            for rr in related_requirements:
                if "," in rr:
                    # iterate through each value
                    rr_arr = str(rr["requirements"]).split(",")
                    for r in rr_arr:
                        split_r = r.split(" ")
                        control_to_match = split_r[1].replace(",", "")
                        if control_match == control_to_match:
                            # enter a reference
                            next_aws_proj_control = schema_aws_control.CreateAWSControlProjControl(
                                aws_control_id=rr["id"],
                                project_control_id=pc_split_id[1],
                            )
                            db_aws_control.create_aws_proj_control(next_aws_proj_control, db)
                            num_aws_proj_cont_mappings += 1
                else:
                    req = str(rr["requirements"])
                    if " " in req:
                        split_r = req.split(" ")
                        if split_r[1] is not None:
                            control_to_match = split_r[1].replace(",", "")
                        else:
                            control_to_match = split_r[0].replace(",", "")

                        if control_match == control_to_match:
                            # enter a reference
                            next_aws_proj_control = schema_aws_control.CreateAWSControlProjControl(
                                aws_control_id=rr["id"],
                                project_control_id=pc_split_id[1],
                            )
                            db_aws_control.create_aws_proj_control(next_aws_proj_control, db)
                            num_aws_proj_cont_mappings += 1
    except Exception as e:
        LOGGER.exception("There was a problem processing this request")
        return {"error": f"{e}"}
    return [num_aws_controls, num_aws_proj_cont_mappings]
