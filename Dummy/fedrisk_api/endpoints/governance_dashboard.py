from fastapi import APIRouter, Depends
from sqlalchemy import Integer, case, func, literal_column, or_, union_all
from sqlalchemy.orm import Session, contains_eager

import logging

from fedrisk_api.db.dashboard import get_framework, get_project
from fedrisk_api.db.database import get_db
from fedrisk_api.db.models import (
    Assessment,
    Control,
    ControlClass,
    ControlFamily,
    ControlPhase,
    ControlStatus,
    Exception,
    ExceptionReview,
    Framework,
    ProjectControl,
)
from fedrisk_api.schema.governance_dashboard import (
    DisplayAssessments,
    DisplayControls,
    # DisplayExceptions,
    DisplayGovernanceDashboardMetrics,
)
from fedrisk_api.schema.exception import DisplayExceptionReview
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.enumsdata import (
    AssessmentsFilterBy,
    ControlFilterByOperation,
    ControlsFilterBy,
    ExceptionsFilterBy,
)
from fedrisk_api.utils.permissions import view_governance_dashboard
from fedrisk_api.utils.utils import PaginateResponse, pagination

LOGGER = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboards/governance", tags=["dashboards"])


CONTROLS_ATTRIBUTES = {
    "control_class": {"Unassigned", "Technical", "Operational", "Management"},
    "control_phase": {"Unassigned", "Procedural", "Technical", "Legal, Regulatory or Compliance"},
    "control_status": {"P0", "P1", "P2", "P3", "1", "2"},
    "control_family": {
        "Security & Privacy",
        "Asset Management",
        "Continuity & Disaster Recovery",
        "Capacity & Performance",
        "Change Management",
        "Cloud Security",
    },
    "control_mitigation": {"High", "Low", "Medium"},
    "control_assessments": {"Yes", "No"},
}

OPERATION_MAPPING = {
    "contains": lambda attribute: lambda value: func.lower(attribute).contains(
        func.lower(f"{value}")
    ),
    "equals": lambda attribute: lambda value: attribute == f"{value}",
}

CONTROL_NAME_MAPPING = {
    "name": Control.name,
    "description": Control.description,
    # "keywords": Control.keywords,
    "framework": Framework.name,
    "control_class": ControlClass.name,
    "control_status": ControlStatus.name,
    "control_phase": ControlPhase.name,
    "control_family": ControlFamily.name,
}

CONTROL_ORDER_BY_MAPPING = {
    "name": Control.name,
    "-name": Control.name.desc(),
    "description": Control.description,
    "-description": Control.description.desc(),
    # "keywords": Control.keywords,
    # "-keywords": Control.keywords.desc(),
    "framework": Framework.name,
    "-framework": Framework.name.desc(),
    "control_status": ControlStatus.name,
    "-control_status": ControlStatus.name.desc(),
    "control_family": ControlFamily.name,
    "-control_family": ControlFamily.name.desc(),
    "control_phase": ControlPhase.name,
    "-control_phase": ControlPhase.name.desc(),
    "control_class": ControlClass.name,
    "-control_class": ControlClass.name.desc(),
}

EXCEPTION_NAME_MAPPING = {
    "name": Exception.name,
    "description": Exception.description,
    "justification": Exception.justification,
    "framework": Framework.name,
    "control_class": ControlClass.name,
    "control_status": ControlStatus.name,
    "control_phase": ControlPhase.name,
    "control_family": ControlFamily.name,
}

EXCEPTION_ORDER_BY_MAPPING = {
    "name": Exception.name,
    "-name": Exception.name.desc(),
    "description": Exception.description,
    "-description": Exception.description.desc(),
    "justification": Exception.justification,
    "-justification": Exception.justification.desc(),
    "control": Control.name,
    "-control": Control.name.desc(),
    "framework": Framework.name,
    "-framework": Framework.name.desc(),
    "control_status": ControlStatus.name,
    "-control_status": ControlStatus.name.desc(),
    "control_family": ControlFamily.name,
    "-control_family": ControlFamily.name.desc(),
    "control_phase": ControlPhase.name,
    "-control_phase": ControlPhase.name.desc(),
    "control_class": ControlClass.name,
    "-control_class": ControlClass.name.desc(),
}

