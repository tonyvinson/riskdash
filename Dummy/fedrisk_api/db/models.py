from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql.functions import current_timestamp
from sqlalchemy.types import (
    DECIMAL,
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    Float,
    Integer,
    String,
    Unicode,
    TEXT,
)
from sqlalchemy_utils import generic_relationship

from fedrisk_api.db.database import Base
from fedrisk_api.db.enums import (
    AssessmentInstanceStatus,
    AuditTestStatus,
    AuditTestInstanceStatus,
    AWSControlStatus,
    AWSSeverity,
    ExceptionReviewStatus,
    IsAssessmentConfirmed,
    ReviewFrequency,
    StatusType,
    TaskPriority,
    TestFrequency,
    ProjectStatus,
    UpcomingEventDeadline,
    TaskLinkType,
    Criticality,
    CapPoamStatus,
    WorkflowFlowchartStatus,
    ApprovalWorkflowStatus,
    ApprovalStatus,
)


class Project(Base):
    __tablename__ = "project"
    __table_args__ = (UniqueConstraint("name", "tenant_id", name="project_name_tenant_key"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    project_group_id = Column(Integer, ForeignKey("project_group.id"))
    project_admin_id = Column(Integer, ForeignKey("user.id"))
    documents = relationship(
        "ProjectDocument", back_populates="project", cascade="all, delete-orphan"
    )
    # controls = relationship("Control", secondary="project_control", back_populates="projects")
    project_controls = relationship(
        "ProjectControl", lazy="joined", join_depth=3, cascade="all, delete-orphan"
    )
    # documents = relationship("Document", back_populates="project")
    project_evaluations = relationship(
        "ProjectEvaluation", back_populates="project", cascade="all, delete-orphan"
    )
    risks = relationship("Risk", back_populates="project", cascade="all, delete-orphan")
    audit_tests = relationship("AuditTest", back_populates="project", cascade="all, delete-orphan")
    project_group = relationship("ProjectGroup", back_populates="projects", uselist=False)
    project_admin = relationship("User", uselist=False)
    users = relationship("User", secondary="project_user", back_populates="projects")

    status = Column(Enum(ProjectStatus), default=ProjectStatus.active.value)

    keywords = relationship(
        "KeywordMapping",
        primaryjoin="Project.id==KeywordMapping.project_id",
        back_populates="project",
        cascade="all, delete-orphan",
    )
    history_user_project = relationship(
        "ProjectHistory", back_populates="project", cascade="all, delete-orphan"
    )
    history_project_user_project = relationship(
        "ProjectUserHistory", back_populates="project", cascade="all, delete-orphan"
    )
    user_notifications_project = relationship(
        "UserNotifications", back_populates="project", cascade="all, delete-orphan"
    )
    features = relationship(
        "FeatureProject", back_populates="project", cascade="all, delete-orphan"
    )
    costs = relationship("ProjectCost", back_populates="project", cascade="all, delete-orphan")

    workflow_flowcharts = relationship(
        "WorkflowFlowchart", back_populates="project", cascade="all, delete-orphan"
    )

    approval_workflows = relationship(
        "ProjectApprovalWorkflow", back_populates="project", cascade="all, delete-orphan"
    )

    surveys = relationship("SurveyModel", back_populates="project", cascade="all, delete-orphan")

    service_provider_projects = relationship(
        "ServiceProviderProject",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    app_projects = relationship(
        "AppProject",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    audit_evidence_project = relationship(
        "AuditEvidenceFilterProject",
        back_populates="project",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, risks: {self.risks}, audit_tests: {self.audit_tests}"


class ProjectUser(Base):
    __tablename__ = "project_user"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", "role_id", name="project_user_role_key"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    role_id = Column(Integer, ForeignKey("role.id"))
    is_active = Column(Boolean, default=True)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    project = relationship("Project", overlaps="users", uselist=False)
    user = relationship("User", overlaps="users", uselist=False)
    role = relationship("Role", uselist=False)

    # history_project_assigned = relationship("ProjectUserHistory", back_populates="assigned_user", primaryjoin="ProjectUser.user_id==ProjectUserHistory.assigned_user_id",)

    def __repr__(self):
        return f"id: {self.id}, project_id: {self.project_id}, user_id: {self.user_id}"


class ProjectGroup(Base):
    __tablename__ = "project_group"
    __table_args__ = (UniqueConstraint("name", "tenant_id", name="project_group_name_tenant_key"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    created_date = last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    projects = relationship("Project", back_populates="project_group")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class ProjectEvaluation(Base):
    __tablename__ = "project_evaluation"
    __table_args__ = (
        UniqueConstraint("name", "project_id", name="project_evaluation_name_project_key"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    comments = Column(String)
    # keywords = Column(String)
    status = Column(Enum(StatusType), default=StatusType.not_started.value)
    project_id = Column(ForeignKey("project.id", use_alter=True))

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    project = relationship(
        "Project",
        foreign_keys=[project_id],
    )

    documents = relationship(
        "ProjectEvaluationDocument",
        back_populates="project_evaluation",
    )

    keywords = relationship(
        "KeywordMapping",
        primaryjoin="ProjectEvaluation.id==KeywordMapping.project_evaluation_id",
        viewonly=True,
        back_populates="project_evaluation",
    )

    history_user_project_evaluation = relationship(
        "ProjectEvaluationHistory", back_populates="project_evaluation"
    )

    costs = relationship(
        "ProjectEvaluationCost", back_populates="project_evaluation", cascade="all, delete-orphan"
    )

    approval_workflows = relationship(
        "ProjectEvaluationApprovalWorkflow", back_populates="project_evaluation"
    )

    # TODO: Add relationship to system users table for the next two . . .
    # primary_owner = Column(String)  # Drop down showing system users
    # secondary_owner = Column(String) # Drop down showing system users

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class ProjectControl(Base):
    __tablename__ = "project_control"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"))
    project = relationship("Project", overlaps="controls,projects,project_controls")
    control_id = Column(Integer, ForeignKey("control.id"))
    control = relationship("Control", overlaps="controls,projects")

    # A Project Control will have one and only one Assessment
    # The Assessment is always automatically added when a Project Control is created
    assessment = relationship("Assessment", back_populates="project_control", uselist=False)

    # A Project Control will have zero or One Exception
    exception = relationship("Exception", back_populates="project_control", uselist=False)

    # A Project Control will have zero or more Audit Tests
    audit_tests = relationship("AuditTest", back_populates="project_control", uselist=False)

    # A Project Control will have zero or more Risks
    risks = relationship("Risk", back_populates="project_control")

    documents = relationship(
        "ProjectControlDocument",
        back_populates="project_control",
    )

    implementation_statement = Column(String)

    mitigation_percentage = Column(DECIMAL(5, 2))
    control_family_id = Column(Integer, ForeignKey("control_family.id"))
    control_family = relationship("ControlFamily", back_populates="project_controls", uselist=False)
    control_phase_id = Column(Integer, ForeignKey("control_phase.id"))
    control_phase = relationship("ControlPhase", back_populates="project_controls", uselist=False)
    control_status_id = Column(Integer, ForeignKey("control_status.id"))
    control_status = relationship("ControlStatus", back_populates="project_controls", uselist=False)
    control_class_id = Column(Integer, ForeignKey("control_class.id"))
    control_class = relationship("ControlClass", back_populates="project_controls", uselist=False)

    keywords = relationship(
        "KeywordMapping",
        primaryjoin="ProjectControl.id==KeywordMapping.project_control_id",
        viewonly=True,
        back_populates="project_control",
    )

    history_user_project_control = relationship(
        "ProjectControlHistory", back_populates="project_control"
    )

    aws_controls = relationship("AWSControlProjectControl", back_populates="project_control")

    cap_poams = relationship("CapPoamProjectControl", back_populates="project_control")

    costs = relationship(
        "ProjectControlCost",
        back_populates="project_control",
    )

    approval_workflows = relationship(
        "ProjectControlApprovalWorkflow", back_populates="project_control"
    )

    evidence = relationship("ProjectControlEvidence", back_populates="project_control")

    service_provider_project_controls = relationship(
        "ServiceProviderProjectControl",
        back_populates="project_control",
        cascade="all, delete-orphan",
    )

    app_project_controls = relationship(
        "AppProjectControl",
        back_populates="project_control",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"id:{self.id},project:{self.project_id}, control:{self.control_id}, mitigation_percentage:{self.mitigation_percentage}"


class Keyword(Base):
    __tablename__ = "keyword"
    __table_args__ = (UniqueConstraint("name", "tenant_id", name="keyword_name_tenant_key"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"))

    documents = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="keyword",
    )
    assessments = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="assessment_keyword",
        overlaps="documents",
    )
    audit_tests = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="audit_test_keyword",
        overlaps="documents,assessments",
    )
    controls = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="control_keyword",
        overlaps="documents,assessments,audit_tests",
    )
    exceptions = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="exception_keyword",
        overlaps="documents,assessments,audit_tests,controls",
    )
    frameworks = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="framework_keyword",
        overlaps="documents,assessments,audit_tests,controls,exceptions",
    )
    framework_versions = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="framework_version_keyword",
        overlaps="documents,assessments,audit_tests,controls,exceptions,frameworks",
    )
    projects = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="project_keyword",
        overlaps="documents,assessments,audit_tests,controls,exceptions,frameworks,framework_versions",
    )
    project_controls = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="project_control_keyword",
        overlaps="projects,documents,assessments,audit_tests,controls,exceptions,frameworks,framework_versions",
    )
    project_evaluations = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="project_evaluation_keyword",
        overlaps="project_controls,projects,documents,assessments,audit_tests,controls,exceptions,frameworks,framework_versions",
    )
    risks = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="risk_keyword",
        overlaps="project_evaluations,project_controls,projects,documents,assessments,audit_tests,controls,exceptions,frameworks,framework_versions",
    )
    tasks = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="task_keyword",
        overlaps="risks,project_evaluations,project_controls,projects,documents,assessments,audit_tests,controls,exceptions,frameworks,framework_versions",
    )
    wbs = relationship(
        "KeywordMapping",
        primaryjoin="Keyword.id==KeywordMapping.keyword_id",
        viewonly=True,
        back_populates="wbs_keyword",
        overlaps="tasks,risks,project_evaluations,project_controls,projects,documents,assessments,audit_tests,controls,exceptions,frameworks,framework_versions",
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class Frequency(Base):
    __tablename__ = "frequency"
    __table_args__ = (UniqueConstraint("name", "tenant_id", name="frequency_name_tenant_key"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"))

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class Framework(Base):
    __tablename__ = "framework"
    # __table_args__ = (UniqueConstraint("name", "tenant_id", name="framework_name_tenant_key"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    # keywords = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    is_preloaded = Column(Boolean, default=False)
    # tenant_id = Column(Integer, ForeignKey("tenant.id"))

    framework_version = relationship("FrameworkVersion", back_populates="framework")

    documents = relationship(
        "FrameworkDocument",
        back_populates="framework",
    )

    keywords = relationship(
        "KeywordMapping",
        primaryjoin="Framework.id==KeywordMapping.framework_id",
        viewonly=True,
        back_populates="framework",
    )

    is_global = Column(Boolean)

    framework_tenant = relationship("FrameworkTenant", back_populates="framework")

    audit_evidence_framework = relationship(
        "AuditEvidenceFilterFramework",
        back_populates="framework",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class FrameworkVersion(Base):
    __tablename__ = "framework_version"
    # __table_args__ = (UniqueConstraint("name", "tenant_id", name="framework_name_tenant_key"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    version_prefix = Column(String)
    version_suffix = Column(String)
    guidance = Column(String)
    release_date = Column(Date, nullable=True)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    is_preloaded = Column(Boolean, default=False)

    framework_id = Column(Integer, ForeignKey("framework.id"))
    framework = relationship("Framework", back_populates="framework_version")

    controls = relationship("Control", secondary="control_framework_version")

    documents = relationship(
        "FrameworkVersionDocument",
        back_populates="framework_version",
    )

    keywords = relationship(
        "KeywordMapping",
        primaryjoin="FrameworkVersion.id==KeywordMapping.framework_version_id",
        viewonly=True,
        back_populates="framework_version",
    )

    def __repr__(self):
        return f"id: {self.id}, version_prefix: {self.version_prefix}, version_suffix: {self.version_suffix}"


class Document(Base):
    __tablename__ = "document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    title = Column(String)
    description = Column(String)
    file_content_type = Column(String)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=True)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    # projects = relationship(
    #     "ProjectDocument", back_populates="document", foreign_keys="ProjectDocument.project_id"
    # )
    tenant = relationship("Tenant")
    projects = relationship(
        "ProjectDocument",
        primaryjoin="Document.id==ProjectDocument.document_id",
        viewonly=True,
    )
    assessments = relationship(
        "AssessmentDocument",
        primaryjoin="Document.id==AssessmentDocument.document_id",
        viewonly=True,
    )
    audit_tests = relationship(
        "AuditTestDocument",
        primaryjoin="Document.id==AuditTestDocument.document_id",
        viewonly=True,
    )
    controls = relationship(
        "ControlDocument",
        primaryjoin="Document.id==ControlDocument.document_id",
        viewonly=True,
    )
    project_controls = relationship(
        "ProjectControlDocument",
        primaryjoin="Document.id==ProjectControlDocument.document_id",
        viewonly=True,
    )
    exceptions = relationship(
        "ExceptionDocument",
        primaryjoin="Document.id==ExceptionDocument.document_id",
        viewonly=True,
    )
    frameworks = relationship(
        "FrameworkDocument",
        primaryjoin="Document.id==FrameworkDocument.document_id",
        viewonly=True,
    )
    framework_versions = relationship(
        "FrameworkVersionDocument",
        primaryjoin="Document.id==FrameworkVersionDocument.document_id",
        viewonly=True,
    )
    risks = relationship(
        "RiskDocument",
        primaryjoin="Document.id==RiskDocument.document_id",
        viewonly=True,
    )
    task = relationship("Task", secondary="task_document", overlaps="document")
    wbs = relationship(
        "WBSDocument",
        primaryjoin="Document.id==WBSDocument.document_id",
        viewonly=True,
    )
    project_evaluations = relationship(
        "ProjectEvaluationDocument",
        primaryjoin="Document.id==ProjectEvaluationDocument.document_id",
        viewonly=True,
    )
    keywords = relationship(
        "KeywordMapping",
        primaryjoin="Document.id==KeywordMapping.document_id",
        viewonly=True,
        back_populates="document",
    )
    history_user_document = relationship("DocumentHistory", back_populates="document")

    fedrisk_object_type = Column(Unicode(255))
    fedrisk_object_id = Column(Integer)
    fedrisk_object = generic_relationship(fedrisk_object_type, fedrisk_object_id)

    owner_id = Column(Integer, ForeignKey("user.id"))
    owner = relationship("User", uselist=False)

    version = Column(String, nullable=True)

    approval_workflows = relationship("DocumentApprovalWorkflow", back_populates="document")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class AuditTest(Base):
    __tablename__ = "audit_test"
    # __table_args__ = (UniqueConstraint("name", "project_id", name="audit_test_name_project_key"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    name = Column(String)
    description = Column(String)
    objective = Column(String)
    expected_results = Column(String)
    approximate_days_to_complete = Column(Integer)
    external_reference_id = Column(String)
    project_id = Column(ForeignKey("project.id", use_alter=True))

    project_control_id = Column(Integer, ForeignKey("project_control.id"))
    project_control = relationship("ProjectControl")

    tester_id = Column(Integer, ForeignKey("user.id"))
    tester = relationship("User")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    status = Column(Enum(AuditTestStatus))
    outcome_passed = Column(Boolean, nullable=True)
    stakeholders = relationship("User", secondary="audit_test_stakeholder")

    test_frequency = Column(Enum(TestFrequency))
    last_test_date = Column(Date, nullable=True)

    documents = relationship(
        "AuditTestDocument",
        back_populates="audit_test",
    )

    keywords = relationship(
        "KeywordMapping",
        primaryjoin="AuditTest.id==KeywordMapping.audit_test_id",
        viewonly=True,
        back_populates="audit_test",
    )

    history_user_audit_test = relationship("AuditTestHistory", back_populates="audit_test")

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    project = relationship(
        "Project",
        foreign_keys=[project_id],
    )
    risks = relationship("Risk", back_populates="audit_test")
    cap_poams = relationship(
        "CapPoam", primaryjoin="AuditTest.id==CapPoam.audit_test_id", back_populates="audit_test"
    )

    audit_test_instances = relationship(
        "AuditTestInstance",
        back_populates="audit_test",
    )

    costs = relationship(
        "AuditTestCost",
        back_populates="audit_test",
    )

    approval_workflows = relationship("AuditTestApprovalWorkflow", back_populates="audit_test")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, cap_poam: {self.cap_poams}"


class AuditTestInstance(Base):
    __tablename__ = "audit_test_instance"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_test_id = Column(Integer, ForeignKey("audit_test.id"))
    status = Column(Enum(AuditTestInstanceStatus))
    comments = Column(String)
    outcome_passed = Column(Boolean, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    audit_test = relationship(
        "AuditTest", foreign_keys=[audit_test_id], back_populates="audit_test_instances"
    )

    def __repr__(self):
        return f"id: {self.id}, audit_test_id: {self.audit_test_id}, status: {self.status}, outcome_passed: {self.outcome_passed}, start_date: {self.start_date}, end_date: {self.end_date}"


class AuditTestStakeHolder(Base):
    __tablename__ = "audit_test_stakeholder"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_test_id = Column(Integer, ForeignKey("audit_test.id"))
    user_id = Column(Integer, ForeignKey("user.id"))

    def __repr__(self):
        return f"id: {self.id}"


class ControlStatus(Base):
    __tablename__ = "control_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    tenant_id = Column(Integer, ForeignKey("tenant.id"))

    project_controls = relationship("ProjectControl", back_populates="control_status")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class ControlFamily(Base):
    __tablename__ = "control_family"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"))

    project_controls = relationship("ProjectControl", back_populates="control_family")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class ControlPhase(Base):
    __tablename__ = "control_phase"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"))

    project_controls = relationship("ProjectControl", back_populates="control_phase")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class ControlClass(Base):
    __tablename__ = "control_class"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"))

    project_controls = relationship("ProjectControl", back_populates="control_class")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class Control(Base):
    __tablename__ = "control"
    __table_args__ = (UniqueConstraint("name", "tenant_id", name="control_name_tenant_key"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    # keywords = Column(String)
    guidance = Column(String)
    is_preloaded = Column(Boolean, default=False)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"))

    framework_versions = relationship(
        "FrameworkVersion", secondary="control_framework_version", overlaps="controls"
    )
    documents = relationship(
        "ControlDocument",
        back_populates="control",
    )
    keywords = relationship(
        "KeywordMapping",
        primaryjoin="Control.id==KeywordMapping.control_id",
        viewonly=True,
        back_populates="control",
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class Assessment(Base):
    __tablename__ = "assessment"
    __table_args__ = (
        UniqueConstraint("name", "project_control_id", name="assessment_name_project_control_key"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    comments = Column(String)
    # keywords = Column(String)
    status = Column(Enum(StatusType), default=StatusType.not_started.value)
    is_assessment_confirmed = Column(
        Enum(IsAssessmentConfirmed), default=IsAssessmentConfirmed.no.value
    )
    test_frequency = Column(Enum(TestFrequency))
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    project_control_id = Column(ForeignKey("project_control.id"))
    project_control = relationship(
        "ProjectControl", back_populates="assessment", foreign_keys=[project_control_id]
    )

    documents = relationship(
        "AssessmentDocument",
        back_populates="assessment",
    )

    keywords = relationship(
        "KeywordMapping",
        primaryjoin="Assessment.id==KeywordMapping.assessment_id",
        viewonly=True,
        back_populates="assessment",
    )

    history_user_assessment = relationship("AssessmentHistory", back_populates="assessment")

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"))

    costs = relationship(
        "AssessmentCost", back_populates="assessment", cascade="all, delete-orphan"
    )

    instances = relationship(
        "AssessmentInstance",
        back_populates="assessment",
    )

    approval_workflows = relationship("AssessmentApprovalWorkflow", back_populates="assessment")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class AssessmentInstance(Base):
    __tablename__ = "assessment_instance"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    comments = Column(String)
    review_status = Column(
        Enum(AssessmentInstanceStatus), default=AssessmentInstanceStatus.not_started.value
    )

    assessment_id = Column(ForeignKey("assessment.id"))

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())

    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    assessment = relationship(
        "Assessment", foreign_keys=[assessment_id], back_populates="instances"
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, assessment_id: {self.assessment_id}"


class Exception(Base):
    __tablename__ = "exception"
    __table_args__ = (
        UniqueConstraint("name", "project_control_id", name="exception_name_project_control_key"),
    )

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    justification = Column(String)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    next_review_date = Column(Date)
    review_frequency = Column(Enum(ReviewFrequency), default=ReviewFrequency.daily.value)
    # review_status = Column(
    #     Enum(ExceptionReviewStatus), default=ExceptionReviewStatus.not_started.value
    # )

    project_control_id = Column(ForeignKey("project_control.id"))
    project_control = relationship(
        "ProjectControl",
        # back_populates="exception",
    )
    owner_id = Column(ForeignKey("user.id"))
    owner = relationship("User")
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"))

    stakeholders = relationship(
        "User",
        secondary="exception_stakeholder",
        back_populates="exceptions",
    )

    documents = relationship(
        "ExceptionDocument",
        back_populates="exception",
    )
    keywords = relationship(
        "KeywordMapping",
        primaryjoin="Exception.id==KeywordMapping.exception_id",
        viewonly=True,
        back_populates="exception",
    )
    history_user_exception = relationship("ExceptionHistory", back_populates="exception")

    reviews = relationship(
        "ExceptionReview",
        back_populates="exception",
    )

    costs = relationship(
        "ExceptionCost",
        back_populates="exception",
    )

    approval_workflows = relationship("ExceptionApprovalWorkflow", back_populates="exception")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class ExceptionReview(Base):
    __tablename__ = "exception_review"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    comments = Column(String)
    review_status = Column(
        Enum(ExceptionReviewStatus), default=ExceptionReviewStatus.not_started.value
    )

    exception_id = Column(ForeignKey("exception.id"))

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())

    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    exception = relationship("Exception", foreign_keys=[exception_id], back_populates="reviews")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, exception_id: {self.exception_id}"


class ExceptionStakeholder(Base):
    __tablename__ = "exception_stakeholder"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    exception_id = Column(Integer, ForeignKey("exception.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"id: {self.id}, exception_id: {self.exception_id}, user_id: {self.user_id}"


class RiskImpact(Base):
    """Used for Dropdown for Current Impact on Risk Form
    - Initial Values:
        Insignificant
        Minor
        Moderate
        Major
        Extreme

    """

    __tablename__ = "risk_impact"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class RiskScore(Base):
    """Used for Dropdown for Risk Score on Risk Form
    - Initial Values:
        External
        People
        Process
        System
    """

    __tablename__ = "risk_score"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class RiskCategory(Base):
    """Used for Dropdown for Category on Risk Form
    - Initial Values:
        Access Management
        Environmental Resilience
        Monitoring
        Physical Security
        Policy & Procedure
        Sensitive Data Management
        Technical Vulnerability
        Third Party Management

    """

    __tablename__ = "risk_category"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class RiskStatus(Base):
    """Used for Dropdown for Risk Status on Risk Form
    - Initial Values:
        Active
        On Hold
        Completed
        Cancelled

    """

    __tablename__ = "risk_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class RiskLikelihood(Base):
    """Used for Dropdown for Current Likelihood on Risk Form
    - Initial Values:
        Remote
        Unlikely
        Credible
        Likely
        Almost Certain

    """

    __tablename__ = "risk_likelihood"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class RiskMapping(Base):
    """Used for Dropdown for risk Mapping on Risk Form
    - Initial Values:
        Test Risk Mapping #1
        Test Risk Mapping #2
        Test Risk Mapping #3
        Test Risk Mapping #4

    """

    __tablename__ = "risk_mapping"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class Risk(Base):
    __tablename__ = "risk"
    __table_args__ = (UniqueConstraint("name", "project_id", name="risk_name_project_key"),)

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)

    project_id = Column(Integer, ForeignKey("project.id"))
    project = relationship("Project", back_populates="risks")

    project_control_id = Column(Integer, ForeignKey("project_control.id"))
    project_control = relationship("ProjectControl", back_populates="risks")

    audit_test_id = Column(Integer, ForeignKey("audit_test.id"))
    audit_test = relationship("AuditTest", back_populates="risks")

    external_reference_id = Column(String)

    risk_status_id = Column(Integer, ForeignKey("risk_status.id"))
    risk_status = relationship("RiskStatus")
    risk_impact_id = Column(Integer, ForeignKey("risk_impact.id"))
    risk_impact = relationship("RiskImpact")
    risk_category_id = Column(Integer, ForeignKey("risk_category.id"))
    risk_category = relationship("RiskCategory")
    risk_score_id = Column(Integer, ForeignKey("risk_score.id"))
    risk_score = relationship("RiskScore")
    current_likelihood_id = Column(Integer, ForeignKey("risk_likelihood.id"))
    current_likelihood = relationship("RiskLikelihood")

    comments = Column(String)
    additional_notes = Column(String)
    technology = Column(String)
    current_impact = Column(Float)
    risk_assessment = Column(String)
    affected_assets = Column(String)
    owner_id = Column(Integer, ForeignKey("user.id"))
    owner = relationship("User", uselist=False)

    owner_supervisor = Column(String)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    additional_stakeholders = relationship("User", secondary="risk_stakeholder")

    documents = relationship(
        "RiskDocument",
        back_populates="risk",
    )

    keywords = relationship(
        "KeywordMapping",
        primaryjoin="Risk.id==KeywordMapping.risk_id",
        viewonly=True,
        back_populates="risk",
    )
    history_user_risk = relationship("RiskHistory", back_populates="risk")

    costs = relationship(
        "RiskCost",
        back_populates="risk",
    )

    approval_workflows = relationship("RiskApprovalWorkflow", back_populates="risk")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class RiskStakeholder(Base):
    __tablename__ = "risk_stakeholder"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    risk_id = Column(Integer, ForeignKey("risk.id"))
    user_id = Column(Integer, ForeignKey("user.id"))

    def __repr__(self):
        return f"id: {self.id}, risk_id: {self.risk_id}, user_id: {self.user_id}"


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    title = Column(String)
    name = Column(String)
    description = Column(String)
    priority = Column(Enum(TaskPriority))
    # Add task status from db association
    task_status_id = Column(Integer, ForeignKey("task_status.id"))
    task_status = relationship("TaskStatus", back_populates="task")
    # Add task category from db association
    task_category_id = Column(Integer, ForeignKey("task_category.id"))
    task_category = relationship("TaskCategory", back_populates="task")
    due_date = Column(Date, nullable=True)
    import_id = Column(Integer, ForeignKey("import_task.id"), nullable=True)

    project_id = Column(Integer, ForeignKey("project.id"), nullable=True)
    project = relationship("Project")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=current_timestamp())
    updated_at = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    task_history = relationship(
        "TaskHistory",
        back_populates="task",
        order_by="desc(TaskHistory.updated_date)",
    )

    wbs_id = Column(Integer, ForeignKey("wbs.id"), nullable=True)
    wbs = relationship("WBS")

    # workflow_flowchart_id = Column(Integer, ForeignKey("wbs.id"), nullable=True)
    # workflow_flowchart = relationship("WorkflowFlowchart")

    actual_start_date = Column(Date, nullable=True)
    actual_end_date = Column(Date, nullable=True)
    duration = Column(String, nullable=True)
    # category = Column(String, nullable=True)
    percent_complete = Column(Integer, nullable=True)

    milestone = Column(Boolean, nullable=True)

    assigned_to = Column(Integer, ForeignKey("user.id"), nullable=True)

    user = relationship("User", foreign_keys=[user_id])
    assigned = relationship("User", foreign_keys=[assigned_to])

    estimated_loe = Column(String, nullable=True)
    actual_loe = Column(String, nullable=True)

    child_task_order = Column(Integer, nullable=True)

    attachments = relationship("Document", secondary="task_document", overlaps="task")

    risks = relationship("Risk", secondary="task_risk")

    audit_tests = relationship("AuditTest", secondary="task_audit_test")

    project_controls = relationship("ProjectControl", secondary="task_project_control")

    parents = relationship(
        "TaskChild",
        back_populates="parent",
        foreign_keys="TaskChild.parent_task_id",
    )

    children = relationship(
        "TaskChild",
        back_populates="child",
        foreign_keys="TaskChild.child_task_id",
    )

    keywords = relationship(
        "KeywordMapping",
        primaryjoin="Task.id==KeywordMapping.task_id",
        viewonly=True,
        back_populates="task",
    )
    history_user_task = relationship("ProjectTaskHistory", back_populates="task")

    task_link_sources = relationship(
        "TaskLink",
        back_populates="sources",
        foreign_keys="TaskLink.source_id",
    )

    task_link_targets = relationship(
        "TaskLink",
        back_populates="targets",
        foreign_keys="TaskLink.target_id",
    )

    resources = relationship("TaskResource", back_populates="task")

    costs = relationship(
        "TaskCost",
        back_populates="task",
    )

    cap_poams = relationship("CapPoamTask", back_populates="task")

    additional_stakeholders = relationship("User", secondary="task_stakeholder")

    # Updated association relationship:
    workflow_task_mappings = relationship("WorkflowTaskMapping", back_populates="task")

    approval_workflows = relationship("TaskApprovalWorkflow", back_populates="task")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, assigned_to: {self.assigned_to}, wbs_id: {self.wbs_id}"


class TaskStakeholder(Base):
    __tablename__ = "task_stakeholder"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("task.id"))
    user_id = Column(Integer, ForeignKey("user.id"))

    def __repr__(self):
        return f"id: {self.id}, task_id: {self.task_id}, user_id: {self.user_id}"


class TaskHistory(Base):
    __tablename__ = "task_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    old_status = Column(String)
    new_status = Column(String)
    comments = Column(String)

    task_id = Column(Integer, ForeignKey("task.id"), nullable=False)
    task = relationship("Task", back_populates="task_history")
    updated_by_id = Column(Integer, ForeignKey("user.id"))
    updated_by = relationship("User", back_populates="task_history")
    # assigned_to_id = Column(Integer, ForeignKey("user.id"))
    # assigned_to = relationship("User", back_populates="task_history")
    updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, new status: {self.new_status}"


class TaskCategory(Base):
    """Used for Dropdown for category on Task Form
    - Initial Values:
        Projects
        Frameworks
        Controls
        Assessments
        Ad-hoc Assessments
        Project Evaluations
        Risks
    """

    __tablename__ = "task_category"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=False)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    task = relationship("Task", back_populates="task_category")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class Tenant(Base):
    __tablename__ = "tenant"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    # domain = Column(String, unique=True)
    is_active = Column(Boolean, default=False)

    # TODO: Better name here - this really should be:
    # allowed_user_licenses - it is a count of how many users are allowed
    # current name sounds like it is a single thing - like a license key?
    user_licence = Column(Integer, default=50)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    customer_id = Column(String, unique=True, nullable=True)
    webhook_api_key = Column(String, unique=True, nullable=True)

    framework_tenant = relationship("FrameworkTenant", back_populates="tenant")

    # subscription = relationship("Subscription", back_populates="tenant", uselist=False)

    s3_bucket = Column(String, unique=True)

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, s3_bucket: {self.s3_bucket}, webhook_api_key: {self.webhook_api_key}"


class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String, nullable=False, unique=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    phone_no = Column(String, nullable=True)
    profile_picture = Column(String, nullable=True)
    is_superuser = Column(Boolean, default=False)
    is_tenant_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    system_role = Column(Integer, ForeignKey("role.id"), nullable=True)
    s3_bucket = Column(String, unique=True)

    tenant = relationship("Tenant")
    projects = relationship(
        "Project", secondary="project_user", back_populates="users", overlaps="user,project"
    )
    project_roles = relationship(
        "Role",
        secondary="project_user",
        back_populates="users",
        overlaps="projects,user,users,role",
    )
    system_role_links = relationship(
        "SystemRole", back_populates="user", cascade="all, delete-orphan"
    )

    # optional convenience shortcut to Role models
    system_roles = relationship(
        "Role",
        secondary="system_role",
        primaryjoin="and_(User.id==SystemRole.user_id, SystemRole.enabled==True)",
        secondaryjoin="Role.id==SystemRole.role_id",
        viewonly=True,
        lazy="joined",
    )

    task_history = relationship("TaskHistory", back_populates="updated_by")
    exceptions = relationship(
        "Exception", secondary="exception_stakeholder", back_populates="stakeholders"
    )

    history_audit_test = relationship("AuditTestHistory", back_populates="author")
    history_cap_poam = relationship("CapPoamHistory", back_populates="author")
    history_assessment = relationship("AssessmentHistory", back_populates="author")
    history_document = relationship("DocumentHistory", back_populates="author")
    history_exception = relationship("ExceptionHistory", back_populates="author")
    history_project_control = relationship("ProjectControlHistory", back_populates="author")
    history_project_evaluation = relationship("ProjectEvaluationHistory", back_populates="author")
    history_project = relationship("ProjectHistory", back_populates="author")
    history_task = relationship("ProjectTaskHistory", back_populates="author")
    history_risk = relationship("RiskHistory", back_populates="author")
    history_wbs = relationship("WBSHistory", back_populates="author")
    history_workflow_flowchart = relationship("WorkflowFlowchartHistory", back_populates="author")
    history_approval_workflow = relationship("ApprovalWorkflowHistory", back_populates="author")
    reporting_settings = relationship("ReportingSettings", back_populates="user")
    tasks = relationship("TaskResource", back_populates="resource")
    surveys = relationship("SurveyResponse", back_populates="user")
    audit_evidence_submitter = relationship(
        "AuditEvidence",
        back_populates="auditor_submitter",
        foreign_keys="AuditEvidence.submission_user_id",
    )
    audit_evidence_auditor = relationship(
        "AuditEvidence", back_populates="auditor_user", foreign_keys="AuditEvidence.auditor_user_id"
    )

    @property
    def status(self):
        if self.is_active:
            return "Active"
        elif self.is_email_verified:
            return "Deactive"
        else:
            return "Pending"

    def __repr__(self):
        return f"id: {self.id}, email: {self.email}, first_name: {self.first_name}, last_name: {self.last_name}, phone_no: {self.phone_no}, profile_picture: {self.profile_picture}, tenant_id: {self.tenant_id}, is_superuser: {self.is_superuser}, s3_bucket: {self.s3_bucket}"


class Role(Base):
    __tablename__ = "role"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)

    permissions = relationship("Permission", secondary="permission_role", back_populates="role")

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    users = relationship(
        "User",
        secondary="project_user",
        back_populates="project_roles",  # <-- FIXED HERE
        overlaps="projects,users,role",
    )

    system_role_links = relationship(
        "SystemRole", back_populates="role", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class SystemRole(Base):
    __tablename__ = "system_role"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("role.id"), nullable=False)
    enabled = Column(Boolean, nullable=False)

    user = relationship("User", back_populates="system_role_links")
    role = relationship("Role", back_populates="system_role_links")

    def __repr__(self):
        return f"id: {self.id}, user_id: {self.user_id}, role_id: {self.role_id}, enabled: {self.enabled}"


class Permission(Base):
    __tablename__ = "permission"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    perm_key = Column(String, unique=True)
    category = Column(String)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    role = relationship("Role", secondary="permission_role", back_populates="permissions")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class PermissionRole(Base):
    __tablename__ = "permission_role"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    permission_id = Column(Integer, ForeignKey("permission.id"))
    role_id = Column(Integer, ForeignKey("role.id"))
    tenant_id = Column(Integer, ForeignKey("tenant.id"))

    enabled = Column(Boolean, default=True, nullable=False)  # <-- Add this

    # Optional for audit
    # updated_at = Column(
    #     DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    # )
    # updated_by = Column(Integer, ForeignKey("user.id"), nullable=True)

    def __repr__(self):
        return f"id: {self.id}, role_id: {self.role_id}, permission_id: {self.permission_id}, tenant_id: {self.tenant_id}, enabled: {self.enabled}"


class UserInvitation(Base):
    __tablename__ = "user_invitation"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(128), nullable=False)
    token = Column(String(128), nullable=False)
    is_used = Column(Boolean, default=False)
    is_expired = Column(Boolean, default=False)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    tenant = relationship("Tenant")

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    user = relationship("User")


# class TenantRegisterOTP(Base):
#     __tablename__ = "tenant_register_otp"

#     id = Column(Integer, primary_key=True, index=True, autoincrement=True)
#     email = Column(String, nullable=False, unique=False, index=True)
#     code = Column(
#         String,
#         nullable=False,
#         unique=False,
#     )
#     is_expired = Column(Boolean, nullable=False, default=False)
#     created_at = Column(DateTime, nullable=False, server_default=current_timestamp())
#     updated_at = Column(
#         DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
#     )

#     def __repr__(self):
#         return f"id: {self.id}, email: {self.email} otp: {self.code}"


class WebHookEvent(Base):
    __tablename__ = "web_hook_event"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    event_id = Column(String, nullable=False, unique=True)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=current_timestamp())

    def __repr__(self):
        return f"id: {self.id}, event: {self.event_id}"


class ImportFramework(Base):
    __tablename__ = "import_framework"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    file_content_type = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    imported = Column(Boolean)
    import_results = Column(String)

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, file_content_type: {self.file_content_type}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}, tenant_id: {self.tenant_id}, imported: {self.imported}, import_results: {self.import_results}"


class ImportTask(Base):
    __tablename__ = "import_task"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    file_content_type = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    imported = Column(Boolean)
    import_results = Column(String)
    wbs_id = Column(Integer, ForeignKey("wbs.id"), nullable=False)

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, file_content_type: {self.file_content_type}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}, tenant_id: {self.tenant_id}, imported: {self.imported}, import_results: {self.import_results}, wbs_id: {self.wbs_id}"


class WBS(Base):
    __tablename__ = "wbs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    project = relationship("Project")
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User")
    created_date = last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    documents = relationship(
        "WBSDocument",
        back_populates="wbs",
    )
    keywords = relationship(
        "KeywordMapping",
        primaryjoin="WBS.id==KeywordMapping.wbs_id",
        viewonly=True,
        back_populates="wbs",
    )
    history_user_wbs = relationship("WBSHistory", back_populates="wbs")

    costs = relationship(
        "WBSCost",
        back_populates="wbs",
    )

    approval_workflows = relationship("WBSApprovalWorkflow", back_populates="wbs")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class TaskRisk(Base):
    __tablename__ = "task_risk"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("task.id"))
    risk_id = Column(Integer, ForeignKey("risk.id"))

    def __repr__(self):
        return f"id: {self.id}, task_id: {self.task_id}, risk_id: {self.risk_id}"


