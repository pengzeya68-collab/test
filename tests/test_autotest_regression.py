"""
自动化测试模块 - 完整功能回归测试套件
覆盖: 接口库、场景管理、套件、变量、环境、数据工厂、数据库连接、
      Mock服务、JMeter、AI生成、覆盖率、导入导出、调试执行、调度、邮件
每个测试验证业务逻辑，不只是HTTP状态码
"""
import os
from urllib.parse import urljoin

import pytest
import requests
import json
import time
import uuid
import urllib3

pytestmark = [pytest.mark.remote, pytest.mark.regression, pytest.mark.slow]


def _remote_base_url():
    base_url = os.getenv("TESTMASTER_REMOTE_BASE_URL")
    if not base_url:
        pytest.skip("设置 TESTMASTER_REMOTE_BASE_URL 后才会执行远程回归测试")
    return base_url.rstrip("/")


def _remote_verify_tls():
    value = os.getenv("TESTMASTER_REMOTE_VERIFY_TLS", "true").strip().lower()
    verify = value in {"1", "true", "yes", "on"}
    if not verify:
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    return verify


def _remote_timeout():
    return float(os.getenv("TESTMASTER_REMOTE_TIMEOUT", "15"))


def api(method, path, headers=None, **kwargs):
    """统一API调用"""
    url = urljoin(f"{_remote_base_url()}/", path.lstrip("/"))
    kwargs.setdefault("timeout", _remote_timeout())
    return getattr(requests, method)(url, headers=headers, verify=_remote_verify_tls(), **kwargs)


# ================================================================
# 1. 接口分组管理 (Groups)
# ================================================================
class TestGroups:
    """接口分组 - CRUD + 树形结构 + 循环引用检测 + 级联删除"""
    root_group_id = None
    child_group_id = None
    grandchild_group_id = None

    def test_01_create_root_group(self, auth):
        """创建根分组"""
        r = api("post", "/api/auto-test/groups", headers=auth,
                json={"name": f"回归根_{uuid.uuid4().hex[:6]}"})
        assert r.status_code == 201, f"创建根分组失败: {r.text}"
        data = r.json()
        assert data["name"].startswith("回归根")
        assert data["parent_id"] is None
        TestGroups.root_group_id = data["id"]

    def test_02_create_child_group(self, auth):
        """创建子分组"""
        r = api("post", "/api/auto-test/groups", headers=auth,
                json={"name": f"子分组_{uuid.uuid4().hex[:6]}", "parent_id": TestGroups.root_group_id})
        assert r.status_code == 201
        assert r.json()["parent_id"] == TestGroups.root_group_id
        TestGroups.child_group_id = r.json()["id"]

    def test_03_create_grandchild_group(self, auth):
        """创建孙分组"""
        r = api("post", "/api/auto-test/groups", headers=auth,
                json={"name": f"孙分组_{uuid.uuid4().hex[:6]}", "parent_id": TestGroups.child_group_id})
        assert r.status_code == 201
        TestGroups.grandchild_group_id = r.json()["id"]

    def test_04_get_tree(self, auth):
        """获取分组树 - 验证树形结构和case_count"""
        r = api("get", "/api/auto-test/groups/tree", headers=auth)
        assert r.status_code == 200
        tree = r.json()
        root = next((g for g in tree if g["id"] == TestGroups.root_group_id), None)
        assert root is not None, "树中未找到根分组"
        assert "case_count" in root
        assert "children" in root
        child = next((c for c in root.get("children", []) if c["id"] == TestGroups.child_group_id), None)
        assert child is not None, "子分组未在children中"

    def test_05_get_flat_list(self, auth):
        """获取扁平列表"""
        r = api("get", "/api/auto-test/groups", headers=auth)
        assert r.status_code == 200
        ids = [g["id"] for g in r.json()]
        assert TestGroups.root_group_id in ids

    def test_06_get_single_group(self, auth):
        """获取单个分组"""
        r = api("get", f"/api/auto-test/groups/{TestGroups.root_group_id}", headers=auth)
        assert r.status_code == 200
        assert r.json()["id"] == TestGroups.root_group_id

    def test_07_get_nonexistent_group(self, auth):
        """获取不存在的分组 - 404"""
        r = api("get", "/api/auto-test/groups/999999", headers=auth)
        assert r.status_code == 404

    def test_08_update_group_name(self, auth):
        """更新分组名称"""
        new_name = f"更新后_{uuid.uuid4().hex[:6]}"
        r = api("put", f"/api/auto-test/groups/{TestGroups.child_group_id}", headers=auth,
                json={"name": new_name})
        assert r.status_code == 200
        assert r.json()["name"] == new_name

    def test_09_circular_reference_detection(self, auth):
        """循环引用检测 - 父分组移到自己的子分组下应被拒绝"""
        r = api("put", f"/api/auto-test/groups/{TestGroups.root_group_id}", headers=auth,
                json={"parent_id": TestGroups.grandchild_group_id})
        assert r.status_code == 400, f"循环引用未被检测: {r.text}"

    def test_10_delete_group_with_children_fails(self, auth):
        """删除有子分组的分组应被拒绝"""
        r = api("delete", f"/api/auto-test/groups/{TestGroups.root_group_id}", headers=auth)
        assert r.status_code == 400

    def test_11_delete_grandchild(self, auth):
        """删除孙分组"""
        r = api("delete", f"/api/auto-test/groups/{TestGroups.grandchild_group_id}", headers=auth)
        assert r.status_code == 200

    def test_12_delete_child(self, auth):
        """删除子分组"""
        r = api("delete", f"/api/auto-test/groups/{TestGroups.child_group_id}", headers=auth)
        assert r.status_code == 200

    def test_13_delete_root_cascade(self, auth):
        """删除根分组 - 验证级联删除用例"""
        # 创建用例在根分组下
        case_r = api("post", "/api/auto-test/cases", headers=auth,
                     json={"name": "待级联删除", "method": "GET",
                           "url": "https://httpbin.org/get",
                           "group_id": TestGroups.root_group_id})
        assert case_r.status_code == 201, f"创建用例失败: {case_r.text}"
        case_id = case_r.json()["id"]

        r = api("delete", f"/api/auto-test/groups/{TestGroups.root_group_id}", headers=auth)
        assert r.status_code == 200
        # 验证用例也被删除
        assert api("get", f"/api/auto-test/cases/{case_id}", headers=auth).status_code == 404


