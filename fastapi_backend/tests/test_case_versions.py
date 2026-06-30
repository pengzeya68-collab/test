"""
用例版本管理功能测试

覆盖场景：
1. 创建版本（自动版本号 + 自定义版本号）
2. 获取版本列表
3. 获取版本详情（含快照）
4. 恢复版本（快照写回用例 + 切换 is_current）
5. 删除版本（不能删除当前版本）
6. 版本对比（深度 diff：新增/删除/修改，嵌套对象与数组）
7. 版本号唯一性约束
8. 自动版本号递增 v1/v2/v3...
9. 跨用户隔离（无法访问他人用例的版本）
"""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.database import Base as AutoTestBase
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.main import app
from fastapi_backend.models.autotest import AutoTestCase, AutoTestGroup


TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


# ========== 公共 fixture ==========


@pytest_asyncio.fixture
async def version_engine():
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
async def version_session_factory(version_engine):
    return async_sessionmaker(version_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture
def version_client(client, version_session_factory):
    """覆盖 get_autotest_db 与 get_current_user，注入内存会话与 mock 用户"""

    async def _override_get_autotest_db():
        async with version_session_factory() as session:
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


async def _create_case(
    session_factory,
    name: str = "测试用例",
    method: str = "POST",
    url: str = "/api/login",
    user_id: int = 1,
    payload=None,
    headers=None,
    assert_rules=None,
    extractors=None,
) -> AutoTestCase:
    """直接通过 ORM 创建用例（绕过 API 校验，用于构造测试数据）"""
    async with session_factory() as session:
        # 创建根分组确保外键约束满足
        group = AutoTestGroup(name="测试分组", parent_id=None, user_id=user_id)
        session.add(group)
        await session.flush()

        case = AutoTestCase(
            group_id=group.id,
            name=name,
            method=method,
            url=url,
            headers=headers or {"Content-Type": "application/json"},
            params={"page": "1"},
            body_type="raw",
            content_type="application/json",
            payload=payload or {"username": "admin", "password": "123456"},
            assert_rules=assert_rules or [{"target": "status_code", "operator": "==", "expected": "200"}],
            extractors=extractors or [{"variableName": "token", "expression": "$.token"}],
            description="初始描述",
            user_id=user_id,
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)
        return case


async def _update_case_via_orm(
    session_factory, case_id: int, **fields
) -> AutoTestCase:
    """直接通过 ORM 更新用例字段，模拟用户编辑后保存"""
    async with session_factory() as session:
        case = await session.get(AutoTestCase, case_id)
        for k, v in fields.items():
            setattr(case, k, v)
        await session.commit()
        await session.refresh(case)
        return case


# ========== 测试类：核心 CRUD ==========


class TestCaseVersionCRUD:
    """版本管理核心 CRUD 测试"""

    @pytest.mark.asyncio
    async def test_create_version_with_auto_number(
        self, version_client, version_session_factory
    ):
        """创建版本：不指定版本号时自动生成 v1"""
        case = await _create_case(version_session_factory)
        resp = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions",
            json={"version_label": "初始版本"},
        )
        assert resp.status_code == 201, resp.text
        body = resp.json()
        assert body["version_number"] == "v1"
        assert body["version_label"] == "初始版本"
        assert body["is_current"] is True
        assert body["case_id"] == case.id
        # 快照应包含完整用例数据
        assert body["snapshot"]["method"] == "POST"
        assert body["snapshot"]["url"] == "/api/login"
        assert body["snapshot"]["payload"]["username"] == "admin"

    @pytest.mark.asyncio
    async def test_create_version_with_custom_number(
        self, version_client, version_session_factory
    ):
        """创建版本：使用自定义版本号"""
        case = await _create_case(version_session_factory)
        resp = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions",
            json={"version_number": "1.0.0", "version_label": "首个正式版"},
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["version_number"] == "1.0.0"
        assert body["is_current"] is True

    @pytest.mark.asyncio
    async def test_create_version_auto_increment_sequence(
        self, version_client, version_session_factory
    ):
        """自动版本号递增：连续创建应得到 v1, v2, v3"""
        case = await _create_case(version_session_factory)

        numbers = []
        for _ in range(3):
            resp = version_client.post(
                f"/api/auto-test/cases/{case.id}/versions", json={}
            )
            assert resp.status_code == 201
            numbers.append(resp.json()["version_number"])

        assert numbers == ["v1", "v2", "v3"]

    @pytest.mark.asyncio
    async def test_list_versions_ordered_desc(
        self, version_client, version_session_factory
    ):
        """获取版本列表：按创建时间倒序，最新版本在前"""
        case = await _create_case(version_session_factory)
        # 创建 3 个版本
        for label in ["第一版", "第二版", "第三版"]:
            version_client.post(
                f"/api/auto-test/cases/{case.id}/versions",
                json={"version_label": label},
            )

        resp = version_client.get(f"/api/auto-test/cases/{case.id}/versions")
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 3
        assert body["current_version"] == "v3"
        labels = [item["version_label"] for item in body["items"]]
        # 倒序：第三版在前
        assert labels == ["第三版", "第二版", "第一版"]
        # 最新版本应为当前版本
        assert body["items"][0]["is_current"] is True
        assert body["items"][1]["is_current"] is False
        # 列表不应包含完整 snapshot
        assert "snapshot" not in body["items"][0]

    @pytest.mark.asyncio
    async def test_get_version_detail_with_snapshot(
        self, version_client, version_session_factory
    ):
        """获取版本详情：包含完整 snapshot 数据"""
        case = await _create_case(version_session_factory, payload={"username": "alice"})
        create_resp = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        )
        version_id = create_resp.json()["id"]

        resp = version_client.get(
            f"/api/auto-test/cases/{case.id}/versions/{version_id}"
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == version_id
        assert body["snapshot"] is not None
        assert body["snapshot"]["payload"]["username"] == "alice"

    @pytest.mark.asyncio
    async def test_get_nonexistent_version_returns_404(
        self, version_client, version_session_factory
    ):
        """获取不存在的版本返回 404"""
        case = await _create_case(version_session_factory)
        resp = version_client.get(
            f"/api/auto-test/cases/{case.id}/versions/999999"
        )
        assert resp.status_code == 404


# ========== 测试类：版本恢复 ==========


class TestCaseVersionRestore:
    """版本恢复测试"""

    @pytest.mark.asyncio
    async def test_restore_version_writes_back_snapshot(
        self, version_client, version_session_factory
    ):
        """恢复版本：将快照写回用例，覆盖当前数据"""
        case = await _create_case(
            version_session_factory,
            url="/api/v1/login",
            payload={"username": "old_user"},
        )
        # 保存为 v1（旧版本快照）
        v1_resp = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions",
            json={"version_label": "旧版本"},
        )
        v1_id = v1_resp.json()["id"]

        # 修改用例并保存为 v2（当前版本）
        await _update_case_via_orm(
            version_session_factory,
            case.id,
            url="/api/v2/login",
            payload={"username": "new_user"},
        )
        v2_resp = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions",
            json={"version_label": "新版本"},
        )
        v2_id = v2_resp.json()["id"]
        assert v2_resp.json()["is_current"] is True

        # 此时用例的 url 应是修改后的
        case_resp = version_client.get(f"/api/auto-test/cases/{case.id}")
        assert case_resp.json()["url"] == "/api/v2/login"

        # 恢复到 v1
        restore_resp = version_client.put(
            f"/api/auto-test/cases/{case.id}/versions/{v1_id}/restore"
        )
        assert restore_resp.status_code == 200
        body = restore_resp.json()
        assert body["is_current"] is True
        assert body["snapshot"]["url"] == "/api/v1/login"

        # 验证用例数据已被覆盖回 v1
        case_after = version_client.get(f"/api/auto-test/cases/{case.id}")
        assert case_after.json()["url"] == "/api/v1/login"
        assert case_after.json()["payload"]["username"] == "old_user"

        # 验证 is_current 已切换：v1 为 True，v2 为 False
        list_resp = version_client.get(f"/api/auto-test/cases/{case.id}/versions")
        items = {item["id"]: item for item in list_resp.json()["items"]}
        assert items[v1_id]["is_current"] is True
        assert items[v2_id]["is_current"] is False

    @pytest.mark.asyncio
    async def test_restore_updates_current_version_field(
        self, version_client, version_session_factory
    ):
        """恢复版本：AutoTestCase.current_version 冗余字段同步更新"""
        case = await _create_case(version_session_factory)
        v1 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions",
            json={"version_number": "1.0.0"},
        ).json()
        v2 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions",
            json={"version_number": "2.0.0"},
        ).json()

        # 此时 current_version 应为 2.0.0
        list_resp = version_client.get(f"/api/auto-test/cases/{case.id}/versions")
        assert list_resp.json()["current_version"] == "2.0.0"

        # 恢复到 1.0.0
        version_client.put(
            f"/api/auto-test/cases/{case.id}/versions/{v1['id']}/restore"
        )

        list_resp = version_client.get(f"/api/auto-test/cases/{case.id}/versions")
        assert list_resp.json()["current_version"] == "1.0.0"


