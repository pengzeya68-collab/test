"""
AutoTest 接口树形分组管理 - 测试套件

覆盖：
1. 创建根分组 / 子分组
2. 获取树形结构（含 case_count、sort_order）
3. 移动分组（改变父分组）
4. 循环检测（A→B→A）
5. 删除分组（子分组拒绝 / 用例移动到父分组）
6. 用例关联分组
7. case_count 统计正确
"""

import pytest
import pytest_asyncio
from types import SimpleNamespace

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.database import Base as AutoTestBase
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.main import app
from fastapi_backend.models.autotest import AutoTestCase, AutoTestGroup
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

TEST_AUTOTEST_DB_URL = "sqlite+aiosqlite:///:memory:"

GROUPS_API = "/api/auto-test/groups"
CASES_API = "/api/auto-test/cases"


@pytest_asyncio.fixture
async def autotest_engine():
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
    """注入内存 autotest DB 与 mock 用户的同步测试客户端"""

    async def _override_get_autotest_db():
        async with autotest_session_factory() as session:
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


# ========== 直接 DB 辅助函数 ==========


async def _create_case_direct(session_factory, group_id, name="测试用例"):
    """直接通过 session 创建用例，关联分组"""
    async with session_factory() as session:
        case = AutoTestCase(
            group_id=group_id,
            name=name,
            method="GET",
            url="http://example.com/api/test",
            user_id=1,
        )
        session.add(case)
        await session.commit()
        await session.refresh(case)
        return case