class TaskAuditTest(Base):
    __tablename__ = "task_audit_test"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("task.id"))
    audit_test_id = Column(Integer, ForeignKey("audit_test.id"))

    def __repr__(self):
        return f"id: {self.id}, task_id: {self.task_id}, audit_test_id: {self.audit_test_id}"


class TaskDocument(Base):
    __tablename__ = "task_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("task.id"))
    document_id = Column(Integer, ForeignKey("document.id"))

    def __repr__(self):
        return f"id: {self.id}, task_id: {self.task_id}, document_id: {self.document_id}"


class TaskProjectControl(Base):
    __tablename__ = "task_project_control"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("task.id"))
    project_control_id = Column(Integer, ForeignKey("project_control.id"))

    def __repr__(self):
        return (
            f"id: {self.id}, task_id: {self.task_id}, project_control_id: {self.project_control_id}"
        )


class TaskChild(Base):
    __tablename__ = "task_child"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    parent_task_id = Column(Integer, ForeignKey("task.id"))
    child_task_id = Column(Integer, ForeignKey("task.id"))
    parent = relationship("Task", foreign_keys=[parent_task_id], back_populates="parents")
    child = relationship("Task", foreign_keys=[child_task_id], back_populates="children")

    def __repr__(self):
        return f"id: {self.id}, parent_task_id: {self.parent_task_id}, child_task_id: {self.child_task_id}"


