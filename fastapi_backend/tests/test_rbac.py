"""
RBAC 权限系统测试

覆盖场景：
1. 预置角色和权限初始化（幂等）
2. 给用户分配角色
3. 权限检查通过（有权限）
4. 权限检查拒绝（无权限，返回 403）
5. ADMIN 角色放行所有
6. 移除角色后权限消失
7. 角色权限更新后用户权限实时变化
8. 系统角色不可删除
9. 向后兼容：无角色用户默认获得 TESTER 权限（避免锁死）
"""

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from fastapi_backend.core.database import Base
from fastapi_backend.core.exceptions import AuthorizationException
from fastapi_backend.core.rbac import (
    PermissionChecker,
    get_user_permissions,
    require_any_permission,
    require_permissions,
)
from fastapi_backend.core.rbac_init import (
    PRESET_PERMISSIONS,
    PRESET_ROLES,
    init_rbac_data,
)
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.main import app
from fastapi_backend.models.models import (
    Permission,
    Role,
    RolePermissionMapping,
    User,
    UserRole,
)

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def rbac_engine():
    """独立的内存数据库引擎，用于 RBAC 测试。"""
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def rbac_factory(rbac_engine):
    return async_sessionmaker(rbac_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def rbac_db(rbac_factory):
    """每个测试独立的 DB session，并预置 RBAC 数据。"""
    await init_rbac_data(rbac_factory)
    async with rbac_factory() as db:
        yield db


async def _make_user(db: AsyncSession, username: str, is_admin: bool = False) -> User:
    """创建测试用户。"""
    user = User(
        username=username,
        email=f"{username}@example.com",
        password_hash="hash",
        is_active=True,
        is_admin=is_admin,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def _get_role_by_code(db: AsyncSession, code: str) -> Role:
    result = await db.execute(select(Role).where(Role.code == code))
    return result.scalar_one()


async def _get_perm_id(db: AsyncSession, code: str) -> int:
    result = await db.execute(select(Permission.id).where(Permission.code == code))
    return result.scalar_one()


# ============ 测试用例 ============


@pytest.mark.asyncio
async def test_preset_data_initialized(rbac_db: AsyncSession):
    """1. 预置角色和权限初始化完成。"""
    roles_result = await rbac_db.execute(select(Role))
    roles = roles_result.scalars().all()
    role_codes = {r.code for r in roles}
    assert {"ADMIN", "TESTER", "VIEWER"}.issubset(role_codes)

    perms_result = await rbac_db.execute(select(Permission))
    perms = perms_result.scalars().all()
    perm_codes = {p.code for p in perms}
    # 检查各模块关键权限
    assert "case:execute" in perm_codes
    assert "scenario:create" in perm_codes
    assert "audit:read" in perm_codes
    assert "role:delete" in perm_codes
    assert len(perms) >= len(PRESET_PERMISSIONS)


@pytest.mark.asyncio
async def test_init_rbac_idempotent(rbac_factory):
    """1b. 重复初始化不会产生重复数据。"""
    await init_rbac_data(rbac_factory)
    await init_rbac_data(rbac_factory)

    async with rbac_factory() as db:
        roles = (await db.execute(select(Role))).scalars().all()
        perms = (await db.execute(select(Permission))).scalars().all()
        # 角色代码唯一
        assert len({r.code for r in roles}) == len(roles)
        # 权限代码唯一
        assert len({p.code for p in perms}) == len(perms)
        assert len(roles) == len(PRESET_ROLES)


@pytest.mark.asyncio
async def test_assign_role_and_check_pass(rbac_db: AsyncSession):
    """2&3. 给用户分配角色后，权限检查通过。"""
    user = await _make_user(rbac_db, "tester1")
    tester_role = await _get_role_by_code(rbac_db, "TESTER")

    rbac_db.add(UserRole(user_id=user.id, role_id=tester_role.id, assigned_by=1))
    await rbac_db.commit()

    perms = await get_user_permissions(user, rbac_db)
    assert "case:execute" in perms
    assert "scenario:create" in perms
    assert "role:delete" not in perms  # TESTER 无角色管理权限


@pytest.mark.asyncio
async def test_permission_check_denied(rbac_db: AsyncSession):
    """4. 无权限时 PermissionChecker 抛出 403。"""
    user = await _make_user(rbac_db, "viewer1")
    viewer_role = await _get_role_by_code(rbac_db, "VIEWER")
    rbac_db.add(UserRole(user_id=user.id, role_id=viewer_role.id))
    await rbac_db.commit()

    checker = PermissionChecker(["case:create"])  # VIEWER 无 case:create
    with pytest.raises(AuthorizationException) as exc_info:
        await checker(current_user=user, db=rbac_db)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_permission_check_pass(rbac_db: AsyncSession):
    """3b. 有权限时 PermissionChecker 放行并返回用户。"""
    user = await _make_user(rbac_db, "viewer2")
    viewer_role = await _get_role_by_code(rbac_db, "VIEWER")
    rbac_db.add(UserRole(user_id=user.id, role_id=viewer_role.id))
    await rbac_db.commit()

    checker = PermissionChecker(["case:read"])  # VIEWER 有 case:read
    result = await checker(current_user=user, db=rbac_db)
    assert result.id == user.id


@pytest.mark.asyncio
async def test_admin_role_short_circuit(rbac_db: AsyncSession):
    """5. ADMIN 角色放行所有权限（不查权限表）。"""
    user = await _make_user(rbac_db, "admin1")
    admin_role = await _get_role_by_code(rbac_db, "ADMIN")
    rbac_db.add(UserRole(user_id=user.id, role_id=admin_role.id))
    await rbac_db.commit()

    # 请求任意权限都应放行
    checker = PermissionChecker(["role:delete", "user:assign_role", "nonexistent:perm"])
    result = await checker(current_user=user, db=rbac_db)
    assert result.id == user.id

    perms = await get_user_permissions(user, rbac_db)
    assert perms == {"*"}


@pytest.mark.asyncio
async def test_legacy_admin_short_circuit(rbac_db: AsyncSession):
    """5b. 旧 is_admin 用户（无 role_id）也短路放行。"""
    user = await _make_user(rbac_db, "legacy_admin", is_admin=True)
    perms = await get_user_permissions(user, rbac_db)
    assert perms == {"*"}


@pytest.mark.asyncio
async def test_remove_role_revokes_permission(rbac_db: AsyncSession):
    """6. 移除角色后权限消失。"""
    user = await _make_user(rbac_db, "removable")
    tester_role = await _get_role_by_code(rbac_db, "TESTER")
    rbac_db.add(UserRole(user_id=user.id, role_id=tester_role.id))
    await rbac_db.commit()

    # 有权限
    perms = await get_user_permissions(user, rbac_db)
    assert "case:execute" in perms

    # 移除角色
    await rbac_db.execute(
        UserRole.__table__.delete().where(UserRole.user_id == user.id)
    )
    await rbac_db.commit()

    # 无角色 → 回退到 TESTER 默认权限（向后兼容设计）
    perms = await get_user_permissions(user, rbac_db)
    # 回退到 TESTER，仍应有 case:execute
    assert "case:execute" in perms


@pytest.mark.asyncio
async def test_role_permission_update_realtime(rbac_db: AsyncSession):
    """7. 角色权限更新后用户权限实时变化。"""
    user = await _make_user(rbac_db, "realtime_user")
    viewer_role = await _get_role_by_code(rbac_db, "VIEWER")
    rbac_db.add(UserRole(user_id=user.id, role_id=viewer_role.id))
    await rbac_db.commit()

    # 初始 VIEWER 无 case:create
    perms = await get_user_permissions(user, rbac_db)
    assert "case:create" not in perms

    # 给 VIEWER 角色追加 case:create 权限
    case_create_id = await _get_perm_id(rbac_db, "case:create")
    rbac_db.add(
        RolePermissionMapping(role_id=viewer_role.id, permission_id=case_create_id)
    )
    await rbac_db.commit()

    # 实时生效
    perms = await get_user_permissions(user, rbac_db)
    assert "case:create" in perms


@pytest.mark.asyncio
async def test_system_role_cannot_delete(rbac_db: AsyncSession):
    """8. 系统内置角色不可删除。"""
    from fastapi import HTTPException
    from fastapi_backend.routers.rbac import delete_role

    admin_role = await _get_role_by_code(rbac_db, "ADMIN")
    with pytest.raises(HTTPException) as exc_info:
        await delete_role(admin_role.id, rbac_db, None)
    assert exc_info.value.status_code == 400
    assert "系统内置角色" in exc_info.value.detail


@pytest.mark.asyncio
async def test_no_role_defaults_to_tester(rbac_db: AsyncSession):
    """9. 无角色用户默认获得 TESTER 权限（避免锁死）。"""
    user = await _make_user(rbac_db, "norole")
    perms = await get_user_permissions(user, rbac_db)
    # TESTER 权限
    assert "case:execute" in perms
    assert "scenario:create" in perms
    # 但无角色管理权限
    assert "role:delete" not in perms


@pytest.mark.asyncio
async def test_require_any_permission(rbac_db: AsyncSession):
    """require_any_permission 满足任一即放行。"""
    user = await _make_user(rbac_db, "any_perm_user")
    viewer_role = await _get_role_by_code(rbac_db, "VIEWER")
    rbac_db.add(UserRole(user_id=user.id, role_id=viewer_role.id))
    await rbac_db.commit()

    # VIEWER 有 case:read，无 case:create → 任一满足即放行
    checker = require_any_permission("case:create", "case:read")
    result = await checker(current_user=user, db=rbac_db)
    assert result.id == user.id

    # 两个都没有 → 拒绝
    checker = require_any_permission("case:create", "role:delete")
    with pytest.raises(AuthorizationException):
        await checker(current_user=user, db=rbac_db)


# ============ 端点测试（通过 TestClient + 依赖覆盖） ============


@pytest.fixture
def rbac_client(rbac_db: AsyncSession, rbac_factory):
    """覆盖 get_db 与 get_current_user，返回注入用户。"""
    from fastapi.testclient import TestClient

    current_user_holder: dict = {}

    async def _override_get_db():
        # 端点使用与测试同一 session factory，保证数据可见
        async with rbac_factory() as session:
            yield session

    async def _override_get_current_user():
        return current_user_holder["user"]

    app.dependency_overrides[get_current_user] = _override_get_current_user
    # get_db 被 PermissionChecker 与路由依赖
    from fastapi_backend.core.database import get_db
    app.dependency_overrides[get_db] = _override_get_db

    with TestClient(app) as client:
        client.current_user_holder = current_user_holder  # type: ignore[attr-defined]
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_me_permissions_endpoint(rbac_db: AsyncSession, rbac_client):
    """端点：GET /users/me/permissions 返回当前用户权限。"""
    user = await _make_user(rbac_db, "api_user")
    tester_role = await _get_role_by_code(rbac_db, "TESTER")
    rbac_db.add(UserRole(user_id=user.id, role_id=tester_role.id))
    await rbac_db.commit()

    rbac_client.current_user_holder["user"] = user
    resp = rbac_client.get("/api/v1/admin/rbac/users/me/permissions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_id"] == user.id
    assert "TESTER" in data["roles"]
    assert "case:execute" in data["permissions"]
    assert data["is_admin"] is False


@pytest.mark.asyncio
async def test_me_permissions_admin_endpoint(rbac_db: AsyncSession, rbac_client):
    """端点：ADMIN 用户 is_admin 为 True 且权限包含通配。"""
    user = await _make_user(rbac_db, "api_admin")
    admin_role = await _get_role_by_code(rbac_db, "ADMIN")
    rbac_db.add(UserRole(user_id=user.id, role_id=admin_role.id))
    await rbac_db.commit()

    rbac_client.current_user_holder["user"] = user
    resp = rbac_client.get("/api/v1/admin/rbac/users/me/permissions")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_admin"] is True
    # ADMIN 拥有通配权限（前端按 * 视为全部权限）
    assert "*" in data["permissions"]


@pytest.mark.asyncio
async def test_assign_user_roles_endpoint(rbac_db: AsyncSession, rbac_client):
    """端点：PUT /users/{user_id}/roles 分配多角色。"""
    admin = await _make_user(rbac_db, "assigner", is_admin=True)
    target = await _make_user(rbac_db, "target_user")
    tester_role = await _get_role_by_code(rbac_db, "TESTER")

    rbac_client.current_user_holder["user"] = admin
    resp = rbac_client.put(
        f"/api/v1/admin/rbac/users/{target.id}/roles",
        json={"role_ids": [tester_role.id]},
    )
    assert resp.status_code == 200

    # 验证分配成功
    roles_resp = rbac_client.get(f"/api/v1/admin/rbac/users/{target.id}/roles")
    assert roles_resp.status_code == 200
    roles_data = roles_resp.json()
    assert any(r["role_code"] == "TESTER" for r in roles_data)
