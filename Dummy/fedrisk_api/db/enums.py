import enum


class StatusType(str, enum.Enum):
    not_started = "Not Started"
    in_progress = "In Progress"
    complete = "Complete"


class IsAssessmentConfirmed(str, enum.Enum):
    yes = "Yes"
    no = "No"


class TaskCategory(str, enum.Enum):
    frameworks = "Frameworks"
    projects = "Projects"
    controls = "Controls"
    assessments = "Assessments"
    ad_hoc_assessments = "Ad-hoc Assessments"
    project_evaluations = "Project Evaluations"
    risks = "Risks"


class TaskStatus(str, enum.Enum):
    not_started = "Not Started"
    in_progress = "In Progress"
    complete = "Complete"


class TaskPriority(str, enum.Enum):
    low = "Low"
    high = "High"
    medium = "Medium"
    immediate = "Immediate"


class TestFrequency(str, enum.Enum):
    daily = "Daily"
    weekly = "Weekly"
    monthly = "Monthly"
    quarterly = "Quarterly"
    annually = "Annually"


class ReviewFrequency(str, enum.Enum):
    daily = "Daily"
    weekly = "Weekly"
    monthly = "Monthly"
    quarterly = "Quarterly"


class AuditTestStatus(str, enum.Enum):
    not_started = "Not Started"
    on_going = "On Going"
    complete = "Complete"
    on_hold = "On Hold"


class AuditTestInstanceStatus(str, enum.Enum):
    not_started = "Not Started"
    on_going = "On Going"
    complete = "Complete"
    on_hold = "On Hold"
    archived = "Archived"


class ExceptionReviewStatus(str, enum.Enum):
    not_started = "Not Started"
    in_progress = "In Progress"
    completed = "Completed"


class AssessmentInstanceStatus(str, enum.Enum):
    not_started = "Not Started"
    in_progress = "In Progress"
    completed = "Completed"


class SubscriptionStatus(str, enum.Enum):
    active = "Active"
    canceled = "Canceled"
    pending = "Pending"


class ProjectStatus(str, enum.Enum):
    active = "Active"
    on_hold = "On Hold"
    completed = "Completed"
    cancelled = "Cancelled"


class UpcomingEventDeadline(str, enum.Enum):
    one_day_prior = "one_day_prior"
    three_days_prior = "three_days_prior"
    five_days_prior = "five_days_prior"
    seven_days_prior = "seven_days_prior"
    fifteen_days_prior = "fifteen_days_prior"
    thirty_days_prior = "thirty_days_prior"
    sixty_days_prior = "sixty_days_prior"
    ninety_days_prior = "ninety_days_prior"


class AWSControlStatus(str, enum.Enum):
    failed = "Failed"
    passed = "Passed"
    no_data = "No Data"


class AWSSeverity(str, enum.Enum):
    low = "Low"
    medium = "Medium"
    high = "High"
    critical = "Critical"


class TaskLinkType(str, enum.Enum):
    finish_to_start = "0"
    start_to_start = "1"
    finish_to_finish = "2"
    start_to_finish = "3"


class Criticality(str, enum.Enum):
    low = "Low"
    medium = "Medium"
    high = "High"


class CapPoamStatus(str, enum.Enum):
    not_started = "Not Started"
    in_progress = "In Progress"
    completed = "Completed"


class WorkflowFlowchartStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    completed = "completed"
    paused = "paused"
    canceled = "canceled"


class ApprovalWorkflowStatus(str, enum.Enum):
    not_started = "not_started"
    in_progress = "in_progress"
    canceled = "canceled"
    paused = "paused"
    rejected = "rejected"
    approved = "approved"


class ApprovalStatus(str, enum.Enum):
    rejected = "rejected"
    approved = "approved"
