"""
RBAC 权限管理路由

提供角色/权限/用户角色分配的完整管理 API：
- 角色列表、创建、更新、删除（系统内置角色不可删除）
- 角色权限查询与分配
- 权限列表查询
- 用户角色查询与分配（多对多）
- 当前用户权限查询（前端按钮控制用）

权限保护：使用 ``fastapi_backend.core.rbac`` 的细粒度权限检查。
- 角色/权限管理需要 ``role:*`` 权限
- 用户角色分配需要 ``user:assign_role`` 权限
- 普通用户可查询自身权限（仅需登录）
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_backend.core.database import get_db
from fastapi_backend.core.rbac import (
    get_user_permissions,
    require_permissions,
)
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import (
    User,
    Role,
    Permission,
    RolePermissionMapping,
    UserRole,
)
from fastapi_backend.schemas.rbac import (
    RoleCreate,
    RoleUpdate,
    RoleSchema,
    PermissionCreate,
    PermissionSchema,
    PermissionAssign,
    UserRoleAssign,
    UserRoleMultiAssign,
    UserRoleSchema,
    UserPermissionsResponse,
)

router = APIRouter(prefix="/api/v1/admin/rbac", tags=["RBAC Management"])


# ============ 角色管理 ============


@router.get("/roles", response_model=list[RoleSchema])
async def list_roles(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("role:read")),
):
    """获取所有角色"""
    result = await db.execute(select(Role).order_by(Role.id))
    return result.scalars().all()


@router.post("/roles", response_model=RoleSchema)
async def create_role(
    data: RoleCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("role:create")),
):
    """创建新角色"""
    existing = await db.execute(select(Role).where(Role.name == data.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="角色名已存在")

    if data.code:
        existing_code = await db.execute(select(Role).where(Role.code == data.code))
        if existing_code.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="角色代码已存在")

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
    _: User = Depends(require_permissions("role:update")),
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
    _: User = Depends(require_permissions("role:delete")),
):
    """删除角色（仅非系统内置角色）"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.is_system:
        raise HTTPException(status_code=400, detail="系统内置角色不可删除")

    # 检查是否有用户通过 user_roles 多对多使用该角色
    count_result = await db.execute(select(func.count(UserRole.role_id)).where(UserRole.role_id == role_id))
    if count_result.scalar() > 0:
        raise HTTPException(status_code=400, detail="该角色下还有用户，无法删除")

    # 同时检查旧 role_id 字段
    legacy_count = await db.execute(select(func.count(User.id)).where(User.role_id == role_id))
    if legacy_count.scalar() > 0:
        raise HTTPException(status_code=400, detail="该角色下还有用户（旧关联），无法删除")

    await db.delete(role)
    await db.commit()
    return {"message": "角色已删除"}


# ============ 权限管理 ============


@router.get("/permissions", response_model=list[PermissionSchema])
async def list_permissions(
    module: str = None,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("role:read")),
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
    _: User = Depends(require_permissions("role:create")),
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
    _: User = Depends(require_permissions("role:read")),
):
    """获取角色拥有的权限"""
    result = await db.execute(select(Role).options(selectinload(Role.permissions)).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    return role.permissions


@router.put("/roles/{role_id}/permissions")
async def update_role_permissions(
    role_id: int,
    data: PermissionAssign,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("role:update")),
):
    """更新角色权限（覆盖式）"""
    result = await db.execute(select(Role).where(Role.id == role_id))
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    if role.is_system and role.code == "ADMIN":
        raise HTTPException(status_code=400, detail="ADMIN 系统角色权限不可修改")

    # 先验证所有权限码是否有效，避免清空后发现无效码导致权限丢失
    valid_perms = []
    invalid_codes = []
    for perm_code in data.permission_codes:
        perm_result = await db.execute(select(Permission).where(Permission.code == perm_code))
        permission = perm_result.scalar_one_or_none()
        if permission:
            valid_perms.append(permission)
        else:
            invalid_codes.append(perm_code)

    if invalid_codes:
        raise HTTPException(status_code=400, detail=f"以下权限码不存在: {', '.join(invalid_codes)}")

    # 验证通过后再清空现有权限
    await db.execute(sa_delete(RolePermissionMapping).where(RolePermissionMapping.role_id == role_id))

    # 分配新权限（按 permission_id 去重，避免唯一索引冲突）
    seen_perm_ids = set()
    for permission in valid_perms:
        if permission.id in seen_perm_ids:
            continue
        seen_perm_ids.add(permission.id)
        mapping = RolePermissionMapping(role_id=role_id, permission_id=permission.id)
        db.add(mapping)

    await db.commit()
    return {"message": "权限分配成功", "permission_count": len(seen_perm_ids)}