class ControlFrameworkVersion(Base):
    __tablename__ = "control_framework_version"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    control_id = Column(Integer, ForeignKey("control.id"))
    framework_version_id = Column(Integer, ForeignKey("framework_version.id"))

    def __repr__(self):
        return f"id: {self.id}, control_id: {self.control_id}, framework_version_id: {self.framework_version_id}"


class ProjectDocument(Base):
    __tablename__ = "project_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    document = relationship("Document", foreign_keys=[document_id], back_populates="projects")
    project = relationship("Project", foreign_keys=[project_id], back_populates="documents")

    def __repr__(self):
        return f"id: {self.id}, project_id: {self.project_id}, document_id: {self.document_id}"


class AssessmentDocument(Base):
    __tablename__ = "assessment_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessment.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    document = relationship("Document", foreign_keys=[document_id], back_populates="assessments")
    assessment = relationship(
        "Assessment", foreign_keys=[assessment_id], back_populates="documents"
    )

    def __repr__(self):
        return (
            f"id: {self.id}, assessment_id: {self.assessment_id}, document_id: {self.document_id}"
        )


class AuditTestDocument(Base):
    __tablename__ = "audit_test_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_test_id = Column(Integer, ForeignKey("audit_test.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    document = relationship("Document", foreign_keys=[document_id], back_populates="audit_tests")
    audit_test = relationship("AuditTest", foreign_keys=[audit_test_id], back_populates="documents")

    def __repr__(self):
        return (
            f"id: {self.id}, audit_test_id: {self.audit_test_id}, document_id: {self.document_id}"
        )