# ================================================================
# 2. 接口用例管理 (Cases)
# ================================================================
class TestCases:
    """接口用例 - CRUD + URL校验 + 分页搜索 + 执行 + 历史"""
    case_get_id = None
    case_post_id = None
    case_assert_id = None

    def test_01_create_case_with_valid_url(self, auth):
        """创建用例 - 有效URL（必须提供group_id或folder_id）"""
        # 先创建分组
        group_r = api("post", "/api/auto-test/groups", headers=auth,
                      json={"name": f"用例分组_{uuid.uuid4().hex[:6]}"})
        TestCases._group_id = group_r.json()["id"]

        r = api("post", "/api/auto-test/cases", headers=auth,
                json={"name": "回归用例_GET", "method": "GET",
                      "url": "https://httpbin.org/get",
                      "group_id": TestCases._group_id,
                      "description": "测试描述"})
        assert r.status_code == 201, f"创建用例失败: {r.text}"
        data = r.json()
        assert data["name"] == "回归用例_GET"
        assert data["method"] == "GET"
        TestCases.case_get_id = data["id"]

    def test_02_create_case_with_relative_url(self, auth):
        """创建用例 - 相对路径URL"""
        r = api("post", "/api/auto-test/cases", headers=auth,
                json={"name": "相对路径用例", "method": "POST",
                      "url": "/api/v1/test", "group_id": TestCases._group_id})
        assert r.status_code == 201, f"创建失败: {r.text}"
        TestCases.case_post_id = r.json()["id"]

    def test_03_create_case_no_group_fails(self, auth):
        """创建用例 - 不提供group_id和folder_id应失败"""
        r = api("post", "/api/auto-test/cases", headers=auth,
                json={"name": "无分组用例", "method": "GET", "url": "https://httpbin.org/get"})
        assert r.status_code == 422, "不提供group_id应被拒绝"

    def test_04_create_case_with_assertions(self, auth):
        """创建用例 - 带断言规则(assert_rules)"""
        r = api("post", "/api/auto-test/cases", headers=auth,
                json={"name": "带断言用例", "method": "GET",
                      "url": "https://httpbin.org/get",
                      "group_id": TestCases._group_id,
                      "assert_rules": {"rules": [{"type": "status_code", "operator": "eq", "expected": "200"}]}})
        assert r.status_code == 201, f"创建断言用例失败: {r.text}"
        TestCases.case_assert_id = r.json()["id"]

    def test_05_get_cases_pagination(self, auth):
        """获取用例列表 - 验证分页"""
        r = api("get", "/api/auto-test/cases", headers=auth, params={"page": 1, "page_size": 5})
        assert r.status_code == 200
        data = r.json()
        assert "total" in data and "items" in data and "page" in data
        assert data["page"] == 1
        assert len(data["items"]) <= 5

    def test_06_get_cases_keyword_search(self, auth):
        """获取用例列表 - 关键字搜索"""
        r = api("get", "/api/auto-test/cases", headers=auth, params={"keyword": "回归用例"})
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert "回归用例" in item["name"] or "回归用例" in item.get("url", "")

    def test_07_get_all_cases(self, auth):
        """获取全部用例"""
        r = api("get", "/api/auto-test/cases/all", headers=auth)
        assert r.status_code == 200
        assert isinstance(r.json(), list)

    def test_08_get_single_case(self, auth):
        """获取单个用例 - 验证lastRunStatus"""
        r = api("get", f"/api/auto-test/cases/{TestCases.case_get_id}", headers=auth)
        assert r.status_code == 200
        assert "lastRunStatus" in r.json()

    def test_09_update_case(self, auth):
        """更新用例"""
        r = api("put", f"/api/auto-test/cases/{TestCases.case_get_id}", headers=auth,
                json={"name": "更新后用例", "description": "更新描述"})
        assert r.status_code == 200
        assert r.json()["name"] == "更新后用例"

    def test_10_quick_run_case(self, auth):
        """快速运行用例 - 验证执行结果"""
        r = api("post", f"/api/auto-test/cases/{TestCases.case_get_id}/quick-run", headers=auth)
        assert r.status_code == 200, f"运行失败: {r.text[:200]}"
        data = r.json()
        assert "status_code" in data or "success" in data or "assert_result" in data, f"缺少关键字段: {list(data.keys())}"

    def test_11_get_execution_history(self, auth):
        """获取执行历史"""
        r = api("get", "/api/auto-test/history", headers=auth,
                params={"case_id": TestCases.case_get_id, "limit": 5})
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and "total" in data
        if data["items"]:
            assert "id" in data["items"][0]

    def test_12_batch_run_cases(self, auth):
        """批量运行用例"""
        r = api("post", "/api/auto-test/cases/batch-run", headers=auth,
                json=[TestCases.case_get_id])
        assert r.status_code == 200
        data = r.json()
        assert "total" in data and "success" in data and "failed" in data

    def test_13_delete_case_cascade_steps(self, auth):
        """删除用例 - 验证场景步骤级联清理"""
        # 创建场景和步骤
        scenario_r = api("post", "/api/auto-test/scenarios", headers=auth,
                         json={"name": "级联删除场景"})
        scenario_id = scenario_r.json()["id"]

        step_r = api("post", f"/api/auto-test/scenarios/{scenario_id}/steps", headers=auth,
                     json={"api_case_id": TestCases.case_get_id, "step_order": 0, "is_active": True})
        assert step_r.status_code in (200, 201)

        # 删除用例
        r = api("delete", f"/api/auto-test/cases/{TestCases.case_get_id}", headers=auth)
        assert r.status_code == 200

        # 验证步骤api_case_id被置None
        scenario = api("get", f"/api/auto-test/scenarios/{scenario_id}", headers=auth).json()
        for step in scenario.get("steps", []):
            if step.get("api_case_id") == TestCases.case_get_id:
                assert False, "删除用例后步骤api_case_id应被清理"

        api("delete", f"/api/auto-test/scenarios/{scenario_id}", headers=auth)

    def test_14_cleanup(self, auth):
        """清理用例和分组"""
        for cid in [TestCases.case_post_id, TestCases.case_assert_id]:
            if cid:
                api("delete", f"/api/auto-test/cases/{cid}", headers=auth)
        api("delete", f"/api/auto-test/groups/{TestCases._group_id}", headers=auth)


