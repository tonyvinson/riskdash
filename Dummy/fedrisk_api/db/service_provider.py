from sqlalchemy import func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.session import Session
import logging

from fedrisk_api.db.enums import CapPoamStatus
from fedrisk_api.db.models import (
    ServiceProvider,
    ServiceProviderAddress,
    ServiceProviderApp,
    ServiceProviderProject,
    ServiceProviderProjectControl,
    Address,
    App,
    AppProjectControl,
    AppProject,
    ProjectControl,
)
from fedrisk_api.schema.service_provider import (
    CreateServiceProvider,
    UpdateServiceProvider,
    CreateAddress,
    UpdateAddress,
    CreateApp,
    CreateAppProject,
    UpdateApp,
    CreateAppProjectControl,
    CreateServiceProviderAddress,
    CreateServiceProviderApp,
    CreateServiceProviderProjectControl,
    CreateServiceProviderProject,
)

LOGGER = logging.getLogger(__name__)


# Database methods

########################## Service Provider ##########################


# create new service provider
async def create_service_provider(
    db: Session, service_provider: CreateServiceProvider, tenant_id: int
):
    service_provider_data = service_provider.dict()
    new_service_provider = ServiceProvider(**service_provider_data, tenant_id=tenant_id)
    db.add(new_service_provider)
    db.commit()
    return new_service_provider


# create a new service provider project control association
async def create_service_provider_project_control_assoc(
    db: Session, request: CreateServiceProviderProjectControl
):
    service_provider_pc_assoc_data = request.dict()
    new_service_provider_pc_assoc = ServiceProviderProjectControl(**service_provider_pc_assoc_data)
    db.add(new_service_provider_pc_assoc)
    db.commit()
    return new_service_provider_pc_assoc


# create a new service provider app association
async def create_service_provider_app_assoc(db: Session, request: CreateServiceProviderApp):
    service_provider_app_assoc_data = request.dict()
    new_service_provider_app_assoc = ServiceProviderApp(**service_provider_app_assoc_data)
    db.add(new_service_provider_app_assoc)
    db.commit()
    return new_service_provider_app_assoc


# create a new service provider project association
async def create_service_provider_project_assoc(db: Session, request: CreateServiceProviderProject):
    service_provider_pro_assoc_data = request.dict()
    new_service_provider_pro_assoc = ServiceProviderProject(**service_provider_pro_assoc_data)
    db.add(new_service_provider_pro_assoc)
    db.commit()
    return new_service_provider_pro_assoc


# update a service provider by ID
async def update_service_provider_by_id(
    service_provider: UpdateServiceProvider,
    db: Session,
    service_provider_id: int,
):
    queryset = db.query(ServiceProvider).filter(ServiceProvider.id == service_provider_id)

    if not queryset.first():
        return False

    queryset.update(service_provider.dict(exclude_unset=True))
    db.commit()
    return True


# GET a service provider by ID
async def get_service_provider_by_id(db: Session, service_provider_id: int):
    queryset = (
        db.query(ServiceProvider)
        .options(
            selectinload(ServiceProvider.service_provider_projects).selectinload(
                ServiceProviderProject.project
            )
        )
        .filter(ServiceProvider.id == service_provider_id)
        .first()
    )
    return queryset


# GET all service providers for a project
async def get_service_providers_by_project_id(db: Session, project_id: int):
    queryset = (
        db.query(ServiceProvider)
        .outerjoin(
            ServiceProviderProjectControl,
            ServiceProvider.id == ServiceProviderProjectControl.service_provider_id,
        )
        .outerjoin(
            ProjectControl, ServiceProviderProjectControl.project_control_id == ProjectControl.id
        )
        .outerjoin(
            ServiceProviderProject, ServiceProvider.id == ServiceProviderProject.service_provider_id
        )
        .filter(
            or_(
                ProjectControl.project_id == project_id,
                ServiceProviderProject.project_id == project_id,
            )
        )
        .distinct()
        .all()
    )
    return queryset