class ControlDocument(Base):
    __tablename__ = "control_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    control_id = Column(Integer, ForeignKey("control.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    document = relationship("Document", foreign_keys=[document_id], back_populates="controls")
    control = relationship("Control", foreign_keys=[control_id], back_populates="documents")

    def __repr__(self):
        return f"id: {self.id}, control_id: {self.control_id}, document_id: {self.document_id}"


class ExceptionDocument(Base):
    __tablename__ = "exception_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    exception_id = Column(Integer, ForeignKey("exception.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    document = relationship("Document", foreign_keys=[document_id], back_populates="exceptions")
    exception = relationship("Exception", foreign_keys=[exception_id], back_populates="documents")

    def __repr__(self):
        return f"id: {self.id}, exception_id: {self.exception_id}, document_id: {self.document_id}"


class RiskDocument(Base):
    __tablename__ = "risk_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    risk_id = Column(Integer, ForeignKey("risk.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    document = relationship("Document", foreign_keys=[document_id], back_populates="risks")
    risk = relationship("Risk", foreign_keys=[risk_id], back_populates="documents")

    def __repr__(self):
        return f"id: {self.id}, risk_id: {self.risk_id}, document_id: {self.document_id}"


class ProjectControlDocument(Base):
    __tablename__ = "project_control_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_control_id = Column(Integer, ForeignKey("project_control.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    document = relationship(
        "Document", foreign_keys=[document_id], back_populates="project_controls"
    )
    project_control = relationship(
        "ProjectControl", foreign_keys=[project_control_id], back_populates="documents"
    )

    def __repr__(self):
        return f"id: {self.id}, project_control_id: {self.project_control_id}, document_id: {self.document_id}"


class ProjectEvaluationDocument(Base):
    __tablename__ = "project_evaluation_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_evaluation_id = Column(Integer, ForeignKey("project_evaluation.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    document = relationship(
        "Document", foreign_keys=[document_id], back_populates="project_evaluations"
    )
    project_evaluation = relationship(
        "ProjectEvaluation", foreign_keys=[project_evaluation_id], back_populates="documents"
    )

    def __repr__(self):
        return f"id: {self.id}, project_evalution_id: {self.project_evaluation_id}, document_id: {self.document_id}"


class WBSDocument(Base):
    __tablename__ = "wbs_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    wbs_id = Column(Integer, ForeignKey("wbs.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    document = relationship("Document", foreign_keys=[document_id], back_populates="wbs")
    wbs = relationship("WBS", foreign_keys=[wbs_id], back_populates="documents")

    def __repr__(self):
        return f"id: {self.id}, wbs_id: {self.wbs_id}, document_id: {self.document_id}"


class FrameworkDocument(Base):
    __tablename__ = "framework_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    framework_id = Column(Integer, ForeignKey("framework.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    document = relationship("Document", foreign_keys=[document_id], back_populates="frameworks")
    framework = relationship("Framework", foreign_keys=[framework_id], back_populates="documents")

    def __repr__(self):
        return f"id: {self.id}, framework_id: {self.framework_id}, document_id: {self.document_id}"


class FrameworkVersionDocument(Base):
    __tablename__ = "framework_version_document"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    framework_version_id = Column(Integer, ForeignKey("framework_version.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    document = relationship(
        "Document", foreign_keys=[document_id], back_populates="framework_versions"
    )
    framework_version = relationship(
        "FrameworkVersion", foreign_keys=[framework_version_id], back_populates="documents"
    )

    def __repr__(self):
        return f"id: {self.id}, framework_version_id: {self.framework_version_id}, document_id: {self.document_id}"


class KeywordMapping(Base):
    __tablename__ = "keyword_mapping"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    keyword_id = Column(Integer, ForeignKey("keyword.id"))
    document_id = Column(Integer, ForeignKey("document.id"))
    assessment_id = Column(Integer, ForeignKey("assessment.id"))
    audit_test_id = Column(Integer, ForeignKey("audit_test.id"))
    control_id = Column(Integer, ForeignKey("control.id"))
    exception_id = Column(Integer, ForeignKey("exception.id"))
    framework_id = Column(Integer, ForeignKey("framework.id"))
    framework_version_id = Column(Integer, ForeignKey("framework_version.id"))
    project_id = Column(Integer, ForeignKey("project.id"))
    project_control_id = Column(Integer, ForeignKey("project_control.id"))
    project_evaluation_id = Column(Integer, ForeignKey("project_evaluation.id"))
    risk_id = Column(Integer, ForeignKey("risk.id"))
    task_id = Column(Integer, ForeignKey("task.id"))
    wbs_id = Column(Integer, ForeignKey("wbs.id"))
    document = relationship("Document", foreign_keys=[document_id], back_populates="keywords")
    keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="documents",
        overlaps="wbs,tasks,risks,project_evaluations,project_controls,projects,assessments,audit_tests,controls,exceptions,frameworks,framework_versions",
    )
    assessment = relationship("Assessment", foreign_keys=[assessment_id], back_populates="keywords")
    assessment_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="assessments",
        overlaps="wbs,tasks,risks,project_evaluations,project_controls,projects,documents,keyword,audit_tests,controls,exceptions,frameworks,framework_versions",
    )
    audit_test = relationship("AuditTest", foreign_keys=[audit_test_id], back_populates="keywords")
    audit_test_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="audit_tests",
        overlaps="wbs,tasks,risks,project_evaluations,project_controls,projects,frameworks,assessment_keyword,assessments,documents,keyword,controls,exceptions,framework_versions",
    )
    control = relationship("Control", foreign_keys=[control_id], back_populates="keywords")
    control_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="controls",
        overlaps="wbs,tasks,risks,project_evaluations,project_controls,projects,framework_versions,frameworks,assessment_keyword,assessments,audit_test_keyword,audit_tests,documents,keyword,exceptions",
    )
    exception = relationship("Exception", foreign_keys=[exception_id], back_populates="keywords")
    exception_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="exceptions",
        overlaps="wbs,tasks,risks,project_evaluations,project_controls,projects,framework_versions,frameworks,assessment_keyword,assessments,audit_test_keyword,audit_tests,control_keyword,controls,documents,keyword",
    )
    framework = relationship("Framework", foreign_keys=[framework_id], back_populates="keywords")
    framework_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="frameworks",
        overlaps="wbs,tasks,risks,project_evaluations,project_controls,projects,assessment_keyword,assessments,audit_test_keyword,audit_tests,control_keyword,controls,documents,exception_keyword,exceptions,keyword,framework_versions",
    )
    framework_version = relationship(
        "FrameworkVersion",
        foreign_keys=[framework_version_id],
        back_populates="keywords",
    )
    framework_version_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="framework_versions",
        overlaps="wbs,tasks,risks,project_evaluations,project_controls,projects,assessment_keyword,assessments,audit_test_keyword,audit_tests,control_keyword,controls,documents,exception_keyword,exceptions,framework_keyword,frameworks,keyword",
    )
    project = relationship(
        "Project",
        foreign_keys=[project_id],
        back_populates="keywords",
    )
    project_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="projects",
        overlaps="wbs,tasks,risks,project_evaluations,project_controls,framework_version_keyword,framework_versions,assessment_keyword,assessments,audit_test_keyword,audit_tests,control_keyword,controls,documents,exception_keyword,exceptions,framework_keyword,frameworks,keyword",
    )
    project_control = relationship(
        "ProjectControl",
        foreign_keys=[project_control_id],
        back_populates="keywords",
    )
    project_control_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="project_controls",
        overlaps="wbs,tasks,risks,project_evaluations,project_keyword,projects,framework_version_keyword,framework_versions,assessment_keyword,assessments,audit_test_keyword,audit_tests,control_keyword,controls,documents,exception_keyword,exceptions,framework_keyword,frameworks,keyword",
    )
    project_evaluation = relationship(
        "ProjectEvaluation",
        foreign_keys=[project_evaluation_id],
        back_populates="keywords",
    )
    project_evaluation_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="project_evaluations",
        overlaps="wbs,tasks,risks,project_control_keyword,project_controls,project_keyword,projects,framework_version_keyword,framework_versions,assessment_keyword,assessments,audit_test_keyword,audit_tests,control_keyword,controls,documents,exception_keyword,exceptions,framework_keyword,frameworks,keyword",
    )
    risk = relationship(
        "Risk",
        foreign_keys=[risk_id],
        back_populates="keywords",
    )
    risk_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="risks",
        overlaps="wbs,tasks,project_evaluation_keyword,project_evaluations,project_control_keyword,project_controls,project_keyword,projects,framework_version_keyword,framework_versions,assessment_keyword,assessments,audit_test_keyword,audit_tests,control_keyword,controls,documents,exception_keyword,exceptions,framework_keyword,frameworks,keyword",
    )
    task = relationship(
        "Task",
        foreign_keys=[task_id],
        back_populates="keywords",
    )
    task_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="tasks",
        overlaps="wbs,risk_keyword,risks,project_evaluation_keyword,project_evaluations,project_control_keyword,project_controls,project_keyword,projects,framework_version_keyword,framework_versions,assessment_keyword,assessments,audit_test_keyword,audit_tests,control_keyword,controls,documents,exception_keyword,exceptions,framework_keyword,frameworks,keyword",
    )
    wbs = relationship(
        "WBS",
        foreign_keys=[wbs_id],
        back_populates="keywords",
    )
    wbs_keyword = relationship(
        "Keyword",
        foreign_keys=[keyword_id],
        back_populates="tasks",
        overlaps="task_keyword,risk_keyword,risks,project_evaluation_keyword,project_evaluations,project_control_keyword,project_controls,project_keyword,projects,framework_version_keyword,framework_versions,assessment_keyword,assessments,audit_test_keyword,audit_tests,control_keyword,controls,documents,exception_keyword,exceptions,framework_keyword,frameworks,keyword",
    )

    def __repr__(self):
        return f"id: {self.id}, keyword_id: {self.keyword_id}, document_id: {self.document_id}, framework_id: {self.framework_id}, framework_version_id: {self.framework_version_id}, project_id: {self.project_id}, project_control_id: {self.project_control_id}, project_evaluation_id: {self.project_evaluation_id}, risk_id: {self.risk_id}, task_id: {self.task_id}, wbs_id: {self.wbs_id}, assessment_id: {self.assessment_id}, audit_test_id: {self.audit_test_id}, exception_id: {self.exception_id}"


class HelpSection(Base):
    __tablename__ = "help_section"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String, unique=True)
    divId = Column(String, unique=True)
    body = Column(TEXT)
    order = Column(Integer)
    created_date = last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, title: {self.title}"


