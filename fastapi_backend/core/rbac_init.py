"""
RBAC 预置数据初始化（幂等）

在应用启动时调用 ``init_rbac_data()`` 检查并创建预置角色与权限。
已存在则跳过，保证可重复执行而不破坏已分配的权限。

预置角色：
- ADMIN：所有权限
- TESTER：用例/场景/套件 CRUD + 执行，不能管理用户和角色
- VIEWER：只读权限 + 执行权限

权限按模块组织：case / scenario / suite / environment / variable /
mock / schedule / audit / user / role。
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.models import Permission, Role, RolePermissionMapping

_logger = logging.getLogger(__name__)

# ============ 预置权限定义 ============
# 结构: (code, name, description, module, action)
PRESET_PERMISSIONS: list[tuple[str, str, str, str, str]] = [
    # case: 接口用例
    ("case:create", "创建用例", "创建接口测试用例", "case", "create"),
    ("case:read", "查看用例", "查看用例详情与列表", "case", "read"),
    ("case:update", "编辑用例", "修改用例内容", "case", "update"),
    ("case:delete", "删除用例", "删除用例", "case", "delete"),
    ("case:execute", "执行用例", "执行单个用例", "case", "execute"),
    ("case:import", "导入用例", "导入 Postman/Swagger 用例", "case", "import"),
    ("case:export", "导出用例", "导出用例数据", "case", "export"),
    # scenario: 测试场景
    ("scenario:create", "创建场景", "创建测试场景", "scenario", "create"),
    ("scenario:read", "查看场景", "查看场景详情", "scenario", "read"),
    ("scenario:update", "编辑场景", "修改场景", "scenario", "update"),
    ("scenario:delete", "删除场景", "删除场景", "scenario", "delete"),
    ("scenario:execute", "执行场景", "执行测试场景", "scenario", "execute"),
    # suite: 回归套件
    ("suite:create", "创建套件", "创建回归套件", "suite", "create"),
    ("suite:read", "查看套件", "查看套件详情", "suite", "read"),
    ("suite:update", "编辑套件", "修改套件", "suite", "update"),
    ("suite:delete", "删除套件", "删除套件", "suite", "delete"),
    ("suite:execute", "执行套件", "执行回归套件", "suite", "execute"),
    ("suite:schedule", "配置套件定时执行", "创建、修改或暂停服务端回归套件定时任务", "suite", "schedule"),
    ("webhook:manage", "管理回归 Webhook", "创建、停用和轮换回归套件的外部 Webhook 密钥", "webhook", "manage"),
    # artifact: 执行产物
    ("artifact:download", "下载执行产物", "查看或下载已授权执行的截图、日志和追踪文件", "artifact", "download"),
    # execution: execution records are shared infrastructure, not suite-only metadata
    ("execution:read", "查看执行记录", "查看自动化执行状态、步骤和事件", "execution", "read"),
    ("execution:cancel", "取消执行", "请求取消仍在运行的自动化执行", "execution", "cancel"),
    # capture: 浏览器流量捕获
    ("capture:create", "创建流量捕获", "创建并写入已脱敏的浏览器流量捕获会话", "capture", "create"),
    ("capture:export", "导出流量捕获", "查看捕获候选并转换为接口测试资产", "capture", "export"),
    # ui: 桌面 UI 自动化资产与执行
    ("ui:read", "查看 UI 自动化", "查看 UI 用例、套件、运行记录与缺陷报告", "ui", "read"),
    ("ui:write", "编辑 UI 自动化", "创建、编辑、版本化 UI 用例、套件和标注", "ui", "write"),
    ("ui:execute", "执行 UI 自动化", "创建 UI 执行并上报受控桌面端运行事件", "ui", "execute"),
    ("ui:agent", "管理 UI Agent", "注册和查看所属桌面 Agent", "ui", "agent"),
    # ai: 受控辅助分析
    ("ai:analyze", "AI 测试分析", "请求脱敏后的失败归因、定位器建议和需求测试点生成", "ai", "analyze"),
    ("ai:feedback", "AI 分析反馈", "提交人工归因修正并查看本人反馈质量指标", "ai", "feedback"),
    # environment: 环境配置
    ("environment:create", "创建环境", "创建测试环境", "environment", "create"),
    ("environment:read", "查看环境", "查看环境配置", "environment", "read"),
    ("environment:update", "编辑环境", "修改环境配置", "environment", "update"),
    ("environment:delete", "删除环境", "删除环境", "environment", "delete"),
    # variable: 全局变量
    ("variable:create", "创建变量", "创建全局变量", "variable", "create"),
    ("variable:read", "查看变量", "查看全局变量", "variable", "read"),
    ("variable:update", "编辑变量", "修改全局变量", "variable", "update"),
    ("variable:delete", "删除变量", "删除全局变量", "variable", "delete"),
    # mock: Mock 服务
    ("mock:create", "创建Mock", "创建 Mock 接口", "mock", "create"),
    ("mock:read", "查看Mock", "查看 Mock 配置", "mock", "read"),
    ("mock:update", "编辑Mock", "修改 Mock 配置", "mock", "update"),
    ("mock:delete", "删除Mock", "删除 Mock 接口", "mock", "delete"),
    ("mock:fault-inject", "注入Mock故障", "配置受控 Mock 故障注入", "mock", "fault-inject"),
    # schedule: 定时任务
    ("schedule:create", "创建定时任务", "创建调度任务", "schedule", "create"),
    ("schedule:read", "查看定时任务", "查看调度任务", "schedule", "read"),
    ("schedule:update", "编辑定时任务", "修改调度任务", "schedule", "update"),
    ("schedule:delete", "删除定时任务", "删除调度任务", "schedule", "delete"),
    # audit: 审计日志
    ("audit:read", "查看审计", "查看审计日志", "audit", "read"),
    ("audit:export", "导出审计", "导出审计日志", "audit", "export"),
    # user: 用户管理
    ("user:read", "查看用户", "查看用户信息", "user", "read"),
    ("user:assign_role", "分配角色", "为用户分配角色", "user", "assign_role"),
    # role: 角色管理
    ("role:create", "创建角色", "创建角色", "role", "create"),
    ("role:read", "查看角色", "查看角色与权限", "role", "read"),
    ("role:update", "编辑角色", "修改角色", "role", "update"),
    ("role:delete", "删除角色", "删除角色", "role", "delete"),
]

# ============ 预置角色定义 ============
# 结构: (name, code, display_name, description, is_system)
PRESET_ROLES: list[tuple[str, str, str, str, bool]] = [
    ("admin", "ADMIN", "管理员", "系统管理员，拥有所有权限", True),
    ("tester", "TESTER", "测试员", "测试人员，拥有测试相关 CRUD 与执行权限，不能管理用户和角色", True),
    ("viewer", "VIEWER", "观察者", "只读权限 + 执行权限", True),
]

# 角色代码 → 该角色拥有的权限代码列表
# 使用通配 "*" 标记 ADMIN 拥有全部权限（实际写入所有预置权限码）
VIEWER_PERMS = [
    "case:read",
    "case:execute",
    "case:export",
    "scenario:read",
    "scenario:execute",
    "suite:read",
    "suite:execute",
    "artifact:download",
    "execution:read",
    "capture:create",
    "capture:export",
    "ui:read",
    "environment:read",
    "variable:read",
    "mock:read",
    "schedule:read",
    "audit:read",
    "user:read",
    "role:read",
]

TESTER_PERMS = [
    # 用例全权限
    "case:create",
    "case:read",
    "case:update",
    "case:delete",
    "case:execute",
    "case:import",
    "case:export",
    # 场景全权限
    "scenario:create",
    "scenario:read",
    "scenario:update",
    "scenario:delete",
    "scenario:execute",
    # 套件全权限
    "suite:create",
    "suite:read",
    "suite:update",
    "suite:delete",
    "suite:execute",
    "suite:schedule",
    "webhook:manage",
    "artifact:download",
    "execution:read",
    "execution:cancel",
    "capture:create",
    "capture:export",
    "ui:read",
    "ui:write",
    "ui:execute",
    "ui:agent",
    "ai:analyze",
    "ai:feedback",
    # 环境/变量/Mock/调度 CRUD（无用户/角色管理）
    "environment:create",
    "environment:read",
    "environment:update",
    "environment:delete",
    "variable:create",
    "variable:read",
    "variable:update",
    "variable:delete",
    "mock:create",
    "mock:read",
    "mock:update",
    "mock:delete",
    "mock:fault-inject",
    "schedule:create",
    "schedule:read",
    "schedule:update",
    "schedule:delete",
    # 审计只读
    "audit:read",
    # 用户只读
    "user:read",
    "role:read",
]

ROLE_PERMISSION_MAP: dict[str, list[str]] = {
    "ADMIN": [],  # 特殊处理：写入所有预置权限码
    "TESTER": TESTER_PERMS,
    "VIEWER": VIEWER_PERMS,
}

# These permissions were mistakenly granted to the built-in VIEWER role in an
# earlier release. Keep the explicit revocation so existing deployments are
# repaired during startup as well as fresh deployments.
_VIEWER_REVOKED_PRESET_PERMS = {"suite:schedule", "webhook:manage"}


async def _ensure_permissions(db: AsyncSession) -> dict[str, int]:
    """创建缺失的预置权限，返回 code→id 映射。"""
    result = await db.execute(select(Permission.code, Permission.id))
    existing = {code: pid for code, pid in result.all()}

    created = 0
    for code, name, desc, module, action in PRESET_PERMISSIONS:
        if code in existing:
            continue
        db.add(
            Permission(
                code=code,
                name=name,
                description=desc,
                module=module,
                action=action,
            )
        )
        created += 1
    if created:
        await db.flush()
    # 重新查询得到完整映射
    result = await db.execute(select(Permission.code, Permission.id))
    return {code: pid for code, pid in result.all()}


async def _ensure_roles(db: AsyncSession) -> dict[str, int]:
    """创建缺失的预置角色，返回 code→id 映射。"""
    result = await db.execute(select(Role.code, Role.name, Role.id))
    existing_by_code: dict[str, int] = {}
    existing_by_name: dict[str, int] = {}
    for code, name, rid in result.all():
        if code:
            existing_by_code[code] = rid
        if name:
            existing_by_name[name] = rid

    created = 0
    for name, code, display_name, desc, is_system in PRESET_ROLES:
        # Historic installations only stored the lowercase role name. Reuse
        # that role instead of inserting a duplicate name during startup.
        if code in existing_by_code or name in existing_by_name:
            continue
        db.add(
            Role(
                name=name,
                code=code,
                display_name=display_name,
                description=desc,
                is_system=is_system,
            )
        )
        created += 1
    if created:
        await db.flush()
    # 重新查询得到完整映射
    result = await db.execute(select(Role.code, Role.name, Role.id))
    role_ids_by_code: dict[str, int] = {}
    role_ids_by_name: dict[str, int] = {}
    for code, name, rid in result.all():
        if code:
            role_ids_by_code[code] = rid
        if name:
            role_ids_by_name[name] = rid

    mapping: dict[str, int] = {}
    for name, code, _display_name, _desc, _is_system in PRESET_ROLES:
        role_id = role_ids_by_code.get(code) or role_ids_by_name.get(name)
        if role_id is not None:
            mapping[code] = role_id
    return mapping


async def _sync_role_permissions(
    db: AsyncSession,
    role_map: dict[str, int],
    perm_map: dict[str, int],
) -> None:
    """同步预置角色的权限分配（仅对系统预置角色，覆盖式写入）。"""
    for _name, role_code, _display, _desc, _is_system in PRESET_ROLES:
        role_id = role_map.get(role_code)
        if role_id is None:
            continue

        # ADMIN 拥有所有预置权限
        if role_code == "ADMIN":
            desired_perm_ids = set(perm_map.values())
            desired_codes = list(perm_map.keys())
        else:
            desired_codes = ROLE_PERMISSION_MAP.get(role_code, [])
            desired_perm_ids = {perm_map[c] for c in desired_codes if c in perm_map}

        # 查询当前已分配的权限 ID
        result = await db.execute(
            select(RolePermissionMapping.permission_id).where(RolePermissionMapping.role_id == role_id)
        )
        existing_perm_ids = {row[0] for row in result.all()}

        # 补齐缺失的权限（不删除用户自定义追加的权限，仅补齐预置项）
        to_add = desired_perm_ids - existing_perm_ids
        for perm_id in to_add:
            db.add(RolePermissionMapping(role_id=role_id, permission_id=perm_id))
        if role_code == "VIEWER":
            revoked_ids = {perm_map[code] for code in _VIEWER_REVOKED_PRESET_PERMS if code in perm_map}
            if revoked_ids:
                await db.execute(
                    delete(RolePermissionMapping).where(
                        RolePermissionMapping.role_id == role_id,
                        RolePermissionMapping.permission_id.in_(revoked_ids),
                    )
                )
    await db.flush()


async def init_rbac_data(session_factory: Any = None) -> None:
    """初始化 RBAC 预置数据（幂等）。

    :param session_factory: 可选的 async_sessionmaker。为空时使用默认 AsyncSessionLocal。
    """
    from fastapi_backend.core.database import AsyncSessionLocal

    factory = session_factory or AsyncSessionLocal
    try:
        async with factory() as db:
            perm_map = await _ensure_permissions(db)
            role_map = await _ensure_roles(db)
            await _sync_role_permissions(db, role_map, perm_map)
            await db.commit()
        _logger.info(
            "RBAC 预置数据初始化完成：角色 %d 个，权限 %d 个",
            len(role_map),
            len(perm_map),
        )
    except Exception as exc:
        _logger.warning("RBAC 预置数据初始化失败（不影响主服务启动）: %s", exc)
        try:
            async with factory() as db:
                await db.rollback()
        except Exception:
            pass