# GET all service providers associated with a project control
async def get_service_providers_by_project_control_id(db: Session, project_control_id: int):
    queryset = (
        db.query(ServiceProvider)
        .join(
            ServiceProviderProjectControl,
            ServiceProviderProjectControl.service_provider_id == ServiceProvider.id,
        )
        .join(ProjectControl, ServiceProviderProjectControl.project_control_id == ProjectControl.id)
        .filter(ProjectControl.id == project_control_id)
        .all()
    )
    return queryset


# GET all service providers associated with a tenant
async def get_service_providers_by_tenant_id(db: Session, tenant_id: int):
    queryset = db.query(ServiceProvider).filter(ServiceProvider.tenant_id == tenant_id).all()
    return queryset


# DELETE a service provider and all associations
async def delete_service_provider_by_id(db: Session, service_provider_id: int):
    service_provider = (
        db.query(ServiceProvider).filter(ServiceProvider.id == service_provider_id).first()
    )

    if not service_provider:
        return False
    # delete all address associations
    db.query(ServiceProviderAddress).filter(
        ServiceProviderAddress.service_provider_id == service_provider_id
    ).delete()
    # delete all app associations
    db.query(ServiceProviderApp).filter(
        ServiceProviderApp.service_provider_id == service_provider_id
    ).delete()
    # delete all project control associations
    db.query(ServiceProviderProjectControl).filter(
        ServiceProviderProjectControl.service_provider_id == service_provider_id
    ).delete()
    db.delete(service_provider)
    db.commit()
    return True


# DELETE a service provider project control association
async def delete_service_provider_project_control_assoc_by_pc_id(
    db: Session, service_provider_id: int, project_control_id: int
):
    service_provider_pc_assoc = (
        db.query(ServiceProviderProjectControl)
        .filter(ServiceProviderProjectControl.service_provider_id == service_provider_id)
        .filter(ServiceProviderProjectControl.project_control_id == project_control_id)
        .first()
    )

    if not service_provider_pc_assoc:
        return False
    db.delete(service_provider_pc_assoc)
    db.commit()
    return True


# DELETE a service provider address association
async def delete_service_provider_address_assoc(
    db: Session, service_provider_id: int, address_id: int
):
    service_provider_address_assoc = (
        db.query(ServiceProviderAddress)
        .filter(ServiceProviderAddress.service_provider_id == service_provider_id)
        .filter(ServiceProviderAddress.address_id == address_id)
        .first()
    )

    if not service_provider_address_assoc:
        return False
    db.delete(service_provider_address_assoc)
    db.commit()
    return True


# DELETE a service provider app association
async def delete_service_provider_app_assoc(db: Session, service_provider_id: int, app_id: int):
    service_provider_app_assoc = (
        db.query(ServiceProviderApp)
        .filter(ServiceProviderApp.service_provider_id == service_provider_id)
        .filter(ServiceProviderApp.app_id == app_id)
        .first()
    )

    if not service_provider_app_assoc:
        return False
    db.delete(service_provider_app_assoc)
    db.commit()
    return True


########################## App ##########################


# create a new app
async def create_app(db: Session, app: CreateApp, tenant_id: int):
    app_data = app.dict()
    new_app = App(**app_data, tenant_id=tenant_id)
    db.add(new_app)
    db.commit()
    return new_app


# create a new app project control association
async def create_app_project_control_assoc(db: Session, request: CreateAppProjectControl):
    app_pc_assoc_data = request.dict()
    new_app_pc_assoc_data = AppProjectControl(**app_pc_assoc_data)
    db.add(new_app_pc_assoc_data)
    db.commit()
    return new_app_pc_assoc_data


# create a new app project association
async def create_app_project_assoc(db: Session, request: CreateAppProject):
    app_pro_assoc_data = request.dict()
    new_app_pro_assoc_data = AppProject(**app_pro_assoc_data)
    db.add(new_app_pro_assoc_data)
    db.commit()
    return new_app_pro_assoc_data