class AuditTestHistory(Base):
    __tablename__ = "audit_test_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_test_id = Column(Integer, ForeignKey("audit_test.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    audit_test = relationship(
        "AuditTest", foreign_keys=[audit_test_id], back_populates="history_user_audit_test"
    )
    author = relationship("User", foreign_keys=[author_id], back_populates="history_audit_test")

    def __repr__(self):
        return f"id: {self.id}, audit_test_id: {self.audit_test_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class CapPoamHistory(Base):
    __tablename__ = "cap_poam_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cap_poam_id = Column(Integer, ForeignKey("cap_poam.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    cap_poam = relationship(
        "CapPoam", foreign_keys=[cap_poam_id], back_populates="history_user_cap_poam"
    )
    author = relationship("User", foreign_keys=[author_id], back_populates="history_cap_poam")

    def __repr__(self):
        return f"id: {self.id}, cap_poam_id: {self.cap_poam_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class AssessmentHistory(Base):
    __tablename__ = "assessment_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessment.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    assessment = relationship(
        "Assessment", foreign_keys=[assessment_id], back_populates="history_user_assessment"
    )
    author = relationship("User", foreign_keys=[author_id], back_populates="history_assessment")

    def __repr__(self):
        return f"id: {self.id}, assessment_id: {self.assessment_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class ExceptionHistory(Base):
    __tablename__ = "exception_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    exception_id = Column(Integer, ForeignKey("exception.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    exception = relationship(
        "Exception", foreign_keys=[exception_id], back_populates="history_user_exception"
    )
    author = relationship("User", foreign_keys=[author_id], back_populates="history_exception")

    def __repr__(self):
        return f"id: {self.id}, exception_id: {self.exception_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class ProjectControlHistory(Base):
    __tablename__ = "project_control_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_control_id = Column(Integer, ForeignKey("project_control.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    project_control = relationship(
        "ProjectControl",
        foreign_keys=[project_control_id],
        back_populates="history_user_project_control",
    )
    author = relationship(
        "User", foreign_keys=[author_id], back_populates="history_project_control"
    )

    def __repr__(self):
        return f"id: {self.id}, project_control_id: {self.project_control_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class ProjectHistory(Base):
    __tablename__ = "project_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    project = relationship(
        "Project", foreign_keys=[project_id], back_populates="history_user_project"
    )
    author = relationship("User", foreign_keys=[author_id], back_populates="history_project")

    def __repr__(self):
        return f"id: {self.id}, project_id: {self.project_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class RiskHistory(Base):
    __tablename__ = "risk_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    risk_id = Column(Integer, ForeignKey("risk.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    risk = relationship("Risk", foreign_keys=[risk_id], back_populates="history_user_risk")
    author = relationship("User", foreign_keys=[author_id], back_populates="history_risk")

    def __repr__(self):
        return f"id: {self.id}, risk_id: {self.risk_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class ProjectEvaluationHistory(Base):
    __tablename__ = "project_evaluation_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_evaluation_id = Column(Integer, ForeignKey("project_evaluation.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    project_evaluation = relationship(
        "ProjectEvaluation",
        foreign_keys=[project_evaluation_id],
        back_populates="history_user_project_evaluation",
    )
    author = relationship(
        "User", foreign_keys=[author_id], back_populates="history_project_evaluation"
    )

    def __repr__(self):
        return f"id: {self.id}, project_evaluation_id: {self.project_evaluation_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class DocumentHistory(Base):
    __tablename__ = "document_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("document.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    document = relationship(
        "Document", foreign_keys=[document_id], back_populates="history_user_document"
    )
    author = relationship("User", foreign_keys=[author_id], back_populates="history_document")

    def __repr__(self):
        return f"id: {self.id}, document_id: {self.document_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class ProjectTaskHistory(Base):
    __tablename__ = "project_task_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("task.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    task = relationship("Task", foreign_keys=[task_id], back_populates="history_user_task")
    author = relationship("User", foreign_keys=[author_id], back_populates="history_task")

    def __repr__(self):
        return f"id: {self.id}, task_id: {self.task_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class WBSHistory(Base):
    __tablename__ = "wbs_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    wbs_id = Column(Integer, ForeignKey("wbs.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    wbs = relationship("WBS", foreign_keys=[wbs_id], back_populates="history_user_wbs")
    author = relationship("User", foreign_keys=[author_id], back_populates="history_wbs")

    def __repr__(self):
        return f"id: {self.id}, wbs_id: {self.wbs_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class ProjectUserHistory(Base):
    __tablename__ = "project_user_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    assigned_user_id = Column(Integer, ForeignKey("user.id"))
    role = Column(TEXT)
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    project = relationship(
        "Project",
        foreign_keys=[project_id],
        back_populates="history_project_user_project",
    )

    # author = relationship("User", foreign_keys=[author_id], back_populates="history_project_author")
    # assigned_user = relationship("ProjectUser", foreign_keys=[assigned_user_id], back_populates="history_project_assigned")
    def __repr__(self):
        return f"id: {self.id}, project_id: {self.project_id}, author_id: {self.author_id}, assigned_user_id: {self.assigned_user_id}, role: {self.role}, updated: {self.updated}"


class UserWatching(Base):
    __tablename__ = "user_watching"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"))
    user_id = Column(Integer, ForeignKey("user.id"))
    project_overview = Column(Boolean)
    project_controls = Column(Boolean)
    project_assessments = Column(Boolean)
    project_risks = Column(Boolean)
    project_evaluations = Column(Boolean)
    project_audit_tests = Column(Boolean)
    project_documents = Column(Boolean)
    project_users = Column(Boolean)
    project_tasks = Column(Boolean)
    project_wbs = Column(Boolean)
    project_workflow_flowcharts = Column(Boolean)
    project_cap_poams = Column(Boolean)

    def __repr__(self):
        return f"id: {self.id}, project_id: {self.project_id}, user_id: {self.user_id}, project_overview: {self.project_overview}, project_controls: {self.project_controls}, project_assessments: {self.project_assessments}, project_risks: {self.project_risks}, project_evaluations: {self.project_evaluations}, project_audit_tests: {self.project_audit_tests}, project_documents: {self.project_documents}, project_users: {self.project_users}, project_tasks: {self.project_tasks}, project_wbs: {self.project_wbs}, project_cap_poams: {self.project_cap_poams}, project_workflow_flowcharts: {self.project_workflow_flowcharts}"


class UserNotifications(Base):
    __tablename__ = "user_notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    notification_data_type = Column(TEXT)
    notification_data_id = Column(Integer)
    notification_data_path = Column(TEXT)
    notification_message = Column(TEXT)
    project_id = Column(Integer, ForeignKey("project.id"))
    created = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    project = relationship(
        "Project", foreign_keys=[project_id], back_populates="user_notifications_project"
    )

    def __repr__(self):
        return f"id: {self.id}, user_id: {self.user_id}, notification_date_type: {self.notification_data_type}, notification_data_id: {self.notification_data_id}, notification_data_path: {self.notification_data_path}, project_id: {self.project_id}, project: {self.project}"


class UserNotificationSettings(Base):
    __tablename__ = "user_notification_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    watch_email = Column(Boolean)
    watch_sms = Column(Boolean)
    assigned_email = Column(Boolean)
    assigned_sms = Column(Boolean)
    scheduled_email = Column(Boolean)
    scheduled_sms = Column(Boolean)
    upcoming_event_deadline = Column(
        Enum(UpcomingEventDeadline), default=UpcomingEventDeadline.three_days_prior.value
    )

    def __repr__(self):
        return f"id: {self.id}, user_id: {self.user_id}, watch_email: {self.watch_email}, watch_sms: {self.watch_sms}, assigned_email: {self.assigned_email}, assigned_sms: {self.assigned_sms}, upcoming_event_deadline: {self.upcoming_event_deadline}"


class EmailNotifications(Base):
    __tablename__ = "email_notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    email = Column(TEXT)
    message = Column(TEXT)
    created = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, user_id: {self.user_id}, email: {self.email}, message: {self.message}, created: {self.created}"


class SMSNotifications(Base):
    __tablename__ = "sms_notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    phone_no = Column(TEXT)
    message = Column(TEXT)
    created = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, user_id: {self.user_id}, phone_no: {self.phone_no}, message: {self.message}, created: {self.created}"


class ChatBotPrompt(Base):
    __tablename__ = "chat_bot_prompt"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    prompt = Column(TEXT)
    message = Column(TEXT)
    created = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, prompt: {self.prompt}, message: {self.message}, created: {self.created}"


class AWSControl(Base):
    __tablename__ = "aws_control"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    aws_id = Column(TEXT)
    aws_title = Column(TEXT)
    aws_control_status = Column(Enum(AWSControlStatus))
    aws_severity = Column(Enum(AWSSeverity))
    aws_failed_checks = Column(Integer)
    aws_unknown_checks = Column(Integer)
    aws_not_available_checks = Column(Integer)
    aws_passed_checks = Column(Integer)
    aws_related_requirements = Column(TEXT)
    aws_custom_parameters = Column(TEXT)
    created = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    project_controls = relationship("AWSControlProjectControl", back_populates="aws_control")

    def __repr__(self):
        return f"id: {self.id}, aws_id: {self.aws_id}, aws_title: {self.aws_title}, created: {self.created}"


class AWSControlProjectControl(Base):
    __tablename__ = "aws_control_project_control"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    aws_control_id = Column(Integer, ForeignKey("aws_control.id"))
    project_control_id = Column(Integer, ForeignKey("project_control.id"))
    aws_control = relationship(
        "AWSControl", foreign_keys=[aws_control_id], back_populates="project_controls"
    )
    project_control = relationship(
        "ProjectControl", foreign_keys=[project_control_id], back_populates="aws_controls"
    )

    def __repr__(self):
        return f"id: {self.id}, aws_control_id: {self.aws_control_id}, project_control_id: {self.project_control_id}"


class ImportAWSControls(Base):
    __tablename__ = "import_aws_controls"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    file_content_type = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    imported = Column(Boolean)
    import_results = Column(String)

    def __repr__(self):
        return f"id: {self.id}, name: {self.name} file_content_type: {self.file_content_type}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}, tenant_id: {self.tenant_id}, imported: {self.imported}, import_results: {self.import_results}, project_id: {self.project_id}"


class Feature(Base):
    __tablename__ = "feature"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=True)
    is_active = Column(Boolean)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    projects = relationship("FeatureProject", back_populates="feature")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, is_active: {self.is_active}"


class FeatureProject(Base):
    __tablename__ = "feature_project"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    feature_id = Column(Integer, ForeignKey("feature.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean)
    feature = relationship("Feature", foreign_keys=[feature_id], back_populates="projects")
    project = relationship("Project", foreign_keys=[project_id], back_populates="features")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, feature_id: {self.feature_id}, project_id: {self.project_id}, is_active: {self.is_active}"


class ReportingSettings(Base):
    __tablename__ = "reporting_settings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    column_state = Column(JSON)
    pivot_state = Column(Boolean)
    graph_state = Column(JSON)
    # selected_row_state = Column(JSON)
    value_columns = Column(JSON)
    grid_cols = Column(JSON)
    # chart_models = Column(JSON)
    # col_def_user = Column(JSON)
    # saved_cell_ranges = Column(JSON)
    # grid_state = Column(JSON)
    user = relationship("User", foreign_keys=[user_id], back_populates="reporting_settings")

    def __repr__(self):
        return f"id: {self.id}, user_id: {self.user_id}, column_state: {self.column_state}"


class FrameworkTenant(Base):
    __tablename__ = "framework_tenant"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    framework_id = Column(Integer, ForeignKey("framework.id"), nullable=False)
    is_enabled = Column(Boolean)
    tenant = relationship("Tenant", foreign_keys=[tenant_id], back_populates="framework_tenant")
    framework = relationship(
        "Framework", foreign_keys=[framework_id], back_populates="framework_tenant"
    )

    def __repr__(self):
        return f"id: {self.id}, tenant_id: {self.tenant_id}, framework_id: {self.framework_id}, is_enabled: {self.is_enabled}"


class TaskLink(Base):
    __tablename__ = "task_link"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("task.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("task.id"), nullable=False)
    type = Column(Enum(TaskLinkType), default=TaskLinkType.finish_to_start.value)
    sources = relationship(
        "Task",
        foreign_keys=[target_id],
        back_populates="task_link_sources",
        overlaps="task_link_targets",
    )
    targets = relationship(
        "Task",
        foreign_keys=[source_id],
        back_populates="task_link_targets",
        overlaps="task_link_sources",
    )

    def __repr__(self):
        return f"id: {self.id}, source_id: {self.source_id}, target_id: {self.target_id}, type: {self.type}"


class TaskResource(Base):
    __tablename__ = "task_resource"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    task_id = Column(Integer, ForeignKey("task.id"), nullable=False)
    value = Column(Integer)
    resource = relationship("User", foreign_keys=[user_id], back_populates="tasks")
    task = relationship("Task", foreign_keys=[task_id], back_populates="resources")

    def __repr__(self):
        return (
            f"id: {self.id}, user_id: {self.user_id}, task_id: {self.task_id}, value: {self.value}"
        )


class CapPoam(Base):
    __tablename__ = "cap_poam"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    owner = relationship("User", foreign_keys=[owner_id])
    project_id = Column(ForeignKey("project.id", use_alter=True))
    audit_test_id = Column(ForeignKey("audit_test.id", use_alter=True))
    audit_test = relationship("AuditTest", foreign_keys=[audit_test_id])
    project = relationship("Project", foreign_keys=[project_id])
    user_defined_id = Column(String)
    description = Column(TEXT)
    comments = Column(TEXT)
    due_date = Column(Date)
    stakeholders = relationship("User", secondary="cap_poam_stakeholder")
    criticality_rating = Column(Enum(Criticality))
    status = Column(Enum(CapPoamStatus))
    history_user_cap_poam = relationship("CapPoamHistory", back_populates="cap_poam")
    project_controls = relationship("CapPoamProjectControl", back_populates="cap_poam")
    tasks = relationship("CapPoamTask", back_populates="cap_poam")
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    costs = relationship(
        "CapPoamCost",
        back_populates="cap_poam",
    )
    approval_workflows = relationship("CapPoamApprovalWorkflow", back_populates="cap_poam")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, project_id: {self.project_id}, audit_test_id: {self.audit_test_id}, owner_id: {self.owner_id}, user_defined_id: {self.user_defined_id}, description: {self.description}, due_date: {self.due_date}"


class CapPoamStakeHolder(Base):
    __tablename__ = "cap_poam_stakeholder"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cap_poam_id = Column(Integer, ForeignKey("cap_poam.id"))
    user_id = Column(Integer, ForeignKey("user.id"))

    def __repr__(self):
        return f"id: {self.id}, cap_poam_id: {self.cap_poam_id}, user_id: {self.user_id}"


class CapPoamProjectControl(Base):
    __tablename__ = "cap_poam_project_control"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cap_poam_id = Column(Integer, ForeignKey("cap_poam.id"))
    project_control_id = Column(Integer, ForeignKey("project_control.id"))
    cap_poam = relationship(
        "CapPoam", foreign_keys=[cap_poam_id], back_populates="project_controls"
    )
    project_control = relationship(
        "ProjectControl", foreign_keys=[project_control_id], back_populates="cap_poams"
    )

    def __repr__(self):
        return f"id: {self.id}, cap_poam_id: {self.cap_poam_id}, project_control_id: {self.project_control_id}"


class CapPoamTask(Base):
    __tablename__ = "cap_poam_task"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cap_poam_id = Column(Integer, ForeignKey("cap_poam.id"))
    task_id = Column(Integer, ForeignKey("task.id"))
    cap_poam = relationship("CapPoam", foreign_keys=[cap_poam_id], back_populates="tasks")
    task = relationship("Task", foreign_keys=[task_id], back_populates="cap_poams")

    def __repr__(self):
        return f"id: {self.id}, cap_poam_id: {self.cap_poam_id}, task_id: {self.task_id}"


# WorkflowFlowchart Model
class WorkflowFlowchart(Base):
    __tablename__ = "workflow_flowchart"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    node_data = Column(JSON)
    link_data = Column(JSON)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    project_id = Column(Integer, ForeignKey("project.id"))
    project = relationship(
        "Project", foreign_keys=[project_id], back_populates="workflow_flowcharts"
    )
    start_date = Column(Date, nullable=True)
    due_date = Column(Date, nullable=True)
    status = Column(Enum(WorkflowFlowchartStatus), default="not_started")

    costs = relationship("WorkflowFlowchartCost", back_populates="workflow_flowchart")
    events = relationship("WorkflowEvent", back_populates="workflow_flowchart")
    history_user_workflow_flowchart = relationship(
        "WorkflowFlowchartHistory", back_populates="workflow_flowchart"
    )

    # Updated relationship name:
    workflow_task_mappings = relationship(
        "WorkflowTaskMapping", back_populates="workflow_flowchart"
    )

    approval_workflows = relationship(
        "WorkflowFlowchartApprovalWorkflow", back_populates="workflow_flowchart"
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, node_data: {self.node_data}, link_data: {self.link_data}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}, project_id: {self.project_id}, start_date: {self.start_date}, due_date: {self.due_date}, status: {self.status}"


class WorkflowFlowchartHistory(Base):
    __tablename__ = "workflow_flowchart_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workflow_flowchart_id = Column(Integer, ForeignKey("workflow_flowchart.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    workflow_flowchart = relationship(
        "WorkflowFlowchart",
        foreign_keys=[workflow_flowchart_id],
        back_populates="history_user_workflow_flowchart",
    )
    author = relationship(
        "User", foreign_keys=[author_id], back_populates="history_workflow_flowchart"
    )

    def __repr__(self):
        return f"id: {self.id}, workflow_flowchart_id: {self.workflow_flowchart_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class WorkflowEvent(Base):
    __tablename__ = "workflow_event"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    workflow_flowchart_node_id = Column(Integer)
    workflow_flowchart_id = Column(Integer, ForeignKey("workflow_flowchart.id"))
    trigger_logic = Column(JSON)
    event_config = Column(JSON)

    workflow_flowchart = relationship(
        "WorkflowFlowchart",
        foreign_keys=[workflow_flowchart_id],
        back_populates="events",
    )

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    logs = relationship(
        "WorkflowEventLog",
        back_populates="workflow_event",
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, workflow_flowchart_node_id: {self.workflow_flowchart_node_id}, workflow_flowchart_id: {self.workflow_flowchart_id}, trigger_logic: {self.trigger_logic}, event_config: {self.event_config}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}, tenant_id: {self.tenant_id}"


class WorkflowEventLog(Base):
    __tablename__ = "workflow_event_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workflow_event_id = Column(Integer, ForeignKey("workflow_event.id"))
    event_type = Column(String)
    event_description = Column(JSON)
    link = Column(String)

    workflow_event = relationship(
        "WorkflowEvent",
        foreign_keys=[workflow_event_id],
        back_populates="logs",
    )

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())

    def __repr__(self):
        return f"id: {self.id}, workflow_event_id: {self.workflow_event_id}, event_type: {self.event_type}, event_description: {self.event_description}, link: {self.link}, created_date: {self.created_date}"


# Association Table: WorkflowTaskMapping
class WorkflowTaskMapping(Base):
    __tablename__ = "workflow_task_mapping"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workflow_flowchart_id = Column(Integer, ForeignKey("workflow_flowchart.id"))
    task_id = Column(Integer, ForeignKey("task.id"))

    # Use a consistent attribute name on both sides:
    task = relationship(
        "Task",
        foreign_keys=[task_id],
        back_populates="workflow_task_mappings",
    )

    workflow_flowchart = relationship(
        "WorkflowFlowchart",
        foreign_keys=[workflow_flowchart_id],
        back_populates="workflow_task_mappings",
    )

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())

    def __repr__(self):
        return f"id: {self.id}, workflow_flowchart_id: {self.workflow_flowchart_id}, task_id: {self.task_id}, created_date: {self.created_date}"


class WorkflowTemplate(Base):
    __tablename__ = "workflow_template"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    node_data = Column(JSON)
    link_data = Column(JSON)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    events = relationship(
        "WorkflowTemplateEvent",
        back_populates="workflow_template",
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, description: {self.description}, node_data: {self.node_data}, link_data: {self.link_data}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}, tenant_id: {self.tenant_id}"


class WorkflowTemplateEvent(Base):
    __tablename__ = "workflow_template_event"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    workflow_template_node_id = Column(Integer)
    workflow_template_id = Column(Integer, ForeignKey("workflow_template.id"))
    trigger_logic = Column(JSON)
    event_config = Column(JSON)

    workflow_template = relationship(
        "WorkflowTemplate",
        foreign_keys=[workflow_template_id],
        back_populates="events",
    )

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, workflow_template_node_id: {self.workflow_template_node_id}, workflow_template_id: {self.workflow_template_id}, trigger_logic: {self.trigger_logic}, event_config: {self.event_config}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}, tenant_id: {self.tenant_id}"


