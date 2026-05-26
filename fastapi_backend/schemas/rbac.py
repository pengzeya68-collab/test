"""
RBAC Pydantic Schemas - 角色/权限/分配
"""
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


# ============ Role Schemas ============

class RoleBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    pass


class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None


class RoleSchema(RoleBase):
    id: int
    is_system: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Permission Schemas ============

class PermissionBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    module: str


class PermissionCreate(PermissionBase):
    pass


class PermissionSchema(PermissionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Assignment Schemas ============

class PermissionAssign(BaseModel):
    """为角色分配权限（覆盖式）"""
    permission_codes: list[str]


class UserRoleAssign(BaseModel):
    """为用户分配角色"""
    role_id: int
