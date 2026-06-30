"""
RBAC Pydantic Schemas - 角色/权限/分配
"""

from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional, List


# ============ Role Schemas ============


class RoleBase(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None


class RoleCreate(RoleBase):
    code: Optional[str] = None  # 角色代码（大写唯一），可选


class RoleUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None


class RoleSchema(RoleBase):
    id: int
    code: Optional[str] = None
    is_system: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Permission Schemas ============


class PermissionBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    module: str
    action: Optional[str] = None


class PermissionCreate(PermissionBase):
    pass


class PermissionSchema(PermissionBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============ Assignment Schemas ============


class PermissionAssign(BaseModel):
    """为角色分配权限（覆盖式）"""

    permission_codes: List[str]


class UserRoleAssign(BaseModel):
    """为用户分配角色（单角色，兼容旧逻辑）"""

    role_id: int


class UserRoleMultiAssign(BaseModel):
    """为用户分配多个角色（覆盖式）"""

    role_ids: List[int]


class UserRoleSchema(BaseModel):
    """用户-角色关联记录"""

    user_id: int
    role_id: int
    role_code: Optional[str] = None
    role_name: Optional[str] = None
    display_name: Optional[str] = None
    assigned_at: Optional[datetime] = None
    assigned_by: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class UserPermissionsResponse(BaseModel):
    """当前用户权限（前端用于按钮控制）"""

    user_id: int
    username: str
    roles: List[str] = []
    permissions: List[str] = []
    is_admin: bool = False