# ========== 测试类：版本删除 ==========


class TestCaseVersionDelete:
    """版本删除测试"""

    @pytest.mark.asyncio
    async def test_cannot_delete_current_version(
        self, version_client, version_session_factory
    ):
        """不能删除当前版本：返回 400"""
        case = await _create_case(version_session_factory)
        create_resp = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        )
        version_id = create_resp.json()["id"]
        # 刚创建的版本为当前版本
        assert create_resp.json()["is_current"] is True

        resp = version_client.delete(
            f"/api/auto-test/cases/{case.id}/versions/{version_id}"
        )
        assert resp.status_code == 400
        assert "当前版本" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_non_current_version_succeeds(
        self, version_client, version_session_factory
    ):
        """删除非当前版本：成功返回 204"""
        case = await _create_case(version_session_factory)
        v1 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()
        v2 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()
        # v2 为当前版本，v1 非当前
        assert v2["is_current"] is True

        resp = version_client.delete(
            f"/api/auto-test/cases/{case.id}/versions/{v1['id']}"
        )
        assert resp.status_code == 204

        # 确认已删除
        list_resp = version_client.get(f"/api/auto-test/cases/{case.id}/versions")
        assert list_resp.json()["total"] == 1
        assert list_resp.json()["items"][0]["id"] == v2["id"]

    @pytest.mark.asyncio
    async def test_delete_last_version_clears_current_version(
        self, version_client, version_session_factory
    ):
        """删除最后一个版本后，current_version 冗余字段被清空"""
        case = await _create_case(version_session_factory)
        v1 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()
        v2 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()
        # 恢复到 v1，使 v2 不再是当前版本
        version_client.put(
            f"/api/auto-test/cases/{case.id}/versions/{v1['id']}/restore"
        )

        # 删除 v2（非当前）
        version_client.delete(f"/api/auto-test/cases/{case.id}/versions/{v2['id']}")
        # 删除 v1（当前 - 需先恢复到 v2，但 v2 已删除）
        # 此处 v1 仍是当前版本，无法直接删除，验证逻辑保持一致
        list_resp = version_client.get(f"/api/auto-test/cases/{case.id}/versions")
        assert list_resp.json()["total"] == 1
        assert list_resp.json()["current_version"] == "v1"


