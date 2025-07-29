from datetime import datetime
from typing import List

from pydantic import BaseModel


class CreatePermissionRole(BaseModel):
    permission_id: int
    role_id: int
    enabled: bool


class PermissionRoleUpdate(BaseModel):
    tenant_id: int
    role_id: int
    permission_id: int
    enabled: bool


class DisplayPermission(BaseModel):
    id: str
    name: str
    perm_key: str
    created_date: datetime = None
    last_updated_date: datetime = None

    class Config:
        orm_mode = True


class DisplayRole(BaseModel):
    id: str
    name: str
    created_date: datetime = None
    last_updated_date: datetime = None
    permissions: List[DisplayPermission] = []

    class Config:
        orm_mode = True
        extra = "allow"


class DisplayRoles(BaseModel):
    items: List[DisplayRole] = []
    total: int

    class Config:
        orm_mode = True


class DisplayPermissions(BaseModel):
    items: List[DisplayPermission] = []
    total: int

    class Config:
        orm_mode = True