class TaskStatus(Base):
    """Used for Dropdown for Status on Task Form
    - Initial Values:
        Not Started
        In Progress
        Completed
        Cancelled
    """

    __tablename__ = "task_status"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=False)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    task = relationship("Task", back_populates="task_status")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class Cost(Base):
    """Used for costs"""

    __tablename__ = "cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=False)
    description = Column(String)
    price = Column(Float)
    currency = Column(String)
    quantity = Column(Integer)
    sales_tax = Column(String)
    rn_number = Column(String)
    serial_number = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    assessment_costs = relationship(
        "AssessmentCost", back_populates="cost", cascade="all, delete-orphan"
    )
    audit_test_costs = relationship(
        "AuditTestCost", back_populates="cost", cascade="all, delete-orphan"
    )
    cap_poam_costs = relationship(
        "CapPoamCost", back_populates="cost", cascade="all, delete-orphan"
    )
    exception_costs = relationship(
        "ExceptionCost", back_populates="cost", cascade="all, delete-orphan"
    )
    project_costs = relationship("ProjectCost", back_populates="cost", cascade="all, delete-orphan")
    project_evaluation_costs = relationship(
        "ProjectEvaluationCost", back_populates="cost", cascade="all, delete-orphan"
    )
    project_control_costs = relationship(
        "ProjectControlCost", back_populates="cost", cascade="all, delete-orphan"
    )
    risk_costs = relationship("RiskCost", back_populates="cost", cascade="all, delete-orphan")
    task_costs = relationship("TaskCost", back_populates="cost", cascade="all, delete-orphan")
    workflow_flowchart_costs = relationship(
        "WorkflowFlowchartCost", back_populates="cost", cascade="all, delete-orphan"
    )
    wbs_costs = relationship("WBSCost", back_populates="cost", cascade="all, delete-orphan")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}"


class TaskCost(Base):
    __tablename__ = "task_cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("task.id"), nullable=False)
    cost_id = Column(Integer, ForeignKey("cost.id"), nullable=False)
    task = relationship("Task", foreign_keys=[task_id], back_populates="costs")
    cost = relationship("Cost", foreign_keys=[cost_id], back_populates="task_costs")

    def __repr__(self):
        return f"id: {self.id}, task_id: {self.task_id}, cost_id: {self.cost_id}"


class AuditTestCost(Base):
    __tablename__ = "audit_test_cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_test_id = Column(Integer, ForeignKey("audit_test.id"), nullable=False)
    cost_id = Column(Integer, ForeignKey("cost.id"), nullable=False)
    audit_test = relationship("AuditTest", foreign_keys=[audit_test_id], back_populates="costs")
    cost = relationship("Cost", foreign_keys=[cost_id], back_populates="audit_test_costs")

    def __repr__(self):
        return f"id: {self.id}, audit_test_id: {self.audit_test_id}, cost_id: {self.cost_id}"


class RiskCost(Base):
    __tablename__ = "risk_cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    risk_id = Column(Integer, ForeignKey("risk.id"), nullable=False)
    cost_id = Column(Integer, ForeignKey("cost.id"), nullable=False)
    risk = relationship("Risk", foreign_keys=[risk_id], back_populates="costs")
    cost = relationship("Cost", foreign_keys=[cost_id], back_populates="risk_costs")

    def __repr__(self):
        return f"id: {self.id}, risk_id: {self.risk_id}, cost_id: {self.cost_id}"


class ProjectCost(Base):
    __tablename__ = "project_cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    cost_id = Column(Integer, ForeignKey("cost.id"), nullable=False)
    project = relationship("Project", foreign_keys=[project_id], back_populates="costs")
    cost = relationship("Cost", foreign_keys=[cost_id], back_populates="project_costs")

    def __repr__(self):
        return f"id: {self.id}, project_id: {self.project_id}, cost_id: {self.cost_id}"


class ExceptionCost(Base):
    __tablename__ = "exception_cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    exception_id = Column(Integer, ForeignKey("exception.id"), nullable=False)
    cost_id = Column(Integer, ForeignKey("cost.id"), nullable=False)
    exception = relationship("Exception", foreign_keys=[exception_id], back_populates="costs")
    cost = relationship("Cost", foreign_keys=[cost_id], back_populates="exception_costs")

    def __repr__(self):
        return f"id: {self.id}, exception_id: {self.exception_id}, cost_id: {self.cost_id}"


class AssessmentCost(Base):
    __tablename__ = "assessment_cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessment.id"), nullable=False)
    cost_id = Column(Integer, ForeignKey("cost.id"), nullable=False)
    assessment = relationship("Assessment", foreign_keys=[assessment_id], back_populates="costs")
    cost = relationship("Cost", foreign_keys=[cost_id], back_populates="assessment_costs")

    def __repr__(self):
        return f"id: {self.id}, assessment_id: {self.assessment_id}, cost_id: {self.cost_id}"


class ProjectControlCost(Base):
    __tablename__ = "project_control_cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_control_id = Column(Integer, ForeignKey("project_control.id"), nullable=False)
    cost_id = Column(Integer, ForeignKey("cost.id"), nullable=False)
    project_control = relationship(
        "ProjectControl", foreign_keys=[project_control_id], back_populates="costs"
    )
    cost = relationship("Cost", foreign_keys=[cost_id], back_populates="project_control_costs")

    def __repr__(self):
        return (
            f"id: {self.id}, project_control_id: {self.project_control_id}, cost_id: {self.cost_id}"
        )


class WBSCost(Base):
    __tablename__ = "wbs_cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    wbs_id = Column(Integer, ForeignKey("wbs.id"), nullable=False)
    cost_id = Column(Integer, ForeignKey("cost.id"), nullable=False)
    wbs = relationship("WBS", foreign_keys=[wbs_id], back_populates="costs")
    cost = relationship("Cost", foreign_keys=[cost_id], back_populates="wbs_costs")

    def __repr__(self):
        return f"id: {self.id}, wbs_id: {self.wbs_id}, cost_id: {self.cost_id}"


class WorkflowFlowchartCost(Base):
    __tablename__ = "workflow_flowchart_cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workflow_flowchart_id = Column(Integer, ForeignKey("workflow_flowchart.id"), nullable=False)
    cost_id = Column(Integer, ForeignKey("cost.id"), nullable=False)
    workflow_flowchart = relationship(
        "WorkflowFlowchart", foreign_keys=[workflow_flowchart_id], back_populates="costs"
    )
    cost = relationship("Cost", foreign_keys=[cost_id], back_populates="workflow_flowchart_costs")

    def __repr__(self):
        return f"id: {self.id}, workflow_flowchart_id: {self.workflow_flowchart_id}, cost_id: {self.cost_id}"


class CapPoamCost(Base):
    __tablename__ = "cap_poam_cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cap_poam_id = Column(Integer, ForeignKey("cap_poam.id"), nullable=False)
    cost_id = Column(Integer, ForeignKey("cost.id"), nullable=False)
    cap_poam = relationship("CapPoam", foreign_keys=[cap_poam_id], back_populates="costs")
    cost = relationship("Cost", foreign_keys=[cost_id], back_populates="cap_poam_costs")

    def __repr__(self):
        return f"id: {self.id}, cap_poam_id: {self.cap_poam_id}, cost_id: {self.cost_id}"


class ProjectEvaluationCost(Base):
    __tablename__ = "project_evaluation_cost"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_evaluation_id = Column(Integer, ForeignKey("project_evaluation.id"), nullable=False)
    cost_id = Column(Integer, ForeignKey("cost.id"), nullable=False)
    project_evaluation = relationship(
        "ProjectEvaluation", foreign_keys=[project_evaluation_id], back_populates="costs"
    )
    cost = relationship("Cost", foreign_keys=[cost_id], back_populates="project_evaluation_costs")

    def __repr__(self):
        return f"id: {self.id}, project_evaluation_id: {self.project_evaluation_id}, cost_id: {self.cost_id}"


# Approvals Workflows