# update a app by ID
async def update_app_by_id(
    app: UpdateApp,
    db: Session,
    app_id: int,
):
    queryset = db.query(App).filter(App.id == app_id)

    if not queryset.first():
        return False

    queryset.update(app.dict(exclude_unset=True))
    db.commit()
    return True


# GET an app by ID
async def get_app_by_id(db: Session, app_id: int):
    queryset = db.query(App).filter(App.id == app_id).first()
    return queryset


# GET all apps for a project
async def get_apps_by_project_id(db: Session, project_id: int):
    queryset = (
        db.query(App)
        .outerjoin(AppProjectControl, App.id == AppProjectControl.app_id)
        .outerjoin(ProjectControl, AppProjectControl.project_control_id == ProjectControl.id)
        .outerjoin(AppProject, App.id == AppProject.app_id)
        .filter(or_(ProjectControl.project_id == project_id, AppProject.project_id == project_id))
        .distinct()
        .all()
    )
    return queryset


# GET all apps for a service provider
async def get_apps_by_service_provider_id(db: Session, service_provider_id: int):
    queryset = (
        db.query(App)
        .join(
            ServiceProviderApp,
            ServiceProviderApp.app_id == App.id,
        )
        .filter(ServiceProviderApp.service_provider_id == service_provider_id)
        .all()
    )
    return queryset


# GET all apps for a project control
async def get_apps_by_project_control_id(db: Session, project_control_id: int):
    queryset = (
        db.query(App)
        .join(
            AppProjectControl,
            AppProjectControl.app_id == App.id,
        )
        .filter(AppProjectControl.project_control_id == project_control_id)
        .all()
    )
    return queryset


# GET all apps by tenant
async def get_apps_by_tenant_id(db: Session, tenant_id: int):
    queryset = db.query(App).filter(App.tenant_id == tenant_id).all()
    return queryset


# DELETE an app and all associations
async def delete_app_by_id(db: Session, app_id: int):
    app = db.query(App).filter(App.id == app_id).first()

    if not app:
        return False
    # delete all service provider associations
    db.query(ServiceProviderApp).filter(ServiceProviderApp.app_id == app_id).delete()
    # delete all project control associations
    db.query(AppProjectControl).filter(AppProjectControl.app_id == app_id).delete()
    db.delete(app)
    db.commit()
    return True


# DELETE an app project control association
async def delete_app_project_control_assoc(db: Session, app_id: int, project_control_id: int):
    app_pc_assoc = (
        db.query(AppProjectControl)
        .filter(AppProjectControl.app_id == app_id)
        .filter(AppProjectControl.project_control_id == project_control_id)
        .first()
    )

    if not app_pc_assoc:
        return False
    db.delete(app_pc_assoc)
    db.commit()
    return True


########################## Address ##########################


# create a new address
async def create_address(db: Session, address: CreateAddress):
    address_data = address.dict()
    new_address = Address(**address_data)
    db.add(new_address)
    db.commit()
    return new_address


# update an address
async def update_address_by_id(
    address: UpdateAddress,
    db: Session,
    address_id: int,
):
    queryset = db.query(Address).filter(Address.id == address_id)

    if not queryset.first():
        return False

    queryset.update(address.dict(exclude_unset=True))
    db.commit()
    return True


# POST a new service provider address association
async def create_service_provider_address_assoc(db: Session, request: CreateServiceProviderAddress):
    sp_add_assoc_data = request.dict()
    new_sp_add_assoc_data = ServiceProviderAddress(**sp_add_assoc_data)
    db.add(new_sp_add_assoc_data)
    db.commit()
    return new_sp_add_assoc_data


# DELETE an address and all associations
async def delete_address_by_id(db: Session, address_id: int):
    address = db.query(Address).filter(Address.id == address_id).first()

    if not address:
        return False
    # delete all service provider associations
    db.query(ServiceProviderAddress).filter(
        ServiceProviderAddress.address_id == address_id
    ).delete()
    db.delete(address)
    db.commit()
    return True