ASSESSMENT_NAME_MAPPING = {
    "name": Assessment.name,
    "description": Assessment.description,
    "status": Assessment.status,
    "control": Control.name,
    "framework": Framework.name,
    "control_class": ControlClass.name,
    "control_status": ControlStatus.name,
    "control_phase": ControlPhase.name,
    "control_family": ControlFamily.name,
}

ASSESSMENT_ORDER_BY_MAPPING = {
    "name": Assessment.name,
    "-name": Assessment.name.desc(),
    "description": Assessment.description,
    "-description": Assessment.description.desc(),
    "status": Assessment.status,
    "-status": Assessment.status.desc(),
    "control": Control.name,
    "-control": Control.name.desc(),
    "framework": Framework.name,
    "-framework": Framework.name.desc(),
    "control_status": ControlStatus.name,
    "-control_status": ControlStatus.name.desc(),
    "control_family": ControlFamily.name,
    "-control_family": ControlFamily.name.desc(),
    "control_phase": ControlPhase.name,
    "-control_phase": ControlPhase.name.desc(),
    "control_class": ControlClass.name,
    "-control_class": ControlClass.name.desc(),
}

STATUS_TYPE_VALUE = {
    "Not Started": "not_started",
    "In Progress": "in_progress",
    "Complete": "complete",
}