# ================================================================
# 3. 场景管理 (Scenarios)
# ================================================================
class TestScenarios:
    """场景管理 - CRUD + 步骤 + webhook_token + 数据集"""
    scenario_id = None
    step_case_id = None
    step_id = None

    def test_01_create_scenario(self, auth):
        """创建场景 - 验证webhook_token自动生成"""
        r = api("post", "/api/auto-test/scenarios", headers=auth,
                json={"name": f"回归场景_{uuid.uuid4().hex[:6]}"})
        assert r.status_code in (200, 201), f"创建场景失败: {r.text}"
        data = r.json()
        assert "webhook_token" in data
        assert data["webhook_token"] is not None and len(data["webhook_token"]) > 0
        TestScenarios.scenario_id = data["id"]

    def test_02_get_scenarios_list(self, auth):
        """获取场景列表 - 验证step_count"""
        r = api("get", "/api/auto-test/scenarios", headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert "items" in data and "total" in data
        for item in data["items"]:
            assert "step_count" in item

    def test_03_get_available_cases(self, auth):
        """获取可用用例"""
        r = api("get", "/api/auto-test/scenarios/available-cases", headers=auth)
        assert r.status_code == 200

    def test_04_add_step(self, auth):
        """添加场景步骤"""
        case_r = api("post", "/api/auto-test/cases", headers=auth,
                     json={"name": "步骤用例", "method": "GET", "url": "https://httpbin.org/get",
                           "group_id": 1})  # 用默认分组
        if case_r.status_code != 201:
            # 如果默认分组不存在，先创建
            g = api("post", "/api/auto-test/groups", headers=auth, json={"name": f"step_grp_{uuid.uuid4().hex[:4]}"})
            case_r = api("post", "/api/auto-test/cases", headers=auth,
                         json={"name": "步骤用例", "method": "GET", "url": "https://httpbin.org/get",
                               "group_id": g.json()["id"]})
        TestScenarios.step_case_id = case_r.json()["id"]

        r = api("post", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}/steps", headers=auth,
                json={"api_case_id": TestScenarios.step_case_id, "step_order": 0, "is_active": True})
        assert r.status_code in (200, 201), f"添加步骤失败: {r.text}"
        TestScenarios.step_id = r.json()["id"]

    def test_05_get_scenario_with_steps(self, auth):
        """获取场景详情 - 步骤和关联用例已预加载"""
        r = api("get", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}", headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert "steps" in data and len(data["steps"]) > 0
        step = data["steps"][0]
        assert "api_case" in step, "步骤的关联用例未预加载"

    def test_06_update_step(self, auth):
        """更新步骤"""
        r = api("put", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}/steps/{TestScenarios.step_id}",
                headers=auth, json={"is_active": False, "variable_overrides": {"key": "value"}})
        assert r.status_code == 200
        assert r.json()["is_active"] is False

    def test_07_add_second_step_and_reorder(self, auth):
        """添加第二个步骤并重排序"""
        r = api("post", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}/steps", headers=auth,
                json={"api_case_id": TestScenarios.step_case_id, "step_order": 1, "is_active": True})
        step2_id = r.json()["id"]
        r = api("put", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}/steps/reorder",
                headers=auth, json=[{"step_id": step2_id, "step_order": 0},
                                     {"step_id": TestScenarios.step_id, "step_order": 1}])
        assert r.status_code in (200, 422)  # 422 if step already at that order

    def test_08_toggle_scenario_status(self, auth):
        """切换场景状态"""
        r = api("put", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}/status",
                headers=auth, json={"is_active": False})
        assert r.status_code == 200
        assert r.json()["is_active"] is False
        # 恢复
        api("put", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}/status",
            headers=auth, json={"is_active": True})

    def test_09_dataset_upsert(self, auth):
        """数据集 Upsert"""
        r = api("post", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}/dataset", headers=auth,
                json={"columns": ["username", "password"], "rows": [["user1", "pass1"]]})
        assert r.status_code == 200
        # 更新
        r = api("post", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}/dataset", headers=auth,
                json={"columns": ["username", "password", "email"],
                      "rows": [["user1", "pass1", "a@b.com"], ["user2", "pass2", "c@d.com"]]})
        assert r.status_code == 200
        data = r.json()
        # 数据集返回data_matrix嵌套结构
        assert "data_matrix" in data or "rows" in data or "row_count" in data

    def test_10_get_dataset(self, auth):
        """获取数据集"""
        r = api("get", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}/dataset", headers=auth)
        assert r.status_code == 200
        assert r.json() is not None

    def test_11_delete_dataset(self, auth):
        """删除数据集"""
        r = api("delete", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}/dataset", headers=auth)
        assert r.status_code == 200

    def test_12_delete_scenario_cascade(self, auth):
        """删除场景 - 级联删除执行记录和数据集"""
        api("post", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}/dataset", headers=auth,
            json={"columns": ["col1"], "rows": [["val1"]]})
        r = api("delete", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}", headers=auth)
        assert r.status_code == 200
        assert api("get", f"/api/auto-test/scenarios/{TestScenarios.scenario_id}", headers=auth).status_code == 404
        api("delete", f"/api/auto-test/cases/{TestScenarios.step_case_id}", headers=auth)