class TestCaseGroups:
    """树形分组管理测试"""

    @pytest.mark.asyncio
    async def test_create_root_group(self, autotest_client):
        """1. 创建根分组（parent_id=null）"""
        resp = autotest_client.post(
            GROUPS_API,
            json={"name": "用户服务", "parent_id": None, "description": "根分组", "sort_order": 0},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["name"] == "用户服务"
        assert data["parent_id"] is None
        assert data["description"] == "根分组"
        assert data["sort_order"] == 0
        assert "id" in data

    @pytest.mark.asyncio
    async def test_create_child_group(self, autotest_client):
        """2. 创建子分组（指定 parent_id）"""
        root = autotest_client.post(GROUPS_API, json={"name": "根"}).json()
        child = autotest_client.post(
            GROUPS_API,
            json={"name": "登录接口", "parent_id": root["id"], "sort_order": 1},
        ).json()
        assert child["parent_id"] == root["id"]
        assert child["name"] == "登录接口"
        assert child["sort_order"] == 1

    @pytest.mark.asyncio
    async def test_create_group_invalid_parent(self, autotest_client):
        """父分组不存在时创建应失败"""
        resp = autotest_client.post(GROUPS_API, json={"name": "孤儿", "parent_id": 99999})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_get_group_tree_structure(self, autotest_client):
        """3. 获取树形结构：根-子-孙三层嵌套，children 始终为数组"""
        root = autotest_client.post(GROUPS_API, json={"name": "用户服务", "sort_order": 0}).json()
        child1 = autotest_client.post(
            GROUPS_API, json={"name": "登录", "parent_id": root["id"], "sort_order": 0}
        ).json()
        child2 = autotest_client.post(
            GROUPS_API, json={"name": "注册", "parent_id": root["id"], "sort_order": 1}
        ).json()
        grandchild = autotest_client.post(GROUPS_API, json={"name": "短信登录", "parent_id": child1["id"]}).json()

        tree = autotest_client.get(f"{GROUPS_API}/tree").json()
        assert len(tree) == 1
        root_node = tree[0]
        assert root_node["id"] == root["id"]
        assert len(root_node["children"]) == 2
        # 按 sort_order 排序：登录(0) 在 注册(1) 前
        assert root_node["children"][0]["id"] == child1["id"]
        assert root_node["children"][1]["id"] == child2["id"]
        # 孙节点
        login_node = root_node["children"][0]
        assert len(login_node["children"]) == 1
        assert login_node["children"][0]["id"] == grandchild["id"]
        # 叶子节点 children 为空数组（非 None）
        assert login_node["children"][0]["children"] == []

    @pytest.mark.asyncio
    async def test_move_group_change_parent(self, autotest_client):
        """4. 移动分组到新父分组"""
        root_a = autotest_client.post(GROUPS_API, json={"name": "A"}).json()
        root_b = autotest_client.post(GROUPS_API, json={"name": "B"}).json()
        child = autotest_client.post(GROUPS_API, json={"name": "可移动子", "parent_id": root_a["id"]}).json()

        moved = autotest_client.put(
            f"{GROUPS_API}/{child['id']}/move",
            json={"parent_id": root_b["id"], "sort_order": 5},
        ).json()
        assert moved["parent_id"] == root_b["id"]
        assert moved["sort_order"] == 5

        # 树形结构验证：child 现在在 root_b 下
        tree = autotest_client.get(f"{GROUPS_API}/tree").json()
        root_b_node = next(n for n in tree if n["id"] == root_b["id"])
        assert any(c["id"] == child["id"] for c in root_b_node["children"])

    @pytest.mark.asyncio
    async def test_move_to_root(self, autotest_client):
        """移动分组到根（parent_id=null）"""
        root = autotest_client.post(GROUPS_API, json={"name": "根"}).json()
        child = autotest_client.post(GROUPS_API, json={"name": "子", "parent_id": root["id"]}).json()

        moved = autotest_client.put(f"{GROUPS_API}/{child['id']}/move", json={"parent_id": None}).json()
        assert moved["parent_id"] is None

    @pytest.mark.asyncio
    async def test_cycle_detection_self(self, autotest_client):
        """5. 循环检测：不能将分组设为自身的子分组"""
        group = autotest_client.post(GROUPS_API, json={"name": "自环"}).json()
        resp = autotest_client.put(f"{GROUPS_API}/{group['id']}/move", json={"parent_id": group["id"]})
        assert resp.status_code == 400
        assert "自身" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_cycle_detection_chain(self, autotest_client):
        """循环检测：A→B→A 链路应被拒绝"""
        a = autotest_client.post(GROUPS_API, json={"name": "A"}).json()
        b = autotest_client.post(GROUPS_API, json={"name": "B", "parent_id": a["id"]}).json()
        # 将 A 移到 B 下会形成 A→B→A 循环
        resp = autotest_client.put(f"{GROUPS_API}/{a['id']}/move", json={"parent_id": b["id"]})
        assert resp.status_code == 400
        assert "循环" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_cycle_detection_via_update(self, autotest_client):
        """通过 PUT 更新 parent_id 也应触发循环检测"""
        a = autotest_client.post(GROUPS_API, json={"name": "A"}).json()
        b = autotest_client.post(GROUPS_API, json={"name": "B", "parent_id": a["id"]}).json()
        resp = autotest_client.put(f"{GROUPS_API}/{a['id']}", json={"parent_id": b["id"]})
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_group_with_children_rejected(self, autotest_client):
        """6. 删除有子分组的分组应被拒绝"""
        root = autotest_client.post(GROUPS_API, json={"name": "根"}).json()
        autotest_client.post(GROUPS_API, json={"name": "子", "parent_id": root["id"]}).json()
        resp = autotest_client.delete(f"{GROUPS_API}/{root['id']}")
        assert resp.status_code == 400
        assert "子分组" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_delete_group_move_cases_to_parent(self, autotest_client, autotest_session_factory):
        """删除分组时，用例移动到父分组"""
        root = autotest_client.post(GROUPS_API, json={"name": "根"}).json()
        child = autotest_client.post(GROUPS_API, json={"name": "子", "parent_id": root["id"]}).json()
        # 在 child 下创建用例
        await _create_case_direct(autotest_session_factory, child["id"], "用例1")
        await _create_case_direct(autotest_session_factory, child["id"], "用例2")

        resp = autotest_client.delete(f"{GROUPS_API}/{child['id']}", params={"move_cases_to_parent": True})
        assert resp.status_code == 200
        assert "移动" in resp.json()["message"]

        # 验证用例已移到 root
        cases_resp = autotest_client.get(f"{CASES_API}", params={"group_id": root["id"]})
        cases = cases_resp.json()
        cases_list = cases["items"] if isinstance(cases, dict) else cases
        assert len(cases_list) == 2

    @pytest.mark.asyncio
    async def test_delete_group_without_parent_deletes_cases(self, autotest_client, autotest_session_factory):
        """删除根分组（无父分组）且 move_cases_to_parent=False 时删除用例"""
        root = autotest_client.post(GROUPS_API, json={"name": "根"}).json()
        await _create_case_direct(autotest_session_factory, root["id"], "用例1")

        resp = autotest_client.delete(f"{GROUPS_API}/{root['id']}", params={"move_cases_to_parent": False})
        assert resp.status_code == 200
        assert "删除" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_case_association_and_count(self, autotest_client, autotest_session_factory):
        """7 & 8. 用例关联分组 + case_count 统计正确"""
        root = autotest_client.post(GROUPS_API, json={"name": "根"}).json()
        child = autotest_client.post(GROUPS_API, json={"name": "子", "parent_id": root["id"]}).json()

        # root 下 2 个用例，child 下 3 个用例
        await _create_case_direct(autotest_session_factory, root["id"], "r1")
        await _create_case_direct(autotest_session_factory, root["id"], "r2")
        await _create_case_direct(autotest_session_factory, child["id"], "c1")
        await _create_case_direct(autotest_session_factory, child["id"], "c2")
        await _create_case_direct(autotest_session_factory, child["id"], "c3")

        tree = autotest_client.get(f"{GROUPS_API}/tree").json()
        root_node = tree[0]
        child_node = root_node["children"][0]
        assert root_node["case_count"] == 2
        assert child_node["case_count"] == 3

    @pytest.mark.asyncio
    async def test_update_group_fields(self, autotest_client):
        """更新分组名称、描述、排序"""
        group = autotest_client.post(GROUPS_API, json={"name": "原名", "sort_order": 0}).json()
        updated = autotest_client.put(
            f"{GROUPS_API}/{group['id']}",
            json={"name": "新名", "description": "更新描述", "sort_order": 10},
        ).json()
        assert updated["name"] == "新名"
        assert updated["description"] == "更新描述"
        assert updated["sort_order"] == 10

    @pytest.mark.asyncio
    async def test_get_single_group(self, autotest_client):
        """获取单个分组详情"""
        group = autotest_client.post(GROUPS_API, json={"name": "详情", "description": "desc"}).json()
        data = autotest_client.get(f"{GROUPS_API}/{group['id']}").json()
        assert data["id"] == group["id"]
        assert data["name"] == "详情"
        assert data["description"] == "desc"

    @pytest.mark.asyncio
    async def test_get_all_groups_flat(self, autotest_client):
        """获取扁平分组列表"""
        autotest_client.post(GROUPS_API, json={"name": "A"}).json()
        autotest_client.post(GROUPS_API, json={"name": "B"}).json()
        groups = autotest_client.get(GROUPS_API).json()
        assert len(groups) == 2
        assert all("sort_order" in g for g in groups)

    @pytest.mark.asyncio
    async def test_move_empty_payload_rejected(self, autotest_client):
        """move 端点空请求体应拒绝"""
        group = autotest_client.post(GROUPS_API, json={"name": "G"}).json()
        resp = autotest_client.put(f"{GROUPS_API}/{group['id']}/move", json={})
        assert resp.status_code == 400