class ApprovalWorkflowTemplate(Base):
    __tablename__ = "approval_workflow_template"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=False)
    description = Column(String)
    approvals = Column(JSON)
    stakeholders = Column(JSON)
    due_date = Column(Date, nullable=True)
    is_private = Column(Boolean, nullable=True)
    digital_signature = Column(Boolean, nullable=True)
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, description: {self.description}, approvals: {self.approvals}, stakeholders: {self.stakeholders}, due_date: {self.due_date}, is_private: {self.is_private}, owner_id: {self.owner_id}, tenant_id: {self.tenant_id}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}"


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, unique=False)
    description = Column(String)
    status = Column(Enum(ApprovalWorkflowStatus), default="not_started")
    due_date = Column(Date, nullable=True)
    is_private = Column(Boolean, nullable=True)
    digital_signature = Column(Boolean, nullable=True)
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    owner = relationship("User")
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    history_user_approval_workflow = relationship(
        "ApprovalWorkflowHistory", back_populates="approval_workflow"
    )

    approvals = relationship("Approval", back_populates="approval_workflow")

    approval_stakeholders = relationship("ApprovalStakeholder", back_populates="approval_workflow")

    tasks = relationship("TaskApprovalWorkflow", back_populates="approval_workflow")
    risks = relationship("RiskApprovalWorkflow", back_populates="approval_workflow")
    audit_tests = relationship("AuditTestApprovalWorkflow", back_populates="approval_workflow")
    assessments = relationship("AssessmentApprovalWorkflow", back_populates="approval_workflow")
    exceptions = relationship("ExceptionApprovalWorkflow", back_populates="approval_workflow")
    documents = relationship("DocumentApprovalWorkflow", back_populates="approval_workflow")
    cap_poams = relationship("CapPoamApprovalWorkflow", back_populates="approval_workflow")
    wbss = relationship("WBSApprovalWorkflow", back_populates="approval_workflow")
    workflow_flowcharts = relationship(
        "WorkflowFlowchartApprovalWorkflow", back_populates="approval_workflow"
    )
    projects = relationship("ProjectApprovalWorkflow", back_populates="approval_workflow")
    project_evaluations = relationship(
        "ProjectEvaluationApprovalWorkflow", back_populates="approval_workflow"
    )
    project_controls = relationship(
        "ProjectControlApprovalWorkflow", back_populates="approval_workflow"
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, description: {self.description}, status: {self.status}, due_date: {self.due_date}, is_private: {self.is_private}, digital_signature: {self.digital_signature}, owner_id: {self.owner_id}, tenant_id: {self.tenant_id}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}"


class ApprovalWorkflowHistory(Base):
    __tablename__ = "approval_workflow_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"))
    author_id = Column(Integer, ForeignKey("user.id"))
    history = Column(TEXT)
    updated = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    approval_workflow = relationship(
        "ApprovalWorkflow",
        foreign_keys=[approval_workflow_id],
        back_populates="history_user_approval_workflow",
    )
    author = relationship(
        "User", foreign_keys=[author_id], back_populates="history_approval_workflow"
    )

    def __repr__(self):
        return f"id: {self.id}, approval_workflow_id: {self.approval_workflow_id}, author_id: {self.author_id}, history: {self.history}, updated: {self.updated}"


class Approval(Base):
    __tablename__ = "approval"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"))
    approval_workflow = relationship(
        "ApprovalWorkflow", foreign_keys=[approval_workflow_id], back_populates="approvals"
    )
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")
    status = Column(Enum(ApprovalStatus), nullable=True)
    weight = Column(Integer)
    completed_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    approval_digital_signature = relationship(
        "ApprovalDigitalSignature", uselist=False, back_populates="approval"
    )

    def __repr__(self):
        return f"id: {self.id}, approval_workflow_id: {self.approval_workflow_id}, user_id: {self.user_id}, status: {self.status}, weight: {self.weight}, completed_date: {self.completed_date}"


class ApprovalStakeholder(Base):
    __tablename__ = "approval_stakeholder"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"))
    approval_workflow = relationship(
        "ApprovalWorkflow",
        foreign_keys=[approval_workflow_id],
        back_populates="approval_stakeholders",
    )
    user_id = Column(Integer, ForeignKey("user.id"))
    user = relationship("User")
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, approval_workflow_id: {self.approval_workflow_id}, user_id: {self.user_id}, created_date: {self.created_date}"