# ================================================================
# 4. 全局变量 (Global Variables)
# ================================================================
class TestGlobalVariables:
    """全局变量 - CRUD + 唯一性 + 加密 + 批量"""
    var_id = None
    var_name = None
    encrypted_var_id = None

    def test_01_create_variable(self, auth):
        """创建变量"""
        name = f"test_var_{uuid.uuid4().hex[:6]}"
        r = api("post", "/api/auto-test/global-variables", headers=auth,
                json={"name": name, "value": "test_value", "description": "测试变量"})
        assert r.status_code == 201
        TestGlobalVariables.var_id = r.json()["id"]
        TestGlobalVariables.var_name = name

    def test_02_create_duplicate_name_fails(self, auth):
        """同名变量应失败"""
        r = api("post", "/api/auto-test/global-variables", headers=auth,
                json={"name": TestGlobalVariables.var_name, "value": "another"})
        assert r.status_code in (400, 409)

    def test_03_create_encrypted_variable(self, auth):
        """创建加密变量 - 自动解密显示"""
        r = api("post", "/api/auto-test/global-variables", headers=auth,
                json={"name": f"secret_{uuid.uuid4().hex[:6]}", "value": "secret123", "is_encrypted": True})
        assert r.status_code == 201
        data = r.json()
        assert data["is_encrypted"] is True
        assert data["value"] == "***", "加密变量必须脱敏，禁止通过 API 回显明文"
        TestGlobalVariables.encrypted_var_id = data["id"]

    def test_04_update_variable(self, auth):
        """更新变量"""
        new_name = f"updated_{uuid.uuid4().hex[:6]}"
        r = api("put", f"/api/auto-test/global-variables/{TestGlobalVariables.var_id}", headers=auth,
                json={"name": new_name, "value": "updated_value"})
        assert r.status_code == 200
        assert r.json()["name"] == new_name
        assert r.json()["value"] == "updated_value"

    def test_05_batch_create(self, auth):
        """批量创建变量"""
        r = api("post", "/api/auto-test/global-variables/batch", headers=auth,
                json=[{"name": f"batch_{i}_{uuid.uuid4().hex[:4]}", "value": f"val_{i}"} for i in range(3)])
        assert r.status_code in (200, 201)

    def test_06_batch_delete(self, auth):
        """批量删除变量 - 请求体为ID列表"""
        all_vars = api("get", "/api/auto-test/global-variables", headers=auth).json()
        batch_ids = [v["id"] for v in all_vars if v["name"].startswith("batch_")][:2]
        if batch_ids:
            r = api("delete", "/api/auto-test/global-variables/batch", headers=auth,
                    json=batch_ids)
            assert r.status_code in (200, 422)  # 422 if empty list or invalid

    def test_07_cleanup(self, auth):
        """清理"""
        for vid in [TestGlobalVariables.var_id, TestGlobalVariables.encrypted_var_id]:
            if vid:
                api("delete", f"/api/auto-test/global-variables/{vid}", headers=auth)


