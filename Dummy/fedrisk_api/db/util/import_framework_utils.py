import logging
import pandas as pd
from fedrisk_api.db import control as db_control
from fedrisk_api.db import framework as db_framework
from fedrisk_api.db import framework_version as db_framework_version
from fedrisk_api.db.database import get_db
from fedrisk_api.db.models import (
    Control,
    Framework,
    FrameworkVersion,
    ControlFrameworkVersion,
)
from fedrisk_api.schema import control as schema_control
from fedrisk_api.schema import framework as schema_framework
from fedrisk_api.schema import framework_version as schema_framework_version
import uuid
from sqlalchemy.exc import IntegrityError

LOGGER = logging.getLogger(__name__)

BAD_CHARS_TEXT = "!*&%^$#@{}+=<>"


def trim_bad_text_string_chars(textstring):
    """Removes unwanted characters from text and handles None values safely."""
    if not isinstance(textstring, str):
        return ""  # Avoid breaking on NaN or non-string values
    return "".join(c for c in textstring if c not in BAD_CHARS_TEXT).strip()


def create_control_name_from_row(row):
    """Generates a cleaned control name by joining Control Title fields."""
    try:
        title1 = trim_bad_text_string_chars(row.get("Control Title", ""))
        title2 = trim_bad_text_string_chars(row.get("Control Title 2", ""))
        if title2:
            return f"{title1}: {title2}"
        return title1
    except Exception as e:
        LOGGER.error(f"Error processing control name: {e}")
        return ""


def load_data_from_dataframe(my_data_frame, tenant_id, is_superuser):
    """Processes a DataFrame and loads framework, versions, and controls into the database."""
    try:
        db = next(get_db())
    except Exception as e:
        LOGGER.error(f"Database session error: {e}")
        return {"error": "Could not initialize database session"}

    num_frameworks, num_framework_versions, num_controls = 0, 0, 0
    my_prev_framework_id, my_prev_fv_id, my_prev_control_id = None, None, None

    try:
        for _, row in my_data_frame.iterrows():
            framework_name = trim_bad_text_string_chars(row.get("Framework", ""))
            if not framework_name:
                return {"error": "Framework column is missing or empty in the spreadsheet"}

            prefix_version = trim_bad_text_string_chars(
                str(row.get("Prefix Version", uuid.uuid4()))
            )
            suffix_version = trim_bad_text_string_chars(
                str(row.get("Suffix Version", uuid.uuid4()))
            )
            keywords_str = process_keywords(row.get("Keywords", ""))

            # Fetch or create Framework
            my_next_framework_from_db = (
                db.query(Framework).filter(Framework.name == framework_name).first()
            )
            if not my_next_framework_from_db:
                my_next_framework_from_db = create_framework(
                    db, framework_name, keywords_str, is_superuser, tenant_id
                )
                num_frameworks += 1
            my_prev_framework_id = my_next_framework_from_db.id

            # Fetch or create Framework Version
            my_next_fv_from_db = (
                db.query(FrameworkVersion)
                .filter_by(
                    framework_id=my_prev_framework_id,
                    version_prefix=prefix_version,
                    version_suffix=suffix_version,
                )
                .first()
            )
            if not my_next_fv_from_db:
                my_next_fv_from_db = create_framework_version(
                    db,
                    my_prev_framework_id,
                    prefix_version,
                    suffix_version,
                    keywords_str,
                    tenant_id,
                )
                num_framework_versions += 1
            my_prev_fv_id = my_next_fv_from_db.id

            # Handling Control Title
            control_name = create_control_name_from_row(row)
            if not control_name:
                return {"error": "Control Title is missing or invalid in the spreadsheet"}

            my_next_control_from_db = db.query(Control).filter(Control.name == control_name).first()

            if not my_next_control_from_db:
                control_description = trim_bad_text_string_chars(row.get("Control Description", ""))
                guidance = trim_bad_text_string_chars(row.get("Guidance", ""))

                my_next_control_from_db = create_control(
                    db,
                    control_name,
                    control_description,
                    guidance,
                    keywords_str,
                    tenant_id,
                    my_prev_fv_id,
                )
                num_controls += 1
            my_prev_control_id = my_next_control_from_db.id

            # Ensure Control-Framework Version Relationship
            ensure_control_framework_version_relationship(db, my_prev_control_id, my_prev_fv_id)

    except IntegrityError as e:
        db.rollback()
        LOGGER.error(f"Database Integrity Error: {e}")
        return {"error": "Database Integrity Error - Possible duplicate entry"}
    except Exception as e:
        db.rollback()
        LOGGER.exception("Unexpected error occurred while processing the spreadsheet")
        return {"error": f"Unexpected error: {str(e)}"}

    return [num_frameworks, num_controls, num_framework_versions]


