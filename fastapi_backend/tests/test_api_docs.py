"""
API 文档生成与分享功能测试

覆盖场景：
1. 从单个用例生成 OpenAPI
2. 从多个用例生成 OpenAPI
3. 按分组生成
4. Markdown 格式正确
5. HTML 包含必要内容
6. 分享链接创建和访问
7. 过期分享链接不可访问
8. 空用例列表处理
"""

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.database import Base as AutoTestBase
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.main import app
from fastapi_backend.models.autotest import ApiDocShare, AutoTestCase, AutoTestGroup

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
API_DOCS = "/api/auto-test/api-docs"


# ========== 公共 fixture ==========


@pytest_asyncio.fixture
async def docs_engine():
    """内存 SQLite 引擎，StaticPool 保证 :memory: 在同一连接内共享"""
    engine = create_async_engine(
        TEST_DB_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(AutoTestBase.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(AutoTestBase.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def docs_session_factory(docs_engine):
    return async_sessionmaker(docs_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
def docs_client(client, docs_session_factory):
    """覆盖 get_autotest_db 与 get_current_user，注入内存会话与 mock 用户"""

    async def _override_get_autotest_db():
        async with docs_session_factory() as session:
            yield session

    async def _override_current_user():
        return SimpleNamespace(
            id=1,
            username="tester",
            is_admin=False,
            is_super_admin=False,
            is_active=True,
            role_id=None,
        )

    app.dependency_overrides[get_autotest_db] = _override_get_autotest_db
    app.dependency_overrides[get_current_user] = _override_current_user
    try:
        yield client
    finally:
        app.dependency_overrides.pop(get_autotest_db, None)
        app.dependency_overrides.pop(get_current_user, None)


# ========== 辅助函数 ==========


async def _create_group(session_factory, name="用户服务", user_id=1):
    """直接通过 session 创建分组"""
    async with session_factory() as session:
        group = AutoTestGroup(name=name, user_id=user_id, sort_order=0)
        session.add(group)
        await session.commit()
        await session.refresh(group)
        return group


async def _create_case(
    session_factory,
    *,
    name="登录接口",
    method="POST",
    url="https://api.example.com/v1/login",
    group_id=None,
    user_id=1,
    headers=None,
    params=None,
    body_type="raw",
    content_type="application/json",
    payload=None,
    description="用户登录",
    response_schema=None,
):
    """直接通过 session 创建用例"""
    if payload is None and body_type != "none":
        payload = {"username": "admin", "password": "123456"}
    if response_schema is None:
        response_schema = {
            "type": "object",
            "properties": {"token": {"type": "string"}},
        }
    async with session_factory() as session:
        case = AutoTestCase(
            group_id=group_id,
            name=name,
            method=method,
            url=url,
            headers=headers or {"Authorization": "Bearer xxx", "X-Request-Id": "abc"},
            params=params or {"page": 1, "size": 10},
            body_type=body_type,
            content_type=content_type,
            payload=payload,
            description=description,
            response_schema=response_schema,
            user_id=user_id,
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)
        return case


# ========== 测试用例 ==========


class TestApiDocGeneration:
    """API 文档生成测试"""

    @pytest.mark.asyncio
    async def test_openapi_from_single_case(self, docs_client, docs_session_factory):
        """1. 从单个用例生成 OpenAPI"""
        case = await _create_case(docs_session_factory, name="登录", method="POST")
        resp = docs_client.get(f"{API_DOCS}/openapi", params={"case_ids": str(case.id)})
        assert resp.status_code == 200, resp.text
        spec = resp.json()
        assert spec["openapi"] == "3.0.0"
        assert "paths" in spec
        assert "/v1/login" in spec["paths"]
        operation = spec["paths"]["/v1/login"]["post"]
        assert operation["summary"] == "登录"
        assert operation["description"] == "用户登录"
        # 请求体应存在
        assert "requestBody" in operation
        # 响应应包含 200
        assert "200" in operation["responses"]
        # tags 应为默认分组
        assert operation["tags"] == ["default"]

    @pytest.mark.asyncio
    async def test_openapi_from_multiple_cases(self, docs_client, docs_session_factory):
        """2. 从多个用例生成 OpenAPI"""
        c1 = await _create_case(docs_session_factory, name="登录", method="POST", url="/api/login")
        c2 = await _create_case(
            docs_session_factory,
            name="获取用户",
            method="GET",
            url="/api/users/1",
            body_type="none",
            payload=None,
        )
        resp = docs_client.get(f"{API_DOCS}/openapi", params={"case_ids": f"{c1.id},{c2.id}"})
        assert resp.status_code == 200, resp.text
        spec = resp.json()
        paths = spec["paths"]
        assert "/api/login" in paths
        assert "/api/users/1" in paths
        assert "post" in paths["/api/login"]
        assert "get" in paths["/api/users/1"]
        # GET 用例不应有 requestBody
        assert "requestBody" not in paths["/api/users/1"]["get"]

    @pytest.mark.asyncio
    async def test_openapi_by_group(self, docs_client, docs_session_factory):
        """3. 按分组生成 OpenAPI（tag 应为分组名）"""
        group = await _create_group(docs_session_factory, name="用户服务")
        await _create_case(
            docs_session_factory,
            name="登录",
            method="POST",
            url="/api/login",
            group_id=group.id,
        )
        await _create_case(
            docs_session_factory,
            name="注册",
            method="POST",
            url="/api/register",
            group_id=group.id,
        )
        resp = docs_client.get(f"{API_DOCS}/openapi", params={"group_id": group.id})
        assert resp.status_code == 200, resp.text
        spec = resp.json()
        # 两个接口都在
        paths = spec["paths"]
        assert "/api/login" in paths
        assert "/api/register" in paths
        # tag 应为分组名 "用户服务"
        assert paths["/api/login"]["post"]["tags"] == ["用户服务"]
        # tags 顶层声明应包含分组
        tag_names = [t["name"] for t in spec["tags"]]
        assert "用户服务" in tag_names

    @pytest.mark.asyncio
    async def test_markdown_format(self, docs_client, docs_session_factory):
        """4. Markdown 格式正确"""
        group = await _create_group(docs_session_factory, name="用户服务")
        await _create_case(
            docs_session_factory,
            name="登录接口",
            method="POST",
            url="https://api.example.com/v1/login",
            group_id=group.id,
            description="用户登录接口",
        )
        resp = docs_client.get(f"{API_DOCS}/markdown", params={"group_id": group.id})
        assert resp.status_code == 200, resp.text
        md = resp.text
        # 标题
        assert "# TestMaster API 文档" in md
        # 分组名
        assert "## 用户服务" in md
        # 接口名
        assert "登录接口" in md
        # 请求方法与路径
        assert "`POST`" in md
        assert "/v1/login" in md
        # 请求头表格
        assert "请求头" in md
        # 代码块
        assert "```json" in md

    @pytest.mark.asyncio
    async def test_html_contains_required_content(self, docs_client, docs_session_factory):
        """5. HTML 包含必要内容（独立 HTML，含样式与脚本）"""
        group = await _create_group(docs_session_factory, name="用户服务")
        await _create_case(
            docs_session_factory,
            name="登录接口",
            method="POST",
            url="/api/login",
            group_id=group.id,
            description="用户登录",
        )
        resp = docs_client.get(f"{API_DOCS}/html", params={"group_id": group.id})
        assert resp.status_code == 200, resp.text
        html_doc = resp.text
        # 独立 HTML 结构
        assert "<!DOCTYPE html>" in html_doc
        assert "<html" in html_doc
        # 内联样式
        assert "<style>" in html_doc
        # 内联脚本（搜索功能）
        assert "filterApi" in html_doc
        # 标题
        assert "TestMaster API 文档" in html_doc
        # 分组名
        assert "用户服务" in html_doc
        # 接口名
        assert "登录接口" in html_doc
        # 方法徽标
        assert "m-post" in html_doc
        # 路径
        assert "/api/login" in html_doc

    @pytest.mark.asyncio
    async def test_empty_case_list_openapi(self, docs_client):
        """8. 空用例列表处理 - OpenAPI 返回空文档（不报错）"""
        resp = docs_client.get(f"{API_DOCS}/openapi")
        assert resp.status_code == 200, resp.text
        spec = resp.json()
        assert spec["openapi"] == "3.0.0"
        assert spec["paths"] == {}
        assert spec["tags"] == []

    @pytest.mark.asyncio
    async def test_empty_case_list_markdown(self, docs_client):
        """8. 空用例列表处理 - Markdown 返回提示"""
        resp = docs_client.get(f"{API_DOCS}/markdown")
        assert resp.status_code == 200, resp.text
        assert "暂无用例数据" in resp.text

    @pytest.mark.asyncio
    async def test_empty_case_list_html(self, docs_client):
        """8. 空用例列表处理 - HTML 返回空提示"""
        resp = docs_client.get(f"{API_DOCS}/html")
        assert resp.status_code == 200, resp.text
        assert "暂无用例数据" in resp.text

    @pytest.mark.asyncio
    async def test_case_without_response_schema_uses_default(self, docs_client, docs_session_factory):
        """向后兼容：用例无 response_schema 时，responses 给默认示例"""
        case = await _create_case(
            docs_session_factory,
            name="无Schema",
            method="GET",
            url="/api/ping",
            body_type="none",
            payload=None,
            response_schema=None,
        )
        resp = docs_client.get(f"{API_DOCS}/openapi", params={"case_ids": str(case.id)})
        assert resp.status_code == 200, resp.text
        spec = resp.json()
        op = spec["paths"]["/api/ping"]["get"]
        resp200 = op["responses"]["200"]
        # 默认响应应包含 example
        content = resp200["content"]["application/json"]
        assert "example" in content or "schema" in content


class TestApiDocShare:
    """API 文档分享功能测试"""

    @pytest.mark.asyncio
    async def test_create_share_link_and_access(self, docs_client, docs_session_factory):
        """6. 分享链接创建和访问"""
        case = await _create_case(docs_session_factory, name="登录", method="POST", url="/api/login")

        # 创建分享链接（D7: 必须显式指定 case_ids，不允许分享全部）
        resp = docs_client.post(
            f"{API_DOCS}/share",
            json={"case_ids": [case.id], "expires_hours": 24, "format": "html"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "token" in data
        assert data["format"] == "html"
        assert data["case_count"] == 1
        assert data["url"].endswith(data["token"])

        token = data["token"]

        # 访问分享文档（公开，HTML 格式直接返回 HTML）
        access_resp = docs_client.get(f"{API_DOCS}/shared/{token}")
        assert access_resp.status_code == 200, access_resp.text
        assert "<!DOCTYPE html>" in access_resp.text
        assert "/api/login" in access_resp.text

    @pytest.mark.asyncio
    async def test_share_openapi_format_access(self, docs_client, docs_session_factory):
        """分享 OpenAPI 格式文档，访问返回 JSON"""
        case = await _create_case(docs_session_factory, name="登录", method="POST", url="/api/login")
        resp = docs_client.post(
            f"{API_DOCS}/share",
            json={"case_ids": [case.id], "expires_hours": 24, "format": "openapi"},
        )
        assert resp.status_code == 200, resp.text
        token = resp.json()["token"]

        access_resp = docs_client.get(f"{API_DOCS}/shared/{token}")
        assert access_resp.status_code == 200, access_resp.text
        data = access_resp.json()
        assert data["format"] == "openapi"
        assert data["content"]["openapi"] == "3.0.0"
        assert "/api/login" in data["content"]["paths"]
        # 浏览次数应自增
        assert data["view_count"] >= 1

    @pytest.mark.asyncio
    async def test_expired_share_not_accessible(self, docs_client, docs_session_factory):
        """7. 过期分享链接不可访问"""
        case = await _create_case(docs_session_factory, name="登录", method="POST", url="/api/login")

        # 直接创建一条已过期的分享记录
        async with docs_session_factory() as session:
            expired_share = ApiDocShare(
                token="expired_token_12345",
                title="过期文档",
                case_ids=json.dumps([case.id]),
                fmt="html",
                expires_at=datetime.now(timezone.utc) - timedelta(hours=1),
                created_by=1,
                view_count=0,
            )
            session.add(expired_share)
            await session.commit()

        # 访问过期分享应返回 410
        resp = docs_client.get(f"{API_DOCS}/shared/expired_token_12345")
        assert resp.status_code == 410, resp.text
        assert "过期" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_nonexistent_share_token(self, docs_client):
        """不存在的 token 返回 404"""
        resp = docs_client.get(f"{API_DOCS}/shared/nonexistent_token_xyz")
        assert resp.status_code == 404, resp.text
        assert "不存在" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_share_empty_cases_rejected(self, docs_client):
        """分享空用例应被拒绝（无可用例）"""
        resp = docs_client.post(
            f"{API_DOCS}/share",
            json={"case_ids": [], "expires_hours": 24, "format": "html"},
        )
        assert resp.status_code == 400, resp.text
        assert "用例" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_share_with_specific_case_ids(self, docs_client, docs_session_factory):
        """分享指定 case_ids 的用例"""
        c1 = await _create_case(docs_session_factory, name="登录", method="POST", url="/api/login")
        await _create_case(docs_session_factory, name="注册", method="POST", url="/api/register")

        resp = docs_client.post(
            f"{API_DOCS}/share",
            json={"case_ids": [c1.id], "expires_hours": 24, "format": "html"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["case_count"] == 1
        token = data["token"]

        # 访问分享文档只应包含 c1
        access_resp = docs_client.get(f"{API_DOCS}/shared/{token}")
        assert access_resp.status_code == 200
        assert "/api/login" in access_resp.text
        assert "/api/register" not in access_resp.text

    @pytest.mark.asyncio
    async def test_share_invalid_case_ids_rejected(self, docs_client):
        """分享不属于自己的 case_ids 应被拒绝"""
        resp = docs_client.post(
            f"{API_DOCS}/share",
            json={"case_ids": [99999], "expires_hours": 24, "format": "html"},
        )
        assert resp.status_code == 400, resp.text

    @pytest.mark.asyncio
    async def test_share_by_group(self, docs_client, docs_session_factory):
        """按分组分享文档"""
        group = await _create_group(docs_session_factory, name="用户服务")
        await _create_case(docs_session_factory, name="登录", method="POST", url="/api/login", group_id=group.id)
        await _create_case(docs_session_factory, name="注册", method="POST", url="/api/register", group_id=group.id)

        resp = docs_client.post(
            f"{API_DOCS}/share",
            json={"group_id": group.id, "expires_hours": 24, "format": "html"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["case_count"] == 2
        token = data["token"]

        access_resp = docs_client.get(f"{API_DOCS}/shared/{token}")
        assert access_resp.status_code == 200
        assert "/api/login" in access_resp.text
        assert "/api/register" in access_resp.text
