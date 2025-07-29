from datetime import datetime

from pydantic import BaseModel


class CreateAWSControl(BaseModel):
    aws_id: str = None
    aws_title: str = None
    aws_control_status: str = None
    aws_severity: str = None
    aws_failed_checks: int = None
    aws_unknown_checks: int = None
    aws_not_available_checks: int = None
    aws_passed_checks: int = None
    aws_related_requirements: str = None
    aws_custom_parameters: str = None


class CreateAWSControlProjControl(BaseModel):
    aws_control_id: str = None
    project_control_id: str = None


class UpdateAWSControl(BaseModel):
    aws_id: str = None
    aws_title: str = None
    aws_control_status: str = None
    aws_severity: str = None
    aws_failed_checks: int = None
    aws_unknown_checks: int = None
    aws_not_available_checks: int = None
    aws_passed_checks: int = None
    aws_related_requirements: str = None
    aws_custom_parameters: str = None

    class Config:
        orm_mode = True


class DisplayAWSControl(BaseModel):
    id: int
    aws_id: str = None
    aws_title: str = None
    aws_control_status: str = None
    aws_severity: str = None
    aws_failed_checks: int = None
    aws_unknown_checks: int = None
    aws_not_available_checks: int = None
    aws_passed_checks: int = None
    aws_related_requirements: str = None
    aws_custom_parameters: str = None
    created_date: datetime = None

    class Config:
        orm_mode = True


class CreateImportAWSControl(BaseModel):
    name: str
    project_id: int


class DisplayImportAWSControl(BaseModel):
    id: str
    name: str
    tenant_id: str = None
    file_content_type: str = None
    created_date: datetime = None
    last_updated_date: datetime = None
    imported: bool = None
    import_results: str = None

    class Config:
        orm_mode = True