@router.get(
    "/metrics/",
    response_model=DisplayGovernanceDashboardMetrics,
    dependencies=[Depends(view_governance_dashboard)],
)
def get_project_framework_metrics(
    project_id: int = None,
    framework_id: int = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    project = get_project(db, project_id=project_id, user=user)
    if not project:
        return DisplayGovernanceDashboardMetrics(
            project_id=-1,
            project_name="",
            framework_name="",
            framework_id=-1,
            control_class=[],
            control_family=[],
            control_status=[],
            control_phase=[],
            control_mitigation=[],
            control_assessment=[],
            control_exception_count=0,
        )

    framework = get_framework(db=db, framework_id=framework_id, project_id=project.id, user=user)

    if not framework:
        return DisplayGovernanceDashboardMetrics(
            project_id=-1,
            project_name="",
            framework_name="",
            framework_id=-1,
            control_class=[],
            control_family=[],
            control_status=[],
            control_phase=[],
            control_mitigation=[],
            control_assessment=[],
            control_exception_count=0,
        )

    control_project_framework_subquery = (
        db.query(Control)
        .join(ProjectControl, ProjectControl.control_id == Control.id)
        .filter(Control.framework_id == framework.id)
        .filter(ProjectControl.project_id == project.id)
        .distinct()
        .subquery()
    )

    control_status = (
        db.query(
            ControlStatus.name,
            func.count(control_project_framework_subquery.c.id).label("count"),
            func.cast(
                func.avg(control_project_framework_subquery.c.mitigation_percentage), Integer
            ).label("mitigation_percentage"),
        )
        .select_from(control_project_framework_subquery)
        .join(
            ControlStatus,
            ControlStatus.id == control_project_framework_subquery.c.control_status_id,
        )
        .group_by(ControlStatus.name)
        .all()
    )
    control_phase = (
        db.query(
            ControlPhase.name,
            func.count(control_project_framework_subquery.c.id).label("count"),
            func.cast(
                func.avg(control_project_framework_subquery.c.mitigation_percentage), Integer
            ).label("mitigation_percentage"),
        )
        .select_from(control_project_framework_subquery)
        .join(
            ControlPhase, ControlPhase.id == control_project_framework_subquery.c.control_phase_id
        )
        .group_by(ControlPhase.name)
        .all()
    )
    control_class = (
        db.query(
            ControlClass.name,
            func.count(control_project_framework_subquery.c.id).label("count"),
            func.cast(
                func.avg(control_project_framework_subquery.c.mitigation_percentage), Integer
            ).label("mitigation_percentage"),
        )
        .select_from(control_project_framework_subquery)
        .join(
            ControlClass, ControlClass.id == control_project_framework_subquery.c.control_class_id
        )
        .group_by(ControlClass.name)
        .all()
    )
    control_family = (
        db.query(
            ControlFamily.name,
            func.count(control_project_framework_subquery.c.id).label("count"),
            func.cast(
                func.avg(control_project_framework_subquery.c.mitigation_percentage), Integer
            ).label("mitigation_percentage"),
        )
        .select_from(control_project_framework_subquery)
        .join(
            ControlFamily,
            ControlFamily.id == control_project_framework_subquery.c.control_family_id,
        )
        .filter(ControlFamily != None)
        .group_by(ControlFamily.name)
        .all()
    )

    mitigation_percentage_case = case(
        [
            (
                control_project_framework_subquery.c.mitigation_percentage <= 33,
                literal_column("'Low'"),
            ),
            (
                control_project_framework_subquery.c.mitigation_percentage <= 66,
                literal_column("'Medium'"),
            ),
            (
                control_project_framework_subquery.c.mitigation_percentage <= 100,
                literal_column("'High'"),
            ),
        ],
        else_=literal_column("'Uninitialized'"),
    ).label("name")

    control_mitigation = (
        db.query(mitigation_percentage_case, func.count("*").label("count"))
        .select_from(control_project_framework_subquery)
        .filter(control_project_framework_subquery.c.mitigation_percentage != None)
        .group_by(mitigation_percentage_case)
        .all()
    )

    control_exception = (
        db.query(func.count("*").label("count"))
        .select_from(ExceptionReview)
        .join(Exception, ExceptionReview.exception_id == Exception.id)
        .join(ProjectControl, ProjectControl.id == Exception.project_control_id)
        .join(Control, Control.id == ProjectControl.control_id)
        .filter(Control.control_class_id != None)
        .filter(Control.control_family_id != None)
        .filter(Control.control_status_id != None)
        .filter(Control.control_phase_id != None)
        .filter(Control.mitigation_percentage != None)
        .filter(Control.framework_id == framework.id)
        .filter(ProjectControl.project_id == project.id)
        .distinct()
        .first()
    )

    control_assessments_subquery = (
        db.query(Assessment)
        .join(ProjectControl, ProjectControl.id == Assessment.project_control_id)
        .join(Control, Control.id == ProjectControl.control_id)
        .filter(Control.control_class_id != None)
        .filter(Control.control_family_id != None)
        .filter(Control.control_status_id != None)
        .filter(Control.control_phase_id != None)
        .filter(Control.mitigation_percentage != None)
        .filter(Control.framework_id == framework.id)
        .filter(ProjectControl.project_id == project.id)
        .distinct()
        .subquery()
    )

    assessment_status_case = case(
        [(control_assessments_subquery.c.status == "Complete", literal_column("'Yes'"))],
        else_=literal_column("'No'"),
    ).label("name")

    control_assessments = (
        db.query(assessment_status_case, func.count("*").label("count"))
        .select_from(control_assessments_subquery)
        .group_by(assessment_status_case)
    )
    control_assessments = union_all(
        control_assessments,
        (
            db.query(
                literal_column("'total'").label("name"), func.count("*").label("count")
            ).select_from(control_assessments_subquery)
        ),
    )
    control_assessments = db.execute(control_assessments).all()

    # Inserting Missing control_family, control_class, control_phase, control_phase, control_family
    default_mapping = [
        (
            control_class,
            {
                class_.name
                for class_ in db.query(ControlClass)
                .filter(
                    or_(ControlClass.tenant_id == user["tenant_id"], ControlClass.tenant_id == None)
                )
                .all()
            },
        ),
        (control_status, CONTROLS_ATTRIBUTES["control_status"].copy()),
        (
            control_phase,
            {
                phase.name
                for phase in db.query(ControlPhase)
                .filter(
                    or_(ControlPhase.tenant_id == user["tenant_id"], ControlPhase.tenant_id == None)
                )
                .all()
            },
        ),
        (
            control_family,
            {
                phase.name
                for phase in db.query(ControlFamily)
                .filter(
                    or_(
                        ControlFamily.tenant_id == user["tenant_id"],
                        ControlFamily.tenant_id == None,
                    )
                )
                .all()
            },
        ),
    ]

    for control_attr_value in default_mapping:
        missing_values = control_attr_value[1] - {obj.name for obj in control_attr_value[0]}
        for missing_value in missing_values:
            control_attr_value[0].append(
                {"name": missing_value, "count": 0, "mitigation_percentage": 0}
            )

    # Inserting Missing control_mitigation control_assessment
    control_mitigation_missing = CONTROLS_ATTRIBUTES["control_mitigation"].copy() - {
        obj.name for obj in control_mitigation
    }
    for control_mitigation_ in control_mitigation_missing:
        control_mitigation.append({"name": control_mitigation_, "count": 0})

    control_assessment_missing = CONTROLS_ATTRIBUTES["control_assessments"].copy() - {
        obj.name for obj in control_assessments
    }
    for control_assessment_ in control_assessment_missing:
        control_assessments.append({"name": control_assessment_, "count": 0})

    return DisplayGovernanceDashboardMetrics(
        project_id=project.id,
        project_name=project.name,
        framework_name=framework.name,
        framework_id=framework.id,
        control_class=control_class,
        control_family=control_family,
        control_status=control_status,
        control_phase=control_phase,
        control_mitigation=control_mitigation,
        control_assessment=control_assessments,
        control_exception_count=control_exception.count,
    )


@router.get(
    "/controls/",
    response_model=PaginateResponse[DisplayControls],
    dependencies=[Depends(view_governance_dashboard)],
)
def get_all_project_control(
    project_id: int = None,
    framework_id: int = None,
    filter_by: ControlsFilterBy = None,
    filter_by_operation: ControlFilterByOperation = None,
    filter_value: str = None,
    order_by: str = "name",
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    project = get_project(db=db, project_id=project_id, user=user)
    if not project:
        return pagination(query=db.query(Control).filter(False), limit=limit, offset=offset)

    framework = get_framework(db=db, framework_id=framework_id, project_id=project_id, user=user)
    if not framework:
        return pagination(query=db.query(Control).filter(False), limit=limit, offset=offset)

    query = (
        db.query(Control)
        .join(ProjectControl, Control.id == ProjectControl.control_id)
        .join(Framework, Control.framework_id == Framework.id)
        .join(ControlClass, ControlClass.id == Control.control_class_id)
        .join(ControlFamily, ControlFamily.id == Control.control_family_id)
        .join(ControlStatus, ControlStatus.id == Control.control_status_id)
        .join(ControlPhase, ControlPhase.id == Control.control_phase_id)
        .filter(ProjectControl.project_id == project.id)
        .filter(Framework.id == framework.id)
        .options(
            contains_eager(Control.framework),
            contains_eager(Control.control_class),
            contains_eager(Control.control_family),
            contains_eager(Control.control_phase),
            contains_eager(Control.control_status),
        )
    )

    if filter_by and filter_by_operation and filter_value:
        attribute = CONTROL_NAME_MAPPING[filter_by.value]
        operation = OPERATION_MAPPING[filter_by_operation.value](attribute)
        query = query.filter(operation(filter_value))
    order_by = CONTROL_ORDER_BY_MAPPING.get(order_by, None)

    if order_by is not None:
        query = query.order_by(order_by)

    query = query.distinct()

    return pagination(query=query, limit=limit, offset=offset)


@router.get(
    "/exceptions/",
    response_model=PaginateResponse[DisplayExceptionReview],
    dependencies=[Depends(view_governance_dashboard)],
)
def get_all_project_exception(
    project_id: int = None,
    framework_id: int = None,
    filter_by: ExceptionsFilterBy = None,
    filter_by_operation: ControlFilterByOperation = None,
    filter_value: str = None,
    order_by: str = "name",
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    project = get_project(db=db, project_id=project_id, user=user)
    if not project:
        return pagination(query=db.query(Exception).filter(False), limit=limit, offset=offset)

    framework = get_framework(db=db, framework_id=framework_id, project_id=project_id, user=user)
    if not framework:
        return pagination(query=db.query(Exception).filter(False), limit=limit, offset=offset)

    query = (
        db.query(ExceptionReview)
        .join(Exception, ExceptionReview.exception_id == Exception.id)
        .join(ProjectControl, ProjectControl.id == Exception.project_control_id)
        .join(Control, Control.id == ProjectControl.control_id)
        .join(Framework, Control.framework_id == Framework.id)
        .join(ControlClass, ControlClass.id == Control.control_class_id)
        .join(ControlFamily, ControlFamily.id == Control.control_family_id)
        .join(ControlStatus, ControlStatus.id == Control.control_status_id)
        .join(ControlPhase, ControlPhase.id == Control.control_phase_id)
        .filter(ProjectControl.project_id == project.id)
        .filter(Framework.id == framework.id)
        .options(
            contains_eager(Exception.project_control)
            .contains_eager(ProjectControl.control)
            .contains_eager(Control.control_class),
            contains_eager(Exception.project_control)
            .contains_eager(ProjectControl.control)
            .contains_eager(Control.control_family),
            contains_eager(Exception.project_control)
            .contains_eager(ProjectControl.control)
            .contains_eager(Control.control_phase),
            contains_eager(Exception.project_control)
            .contains_eager(ProjectControl.control)
            .contains_eager(Control.control_status),
            contains_eager(Exception.project_control)
            .contains_eager(ProjectControl.control)
            .contains_eager(Control.framework),
            contains_eager(Exception.project_control).selectinload(ProjectControl.project),
        )
    )

    if filter_by and filter_by_operation and filter_value:
        attribute = EXCEPTION_NAME_MAPPING[filter_by.value]
        operation = OPERATION_MAPPING[filter_by_operation.value](attribute)
        query = query.filter(operation(filter_value))

    order_by = EXCEPTION_ORDER_BY_MAPPING.get(order_by, None)
    if order_by is not None:
        query = query.order_by(order_by)

    query = query.distinct()

    return pagination(query=query, limit=limit, offset=offset)


@router.get(
    "/assessments/",
    response_model=PaginateResponse[DisplayAssessments],
    dependencies=[Depends(view_governance_dashboard)],
)
def get_all_project_assessments(
    project_id: int = None,
    framework_id: int = None,
    filter_by: AssessmentsFilterBy = None,
    filter_by_operation: ControlFilterByOperation = None,
    filter_value: str = None,
    order_by: str = "name",
    limit: int = 10,
    offset: int = 0,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    project = get_project(db=db, project_id=project_id, user=user)
    if not project:
        return pagination(query=db.query(Assessment).filter(False), limit=limit, offset=offset)

    framework = get_framework(db=db, framework_id=framework_id, project_id=project_id, user=user)
    if not framework:
        return pagination(query=db.query(Assessment).filter(False), limit=limit, offset=offset)

    query = (
        db.query(Assessment)
        .join(ProjectControl, ProjectControl.id == Assessment.project_control_id)
        .join(Control, Control.id == ProjectControl.control_id)
        .join(Framework, Control.framework_id == Framework.id)
        .join(ControlClass, ControlClass.id == Control.control_class_id)
        .join(ControlFamily, ControlFamily.id == Control.control_family_id)
        .join(ControlStatus, ControlStatus.id == Control.control_status_id)
        .join(ControlPhase, ControlPhase.id == Control.control_phase_id)
        .filter(ProjectControl.project_id == project.id)
        .filter(Framework.id == framework.id)
        .options(
            contains_eager(Assessment.project_control)
            .contains_eager(ProjectControl.control)
            .contains_eager(Control.control_class),
            contains_eager(Assessment.project_control)
            .contains_eager(ProjectControl.control)
            .contains_eager(Control.control_family),
            contains_eager(Assessment.project_control)
            .contains_eager(ProjectControl.control)
            .contains_eager(Control.control_phase),
            contains_eager(Assessment.project_control)
            .contains_eager(ProjectControl.control)
            .contains_eager(Control.control_status),
            contains_eager(Assessment.project_control)
            .contains_eager(ProjectControl.control)
            .contains_eager(Control.framework),
            contains_eager(Assessment.project_control).selectinload(ProjectControl.project),
        )
    )

    if filter_by == AssessmentsFilterBy.status:
        for key, value in STATUS_TYPE_VALUE.items():
            if filter_by_operation == "equals" and filter_value == key:
                filter_by_operation = ControlFilterByOperation("equals").equals
                filter_value = value
                break
            elif filter_by_operation == "contains" and filter_value.lower() in key.lower():
                filter_by_operation = ControlFilterByOperation("equals").equals
                filter_value = value
                break
        else:
            return pagination(query=db.query(Assessment).filter(False), limit=limit, offset=offset)

    if filter_by and filter_by_operation and filter_value:
        attribute = ASSESSMENT_NAME_MAPPING[filter_by.value]
        operation = OPERATION_MAPPING[filter_by_operation.value](attribute)
        query = query.filter(operation(filter_value))

    order_by = ASSESSMENT_ORDER_BY_MAPPING.get(order_by, None)
    if order_by is not None:
        query = query.order_by(order_by)

    query = query.distinct()

    return pagination(query=query, limit=limit, offset=offset)


@router.get(
    "/project_controls/mit-percentage/",
)
def get_mit_percentage(
    project_id: int = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    mit_perc_joins = db.query(ProjectControl).join(Control)
    mit_perc_filter = mit_perc_joins.filter(ProjectControl.project_id == project_id)
    mit_perc_filter_subquery = mit_perc_filter.with_entities(
        ProjectControl.mitigation_percentage,
        Control.name,
    ).subquery()
    mit_results = db.query(mit_perc_filter_subquery).all()
    chart_data = []
    for result in mit_results:
        datapoint = {"x": result.name, "y": result.mitigation_percentage}
        chart_data.append(datapoint)
    return chart_data


@router.get(
    "/project_controls/class-names-percentage/",
)
def get_class_names_percentage(
    project_id: int = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    # get all the project controls
    class_perc_joins = db.query(ProjectControl)
    class_perc_filter = class_perc_joins.filter(ProjectControl.project_id == project_id)
    class_perc_filter_subquery = class_perc_filter.with_entities(
        ProjectControl.mitigation_percentage,
        ProjectControl.control_class_id,
    ).subquery()
    class_perc_results = db.query(class_perc_filter_subquery).all()
    # get all the control class ids and names
    classes = db.query(ControlClass)
    class_filter = classes.filter(ControlClass.tenant_id == user["tenant_id"])
    class_filter_subquery = class_filter.with_entities(
        ControlClass.name,
        ControlClass.id,
    ).subquery()
    class_results = db.query(class_filter_subquery).all()
    chart_data = []
    matches = 0
    percent = 0
    for classres in class_results:
        for classperc in class_perc_results:
            if classres.id == classperc.control_class_id:
                percent = percent + classperc.mitigation_percentage
                matches = matches + 1
        if matches > 1:
            average = percent / round(matches, 2)
            datapoint = {"x": classres.name, "y": matches, "percent": round(average, 2)}
            chart_data.append(datapoint)
        else:
            datapoint = {"x": classres.name, "y": matches, "percent": percent}
            chart_data.append(datapoint)
        matches = 0
        percent = 0
    return chart_data


@router.get(
    "/project_controls/class-family-percentage/",
)
def get_class_family_percentage(
    project_id: int = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    # get all the project controls
    class_perc_joins = db.query(ProjectControl)
    class_perc_filter = class_perc_joins.filter(ProjectControl.project_id == project_id)
    class_perc_filter_subquery = class_perc_filter.with_entities(
        ProjectControl.mitigation_percentage,
        ProjectControl.control_family_id,
    ).subquery()
    class_perc_results = db.query(class_perc_filter_subquery).all()
    # get all the control class ids and names
    classes = db.query(ControlFamily)
    class_filter = classes.filter(ControlFamily.tenant_id == user["tenant_id"])
    class_filter_subquery = class_filter.with_entities(
        ControlFamily.name,
        ControlFamily.id,
    ).subquery()
    class_results = db.query(class_filter_subquery).all()
    chart_data = []
    matches = 0
    percent = 0
    for classres in class_results:
        for classperc in class_perc_results:
            if classres.id == classperc.control_family_id:
                percent = percent + classperc.mitigation_percentage
                matches = matches + 1
        if matches > 1:
            average = percent / round(matches, 2)
            datapoint = {"x": classres.name, "y": matches, "percent": round(average, 2)}
            chart_data.append(datapoint)
        else:
            datapoint = {"x": classres.name, "y": matches, "percent": percent}
            chart_data.append(datapoint)
        matches = 0
        percent = 0
    return chart_data


@router.get(
    "/project_controls/class-phase-percentage/",
)
def get_class_phase_percentage(
    project_id: int = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    # get all the project controls
    class_perc_joins = db.query(ProjectControl)
    class_perc_filter = class_perc_joins.filter(ProjectControl.project_id == project_id)
    class_perc_filter_subquery = class_perc_filter.with_entities(
        ProjectControl.mitigation_percentage,
        ProjectControl.control_phase_id,
    ).subquery()
    class_perc_results = db.query(class_perc_filter_subquery).all()
    # get all the control class ids and names
    classes = db.query(ControlPhase)
    class_filter = classes.filter(ControlPhase.tenant_id == user["tenant_id"])
    class_filter_subquery = class_filter.with_entities(
        ControlPhase.name,
        ControlPhase.id,
    ).subquery()
    class_results = db.query(class_filter_subquery).all()
    chart_data = []
    matches = 0
    percent = 0
    for classres in class_results:
        for classperc in class_perc_results:
            if classres.id == classperc.control_phase_id:
                percent = percent + classperc.mitigation_percentage
                matches = matches + 1
        if matches > 1:
            average = percent / round(matches, 2)
            datapoint = {"x": classres.name, "y": matches, "percent": round(average, 2)}
            chart_data.append(datapoint)
        else:
            datapoint = {"x": classres.name, "y": matches, "percent": percent}
            chart_data.append(datapoint)
        matches = 0
        percent = 0
    return chart_data


@router.get(
    "/project_controls/class-status-percentage/",
)
def get_class_status_percentage(
    project_id: int = None,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    # get all the project controls
    class_perc_joins = db.query(ProjectControl)
    class_perc_filter = class_perc_joins.filter(ProjectControl.project_id == project_id)
    class_perc_filter_subquery = class_perc_filter.with_entities(
        ProjectControl.mitigation_percentage,
        ProjectControl.control_status_id,
    ).subquery()
    class_perc_results = db.query(class_perc_filter_subquery).all()
    # get all the control class ids and names
    classes = db.query(ControlStatus)
    class_filter = classes.filter(ControlStatus.tenant_id == user["tenant_id"])
    class_filter_subquery = class_filter.with_entities(
        ControlStatus.name,
        ControlStatus.id,
    ).subquery()
    class_results = db.query(class_filter_subquery).all()
    chart_data = []
    matches = 0
    percent = 0
    for classres in class_results:
        for classperc in class_perc_results:
            if classres.id == classperc.control_status_id:
                percent = percent + classperc.mitigation_percentage
                matches = matches + 1
        if matches > 1:
            average = percent / round(matches, 2)
            datapoint = {"x": classres.name, "y": matches, "percent": round(average, 2)}
            chart_data.append(datapoint)
        else:
            datapoint = {"x": classres.name, "y": matches, "percent": percent}
            chart_data.append(datapoint)
        matches = 0
        percent = 0
    return chart_data