class TaskApprovalWorkflow(Base):
    __tablename__ = "task_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("task.id"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    task = relationship("Task", foreign_keys=[task_id], back_populates="approval_workflows")
    approval_workflow = relationship(
        "ApprovalWorkflow", foreign_keys=[approval_workflow_id], back_populates="tasks"
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, task_id: {self.task_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class RiskApprovalWorkflow(Base):
    __tablename__ = "risk_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    risk_id = Column(Integer, ForeignKey("risk.id"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    risk = relationship("Risk", foreign_keys=[risk_id], back_populates="approval_workflows")
    approval_workflow = relationship(
        "ApprovalWorkflow", foreign_keys=[approval_workflow_id], back_populates="risks"
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, risk_id: {self.risk_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class AuditTestApprovalWorkflow(Base):
    __tablename__ = "audit_test_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_test_id = Column(Integer, ForeignKey("audit_test.id"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    audit_test = relationship(
        "AuditTest", foreign_keys=[audit_test_id], back_populates="approval_workflows"
    )
    approval_workflow = relationship(
        "ApprovalWorkflow", foreign_keys=[approval_workflow_id], back_populates="audit_tests"
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, audit_test_id: {self.audit_test_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class AssessmentApprovalWorkflow(Base):
    __tablename__ = "assessment_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    assessment_id = Column(Integer, ForeignKey("assessment.id"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    assessment = relationship(
        "Assessment", foreign_keys=[assessment_id], back_populates="approval_workflows"
    )
    approval_workflow = relationship(
        "ApprovalWorkflow", foreign_keys=[approval_workflow_id], back_populates="assessments"
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, assessment_id: {self.assessment_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class ExceptionApprovalWorkflow(Base):
    __tablename__ = "exception_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    exception_id = Column(Integer, ForeignKey("exception.id"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    exception = relationship(
        "Exception", foreign_keys=[exception_id], back_populates="approval_workflows"
    )
    approval_workflow = relationship(
        "ApprovalWorkflow", foreign_keys=[approval_workflow_id], back_populates="exceptions"
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, exception_id: {self.exception_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class DocumentApprovalWorkflow(Base):
    __tablename__ = "document_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("document.id"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    document = relationship(
        "Document", foreign_keys=[document_id], back_populates="approval_workflows"
    )
    approval_workflow = relationship(
        "ApprovalWorkflow", foreign_keys=[approval_workflow_id], back_populates="documents"
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, document_id: {self.document_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class CapPoamApprovalWorkflow(Base):
    __tablename__ = "cap_poam_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    cap_poam_id = Column(Integer, ForeignKey("cap_poam.id"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    cap_poam = relationship(
        "CapPoam", foreign_keys=[cap_poam_id], back_populates="approval_workflows"
    )
    approval_workflow = relationship(
        "ApprovalWorkflow", foreign_keys=[approval_workflow_id], back_populates="cap_poams"
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, cap_poam_id: {self.cap_poam_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class WBSApprovalWorkflow(Base):
    __tablename__ = "wbs_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    wbs_id = Column(Integer, ForeignKey("wbs.id"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    wbs = relationship("WBS", foreign_keys=[wbs_id], back_populates="approval_workflows")
    approval_workflow = relationship(
        "ApprovalWorkflow", foreign_keys=[approval_workflow_id], back_populates="wbss"
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, wbs_id: {self.wbs_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class WorkflowFlowchartApprovalWorkflow(Base):
    __tablename__ = "workflow_flowchart_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    workflow_flowchart_id = Column(Integer, ForeignKey("workflow_flowchart.id"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    workflow_flowchart = relationship(
        "WorkflowFlowchart",
        foreign_keys=[workflow_flowchart_id],
        back_populates="approval_workflows",
    )
    approval_workflow = relationship(
        "ApprovalWorkflow",
        foreign_keys=[approval_workflow_id],
        back_populates="workflow_flowcharts",
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, workflow_flowchart_id: {self.workflow_flowchart_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class ProjectApprovalWorkflow(Base):
    __tablename__ = "project_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    project = relationship(
        "Project", foreign_keys=[project_id], back_populates="approval_workflows"
    )
    approval_workflow = relationship(
        "ApprovalWorkflow", foreign_keys=[approval_workflow_id], back_populates="projects"
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, project_id: {self.project_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class ProjectEvaluationApprovalWorkflow(Base):
    __tablename__ = "project_evaluation_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_evaluation_id = Column(Integer, ForeignKey("project_evaluation.id"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    project_evaluation = relationship(
        "ProjectEvaluation",
        foreign_keys=[project_evaluation_id],
        back_populates="approval_workflows",
    )
    approval_workflow = relationship(
        "ApprovalWorkflow",
        foreign_keys=[approval_workflow_id],
        back_populates="project_evaluations",
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, project_evaluation_id: {self.project_evaluation_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class ProjectControlApprovalWorkflow(Base):
    __tablename__ = "project_control_approval_workflow"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_control_id = Column(Integer, ForeignKey("project_control.id"), nullable=False)
    approval_workflow_id = Column(Integer, ForeignKey("approval_workflow.id"), nullable=False)
    project_control = relationship(
        "ProjectControl",
        foreign_keys=[project_control_id],
        back_populates="approval_workflows",
    )
    approval_workflow = relationship(
        "ApprovalWorkflow",
        foreign_keys=[approval_workflow_id],
        back_populates="project_controls",
    )
    created_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )

    def __repr__(self):
        return f"id: {self.id}, project_control_id: {self.project_control_id}, approval_workflow_id: {self.approval_workflow_id}, created_date: {self.created_date}"


class SurveyTemplate(Base):
    __tablename__ = "survey_template"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    survey_json = Column(JSON)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    def __repr__(self):
        return f"id: {self.id}, name: {self.name},  survey_json: {self.survey_json}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}, tenant_id: {self.tenant_id}"


class SurveyModel(Base):
    __tablename__ = "survey_model"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    survey_json = Column(JSON)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    published = Column(Boolean, default=False)
    project = relationship(
        "Project",
        foreign_keys=[project_id],
        back_populates="surveys",
    )
    responses = relationship(
        "SurveyResponse",
        back_populates="survey_model",
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name},  survey_json: {self.survey_json}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}, project_id: {self.project_id}, published: {self.published}"


class SurveyResponse(Base):
    __tablename__ = "survey_response"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    # name = Column(String)
    survey_response = Column(JSON)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="surveys",
    )
    survey_model_id = Column(Integer, ForeignKey("survey_model.id"), nullable=False)

    survey_model = relationship(
        "SurveyModel",
        foreign_keys=[survey_model_id],
        back_populates="responses",
    )
    test = Column(Boolean, default=True)

    def __repr__(self):
        return f"id: {self.id}, survey_response: {self.survey_response}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}, user_id: {self.user_id}, survey_model_id: {self.survey_model_id}, test: {self.test}"


class Evidence(Base):
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    machine_readable = Column(JSON)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    last_updated_date = Column(
        DateTime, nullable=False, server_default=current_timestamp(), onupdate=current_timestamp()
    )
    project_controls = relationship("ProjectControlEvidence", back_populates="evidence")

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, description: {self.description}, machine_readable: {self.machine_readable}, created_date: {self.created_date}, last_updated_date: {self.last_updated_date}"


class ProjectControlEvidence(Base):
    __tablename__ = "project_control_evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())

    project_control_id = Column(Integer, ForeignKey("project_control.id"), nullable=False)
    project_control = relationship(
        "ProjectControl",
        foreign_keys=[project_control_id],
        back_populates="evidence",
    )

    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)

    evidence = relationship(
        "Evidence",
        foreign_keys=[evidence_id],
        back_populates="project_controls",
    )

    def __repr__(self):
        return f"id: {self.id}, created_date: {self.created_date}, project_control_id: {self.project_control_id}, evidence_id: {self.evidence_id}"


class DigitalSignature(Base):
    __tablename__ = "digital_signature"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String)
    checksum = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())

    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    user = relationship("User")

    approval_digital_signature = relationship(
        "ApprovalDigitalSignature", back_populates="digital_signature"
    )

    audit_evidence_review_dig_sig = relationship(
        "AuditEvidenceReviewDigSig",
        back_populates="digital_signature",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return (
            f"id: {self.id}, created_date: {self.created_date}, "
            f"user_id: {self.user_id}, user: {self.user}"
        )


class ApprovalDigitalSignature(Base):
    __tablename__ = "approval_digital_signature"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())

    approval_id = Column(Integer, ForeignKey("approval.id"), nullable=False)

    approval = relationship(
        "Approval",
        foreign_keys=[approval_id],
        back_populates="approval_digital_signature",
    )

    digital_signature_id = Column(Integer, ForeignKey("digital_signature.id"), nullable=False)

    digital_signature = relationship(
        "DigitalSignature",
        foreign_keys=[digital_signature_id],
        back_populates="approval_digital_signature",
    )

    def __repr__(self):
        return f"id: {self.id}, created_date: {self.created_date}, approval_id: {self.approval_id}, digital_signature_id: {self.digital_signature_id}"


# Service Provider
class ServiceProvider(Base):
    __tablename__ = "service_provider"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    contact_email = Column(String)
    contact_phone = Column(String)
    business_type = Column(String)
    category = Column(String)
    category_type = Column(String)
    hosting_environment = Column(String)
    owner = Column(String)
    parent_company = Column(String)
    certification = Column(String)
    license = Column(String)

    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())

    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    service_provider_apps = relationship(
        "ServiceProviderApp", back_populates="service_provider", cascade="all, delete-orphan"
    )

    service_provider_addresses = relationship(
        "ServiceProviderAddress", back_populates="service_provider", cascade="all, delete-orphan"
    )

    service_provider_project_controls = relationship(
        "ServiceProviderProjectControl",
        back_populates="service_provider",
        cascade="all, delete-orphan",
    )

    service_provider_projects = relationship(
        "ServiceProviderProject",
        back_populates="service_provider",
        cascade="all, delete-orphan",
    )

    audit_evidence_service_provider = relationship(
        "AuditEvidenceFilterServiceProvider",
        back_populates="service_provider",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, contact_email: {self.contact_email}, contact_phone: {self.contact_phone}, business_type: {self.business_type}, category: {self.category}, category_type: {self.category_type}, owner: {self.owner}, parent_company: {self.parent_company}, certification: {self.certification}, license: {self.license}, created_date: {self.created_date}"


# Address
class Address(Base):
    __tablename__ = "address"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    street_address_1 = Column(String)
    street_address_2 = Column(String)
    city = Column(String)
    zip_code = Column(String)
    country_code = Column(String)
    region = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())

    service_provider_addresses = relationship(
        "ServiceProviderAddress", back_populates="address", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"id: {self.id}, street_address_1: {self.street_address_1}, street_address_2: {self.street_address_2}, city: {self.city}, zip_code: {self.zip_code}, country_code: {self.country_code}, region: {self.region}, created_date: {self.created_date}"


# App
class App(Base):
    __tablename__ = "app"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String)
    description = Column(String)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())

    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    service_provider_apps = relationship(
        "ServiceProviderApp", back_populates="app", cascade="all, delete-orphan"
    )

    app_project_controls = relationship(
        "AppProjectControl",
        back_populates="app",
        cascade="all, delete-orphan",
    )

    app_projects = relationship(
        "AppProject",
        back_populates="app",
        cascade="all, delete-orphan",
    )

    audit_evidence_app = relationship(
        "AuditEvidenceFilterApp",
        back_populates="app",
        cascade="all, delete-orphan",
    )

    def __repr__(self):
        return f"id: {self.id}, name: {self.name}, description: {self.description}, created_date: {self.created_date}"


# Service Provider → App
class ServiceProviderApp(Base):
    __tablename__ = "service_provider_app"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    service_provider_id = Column(Integer, ForeignKey("service_provider.id"), nullable=False)
    service_provider = relationship(
        "ServiceProvider",
        foreign_keys=[service_provider_id],
        back_populates="service_provider_apps",
    )
    app_id = Column(Integer, ForeignKey("app.id"), nullable=False)
    app = relationship(
        "App",
        foreign_keys=[app_id],
        back_populates="service_provider_apps",
    )

    def __repr__(self):
        return f"id: {self.id}, created_date: {self.created_date}, service_provider_id: {self.service_provider_id}, app_id: {self.app_id}"


# Service Provider → Address
class ServiceProviderAddress(Base):
    __tablename__ = "service_provider_address"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    service_provider_id = Column(Integer, ForeignKey("service_provider.id"), nullable=False)
    service_provider = relationship(
        "ServiceProvider",
        foreign_keys=[service_provider_id],
        back_populates="service_provider_addresses",
    )
    address_id = Column(Integer, ForeignKey("address.id"), nullable=False)
    address = relationship(
        "Address",
        foreign_keys=[address_id],
        back_populates="service_provider_addresses",
    )

    def __repr__(self):
        return f"id: {self.id}, created_date: {self.created_date}, service_provider_id: {self.service_provider_id}, address_id: {self.address_id}"


# Service Provider → Project
class ServiceProviderProject(Base):
    __tablename__ = "service_provider_project"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    service_provider_id = Column(Integer, ForeignKey("service_provider.id"), nullable=False)
    service_provider = relationship(
        "ServiceProvider",
        foreign_keys=[service_provider_id],
        back_populates="service_provider_projects",
    )
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    project = relationship(
        "Project",
        foreign_keys=[project_id],
        back_populates="service_provider_projects",
    )

    def __repr__(self):
        return f"id: {self.id}, created_date: {self.created_date}, service_provider_id: {self.service_provider_id}, project_id: {self.project_id}"


# Service Provider → Project Control
class ServiceProviderProjectControl(Base):
    __tablename__ = "service_provider_project_control"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    service_provider_id = Column(Integer, ForeignKey("service_provider.id"), nullable=False)
    service_provider = relationship(
        "ServiceProvider",
        foreign_keys=[service_provider_id],
        back_populates="service_provider_project_controls",
    )
    project_control_id = Column(Integer, ForeignKey("project_control.id"), nullable=False)
    project_control = relationship(
        "ProjectControl",
        foreign_keys=[project_control_id],
        back_populates="service_provider_project_controls",
    )

    def __repr__(self):
        return f"id: {self.id}, created_date: {self.created_date}, service_provider_id: {self.service_provider_id}, project_control_id: {self.project_control_id}"


# App → Project Control
class AppProjectControl(Base):
    __tablename__ = "app_project_control"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    app_id = Column(Integer, ForeignKey("app.id"), nullable=False)
    app = relationship(
        "App",
        foreign_keys=[app_id],
        back_populates="app_project_controls",
    )
    project_control_id = Column(Integer, ForeignKey("project_control.id"), nullable=False)
    project_control = relationship(
        "ProjectControl",
        foreign_keys=[project_control_id],
        back_populates="app_project_controls",
    )

    def __repr__(self):
        return f"id: {self.id}, created_date: {self.created_date}, app_id: {self.app_id}, project_control_id: {self.project_control_id}"


# App → Project
class AppProject(Base):
    __tablename__ = "app_project"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_date = Column(DateTime, nullable=False, server_default=current_timestamp())
    app_id = Column(Integer, ForeignKey("app.id"), nullable=False)
    app = relationship(
        "App",
        foreign_keys=[app_id],
        back_populates="app_projects",
    )
    project_id = Column(Integer, ForeignKey("project.id", ondelete="CASCADE"), nullable=False)
    project = relationship(
        "Project",
        foreign_keys=[project_id],
        back_populates="app_projects",
    )

    def __repr__(self):
        return f"id: {self.id}, created_date: {self.created_date}, app_id: {self.app_id}, project_id: {self.project_id}"


# Audit Evidence
class AuditEvidence(Base):
    __tablename__ = "audit_evidence"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    external_organization = Column(String)
    submission_user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    rationale = Column(String)
    commercial_audit_type = Column(String)
    auditor_user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    submission_version = Column(String)
    cc_emails = Column(String)
    auditor_name = Column(String)

    submitted_on = Column(DateTime, nullable=False, server_default=current_timestamp())
    tenant_id = Column(Integer, ForeignKey("tenant.id"), nullable=False)

    # Relationships
    auditor_submitter = relationship(
        "User",
        back_populates="audit_evidence_submitter",
        foreign_keys=[submission_user_id],
    )

    auditor_user = relationship(
        "User",
        back_populates="audit_evidence_auditor",
        foreign_keys=[auditor_user_id],
    )

    audit_evidence_app = relationship(
        "AuditEvidenceFilterApp",
        back_populates="audit_evidence",
        cascade="all, delete-orphan",
    )

    audit_evidence_service_provider = relationship(
        "AuditEvidenceFilterServiceProvider",
        back_populates="audit_evidence",
        cascade="all, delete-orphan",
    )

    audit_evidence_project = relationship(
        "AuditEvidenceFilterProject",
        back_populates="audit_evidence",
        cascade="all, delete-orphan",
    )

    audit_evidence_framework = relationship(
        "AuditEvidenceFilterFramework",
        back_populates="audit_evidence",
        cascade="all, delete-orphan",
    )

    # ✅ Add this relationship to expose AuditEvidenceReview
    audit_evidence_review = relationship(
        "AuditEvidenceReview", uselist=False, backref="audit_evidence", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return (
            f"id: {self.id}, external_organization: {self.external_organization}, "
            f"rationale: {self.rationale}, commercial_audit_type: {self.commercial_audit_type}, "
            f"auditor_user_id: {self.auditor_user_id}, submission_user_id: {self.submission_user_id}, "
            f"cc_emails: {self.cc_emails}, auditor_name: {self.auditor_name}, "
            f"submission_version: {self.submission_version}, submitted_on: {self.submitted_on}"
        )


# Audit Evidence Review
class AuditEvidenceReview(Base):
    __tablename__ = "audit_evidence_review"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_evidence_id = Column(Integer, ForeignKey("audit_evidence.id"), nullable=False)
    assessment_summary = Column(String)
    approved = Column(Boolean)
    reviewed_on = Column(DateTime, nullable=False, server_default=current_timestamp())

    audit_evidence_review_dig_sig = relationship(
        "AuditEvidenceReviewDigSig",
        back_populates="audit_evidence_review",
        cascade="all, delete-orphan",
        uselist=False,  # If one-to-one (one sig per review)
    )

    def __repr__(self):
        return (
            f"id: {self.id}, audit_evidence_id: {self.audit_evidence_id}, "
            f"assessment_summary: {self.assessment_summary}, approved: {self.approved}, "
            f"reviewed_on: {self.reviewed_on}"
        )


# Audit Evidence Review Project Control
class AuditEvidenceReviewProjectControl(Base):
    __tablename__ = "audit_evidence_review_project_control"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_evidence_id = Column(Integer, ForeignKey("audit_evidence.id"), nullable=False)
    project_control_id = Column(Integer, ForeignKey("project_control.id"), nullable=False)
    evidence_id = Column(Integer, ForeignKey("evidence.id"), nullable=False)
    assessment_summary = Column(String)
    approved = Column(Boolean)
    reviewed_on = Column(DateTime, nullable=False, server_default=current_timestamp())

    def __repr__(self):
        return f"id: {self.id}, audit_evidence_id: {self.audit_evidence_id}, project_control_id: {self.project_control_id}, evidence_id: {self.evidence_id}, assessment_summary: {self.assessment_summary}, approved: {self.approved}, reviewed_on: {self.reviewed_on}"


# Mapping Filters for Audit Evidence


# Audit Evidence Filter App
class AuditEvidenceFilterApp(Base):
    __tablename__ = "audit_evidence_filter_app"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_evidence_id = Column(Integer, ForeignKey("audit_evidence.id"), nullable=False)
    app_id = Column(Integer, ForeignKey("app.id"), nullable=False)

    audit_evidence = relationship(
        "AuditEvidence",
        foreign_keys=[audit_evidence_id],  # ✅ Correct foreign key
        back_populates="audit_evidence_app",
    )
    app = relationship(
        "App",
        foreign_keys=[app_id],
        back_populates="audit_evidence_app",
    )

    def __repr__(self):
        return f"id: {self.id}, audit_evidence_id: {self.audit_evidence_id}, app_id: {self.app_id}"


# Audit Evidence Filter Service Provider
class AuditEvidenceFilterServiceProvider(Base):
    __tablename__ = "audit_evidence_filter_service_provider"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_evidence_id = Column(Integer, ForeignKey("audit_evidence.id"), nullable=False)
    service_provider_id = Column(Integer, ForeignKey("service_provider.id"), nullable=False)

    audit_evidence = relationship(
        "AuditEvidence",
        foreign_keys=[audit_evidence_id],  # ✅ Correct foreign key
        back_populates="audit_evidence_service_provider",
    )

    service_provider = relationship(
        "ServiceProvider",
        foreign_keys=[service_provider_id],
        back_populates="audit_evidence_service_provider",
    )

    def __repr__(self):
        return f"id: {self.id}, audit_evidence_id: {self.audit_evidence_id}, service_provider_id: {self.service_provider_id}"


# Audit Evidence Filter Project
class AuditEvidenceFilterProject(Base):
    __tablename__ = "audit_evidence_filter_project"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_evidence_id = Column(Integer, ForeignKey("audit_evidence.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)

    audit_evidence = relationship(
        "AuditEvidence",
        foreign_keys=[audit_evidence_id],  # ✅ Correct foreign key
        back_populates="audit_evidence_project",
    )

    project = relationship(
        "Project",
        foreign_keys=[project_id],
        back_populates="audit_evidence_project",
    )

    def __repr__(self):
        return f"id: {self.id}, audit_evidence_id: {self.audit_evidence_id}, project_id: {self.project_id}"


# Audit Evidence Filter Framework
class AuditEvidenceFilterFramework(Base):
    __tablename__ = "audit_evidence_filter_framework"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_evidence_id = Column(Integer, ForeignKey("audit_evidence.id"), nullable=False)
    framework_id = Column(Integer, ForeignKey("framework.id"), nullable=False)

    audit_evidence = relationship(
        "AuditEvidence",
        foreign_keys=[audit_evidence_id],  # ✅ Correct foreign key
        back_populates="audit_evidence_framework",
    )

    framework = relationship(
        "Framework",
        foreign_keys=[framework_id],
        back_populates="audit_evidence_framework",
    )

    def __repr__(self):
        return f"id: {self.id}, audit_evidence_id: {self.audit_evidence_id}, framework_id: {self.framework_id}"


# Audit Evidence Review Digital Signature
class AuditEvidenceReviewDigSig(Base):
    __tablename__ = "audit_evidence_review_dig_sig"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_evidence_review_id = Column(
        Integer, ForeignKey("audit_evidence_review.id"), nullable=False
    )
    digital_signature_id = Column(Integer, ForeignKey("digital_signature.id"), nullable=False)
    signed_on = Column(DateTime, nullable=False, server_default=current_timestamp())

    audit_evidence_review = relationship(
        "AuditEvidenceReview",
        back_populates="audit_evidence_review_dig_sig",
    )

    digital_signature = relationship(
        "DigitalSignature",
        back_populates="audit_evidence_review_dig_sig",
    )

    def __repr__(self):
        return (
            f"id: {self.id}, audit_evidence_review_id: {self.audit_evidence_review_id}, "
            f"digital_signature_id: {self.digital_signature_id}, signed_on: {self.signed_on}"
        )


# Audit Evidence Review Project Control Digital Signature
class AuditEvidenceReviewProjContDigSig(Base):
    __tablename__ = "audit_evidence_review_proj_cont_dig_sig"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    audit_evidence_review_project_control_id = Column(
        Integer, ForeignKey("audit_evidence_review_project_control.id"), nullable=False
    )
    digital_signature_id = Column(Integer, ForeignKey("digital_signature.id"), nullable=False)
    signed_on = Column(DateTime, nullable=False, server_default=current_timestamp())

    def __repr__(self):
        return f"id: {self.id}, audit_evidence_review_project_control_id: {self.audit_evidence_review_project_control_id}, digital_signature_id: {self.digital_signature_id}, signed_on: {self.signed_on}"
