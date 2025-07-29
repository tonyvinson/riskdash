from pydantic import BaseModel, root_validator
from datetime import datetime

from typing import List

from fedrisk_api.schema.project import DisplayProjectControl, DisplayProject

import logging

LOGGER = logging.getLogger(__name__)


#################### ServiceProviderProjectControl #########################
## Create ##
class CreateServiceProviderProjectControl(BaseModel):
    service_provider_id: int = None
    project_control_id: int = None


## Display ##
class DisplayServiceProviderProjectControl(BaseModel):
    service_provider_id: int = None
    project_control_id: int = None
    project_control: DisplayProjectControl = None
    created_date: datetime

    class Config:
        orm_mode = True


#################### ServiceProviderProject #########################
## Create ##
class CreateServiceProviderProject(BaseModel):
    service_provider_id: int = None
    project_id: int = None


## Display ##
class DisplayServiceProviderProject(BaseModel):
    service_provider_id: int = None
    project_id: int = None
    project: DisplayProject = None
    created_date: datetime

    class Config:
        orm_mode = True


#################### Address #########################
## Create ##
class CreateAddress(BaseModel):
    street_address_1: str = None
    street_address_2: str = None
    city: str = None
    zip_code: str = None
    country_code: str = None
    region: str = None


## Update ##
class UpdateAddress(BaseModel):
    street_address_1: str = None
    street_address_2: str = None
    city: str = None
    zip_code: str = None
    country_code: str = None
    region: str = None


## Display ##
class DisplayAddress(BaseModel):
    id: str
    street_address_1: str = None
    street_address_2: str = None
    city: str = None
    zip_code: str = None
    country_code: str = None
    region: str = None
    created_date: datetime

    class Config:
        orm_mode = True


#################### ServiceProviderAddress #########################
## Create ##
class CreateServiceProviderAddress(BaseModel):
    service_provider_id: int = None
    address_id: int = None


## Display ##
class DisplayServiceProviderAddress(BaseModel):
    service_provider_id: int = None
    address_id: int = None
    address: DisplayAddress = None
    created_date: datetime

    class Config:
        orm_mode = True


#################### App #########################
## Create ##
class CreateApp(BaseModel):
    name: str = None
    description: str = None


## Update ##
class UpdateApp(BaseModel):
    name: str = None
    description: str = None


## Display ##
class DisplayShortServiceProvider(BaseModel):
    id: str
    name: str = None

    class Config:
        orm_mode = True


class DisplayProjectMap(BaseModel):
    id: str
    project_id: int = None
    project: DisplayProject = None

    class Config:
        orm_mode = True


class DisplayProjectControlMap(BaseModel):
    id: str
    project_control_id: int = None
    project_control: DisplayProjectControl = None

    class Config:
        orm_mode = True


class DisplayShortServiceProviderMap(BaseModel):
    id: str
    service_provider_id: int = None
    service_provider: DisplayShortServiceProvider = None

    class Config:
        orm_mode = True


class DisplayApp(BaseModel):
    id: str
    name: str = None
    description: str = None
    created_date: datetime = None
    app_projects: List[DisplayProjectMap] = []
    app_project_controls: List[DisplayProjectControlMap] = []
    service_provider_apps: List[DisplayShortServiceProviderMap] = []

    class Config:
        orm_mode = True


#################### ServiceProviderApp #########################
## Create ##
class CreateServiceProviderApp(BaseModel):
    service_provider_id: int = None
    app_id: int = None


## Display ##
class DisplayServiceProviderApp(BaseModel):
    service_provider_id: int = None
    app_id: int = None
    app: DisplayApp = None
    created_date: datetime

    class Config:
        orm_mode = True


#################### AppProject #########################
## Create ##
class CreateAppProject(BaseModel):
    app_id: int = None
    project_id: int = None


## Display ##
class DisplayAppProject(BaseModel):
    app_id: int = None
    project_id: int = None
    project: DisplayProject = None
    created_date: datetime

    class Config:
        orm_mode = True


#################### Service Provider #########################
## Create ##
class CreateServiceProvider(BaseModel):
    name: str
    contact_email: str = None
    contact_phone: str = None
    business_type: str = None
    category: str = None
    category_type: str = None
    hosting_environment: str = None
    owner: str = None
    parent_company: str = None
    certification: str = None
    license: str = None


## Update ##
class UpdateServiceProvider(BaseModel):
    name: str = None
    contact_email: str = None
    contact_phone: str = None
    business_type: str = None
    category: str = None
    category_type: str = None
    hosting_environment: str = None
    owner: str = None
    parent_company: str = None
    certification: str = None
    license: str = None


## Display ##
class DisplayServiceProvider(BaseModel):
    id: str = None
    name: str = None
    contact_email: str = None
    contact_phone: str = None
    business_type: str = None
    category: str = None
    category_type: str = None
    hosting_environment: str = None
    owner: str = None
    parent_company: str = None
    certification: str = None
    license: str = None
    created_date: datetime = None
    service_provider_addresses: List[DisplayServiceProviderAddress] = []
    service_provider_project_controls: List[DisplayServiceProviderProjectControl] = []
    service_provider_apps: List[DisplayServiceProviderApp] = []
    service_provider_projects: List[DisplayServiceProviderProject] = []

    class Config:
        orm_mode = True


#################### AppProjectControl #########################
## Create ##
class CreateAppProjectControl(BaseModel):
    app_id: int = None
    project_control_id: int = None


## Display ##
class DisplayAppProjectControl(BaseModel):
    app_id: int = None
    project_control_id: int = None
    project_control: DisplayProjectControl = None
    created_date: datetime

    class Config:
        orm_mode = True
