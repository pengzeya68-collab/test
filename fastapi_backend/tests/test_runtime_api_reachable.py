"""
FastAPI TestClient 运行时可达性验证

用真实 HTTP 请求验证所有新增 API 端点的端到端可达性，
覆盖之前单元测试（mock 了数据库和路由）的盲区：
- 路由是否成功注册
- 依赖注入是否可解析
- 中间件是否正常
- 路径前缀是否匹配

策略：不带认证发请求，预期 401/403（需认证）或 200（公开），
关键检查：不应返回 404（路由未注册）或 500（运行时错误）。
"""

import os
import sys

# 必须在导入 app 之前设置环境变量，避免 lifespan 执行建表等副作用
os.environ.setdefault("ENVIRONMENT", "testing")

sys.path.insert(0, r"c:\Users\lenovo\Desktop\TestMasterProject")

import pytest
from fastapi.testclient import TestClient

# 尝试导入 app
try:
    from fastapi_backend.main import app
    HAS_APP = True
    IMPORT_ERROR = ""
except Exception as e:
    HAS_APP = False
    IMPORT_ERROR = f"{type(e).__name__}: {e}"


@pytest.fixture(scope="module", autouse=True)
def _ensure_tables():
    """确保测试数据库表存在（模拟生产环境 Alembic 迁移后的状态）。

    在 testing 模式下 lifespan 跳过建表，导致公开端点（如 api-docs/shared）
    直接查表时返回 500。此 fixture 用同步引擎补齐缺失的表，create_all 幂等。
    """
    if not HAS_APP:
        return
    from sqlalchemy import create_engine

    from fastapi_backend.core.config import settings
    from fastapi_backend.core.database import Base

    # 将 async 驱动替换为 sync 驱动
    sync_url = settings.DATABASE_URL.replace("+aiosqlite", "").replace("+asyncpg", "")
    sync_engine = create_engine(sync_url)
    try:
        Base.metadata.create_all(sync_engine)
    finally:
        sync_engine.dispose()


@pytest.fixture(scope="module")
def client(_ensure_tables):
    """创建不覆盖任何依赖的 TestClient，测试真实运行时行为"""
    if not HAS_APP:
        pytest.skip(f"无法导入 app: {IMPORT_ERROR}")
    with TestClient(app) as c:
        yield c


# ========== 预期路由清单 ==========
# (method, path, 允许的状态码集合, 描述)
EXPECTED_ROUTES = [
    # 1. 接口分组管理
    ("GET",    "/api/auto-test/groups/tree",                 {200, 401, 403}, "分组树"),
    ("POST",   "/api/auto-test/groups",                      {201, 401, 403, 422}, "创建分组"),
    ("PUT",    "/api/auto-test/groups/1",                    {200, 401, 403, 404, 422}, "更新分组"),
    ("DELETE", "/api/auto-test/groups/1",                    {200, 401, 403, 404}, "删除分组"),
    ("PUT",    "/api/auto-test/groups/1/move",               {200, 401, 403, 404, 422}, "移动分组"),

    # 2. 接口版本管理
    ("GET",    "/api/auto-test/cases/1/versions",            {200, 401, 403, 404}, "版本列表"),
    ("POST",   "/api/auto-test/cases/1/versions",            {201, 401, 403, 404, 422}, "创建版本"),
    ("GET",    "/api/auto-test/cases/1/versions/1",          {200, 401, 403, 404}, "版本详情"),
    ("PUT",    "/api/auto-test/cases/1/versions/1/restore",  {200, 401, 403, 404}, "恢复版本"),
    ("DELETE", "/api/auto-test/cases/1/versions/1",          {204, 401, 403, 404}, "删除版本"),
    ("GET",    "/api/auto-test/cases/1/versions/diff?v1=1&v2=2", {200, 401, 403, 400, 404}, "版本对比"),

    # 3. API 文档
    ("GET",    "/api/auto-test/api-docs/openapi",            {200, 401, 403}, "OpenAPI 文档"),
    ("GET",    "/api/auto-test/api-docs/markdown",           {200, 401, 403}, "Markdown 文档"),
    ("GET",    "/api/auto-test/api-docs/html",               {200, 401, 403}, "HTML 文档"),
    ("POST",   "/api/auto-test/api-docs/share",              {200, 201, 401, 403, 422}, "创建分享链接"),
    ("GET",    "/api/auto-test/api-docs/shared/nonexistent-token-xyz", {200, 404, 410}, "公开访问分享文档"),

    # 4. RBAC
    ("GET",    "/api/v1/admin/rbac/roles",                   {200, 401, 403}, "角色列表"),
    ("POST",   "/api/v1/admin/rbac/roles",                   {200, 201, 401, 403, 422}, "创建角色"),
    ("GET",    "/api/v1/admin/rbac/permissions",             {200, 401, 403}, "权限列表"),
    ("GET",    "/api/v1/admin/rbac/users/me/permissions",    {200, 401, 403}, "当前用户权限"),

    # 5. 审计日志
    ("GET",    "/api/v1/admin/audit-logs",                   {200, 401, 403}, "审计日志列表"),
    ("GET",    "/api/v1/admin/audit-logs/stats",             {200, 401, 403}, "审计日志统计"),
    ("GET",    "/api/v1/admin/audit-logs/export",            {200, 401, 403}, "导出审计日志"),

    # 6. 环境继承
    ("GET",    "/api/auto-test/environments/1/effective-variables",  {200, 401, 403, 404}, "有效变量"),
    ("GET",    "/api/auto-test/environments/1/inheritance-chain",    {200, 401, 403, 404}, "继承链"),
]