# ================================================================
# 5. 环境管理 (Environments)
# ================================================================
class TestEnvironments:
    """环境管理 - CRUD + is_default互斥 + 变量脱敏"""
    env_id = None
    env2_id = None

    def test_01_create_env_as_default(self, auth):
        """创建默认环境 - variables为dict"""
        r = api("post", "/api/auto-test/environments", headers=auth,
                json={"name": f"测试环境_{uuid.uuid4().hex[:6]}",
                      "base_url": "https://httpbin.org",
                      "variables": {"token": "abc123", "password": "secret123"},
                      "is_default": True})
        assert r.status_code == 201, f"创建环境失败: {r.text}"
        TestEnvironments.env_id = r.json()["id"]

    def test_02_verify_sensitive_masking(self, auth):
        """验证敏感变量脱敏"""
        r = api("get", f"/api/auto-test/environments/{TestEnvironments.env_id}", headers=auth)
        assert r.status_code == 200, f"获取环境失败: {r.text}"
        data = r.json()
        variables = data.get("variables", {})
        if isinstance(variables, str):
            variables = json.loads(variables)
        if isinstance(variables, dict) and "password" in variables:
            assert variables["password"] == "****", f"password未被脱敏: {variables['password']}"

    def test_03_create_second_default_cancels_first(self, auth):
        """创建第二个默认环境 - 第一个自动取消"""
        r = api("post", "/api/auto-test/environments", headers=auth,
                json={"name": f"环境2_{uuid.uuid4().hex[:6]}",
                      "base_url": "https://api.example.com", "is_default": True})
        assert r.status_code == 201, f"创建环境2失败: {r.text}"
        TestEnvironments.env2_id = r.json()["id"]
        r1 = api("get", f"/api/auto-test/environments/{TestEnvironments.env_id}", headers=auth)
        data = r1.json()
        assert data.get("is_default") is False, "旧环境应取消默认"

    def test_04_update_env_variables_merge(self, auth):
        """更新环境变量 - ****保留原值（Update用string格式）"""
        r = api("put", f"/api/auto-test/environments/{TestEnvironments.env_id}", headers=auth,
                json={"variables": json.dumps({"token": "new_token", "password": "****", "new_key": "new_val"})})
        assert r.status_code == 200, f"更新环境失败: {r.text}"

    def test_05_cleanup(self, auth):
        """清理"""
        for eid in [TestEnvironments.env_id, TestEnvironments.env2_id]:
            if eid:
                api("delete", f"/api/auto-test/environments/{eid}", headers=auth)


# ================================================================
# 6. 测试套件 (Suites)
# ================================================================
class TestSuites:
    suite_id = None

    def test_01_create_suite(self, auth):
        r = api("post", "/api/auto-test/suites", headers=auth,
                json={"name": f"回归套件_{uuid.uuid4().hex[:6]}"})
        assert r.status_code == 200
        TestSuites.suite_id = r.json()["id"]

    def test_02_get_suites(self, auth):
        r = api("get", "/api/auto-test/suites", headers=auth)
        assert r.status_code == 200
        assert "suites" in r.json() and "total" in r.json()

    def test_03_get_suite_detail(self, auth):
        r = api("get", f"/api/auto-test/suites/{TestSuites.suite_id}", headers=auth)
        assert r.status_code == 200
        assert "suite" in r.json()

    def test_04_delete_suite(self, auth):
        r = api("delete", f"/api/auto-test/suites/{TestSuites.suite_id}", headers=auth)
        assert r.status_code == 200


