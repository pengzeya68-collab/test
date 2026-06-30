"""
环境变量继承机制测试

覆盖场景：
1. 单层继承：子环境变量覆盖父环境
2. 多层继承：A→B→C，变量正确合并
3. 循环继承检测：A→B→A 抛出明确错误
4. 最大深度限制（MAX_INHERITANCE_DEPTH=5）
5. 无 parent_id 时回退到原有行为
6. effective-variables API 返回正确的来源标注
7. inheritance-chain API 返回正确的链路
8. 创建/更新环境时 parent_id 循环校验
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.database import Base as AutoTestBase
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.main import app
from fastapi_backend.models.autotest import AutoTestEnvironment
from fastapi_backend.services.autotest_variable_service import (
    MAX_INHERITANCE_DEPTH,
    CyclicInheritanceError,
    EnvironmentNotFoundError,
    MaxDepthExceededError,
    get_effective_variables,
    get_inheritance_chain,
    validate_parent_id,
)


TEST_AUTOTEST_DB_URL = "sqlite+aiosqlite:///:memory:"


# ========== 公共 fixture ==========


@pytest_asyncio.fixture
async def autotest_engine():
    """内存 SQLite 引擎，StaticPool 保证 :memory: 在同一连接内共享"""
    engine = create_async_engine(
        TEST_AUTOTEST_DB_URL,
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
async def autotest_session_factory(autotest_engine):
    return async_sessionmaker(autotest_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
def autotest_client(client, autotest_session_factory):
    """覆盖 get_autotest_db 与 get_current_user，注入内存会话与 mock 用户"""

    async def _override_get_autotest_db():
        async with autotest_session_factory() as session:
            yield session

    async def _override_current_user():
        from types import SimpleNamespace

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


async def _create_env(
    session_factory,
    name: str,
    variables: dict | None = None,
    parent_id: int | None = None,
    user_id: int = 1,
) -> AutoTestEnvironment:
    """直接通过 ORM 创建环境（绕过 API 校验，用于构造测试数据）"""
    async with session_factory() as session:
        env = AutoTestEnvironment(
            env_name=name,
            base_url=None,
            variables=variables or {},
            is_default=False,
            parent_id=parent_id,
            user_id=user_id,
        )
        session.add(env)
        await session.commit()
        await session.refresh(env)
        return env


# ========== 服务层测试 ==========


class TestInheritanceService:
    """直接测试服务层继承解析逻辑"""

    @pytest.mark.asyncio
    async def test_single_level_inheritance_child_overrides_parent(
        self, autotest_session_factory
    ):
        """单层继承：子环境变量覆盖父环境同名变量"""
        parent = await _create_env(
            autotest_session_factory, "基础环境", {"host": "prod.example.com", "port": "443"}
        )
        child = await _create_env(
            autotest_session_factory,
            "测试环境",
            {"host": "test.example.com", "debug": "true"},
            parent_id=parent.id,
        )

        async with autotest_session_factory() as session:
            effective = await get_effective_variables(session, child.id)

        effective_map = {v["name"]: v for v in effective}
        # 子环境覆盖父环境
        assert effective_map["host"]["value"] == "test.example.com"
        assert effective_map["host"]["source_environment_id"] == child.id
        assert effective_map["host"]["is_overridden"] is True
        # 父环境独有变量保留
        assert effective_map["port"]["value"] == "443"
        assert effective_map["port"]["source_environment_id"] == parent.id
        assert effective_map["port"]["is_overridden"] is False
        # 子环境独有变量
        assert effective_map["debug"]["value"] == "true"
        assert effective_map["debug"]["is_overridden"] is False

    @pytest.mark.asyncio
    async def test_multi_level_inheritance_a_to_b_to_c(self, autotest_session_factory):
        """多层继承：A(根) → B → C，变量逐层合并"""
        env_a = await _create_env(
            autotest_session_factory, "A", {"v1": "a1", "v2": "a2", "shared": "from_a"}
        )
        env_b = await _create_env(
            autotest_session_factory,
            "B",
            {"v2": "b2", "shared": "from_b"},
            parent_id=env_a.id,
        )
        env_c = await _create_env(
            autotest_session_factory,
            "C",
            {"v3": "c3", "shared": "from_c"},
            parent_id=env_b.id,
        )

        async with autotest_session_factory() as session:
            chain = await get_inheritance_chain(session, env_c.id)
            effective = await get_effective_variables(session, env_c.id)

        # 继承链：[A, B, C]
        assert [e.id for e in chain] == [env_a.id, env_b.id, env_c.id]
        effective_map = {v["name"]: v for v in effective}
        # v1 只在 A 定义
        assert effective_map["v1"]["value"] == "a1"
        assert effective_map["v1"]["source_environment_id"] == env_a.id
        assert effective_map["v1"]["is_overridden"] is False
        # v2 被 B 覆盖
        assert effective_map["v2"]["value"] == "b2"
        assert effective_map["v2"]["source_environment_id"] == env_b.id
        assert effective_map["v2"]["is_overridden"] is True
        # shared 被 C 覆盖（覆盖两次）
        assert effective_map["shared"]["value"] == "from_c"
        assert effective_map["shared"]["source_environment_id"] == env_c.id
        assert effective_map["shared"]["is_overridden"] is True
        # v3 只在 C 定义
        assert effective_map["v3"]["value"] == "c3"
        assert effective_map["v3"]["is_overridden"] is False

    @pytest.mark.asyncio
    async def test_cyclic_inheritance_detected(self, autotest_session_factory):
        """循环继承检测：A→B→A 抛出 CyclicInheritanceError"""
        env_a = await _create_env(autotest_session_factory, "A", {"v": "a"})
        env_b = await _create_env(
            autotest_session_factory, "B", {"v": "b"}, parent_id=env_a.id
        )
        # 直接通过 ORM 构造循环（绕过 validate_parent_id）
        async with autotest_session_factory() as session:
            env_a_obj = await session.get(AutoTestEnvironment, env_a.id)
            env_a_obj.parent_id = env_b.id
            await session.commit()

        async with autotest_session_factory() as session:
            with pytest.raises(CyclicInheritanceError) as exc_info:
                await get_inheritance_chain(session, env_b.id)
            assert "循环继承" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_max_depth_limit_exceeded(self, autotest_session_factory):
        """最大深度限制：超过 MAX_INHERITANCE_DEPTH 层抛出 MaxDepthExceededError"""
        # 构造 6 层链：A→B→C→D→E→F，超出 5 层限制
        env_a = await _create_env(autotest_session_factory, "A", {"v": "a"})
        env_b = await _create_env(
            autotest_session_factory, "B", {"v": "b"}, parent_id=env_a.id
        )
        env_c = await _create_env(
            autotest_session_factory, "C", {"v": "c"}, parent_id=env_b.id
        )
        env_d = await _create_env(
            autotest_session_factory, "D", {"v": "d"}, parent_id=env_c.id
        )
        env_e = await _create_env(
            autotest_session_factory, "E", {"v": "e"}, parent_id=env_d.id
        )
        env_f = await _create_env(
            autotest_session_factory, "F", {"v": "f"}, parent_id=env_e.id
        )

        async with autotest_session_factory() as session:
            with pytest.raises(MaxDepthExceededError) as exc_info:
                await get_inheritance_chain(session, env_f.id)
            assert str(MAX_INHERITANCE_DEPTH) in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_max_depth_boundary_ok(self, autotest_session_factory):
        """恰好 5 层（边界）应该正常工作，不抛异常"""
        env_a = await _create_env(autotest_session_factory, "A", {"v": "a"})
        env_b = await _create_env(
            autotest_session_factory, "B", {"v": "b"}, parent_id=env_a.id
        )
        env_c = await _create_env(
            autotest_session_factory, "C", {"v": "c"}, parent_id=env_b.id
        )
        env_d = await _create_env(
            autotest_session_factory, "D", {"v": "d"}, parent_id=env_c.id
        )
        env_e = await _create_env(
            autotest_session_factory, "E", {"v": "e"}, parent_id=env_d.id
        )

        async with autotest_session_factory() as session:
            chain = await get_inheritance_chain(session, env_e.id)
            assert len(chain) == 5
            assert [e.env_name for e in chain] == ["A", "B", "C", "D", "E"]

    @pytest.mark.asyncio
    async def test_no_parent_falls_back_to_original_behavior(self, autotest_session_factory):
        """无 parent_id 时回退到原有行为：只返回自身变量"""
        env = await _create_env(
            autotest_session_factory, "独立环境", {"host": "localhost", "port": "8080"}
        )

        async with autotest_session_factory() as session:
            chain = await get_inheritance_chain(session, env.id)
            effective = await get_effective_variables(session, env.id)

        # 链路只包含自身
        assert len(chain) == 1
        assert chain[0].id == env.id
        # 有效变量等于自身变量
        effective_map = {v["name"]: v for v in effective}
        assert effective_map["host"]["value"] == "localhost"
        assert effective_map["port"]["value"] == "8080"
        # 无覆盖
        assert all(v["is_overridden"] is False for v in effective)

    @pytest.mark.asyncio
    async def test_validate_parent_id_rejects_self_reference(self, autotest_session_factory):
        """validate_parent_id 拒绝环境继承自身"""
        env_a = await _create_env(autotest_session_factory, "A", {"v": "a"})

        async with autotest_session_factory() as session:
            with pytest.raises(CyclicInheritanceError):
                await validate_parent_id(session, env_id=env_a.id, parent_id=env_a.id)

    @pytest.mark.asyncio
    async def test_validate_parent_id_rejects_nonexistent_parent(
        self, autotest_session_factory
    ):
        """validate_parent_id 拒绝不存在的父环境"""
        async with autotest_session_factory() as session:
            with pytest.raises(EnvironmentNotFoundError):
                await validate_parent_id(session, env_id=None, parent_id=999999)

    @pytest.mark.asyncio
    async def test_validate_parent_id_rejects_cycle_on_update(
        self, autotest_session_factory
    ):
        """更新环境时检测会形成循环的 parent_id"""
        env_a = await _create_env(autotest_session_factory, "A", {"v": "a"})
        env_b = await _create_env(
            autotest_session_factory, "B", {"v": "b"}, parent_id=env_a.id
        )
        # 尝试把 A 的 parent 设为 B，会形成 A→B→A 循环
        async with autotest_session_factory() as session:
            with pytest.raises(CyclicInheritanceError):
                await validate_parent_id(session, env_id=env_a.id, parent_id=env_b.id)

    @pytest.mark.asyncio
    async def test_validate_parent_id_rejects_exceeding_depth_on_create(
        self, autotest_session_factory
    ):
        """创建环境时检测会超出最大深度的 parent_id"""
        env_a = await _create_env(autotest_session_factory, "A", {"v": "a"})
        env_b = await _create_env(
            autotest_session_factory, "B", {"v": "b"}, parent_id=env_a.id
        )
        env_c = await _create_env(
            autotest_session_factory, "C", {"v": "c"}, parent_id=env_b.id
        )
        env_d = await _create_env(
            autotest_session_factory, "D", {"v": "d"}, parent_id=env_c.id
        )
        env_e = await _create_env(
            autotest_session_factory, "E", {"v": "e"}, parent_id=env_d.id
        )
        # E 已是第 5 层，再以 E 为父创建 F 会超出限制
        async with autotest_session_factory() as session:
            with pytest.raises(MaxDepthExceededError):
                await validate_parent_id(session, env_id=None, parent_id=env_e.id)


# ========== API 端点测试 ==========


class TestInheritanceAPI:
    """通过 HTTP API 测试继承相关端点"""

    @pytest.mark.asyncio
    async def test_effective_variables_api_returns_source_annotation(
        self, autotest_client, autotest_session_factory
    ):
        """effective-variables API 返回合并后变量及来源标注"""
        parent = await _create_env(
            autotest_session_factory, "基础环境", {"host": "prod.example.com", "port": "443"}
        )
        child = await _create_env(
            autotest_session_factory,
            "测试环境",
            {"host": "test.example.com", "debug": "true"},
            parent_id=parent.id,
        )

        resp = autotest_client.get(
            f"/api/auto-test/environments/{child.id}/effective-variables"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["env_id"] == child.id
        assert body["env_name"] == "测试环境"
        vars_map = {v["name"]: v for v in body["variables"]}
        # 子覆盖父
        assert vars_map["host"]["value"] == "test.example.com"
        assert vars_map["host"]["source_environment_id"] == child.id
        assert vars_map["host"]["is_overridden"] is True
        # 父独有
        assert vars_map["port"]["value"] == "443"
        assert vars_map["port"]["source_environment_id"] == parent.id
        assert vars_map["port"]["is_overridden"] is False
        # 子独有
        assert vars_map["debug"]["is_overridden"] is False
        assert body["count"] == 3

    @pytest.mark.asyncio
    async def test_inheritance_chain_api_returns_chain(
        self, autotest_client, autotest_session_factory
    ):
        """inheritance-chain API 返回从根到当前的链路"""
        env_a = await _create_env(autotest_session_factory, "A", {"v": "a"})
        env_b = await _create_env(
            autotest_session_factory, "B", {"v": "b"}, parent_id=env_a.id
        )
        env_c = await _create_env(
            autotest_session_factory, "C", {"v": "c"}, parent_id=env_b.id
        )

        resp = autotest_client.get(
            f"/api/auto-test/environments/{env_c.id}/inheritance-chain"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["env_id"] == env_c.id
        assert body["depth"] == 3
        chain = body["chain"]
        assert [item["id"] for item in chain] == [env_a.id, env_b.id, env_c.id]
        assert [item["env_name"] for item in chain] == ["A", "B", "C"]
        # 深度从 0 开始
        assert [item["depth"] for item in chain] == [0, 1, 2]
        # 父子关系正确
        assert chain[0]["parent_id"] is None
        assert chain[1]["parent_id"] == env_a.id
        assert chain[2]["parent_id"] == env_b.id

    @pytest.mark.asyncio
    async def test_create_environment_with_parent_id(
        self, autotest_client, autotest_session_factory
    ):
        """创建环境时指定 parent_id，响应中应包含 parent_id 与 parent_name"""
        parent = await _create_env(
            autotest_session_factory, "父环境", {"k": "v"}
        )

        resp = autotest_client.post(
            "/api/auto-test/environments",
            json={
                "name": "子环境",
                "base_url": None,
                "variables": {"child_key": "child_val"},
                "is_default": False,
                "parent_id": parent.id,
            },
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["parent_id"] == parent.id
        assert body["parent_name"] == "父环境"

    @pytest.mark.asyncio
    async def test_create_environment_rejects_nonexistent_parent(
        self, autotest_client
    ):
        """创建环境时 parent_id 指向不存在的环境应返回 404"""
        resp = autotest_client.post(
            "/api/auto-test/environments",
            json={
                "name": "孤儿环境",
                "is_default": False,
                "parent_id": 999999,
            },
        )
        assert resp.status_code == 404
        body = resp.json()
        assert body["code"] == "environment_not_found"
        assert "999999" in body["detail"]

    @pytest.mark.asyncio
    async def test_update_environment_rejects_cyclic_parent(
        self, autotest_client, autotest_session_factory
    ):
        """更新环境时设置会形成循环的 parent_id 应返回 400"""
        env_a = await _create_env(autotest_session_factory, "A", {"v": "a"})
        env_b = await _create_env(
            autotest_session_factory, "B", {"v": "b"}, parent_id=env_a.id
        )

        # 尝试把 A 的 parent 设为 B，形成 A→B→A 循环
        resp = autotest_client.put(
            f"/api/auto-test/environments/{env_a.id}",
            json={"parent_id": env_b.id},
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == "cyclic_inheritance"

    @pytest.mark.asyncio
    async def test_update_environment_rejects_exceeding_depth(
        self, autotest_client, autotest_session_factory
    ):
        """更新环境时设置会超出最大深度的 parent_id 应返回 400"""
        env_a = await _create_env(autotest_session_factory, "A", {"v": "a"})
        env_b = await _create_env(
            autotest_session_factory, "B", {"v": "b"}, parent_id=env_a.id
        )
        env_c = await _create_env(
            autotest_session_factory, "C", {"v": "c"}, parent_id=env_b.id
        )
        env_d = await _create_env(
            autotest_session_factory, "D", {"v": "d"}, parent_id=env_c.id
        )
        env_e = await _create_env(
            autotest_session_factory, "E", {"v": "e"}, parent_id=env_d.id
        )

        # 尝试以 E 为父创建 F，应被拒绝
        resp = autotest_client.post(
            "/api/auto-test/environments",
            json={
                "name": "F",
                "parent_id": env_e.id,
            },
        )
        assert resp.status_code == 400
        body = resp.json()
        assert body["code"] == "max_depth_exceeded"

    @pytest.mark.asyncio
    async def test_get_environment_returns_parent_fields(
        self, autotest_client, autotest_session_factory
    ):
        """GET /environments/{id} 返回 parent_id 与 parent_name"""
        parent = await _create_env(autotest_session_factory, "父", {"k": "v"})
        child = await _create_env(
            autotest_session_factory, "子", {"k2": "v2"}, parent_id=parent.id
        )

        resp = autotest_client.get(f"/api/auto-test/environments/{child.id}")
        assert resp.status_code == 200
        body = resp.json()
        assert body["parent_id"] == parent.id
        assert body["parent_name"] == "父"

    @pytest.mark.asyncio
    async def test_list_environments_returns_parent_fields(
        self, autotest_client, autotest_session_factory
    ):
        """GET /environments 列表也返回 parent_id / parent_name"""
        parent = await _create_env(autotest_session_factory, "父列表", {"k": "v"})
        child = await _create_env(
            autotest_session_factory, "子列表", {"k2": "v2"}, parent_id=parent.id
        )

        resp = autotest_client.get("/api/auto-test/environments")
        assert resp.status_code == 200
        envs = {e["id"]: e for e in resp.json()}
        assert envs[child.id]["parent_id"] == parent.id
        assert envs[child.id]["parent_name"] == "父列表"
        assert envs[parent.id]["parent_id"] is None
        assert envs[parent.id]["parent_name"] is None

    @pytest.mark.asyncio
    async def test_effective_variables_api_no_parent(
        self, autotest_client, autotest_session_factory
    ):
        """无 parent 的环境调用 effective-variables 应返回自身变量且无覆盖"""
        env = await _create_env(
            autotest_session_factory, "独立", {"host": "localhost"}
        )

        resp = autotest_client.get(
            f"/api/auto-test/environments/{env.id}/effective-variables"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 1
        var = body["variables"][0]
        assert var["name"] == "host"
        assert var["value"] == "localhost"
        assert var["is_overridden"] is False
        assert var["source_environment_id"] == env.id

    @pytest.mark.asyncio
    async def test_effective_variables_api_not_found(self, autotest_client):
        """不存在的环境 ID 返回 404"""
        resp = autotest_client.get(
            "/api/auto-test/environments/999999/effective-variables"
        )
        assert resp.status_code == 404
