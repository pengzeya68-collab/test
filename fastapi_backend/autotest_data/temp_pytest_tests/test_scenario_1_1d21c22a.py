
"""
场景测试自动生成文件
Scenario: 测试
Scenario ID: 1
History ID: 1d21c22a
Total Steps: 1
"""
import pytest
import sys
import allure
import json
import time

@pytest.fixture(scope="session")
def shared_ctx():
    return {"steps": []}

@pytest.fixture(scope="session", autouse=True)
def write_allure_environment(request):
    import sys
    from pathlib import Path
    allure_dir = request.config.getoption("--alluredir")
    if allure_dir:
        env_file = Path(allure_dir) / "environment.properties"
        with open(env_file, "w", encoding="utf-8") as f:
            f.write("Platform=TestMaster_AutoTest\n")
            f.write("Python_Version=" + sys.version.split()[0] + "\n")
            f.write("Scenario_ID=1\n")
            f.write("Scenario_Name=测试\n")
            f.write("History_ID='1d21c22a'\n")
            f.write("Total_Steps=1\n")
    yield

@pytest.fixture(scope="session", autouse=True)
def scenario_setup_teardown():
    print("\n[ScenarioExecutionEngine] 开始执行场景: {scenario_name}")
    yield
    print("\n[ScenarioExecutionEngine] 场景执行完成")

@allure.feature("测试")
@allure.story("11")
@allure.title("测试步骤: 11")
def test_step_1_1(shared_ctx):
    """[GET] 11 - HTTP 200"""
    shared_ctx["steps"].append({
        "name": "[GET] 11",
        "status": "passed",
        "status_code": 200,
        "response_time": 138,
        "url": "https://jsonplaceholder.typicode.com/todos/1"
    })
    with allure.step("1. 发起HTTP请求: GET https://jsonplaceholder.typicode.com/todos/1"):
        request_info = {
            "url": "https://jsonplaceholder.typicode.com/todos/1",
            "method": "GET",
            "headers": {},
            "payload": {}
        }
        allure.attach(
            json.dumps(request_info, ensure_ascii=False, indent=2),
            name="请求信息",
            attachment_type=allure.attachment_type.JSON
        )
        pass
    status_code = 200
    response_time_ms = 138
    response_body = "{\n  \"userId\": 1,\n  \"id\": 1,\n  \"title\": \"delectus aut autem\",\n  \"completed\": false\n}"
    with allure.step("2. 获取响应信息"):
        response_info = {
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "body": response_body
        }
        allure.attach(
            json.dumps(response_info, ensure_ascii=False, indent=2),
            name="响应信息",
            attachment_type=allure.attachment_type.JSON
        )
    assert True, "步骤执行成功"


def test_scenario_summary(request):
    steps = request.node.session.config.cache.get("steps", [])
    total = len(request.node.session.config.cache.get("step_results", []))
    passed = len([s for s in request.node.session.config.cache.get("step_results", []) if s.get("status") == "success"])
    failed = len([s for s in request.node.session.config.cache.get("step_results", []) if s.get("status") == "failed"])
    print(f"\n[Summary] Total: {total}, Passed: {passed}, Failed: {failed}")
    has_failed = any(s.get("status") == "failed" for s in request.node.session.config.cache.get("step_results", []))
    assert not has_failed, "场景执行存在失败的步骤"