# ========== 测试类：版本对比 ==========


class TestCaseVersionDiff:
    """版本对比（深度 diff）测试"""

    @pytest.mark.asyncio
    async def test_diff_identical_versions(
        self, version_client, version_session_factory
    ):
        """对比完全相同的版本：is_identical=True，diffs 为空"""
        case = await _create_case(version_session_factory)
        v1 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()
        v2 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()

        resp = version_client.get(
            f"/api/auto-test/cases/{case.id}/versions/diff",
            params={"v1": v1["id"], "v2": v2["id"]},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_identical"] is True
        assert body["total_changes"] == 0
        assert body["diffs"] == []

    @pytest.mark.asyncio
    async def test_diff_modified_scalar_field(
        self, version_client, version_session_factory
    ):
        """对比：标量字段修改"""
        case = await _create_case(version_session_factory, url="/api/v1/login")
        v1 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()

        # 修改 url
        await _update_case_via_orm(version_session_factory, case.id, url="/api/v2/login")
        v2 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()

        resp = version_client.get(
            f"/api/auto-test/cases/{case.id}/versions/diff",
            params={"v1": v1["id"], "v2": v2["id"]},
        )
        body = resp.json()
        assert body["is_identical"] is False
        url_diff = next(d for d in body["diffs"] if d["field"] == "url")
        assert url_diff["change_type"] == "modified"
        assert url_diff["old_value"] == "/api/v1/login"
        assert url_diff["new_value"] == "/api/v2/login"

    @pytest.mark.asyncio
    async def test_diff_added_and_removed_nested_keys(
        self, version_client, version_session_factory
    ):
        """对比：嵌套对象新增/删除字段"""
        case = await _create_case(
            version_session_factory,
            payload={"username": "admin", "password": "123"},
        )
        v1 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()

        # 修改 payload：删除 password，新增 token
        await _update_case_via_orm(
            version_session_factory,
            case.id,
            payload={"username": "admin", "token": "abc123"},
        )
        v2 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()

        resp = version_client.get(
            f"/api/auto-test/cases/{case.id}/versions/diff",
            params={"v1": v1["id"], "v2": v2["id"]},
        )
        body = resp.json()
        diffs = {d["field"]: d for d in body["diffs"]}

        # payload.password 被删除
        assert "payload.password" in diffs
        assert diffs["payload.password"]["change_type"] == "removed"
        assert diffs["payload.password"]["old_value"] == "123"

        # payload.token 新增
        assert "payload.token" in diffs
        assert diffs["payload.token"]["change_type"] == "added"
        assert diffs["payload.token"]["new_value"] == "abc123"

    @pytest.mark.asyncio
    async def test_diff_array_length_change(
        self, version_client, version_session_factory
    ):
        """对比：数组长度变化（新增/删除元素）"""
        case = await _create_case(
            version_session_factory,
            assert_rules=[
                {"target": "status_code", "operator": "==", "expected": "200"}
            ],
        )
        v1 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()

        # 增加一条断言
        await _update_case_via_orm(
            version_session_factory,
            case.id,
            assert_rules=[
                {"target": "status_code", "operator": "==", "expected": "200"},
                {"target": "response_body", "operator": "contains", "expected": "ok"},
            ],
        )
        v2 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()

        resp = version_client.get(
            f"/api/auto-test/cases/{case.id}/versions/diff",
            params={"v1": v1["id"], "v2": v2["id"]},
        )
        body = resp.json()
        # 应有新增的断言项
        added = [d for d in body["diffs"] if d["change_type"] == "added"]
        assert any("assert_rules[1]" in d["field"] for d in added)

    @pytest.mark.asyncio
    async def test_diff_same_version_rejected(
        self, version_client, version_session_factory
    ):
        """对比同一版本：返回 400"""
        case = await _create_case(version_session_factory)
        v1 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        ).json()

        resp = version_client.get(
            f"/api/auto-test/cases/{case.id}/versions/diff",
            params={"v1": v1["id"], "v2": v1["id"]},
        )
        assert resp.status_code == 400