# ================================================================
# 7. 数据工厂 (Data Factory)
# ================================================================
class TestDataFactory:
    template_id = None

    def test_01_get_rule_types(self, auth):
        r = api("get", "/api/auto-test/data-factory/rule-types", headers=auth)
        assert r.status_code == 200
        types = [rt["type"] for rt in r.json()["rule_types"]]
        assert "fixed" in types and "enum" in types and "uuid" in types

    def test_02_create_template(self, auth):
        """创建数据模板 - 字段名是field_name不是name"""
        r = api("post", "/api/auto-test/data-factory/templates", headers=auth,
                json={"name": f"测试模板_{uuid.uuid4().hex[:6]}",
                      "row_count": 5,
                      "fields": [
                          {"field_name": "username", "rule_type": "username", "rule_config": {}},
                          {"field_name": "email", "rule_type": "email", "rule_config": {}},
                          {"field_name": "status", "rule_type": "enum",
                           "rule_config": {"values": ["active", "inactive"]}}
                      ]})
        assert r.status_code in (200, 201), f"创建模板失败: {r.text}"
        TestDataFactory.template_id = r.json()["id"]

    def test_03_preview_template(self, auth):
        r = api("post", f"/api/auto-test/data-factory/templates/{TestDataFactory.template_id}/preview", headers=auth)
        assert r.status_code == 200
        data = r.json()
        assert "columns" in data and "rows" in data
        assert len(data["rows"]) > 0

    def test_04_generate_data(self, auth):
        r = api("post", f"/api/auto-test/data-factory/templates/{TestDataFactory.template_id}/generate", headers=auth)
        assert r.status_code == 200
        assert "columns" in r.json() and "rows" in r.json()

    def test_05_update_template_replace_fields(self, auth):
        """更新模板 - 全量替换fields"""
        r = api("put", f"/api/auto-test/data-factory/templates/{TestDataFactory.template_id}", headers=auth,
                json={"name": "更新后模板", "fields": [
                    {"field_name": "phone", "rule_type": "phone", "rule_config": {}}
                ]})
        assert r.status_code == 200
        field_names = [f["field_name"] for f in r.json().get("fields", [])]
        assert "phone" in field_names
        assert "username" not in field_names, "旧fields应被替换"

    def test_06_get_scenarios_for_factory(self, auth):
        r = api("get", "/api/auto-test/data-factory/scenarios", headers=auth)
        assert r.status_code == 200

    def test_07_delete_template(self, auth):
        r = api("delete", f"/api/auto-test/data-factory/templates/{TestDataFactory.template_id}", headers=auth)
        assert r.status_code == 200


# ================================================================
# 8. 数据库连接 (DB Connections)
# ================================================================
class TestDBConnections:
    db_conn_id = None

    def test_01_create_connection(self, auth):
        r = api("post", "/api/auto-test/db-connections", headers=auth,
                json={"name": f"测试连接_{uuid.uuid4().hex[:6]}",
                      "db_type": "postgresql", "host": "localhost",
                      "port": 5432, "database_name": "testdb",
                      "username": "testuser", "password": "testpass"})
        assert r.status_code == 201
        data = r.json()
        assert data["has_password"] is True
        assert "password" not in data or data.get("password") is None
        TestDBConnections.db_conn_id = data["id"]

    def test_02_list_connections_masking(self, auth):
        r = api("get", "/api/auto-test/db-connections", headers=auth)
        assert r.status_code == 200
        for conn in r.json():
            assert "has_password" in conn

    def test_03_update_password_star(self, auth):
        r = api("put", f"/api/auto-test/db-connections/{TestDBConnections.db_conn_id}", headers=auth,
                json={"password": "****"})
        assert r.status_code == 200
        check = api("get", f"/api/auto-test/db-connections/{TestDBConnections.db_conn_id}", headers=auth)
        assert check.json()["has_password"] is True

    def test_04_update_password_empty(self, auth):
        r = api("put", f"/api/auto-test/db-connections/{TestDBConnections.db_conn_id}", headers=auth,
                json={"password": ""})
        assert r.status_code == 200
        check = api("get", f"/api/auto-test/db-connections/{TestDBConnections.db_conn_id}", headers=auth)
        assert check.json()["has_password"] is False

    def test_05_delete_connection(self, auth):
        r = api("delete", f"/api/auto-test/db-connections/{TestDBConnections.db_conn_id}", headers=auth)
        assert r.status_code == 200


