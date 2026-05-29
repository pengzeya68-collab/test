"""
RBAC 权限管理路由

仅后端 API，暂不提供前端管理界面。
所有接口需要 system:config 或 user:manage 权限。
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import require_permission
from fastapi_backend.models.models import (
    User,
    Role,
    Permission,
    RolePermissionMapping,
)
from fastapi_backend.schemas.rbac import (
    RoleCreate,
    RoleUpdate,
    RoleSchema,
    PermissionCreate,
    PermissionSchema,
    PermissionAssign,
    UserRoleAssign,
)

router = APIRouter(prefix="/api/v1/admin/rbac", tags=["RBAC Management"])


# ============ 角色管理 ============


@router.get("/roles", response_model=list[RoleSchema])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:config")),
):
    """获取所有角色"""
    result = await db.execute(select(Role).order_by(Role.id))
    return result.scalars().all()


@router.post("/roles", response_model=RoleSchema)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:config")),
):
    """创建新角色"""
    existing = await db.execute(select(Role).where(Role.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="角色名已存在")

    role = Role(**data.model_dump())
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


@router.put("/roles/{role_id}", response_model=RoleSchema)
async def update_role(
    role_id: int,
    data: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:config")),
):
    """更新角色信息"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.is_system:
        raise HTTPException(status_code=400, detail="系统内置角色不可修改")

    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(role, key, value)

    await db.commit()
    await db.refresh(role)
    return role


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:config")),
):
    """删除角色（仅非系统内置角色）"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.is_system:
        raise HTTPException(status_code=400, detail="系统内置角色不可删除")

    # 检查是否有用户使用该角色
    count_result = await db.execute(select(func.count(User.id)).where(User.role_id == role_id))
    if count_result.scalar() > 0:
        raise HTTPException(status_code=400, detail="该角色下还有用户，无法删除")

    await db.delete(role)
    await db.commit()
    return {"message": "角色已删除"}


# ============ 权限管理 ============


@router.get("/permissions", response_model=list[PermissionSchema])
async def list_permissions(
    module: str = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:config")),
):
    """获取所有权限（可按模块筛选）"""
    query = select(Permission).order_by(Permission.module, Permission.code)
    if module:
        query = query.where(Permission.module == module)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/permissions", response_model=PermissionSchema)
async def create_permission(
    data: PermissionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:config")),
):
    """创建新权限"""
    existing = await db.execute(select(Permission).where(Permission.code == data.code))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="权限代码已存在")

    permission = Permission(**data.model_dump())
    db.add(permission)
    await db.commit()
    await db.refresh(permission)
    return permission


# ============ 角色权限分配 ============


@router.get("/roles/{role_id}/permissions", response_model=list[PermissionSchema])
async def get_role_permissions(
    role_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:config")),
):
    """获取角色拥有的权限"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    return role.permissions


@router.post("/roles/{role_id}/permissions")
async def assign_permissions_to_role(
    role_id: int,
    data: PermissionAssign,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("system:config")),
):
    """为角色分配权限（覆盖式）"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 清空现有权限
    await db.execute(sa_delete(RolePermissionMapping).where(RolePermissionMapping.role_id == role_id))

    # 分配新权限
    for perm_code in data.permission_codes:
        perm_result = await db.execute(select(Permission).where(Permission.code == perm_code))
        permission = perm_result.scalar_one_or_none()
        if permission:
            mapping = RolePermissionMapping(role_id=role_id, permission_id=permission.id)
            db.add(mapping)

    await db.commit()
    return {"message": "权限分配成功"}


# ============ 用户角色管理 ============


@router.put("/users/{user_id}/role")
async def assign_role_to_user(
    user_id: int,
    data: UserRoleAssign,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permission("user:manage")),
):
    """为用户分配角色"""
    # 检查用户是否存在
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 检查角色是否存在
    role_result = await db.execute(select(Role).where(Role.id == data.role_id))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    user.role_id = data.role_id
    await db.commit()
    return {"message": f"已为用户 {user.username} 分配角色 {role.display_name}"}