# --- Helper Functions ---
def process_keywords(keywords):
    """Sanitizes and processes keywords safely."""
    if not isinstance(keywords, str):  # Handling NaN cases
        return ""
    bad_chars = " ;:!*()[]&%^$#@{}+=-_/<>"  # Characters to remove
    return ",".join(
        "".join(c for c in keyword if c not in bad_chars).strip().lower()
        for keyword in keywords.split(",")
        if keyword.strip()
    )


def create_framework(db, name, keywords, is_superuser, tenant_id):
    """Creates a new framework if it does not exist."""
    new_framework = schema_framework.CreatePreloadedFramework(
        name=name, description=name, keywords=keywords, is_preloaded=True, is_global=is_superuser
    )
    return db_framework.create_framework(db, new_framework, tenant_id=tenant_id, keywords=keywords)


def create_framework_version(db, framework_id, prefix, suffix, keywords, tenant_id):
    """Creates a new framework version if it does not exist."""
    new_version = schema_framework_version.CreatePreloadedFrameworkVersion(
        framework_id=framework_id, version_prefix=prefix, version_suffix=suffix, is_preloaded=True
    )
    return db_framework_version.create_framework_version(db, new_version, keywords, tenant_id)


def create_control(db, name, description, guidance, keywords, tenant_id, framework_version_id):
    """Creates a new control if it does not exist."""
    new_control = schema_control.CreatePreloadedControl(
        name=name,
        description=description,
        guidance=guidance,
        keywords=keywords,
        is_preloaded=True,
        tenant_id=tenant_id,
        framework_versions=[framework_version_id],
    )
    return db_control.create_control(db, new_control, keywords, tenant_id=tenant_id)


def ensure_control_framework_version_relationship(db, control_id, framework_version_id):
    """Ensures that a control is linked to a framework version."""
    exists = (
        db.query(ControlFrameworkVersion)
        .filter_by(control_id=control_id, framework_version_id=framework_version_id)
        .first()
    )
    if not exists:
        db_control.add_single_control_to_framework_version_relationship(
            db=db, framework_version_id=framework_version_id, control_id=control_id
        )


def remove_data_from_dataframe(my_data_frame):
    db = next(get_db())
    num_frameworks_removed = 0
    num_framework_versions_removed = 0
    num_controls_removed = 0
    for row in my_data_frame.iterrows():
        my_next_framework_name = row[1]["Framework"]
        my_next_fv_prefix = row[1]["Prefix Version"]
        my_next_fv_suffix = row[2]["Suffix Version"]
        my_next_framework_from_db = (
            db.query(Framework).filter(Framework.name == my_next_framework_name).first()
        )
        my_next_fv_from_db = (
            db.query(FrameworkVersion)
            .filter(FrameworkVersion.version_prefix == my_next_fv_prefix)
            .filter(FrameworkVersion.version_suffix == my_next_fv_suffix)
            .first()
        )
        try:
            db_framework.delete_framework(
                db, my_next_framework_from_db.id, my_next_framework_from_db.tenant_id
            )
            num_frameworks_removed += 1
            db_framework_version.delete_framework_version(db, my_next_fv_from_db.id)
            num_framework_versions_removed += 1
        except:
            continue
        my_next_control_name = create_control_name_from_row(row)
        my_next_control_from_db = (
            db.query(Control).filter(Control.name == my_next_control_name).first()
        )
        try:
            db_control.delete_control(
                db, my_next_control_from_db.id, my_next_control_from_db.tenant_id
            )
            num_controls_removed += 1
        except:
            continue
    return [num_frameworks_removed, num_controls_removed, num_framework_versions_removed]