# 兼容旧 POST 接口（保持向后兼容）
@router.post("/roles/{role_id}/permissions")
async def assign_permissions_to_role(
    role_id: int,
    data: PermissionAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("role:update")),
):
    """为角色分配权限（覆盖式）- POST 兼容接口"""
    return await update_role_permissions(role_id, data, db, current_user)


# ============ 用户角色管理 ============


@router.get("/users/{user_id}/roles", response_model=list[UserRoleSchema])
async def get_user_roles(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_permissions("user:read")),
):
    """获取用户的所有角色（多对多）"""
    user_result = await db.execute(select(User).where(User.id == user_id))
    if not user_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="用户不存在")

    result = await db.execute(
        select(
            UserRole.user_id,
            UserRole.role_id,
            Role.code,
            Role.name,
            Role.display_name,
            UserRole.assigned_at,
            UserRole.assigned_by,
        )
        .join(Role, UserRole.role_id == Role.id)
        .where(UserRole.user_id == user_id)
        .order_by(UserRole.assigned_at)
    )
    rows = result.all()
    return [
        UserRoleSchema(
            user_id=row[0],
            role_id=row[1],
            role_code=row[2],
            role_name=row[3],
            display_name=row[4],
            assigned_at=row[5],
            assigned_by=row[6],
        )
        for row in rows
    ]


@router.put("/users/{user_id}/roles")
async def assign_user_roles(
    user_id: int,
    data: UserRoleMultiAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("user:assign_role")),
):
    """为用户分配多个角色（覆盖式，仅 ADMIN）"""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 校验所有角色是否存在
    if data.role_ids:
        roles_result = await db.execute(select(Role.id).where(Role.id.in_(data.role_ids)))
        valid_role_ids = {row[0] for row in roles_result.all()}
        invalid_ids = set(data.role_ids) - valid_role_ids
        if invalid_ids:
            raise HTTPException(status_code=400, detail=f"以下角色ID不存在: {sorted(invalid_ids)}")

    # 覆盖式：先清空再写入（去重，避免复合主键冲突）
    await db.execute(sa_delete(UserRole).where(UserRole.user_id == user_id))
    seen_role_ids = set()
    for rid in data.role_ids:
        if rid in seen_role_ids:
            continue
        seen_role_ids.add(rid)
        db.add(UserRole(user_id=user_id, role_id=rid, assigned_by=current_user.id))

    await db.commit()
    return {"message": f"已为用户 {user.username} 分配 {len(seen_role_ids)} 个角色"}


# 兼容旧单角色分配接口（同时更新 user_roles 与 role_id）
@router.put("/users/{user_id}/role")
async def assign_role_to_user(
    user_id: int,
    data: UserRoleAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("user:assign_role")),
):
    """为用户分配单个角色（兼容旧接口，同时写入 role_id 与 user_roles）"""
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    role_result = await db.execute(select(Role).where(Role.id == data.role_id))
    role = role_result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="角色不存在")

    # 更新旧 role_id 字段
    user.role_id = data.role_id

    # 同步写入 user_roles（如不存在）
    existing = await db.execute(select(UserRole).where(UserRole.user_id == user_id, UserRole.role_id == data.role_id))
    if not existing.scalar_one_or_none():
        db.add(UserRole(user_id=user_id, role_id=data.role_id, assigned_by=current_user.id))

    await db.commit()
    return {"message": f"已为用户 {user.username} 分配角色 {role.display_name}"}


# ============ 当前用户权限 ============


@router.get("/users/me/permissions", response_model=UserPermissionsResponse)
async def get_my_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户权限（前端用于按钮控制，仅需登录）"""
    perm_set = await get_user_permissions(current_user, db)

    # 聚合角色代码用于展示
    role_codes: list[str] = []
    if current_user.is_super_admin:
        role_codes.append("SUPER_ADMIN")
    if current_user.is_admin:
        role_codes.append("ADMIN")

    if current_user.role_id:
        r = await db.execute(select(Role.code, Role.name).where(Role.id == current_user.role_id))
        row = r.first()
        if row:
            role_codes.append(row[0] or row[1])

    ur_result = await db.execute(
        select(Role.code, Role.name)
        .join(UserRole, UserRole.role_id == Role.id)
        .where(UserRole.user_id == current_user.id)
    )
    for code, name in ur_result.all():
        role_codes.append(code or name)

    # 去重保序
    seen = set()
    unique_roles = []
    for rc in role_codes:
        if rc and rc not in seen:
            seen.add(rc)
            unique_roles.append(rc)

    is_admin = (
        current_user.is_super_admin
        or current_user.is_admin
        or bool({"ADMIN", "admin", "SUPER_ADMIN"} & set(unique_roles))
    )

    return UserPermissionsResponse(
        user_id=current_user.id,
        username=current_user.username,
        roles=unique_roles,
        permissions=sorted(perm_set),
        is_admin=is_admin,
    )
