import logging

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fedrisk_api.db import service_provider as db_service_provider
from fedrisk_api.db.database import get_db
from fedrisk_api.schema.service_provider import (
    CreateAddress,
    CreateApp,
    CreateAppProject,
    CreateAppProjectControl,
    CreateServiceProvider,
    CreateServiceProviderAddress,
    CreateServiceProviderApp,
    CreateServiceProviderProjectControl,
    CreateServiceProviderProject,
    DisplayAddress,
    DisplayApp,
    DisplayAppProjectControl,
    DisplayServiceProvider,
    DisplayServiceProviderAddress,
    DisplayServiceProviderApp,
    DisplayServiceProviderProjectControl,
    DisplayServiceProviderProject,
    UpdateAddress,
    UpdateApp,
    UpdateServiceProvider,
    DisplayAppProject,
)
from fedrisk_api.utils.authentication import custom_auth
from fedrisk_api.utils.permissions import (
    create_service_provider_permission,
    delete_service_provider_permission,
    update_service_provider_permission,
    view_service_provider_permission,
)

LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/service_provider", tags=["service_provider"])


# Endpoints
########################### Service Provider ##########################
# POST new service provider
@router.post(
    "/",
    response_model=DisplayServiceProvider,
    dependencies=[Depends(create_service_provider_permission)],
)
async def create_service_provider(
    request: CreateServiceProvider, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        service_provider = await db_service_provider.create_service_provider(
            service_provider=request, db=db, tenant_id=user["tenant_id"]
        )
    except IntegrityError as ie:
        LOGGER.exception("Create Service Provider Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return service_provider


# POST a new service provider project control association
@router.post(
    "/service_provider_pc_assoc",
    response_model=DisplayServiceProviderProjectControl,
    dependencies=[Depends(create_service_provider_permission)],
)
async def create_service_provider_pc_assoc(
    request: CreateServiceProviderProjectControl,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        service_provider_pc_assoc = (
            await db_service_provider.create_service_provider_project_control_assoc(
                request=request, db=db
            )
        )
    except IntegrityError as ie:
        LOGGER.exception(
            "Create Service Provider Project Control association Error. Invalid request"
        )
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return service_provider_pc_assoc


# POST a new service provider project association
@router.post(
    "/service_provider_proj_assoc",
    response_model=DisplayServiceProviderProject,
    dependencies=[Depends(create_service_provider_permission)],
)
async def create_service_provider_proj_assoc(
    request: CreateServiceProviderProject,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        service_provider_pro_assoc = (
            await db_service_provider.create_service_provider_project_assoc(request=request, db=db)
        )
    except IntegrityError as ie:
        LOGGER.exception("Create Service Provider Project association Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return service_provider_pro_assoc


# POST a new service provider app association
@router.post(
    "/service_provider_app_assoc",
    response_model=DisplayServiceProviderApp,
    dependencies=[Depends(create_service_provider_permission)],
)
async def create_service_provider_app_assoc(
    request: CreateServiceProviderApp, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        service_provider_app_assoc = await db_service_provider.create_service_provider_app_assoc(
            request=request, db=db
        )
    except IntegrityError as ie:
        LOGGER.exception("Create Service Provider App association Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return service_provider_app_assoc


# POST a new service provider address association
@router.post(
    "/service_provider_address_assoc",
    response_model=DisplayServiceProviderAddress,
    dependencies=[Depends(create_service_provider_permission)],
)
async def create_service_provider_address_assoc(
    request: CreateServiceProviderAddress, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        service_provider_address_assoc = (
            await db_service_provider.create_service_provider_address_assoc(request=request, db=db)
        )
    except IntegrityError as ie:
        LOGGER.exception("Create Service Provider Address association Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return service_provider_address_assoc


# PUT update a service provider by ID
@router.put("/{id}", dependencies=[Depends(update_service_provider_permission)])
async def update_service_provider_by_id(
    request: UpdateServiceProvider,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = await db_service_provider.update_service_provider_by_id(
            service_provider=request, db=db, service_provider_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Service Provider with specified id does not exist",
            )
        return {"detail": "Successfully updated Service Provider."}
    except IntegrityError as ie:
        LOGGER.exception("Get Service Provider Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET a service provider by ID
@router.get(
    "/{id}",
    response_model=DisplayServiceProvider,
    dependencies=[Depends(view_service_provider_permission)],
)
async def get_service_provider_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = await db_service_provider.get_service_provider_by_id(db=db, service_provider_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service Provider with specified id does not exist",
        )
    return queryset


# GET all service providers for a project
@router.get(
    "/project/{id}",
    response_model=List[DisplayServiceProvider],
    dependencies=[Depends(view_service_provider_permission)],
)
async def get_service_providers_by_project_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = await db_service_provider.get_service_providers_by_project_id(db=db, project_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service Providers for project with specified id do not exist",
        )
    return queryset


# GET all service providers associated with a project control
@router.get(
    "/project_control/{id}",
    response_model=List[DisplayServiceProvider],
    dependencies=[Depends(view_service_provider_permission)],
)
async def get_service_providers_by_project_control_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = await db_service_provider.get_service_providers_by_project_control_id(
        db=db, project_control_id=id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service Providers for project control with specified id do not exist",
        )
    return queryset


# GET all service providers for tenant
@router.get(
    "/",
    response_model=List[DisplayServiceProvider],
    dependencies=[Depends(view_service_provider_permission)],
)
async def get_service_providers_by_current_tenant(
    db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = await db_service_provider.get_service_providers_by_tenant_id(
        db=db, tenant_id=user["tenant_id"]
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service Providers for tenant with specified id do not exist",
        )
    return queryset


# DELETE a service provider and all associations
@router.delete("/{id}", dependencies=[Depends(delete_service_provider_permission)])
async def delete_service_provider_by_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    db_status = await db_service_provider.delete_service_provider_by_id(
        db=db, service_provider_id=id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service Provider with specified id does not exist",
        )
    return {"detail": "Successfully deleted Service Provider."}


# DELETE a service provider project control association
@router.delete(
    "/service_provider_pc_assoc/{service_provider_id}/{project_control_id}",
    dependencies=[Depends(delete_service_provider_permission)],
)
async def delete_service_provider_pc_assoc(
    service_provider_id: int,
    project_control_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    db_status = await db_service_provider.delete_service_provider_project_control_assoc_by_pc_id(
        db=db, service_provider_id=service_provider_id, project_control_id=project_control_id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service Provider associated with specified Project Control id does not exist",
        )
    return {"detail": "Successfully deleted Service Provider Project Control assoc."}


# DELETE a service provider address association
@router.delete(
    "/service_provider_address_assoc/{service_provider_id}/{address_id}",
    dependencies=[Depends(delete_service_provider_permission)],
)
async def delete_service_provider_address_assoc(
    service_provider_id: int,
    address_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    db_status = await db_service_provider.delete_service_provider_address_assoc(
        db=db, service_provider_id=service_provider_id, address_id=address_id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service Provider associated with specified Address id does not exist",
        )
    return {"detail": "Successfully deleted Service Provider Address assoc."}


# DELETE a service provider app association
@router.delete(
    "/service_provider_app_assoc/",
    dependencies=[Depends(delete_service_provider_permission)],
)
async def delete_service_provider_app_assoc(
    service_provider_id: int,
    app_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    db_status = await db_service_provider.delete_service_provider_app_assoc(
        db=db, service_provider_id=service_provider_id, app_id=app_id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service Provider associated with specified App id does not exist",
        )
    return {"detail": "Successfully deleted Service Provider App assoc."}


########################### App ##########################
# POST a new app
@router.post(
    "/app",
    response_model=DisplayApp,
    dependencies=[Depends(create_service_provider_permission)],
)
async def create_app(request: CreateApp, db: Session = Depends(get_db), user=Depends(custom_auth)):
    try:
        app = await db_service_provider.create_app(db=db, app=request, tenant_id=user["tenant_id"])
    except IntegrityError as ie:
        LOGGER.exception("Create App Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return app


# POST a new app project control association
@router.post(
    "/app_project_control_assoc",
    response_model=DisplayAppProjectControl,
    dependencies=[Depends(create_service_provider_permission)],
)
async def create_app_project_control_assoc(
    request: CreateAppProjectControl, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        app_project_control_assoc = await db_service_provider.create_app_project_control_assoc(
            request=request, db=db
        )
    except IntegrityError as ie:
        LOGGER.exception("Create App Project Control association Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return app_project_control_assoc


# POST a new app project association
@router.post(
    "/app_project_assoc",
    response_model=DisplayAppProject,
    dependencies=[Depends(create_service_provider_permission)],
)
async def create_app_project_assoc(
    request: CreateAppProject, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        app_project_assoc = await db_service_provider.create_app_project_assoc(
            request=request, db=db
        )
    except IntegrityError as ie:
        LOGGER.exception("Create App Project association Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return app_project_assoc


# PUT update an app by ID
@router.put("/app/{id}", dependencies=[Depends(update_service_provider_permission)])
async def update_app_by_id(
    request: UpdateApp,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = await db_service_provider.update_service_provider_by_id(
            service_provider=request, db=db, service_provider_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="App with specified id does not exist",
            )
        return {"detail": "Successfully updated App."}
    except IntegrityError as ie:
        LOGGER.exception("Get App Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# GET an app by ID
@router.get(
    "/app/{id}",
    response_model=DisplayApp,
    dependencies=[Depends(view_service_provider_permission)],
)
async def get_app_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = await db_service_provider.get_app_by_id(db=db, app_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App with specified id does not exist",
        )
    return queryset


# GET all apps for a project
@router.get(
    "/app/project/{id}",
    response_model=List[DisplayApp],
    dependencies=[Depends(view_service_provider_permission)],
)
async def get_apps_by_project_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = await db_service_provider.get_apps_by_project_id(db=db, project_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App associated with specified project id does not exist",
        )
    return queryset


# GET all apps for a service provider
@router.get(
    "/app/service_provider/{id}",
    response_model=List[DisplayApp],
    dependencies=[Depends(view_service_provider_permission)],
)
async def get_apps_by_service_provider_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = await db_service_provider.get_apps_by_service_provider_id(db=db, project_id=id)
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App associated with specified service provider id does not exist",
        )
    return queryset


# GET all apps for a project control
@router.get(
    "/app/project_control/{id}",
    response_model=List[DisplayApp],
    dependencies=[Depends(view_service_provider_permission)],
)
async def get_apps_by_project_control_id(
    id: int, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    queryset = await db_service_provider.get_apps_by_project_control_id(
        db=db, project_control_id=id
    )
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App associated with specified project control id does not exist",
        )
    return queryset


# DELETE an app and all associations
@router.delete("/app/{id}", dependencies=[Depends(delete_service_provider_permission)])
async def delete_app_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = await db_service_provider.delete_app_by_id(db=db, app_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App with specified id does not exist",
        )
    return {"detail": "Successfully deleted App."}


# DELETE an app project control association
@router.delete(
    "/app_pc_assoc/{app_id}/{project_control_id}",
    dependencies=[Depends(delete_service_provider_permission)],
)
async def delete_app_pc_assoc(
    app_id: int,
    project_control_id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    db_status = await db_service_provider.delete_app_project_control_assoc(
        db=db, app_id=app_id, project_control_id=project_control_id
    )
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="App associated with specified Project Control id does not exist",
        )
    return {"detail": "Successfully deleted App Project Control assoc."}


# GET all apps for tenant
@router.get(
    "/app/",
    response_model=List[DisplayApp],
    dependencies=[Depends(view_service_provider_permission)],
)
async def get_apps_by_current_tenant(db: Session = Depends(get_db), user=Depends(custom_auth)):
    queryset = await db_service_provider.get_apps_by_tenant_id(db=db, tenant_id=user["tenant_id"])
    if not queryset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Apps for tenant with specified id do not exist",
        )
    return queryset


########################### Address ##########################
# POST a new address
@router.post(
    "/address",
    response_model=DisplayAddress,
    dependencies=[Depends(create_service_provider_permission)],
)
async def create_address(
    request: CreateAddress, db: Session = Depends(get_db), user=Depends(custom_auth)
):
    try:
        address = await db_service_provider.create_address(db=db, address=request)
    except IntegrityError as ie:
        LOGGER.exception("Create Address Error. Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)
    return address


# PUT update an address
@router.put("/address/{id}", dependencies=[Depends(update_service_provider_permission)])
async def update_address_by_id(
    request: UpdateAddress,
    id: int,
    db: Session = Depends(get_db),
    user=Depends(custom_auth),
):
    try:
        queryset = await db_service_provider.update_address_by_id(
            address=request, db=db, address_id=id
        )
        if not queryset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Address with specified id does not exist",
            )
        return {"detail": "Successfully updated Address."}
    except IntegrityError as ie:
        LOGGER.exception("Get Address Error - Invalid request")
        detail_message = str(ie)
        raise HTTPException(status_code=409, detail=detail_message)


# DELETE an address
@router.delete("/address/{id}", dependencies=[Depends(delete_service_provider_permission)])
async def delete_address_by_id(id: int, db: Session = Depends(get_db), user=Depends(custom_auth)):
    db_status = await db_service_provider.delete_address_by_id(db=db, address_id=id)
    if not db_status:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Address with specified id does not exist",
        )
    return {"detail": "Successfully deleted Address."}
