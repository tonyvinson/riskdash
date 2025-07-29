import enum


class ControlsFilterBy(str, enum.Enum):
    name = "name"
    description = "description"
    keywords = "keywords"
    framework = "framework"
    control_class = "control_class"
    control_status = "control_status"
    control_phase = "control_phase"
    control_family = "control_family"


class ExceptionsFilterBy(str, enum.Enum):
    name = "name"
    description = "description"
    justification = "justification"
    control = "control"
    framework = "framework"
    control_class = "control_class"
    control_status = "control_status"
    control_phase = "control_phase"
    control_family = "control_family"


class AssessmentsFilterBy(str, enum.Enum):
    name = "name"
    description = "description"
    status = "status"
    control = "control"
    framework = "framework"
    control_class = "control_class"
    control_status = "control_status"
    control_phase = "control_phase"
    control_family = "control_family"


class ControlFilterByOperation(str, enum.Enum):
    contains = "contains"
    equals = "equals"