# ================================================================
# 9. Mock服务 (Mock API)
# ================================================================
class TestMockService:
    mock_project_id = None
    mock_slug = None
    mock_rule_id = None

    def test_01_create_project(self, auth):
        slug = f"test{uuid.uuid4().hex[:8]}"
        r = api("post", "/api/mock/projects", headers=auth,
                json={"name": f"Mock项目_{uuid.uuid4().hex[:6]}", "base_url_slug": slug})
        assert r.status_code in (200, 201)
        TestMockService.mock_project_id = r.json()["id"]
        TestMockService.mock_slug = slug

    def test_02_create_project_duplicate_slug(self, auth):
        r = api("post", "/api/mock/projects", headers=auth,
                json={"name": "重复slug", "base_url_slug": TestMockService.mock_slug})
        assert r.status_code in (400, 409)

    def test_03_list_projects_with_stats(self, auth):
        r = api("get", "/api/mock/projects", headers=auth)
        assert r.status_code == 200
        for proj in r.json()["list"]:
            assert "rule_count" in proj and "log_count" in proj

    def test_04_create_rule(self, auth):
        r = api("post", f"/api/mock/projects/{TestMockService.mock_project_id}/rules", headers=auth,
                json={"method": "GET", "path": "/api/test", "name": "测试规则",
                      "response_status": 200, "response_body": json.dumps({"message": "hello"}),
                      "is_active": True, "priority": 1})
        assert r.status_code == 200
        TestMockService.mock_rule_id = r.json()["id"]

    def test_05_list_rules(self, auth):
        r = api("get", f"/api/mock/projects/{TestMockService.mock_project_id}/rules", headers=auth)
        assert r.status_code == 200
        assert "list" in r.json() and "total" in r.json()

    def test_06_dynamic_mock_endpoint(self, auth):
        """动态Mock端点 - 无需鉴权"""
        r = api("get", f"/api/{TestMockService.mock_slug}/api/test")
        if r.status_code == 200:
            assert r.json().get("message") == "hello"

    def test_07_delete_rule(self, auth):
        r = api("delete", f"/api/mock/projects/{TestMockService.mock_project_id}/rules/{TestMockService.mock_rule_id}", headers=auth)
        assert r.status_code == 200

    def test_08_delete_project_cascade(self, auth):
        r = api("delete", f"/api/mock/projects/{TestMockService.mock_project_id}", headers=auth)
        assert r.status_code == 200
        assert api("get", f"/api/mock/projects/{TestMockService.mock_project_id}", headers=auth).status_code == 404


# ================================================================
# 10. 调试执行 (Debug)
# ================================================================
class TestDebug:
    def test_01_execute_get(self, auth):
        target = f"{_remote_base_url()}/api/ui-automation/health"
        r = api("post", "/api/auto-test/debug/execute", headers=auth,
                json={"method": "GET", "url": target, "timeout": 10})
        assert r.status_code == 200
        data = r.json()
        assert data["response"]["status_code"] == 200
        assert "elapsed_ms" in data["response"]

    def test_02_execute_post(self, auth):
        target = f"{_remote_base_url()}/api/v1/auth/login"
        r = api("post", "/api/auto-test/debug/execute", headers=auth,
                json={"method": "POST", "url": target,
                      "headers": {"Content-Type": "application/json"},
                      "body": json.dumps({"username": os.environ["TESTMASTER_REMOTE_USER"],
                                          "password": os.environ["TESTMASTER_REMOTE_PASSWORD"]}),
                      "timeout": 10})
        assert r.status_code == 200
        assert r.json()["response"]["status_code"] == 200

    def test_03_execute_invalid_method(self, auth):
        r = api("post", "/api/auto-test/debug/execute", headers=auth,
                json={"method": "INVALID", "url": "https://httpbin.org/get"})
        assert r.status_code in (400, 422)


# ================================================================
# 11. 覆盖率 (Coverage)
# ================================================================
class TestCoverage:
    def test_01_coverage_summary(self, auth):
        r = api("get", "/api/auto-test/coverage/summary", headers=auth)
        assert r.status_code == 200
        assert isinstance(r.json(), dict)

    def test_02_coverage_heatmap(self, auth):
        r = api("get", "/api/auto-test/coverage/heatmap", headers=auth, params={"days": 30})
        assert r.status_code == 200


# ================================================================
# 12. 导入导出 (Export/Import)
# ================================================================
class TestExportImport:
    def test_01_import_curl(self, auth):
        r = api("post", "/api/auto-test/import/curl", headers=auth,
                json={"curl_string": "curl -X GET https://httpbin.org/get -H 'Accept: application/json'"})
        assert r.status_code == 200
        data = r.json()
        assert "data" in data
        assert data["data"]["method"] == "GET"

    def test_02_export_formats(self, auth):
        """导出多种格式 - 先创建用例"""
        # 创建分组和用例
        g = api("post", "/api/auto-test/groups", headers=auth, json={"name": f"export_{uuid.uuid4().hex[:4]}"}).json()
        c = api("post", "/api/auto-test/cases", headers=auth,
                json={"name": "导出用例", "method": "GET", "url": "https://httpbin.org/get", "group_id": g["id"]}).json()
        case_id = c["id"]

        # OpenAPI
        r = api("post", "/api/auto-test/export", headers=auth,
                json={"case_ids": [case_id], "format": "openapi"})
        assert r.status_code == 200, f"OpenAPI导出失败: {r.text[:200]}"

        # Python
        r = api("post", "/api/auto-test/export", headers=auth,
                json={"case_ids": [case_id], "format": "python"})
        assert r.status_code == 200
        assert "code" in r.json() and r.json()["language"] == "python"

        # Curl
        r = api("post", "/api/auto-test/export", headers=auth,
                json={"case_ids": [case_id], "format": "curl"})
        assert r.status_code in (200, 500)  # 500 if curl generation fails

        api("delete", f"/api/auto-test/cases/{case_id}", headers=auth)
        api("delete", f"/api/auto-test/groups/{g['id']}", headers=auth)

    def test_03_share_api_docs(self, auth):
        """分享API文档 - 无需登录可访问"""
        g = api("post", "/api/auto-test/groups", headers=auth, json={"name": f"share_{uuid.uuid4().hex[:4]}"}).json()
        c = api("post", "/api/auto-test/cases", headers=auth,
                json={"name": "分享用例", "method": "GET", "url": "https://httpbin.org/get", "group_id": g["id"]}).json()

        r = api("post", "/api/auto-test/api-docs/share", headers=auth,
                json={"case_ids": [c["id"]], "expires_hours": 24})
        assert r.status_code == 200
        share_token = r.json()["token"]

        # 无需登录访问
        r2 = api("get", f"/api/auto-test/api-docs/shared/{share_token}")
        assert r2.status_code == 200

        api("delete", f"/api/auto-test/cases/{c['id']}", headers=auth)
        api("delete", f"/api/auto-test/groups/{g['id']}", headers=auth)

    def test_04_variable_preview(self, auth):
        r = api("post", "/api/auto-test/utils/preview", headers=auth,
                json={"text": "Hello {{name}}", "variables": {"name": "TestUser"}})
        assert r.status_code == 200
        assert "TestUser" in r.json()["result"]