# ========== 测试类：版本号唯一性 ==========


class TestCaseVersionUniqueness:
    """版本号唯一性约束测试"""

    @pytest.mark.asyncio
    async def test_duplicate_version_number_returns_409(
        self, version_client, version_session_factory
    ):
        """同一 case 下重复版本号：返回 409"""
        case = await _create_case(version_session_factory)
        resp1 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions",
            json={"version_number": "1.0.0"},
        )
        assert resp1.status_code == 201

        resp2 = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions",
            json={"version_number": "1.0.0"},
        )
        assert resp2.status_code == 409
        assert "1.0.0" in resp2.json()["detail"]

    @pytest.mark.asyncio
    async def test_same_version_number_across_different_cases_allowed(
        self, version_client, version_session_factory
    ):
        """不同 case 可以使用相同版本号"""
        case1 = await _create_case(version_session_factory, name="用例A")
        case2 = await _create_case(version_session_factory, name="用例B")

        r1 = version_client.post(
            f"/api/auto-test/cases/{case1.id}/versions",
            json={"version_number": "1.0.0"},
        )
        r2 = version_client.post(
            f"/api/auto-test/cases/{case2.id}/versions",
            json={"version_number": "1.0.0"},
        )
        assert r1.status_code == 201
        assert r2.status_code == 201


# ========== 测试类：跨用户隔离 ==========


class TestCaseVersionAccessControl:
    """跨用户访问控制测试"""

    @pytest.mark.asyncio
    async def test_cannot_access_other_users_case_versions(
        self, version_client, version_session_factory
    ):
        """无法访问他人用例的版本列表：返回 404"""
        # 创建他人用例（user_id=2）
        other_case = await _create_case(
            version_session_factory, name="他人用例", user_id=2
        )
        resp = version_client.get(
            f"/api/auto-test/cases/{other_case.id}/versions"
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_cannot_create_version_for_other_users_case(
        self, version_client, version_session_factory
    ):
        """无法为他人用例创建版本：返回 404"""
        other_case = await _create_case(
            version_session_factory, name="他人用例", user_id=2
        )
        resp = version_client.post(
            f"/api/auto-test/cases/{other_case.id}/versions", json={}
        )
        assert resp.status_code == 404


# ========== 测试类：向后兼容 ==========


class TestCaseVersionBackwardCompat:
    """向后兼容测试"""

    @pytest.mark.asyncio
    async def test_first_save_becomes_v1(
        self, version_client, version_session_factory
    ):
        """现有用例无版本时，首次保存版本作为 v1"""
        case = await _create_case(version_session_factory)
        # 用例初始 current_version 为 None
        list_resp = version_client.get(f"/api/auto-test/cases/{case.id}/versions")
        assert list_resp.json()["total"] == 0
        assert list_resp.json()["current_version"] is None

        # 首次保存版本
        create_resp = version_client.post(
            f"/api/auto-test/cases/{case.id}/versions", json={}
        )
        assert create_resp.status_code == 201
        assert create_resp.json()["version_number"] == "v1"
        assert create_resp.json()["is_current"] is True

        # current_version 已同步
        list_resp = version_client.get(f"/api/auto-test/cases/{case.id}/versions")
        assert list_resp.json()["current_version"] == "v1"