# 用于路由注册检查的路径模板（去掉查询字符串）
ROUTE_PATHS = [
    "/api/auto-test/groups/tree",
    "/api/auto-test/groups",
    "/api/auto-test/groups/{group_id}",
    "/api/auto-test/groups/{group_id}/move",
    "/api/auto-test/cases/{case_id}/versions",
    "/api/auto-test/cases/{case_id}/versions/diff",
    "/api/auto-test/cases/{case_id}/versions/{version_id}",
    "/api/auto-test/cases/{case_id}/versions/{version_id}/restore",
    "/api/auto-test/api-docs/openapi",
    "/api/auto-test/api-docs/markdown",
    "/api/auto-test/api-docs/html",
    "/api/auto-test/api-docs/share",
    "/api/auto-test/api-docs/shared/{token}",
    "/api/v1/admin/rbac/roles",
    "/api/v1/admin/rbac/permissions",
    "/api/v1/admin/rbac/users/me/permissions",
    "/api/v1/admin/audit-logs",
    "/api/v1/admin/audit-logs/stats",
    "/api/v1/admin/audit-logs/export",
    "/api/auto-test/environments/{env_id}/effective-variables",
    "/api/auto-test/environments/{env_id}/inheritance-chain",
]


# ========== App 导入测试 ==========


def test_app_import_success():
    """验证 app 能成功导入（无循环导入、缺少依赖等问题）"""
    if not HAS_APP:
        pytest.fail(f"app 导入失败: {IMPORT_ERROR}")


# ========== 路由注册检查 ==========


def test_all_routes_registered(client):
    """验证所有预期路由都在 app.routes 中注册"""
    registered = {r.path for r in app.routes}
    missing = [p for p in ROUTE_PATHS if p not in registered]
    assert not missing, f"以下路由未注册: {missing}"


def test_openapi_schema_contains_paths(client):
    """验证 OpenAPI schema 包含所有新增端点"""
    schema = client.get("/api/openapi.json").json()
    paths = schema.get("paths", {})
    missing = [p for p in ROUTE_PATHS if p not in paths]
    assert not missing, f"以下路径不在 OpenAPI schema 中: {missing}"


# ========== 端点可达性测试 ==========


@pytest.mark.parametrize(
    "method, path, allowed_codes, desc",
    EXPECTED_ROUTES,
    ids=[f"{m} {d}" for m, _, _, d in EXPECTED_ROUTES],
)
def test_endpoint_reachable(client, method, path, allowed_codes, desc):
    """对每个端点发请求，验证路由可达（不返回 404/500）"""
    # 去掉查询字符串部分用于 404 判断
    base_path = path.split("?")[0]

    if method == "GET":
        r = client.get(path)
    elif method == "POST":
        r = client.post(path, json={})
    elif method == "PUT":
        r = client.put(path, json={})
    elif method == "DELETE":
        r = client.delete(path)
    else:
        pytest.fail(f"不支持的方法: {method}")

    # 关键断言：不应 404（路由未注册）
    assert r.status_code != 404 or base_path.endswith("nonexistent-token-xyz"), (
        f"[{method} {path}] {desc}: 返回 404，路由可能未注册"
    )
    # 不应 500（运行时错误）
    assert r.status_code != 500, (
        f"[{method} {path}] {desc}: 返回 500，运行时错误: {r.text[:300]}"
    )
    # 状态码应在允许范围内
    assert r.status_code in allowed_codes, (
        f"[{method} {path}] {desc}: 意外状态码 {r.status_code}，"
        f"预期 {sorted(allowed_codes)}，响应: {r.text[:300]}"
    )