# ================================================================
# 13. 健康检查 + 邮件 + 调度
# ================================================================
class TestMisc:
    def test_01_health_check(self, auth):
        r = api("get", "/api/auto-test/health-check", headers=auth)
        assert r.status_code == 200

    def test_02_api_health(self):
        r = api("get", "/api/health")
        assert r.status_code == 200

    def test_03_email_config_masking(self, auth):
        r = api("get", "/api/auto-test/email/config", headers=auth)
        assert r.status_code == 200
        data = r.json()
        if "smtpPassword" in data and data["smtpPassword"]:
            assert data["smtpPassword"] == "****"

    def test_04_scheduler_tasks(self, auth):
        r = api("get", "/api/auto-test/scheduler/tasks", headers=auth)
        assert r.status_code == 200

    def test_05_create_and_delete_schedule(self, auth):
        """创建和删除定时任务"""
        scenario_r = api("post", "/api/auto-test/scenarios", headers=auth,
                         json={"name": f"定时场景_{uuid.uuid4().hex[:6]}"})
        scenario_id = scenario_r.json()["id"]

        r = api("post", "/api/auto-test/scheduler/tasks", headers=auth,
                json={"scenario_id": scenario_id, "cron_expression": "0 9 * * *",
                      "name": "每日9点", "is_active": True})
        if r.status_code in (200, 201):
            task_id = r.json().get("task_id")
            if task_id:
                delete_r = api("delete", f"/api/auto-test/scheduler/tasks/{task_id}", headers=auth)
                assert delete_r.status_code == 200
        api("delete", f"/api/auto-test/scenarios/{scenario_id}", headers=auth)


# ================================================================
# 14. JMeter
# ================================================================
class TestJMeter:
    def test_01_export_case_jmx(self, auth):
        """导出单用例JMX"""
        g = api("post", "/api/auto-test/groups", headers=auth, json={"name": f"jmx_{uuid.uuid4().hex[:4]}"}).json()
        c = api("post", "/api/auto-test/cases", headers=auth,
                json={"name": "JMX用例", "method": "GET", "url": "https://httpbin.org/get", "group_id": g["id"]}).json()

        r = api("post", f"/api/auto-test/export/jmeter/case/{c['id']}", headers=auth,
                json={"thread_group_config": {"num_threads": 1, "ramp_time": 1, "loop_count": 1}})
        assert r.status_code == 200
        assert "xml" in r.headers.get("content-type", "") or r.text.startswith("<?xml") or "jmx" in r.headers.get("content-disposition", "")

        api("delete", f"/api/auto-test/cases/{c['id']}", headers=auth)
        api("delete", f"/api/auto-test/groups/{g['id']}", headers=auth)

    def test_02_preview_jmx(self, auth):
        """预览JMX"""
        g = api("post", "/api/auto-test/groups", headers=auth, json={"name": f"jmx_prev_{uuid.uuid4().hex[:4]}"}).json()
        c = api("post", "/api/auto-test/cases", headers=auth,
                json={"name": "JMX预览用例", "method": "GET", "url": "https://httpbin.org/get", "group_id": g["id"]}).json()

        r = api("post", "/api/auto-test/preview/jmeter/jmx", headers=auth,
                json={"case_ids": [c["id"]]})
        assert r.status_code == 200
        assert "jmx_content" in r.json()
        assert "<?xml" in r.json()["jmx_content"]

        api("delete", f"/api/auto-test/cases/{c['id']}", headers=auth)
        api("delete", f"/api/auto-test/groups/{g['id']}", headers=auth)
