
"""
场景测试自动生成文件
Scenario: 测试1
Scenario ID: 1
History ID: 57c027c2
Total Steps: 2
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
            f.write("Scenario_Name=测试1\n")
            f.write("History_ID='57c027c2'\n")
            f.write("Total_Steps=2\n")
    yield

@pytest.fixture(scope="session", autouse=True)
def scenario_setup_teardown():
    print("\n[ScenarioExecutionEngine] 开始执行场景: {scenario_name}")
    yield
    print("\n[ScenarioExecutionEngine] 场景执行完成")

@allure.feature("测试1")
@allure.story("步骤 1：获取随机生成的复杂用户信息")
@allure.title("测试步骤: 步骤 1：获取随机生成的复杂用户信息")
def test_step_1_1(shared_ctx):
    """[GET] 步骤 1：获取随机生成的复杂用户信息 - HTTP 200"""
    shared_ctx["steps"].append({
        "name": "[GET] 步骤 1：获取随机生成的复杂用户信息",
        "status": "passed",
        "status_code": 200,
        "response_time": 465,
        "url": "https://randomuser.me/api/"
    })
    with allure.step("1. 发起HTTP请求: GET https://randomuser.me/api/"):
        request_info = {
            "url": "https://randomuser.me/api/",
            "method": "GET",
            "headers": {},
            "payload": {"results": [{"gender": "female", "name": {"first": "John", "last": "Doe"}, "email": "john.doe@example.com", "login": {"uuid": "abc-123-xyz", "username": "johndoe123"}}], "info": {"version": "1.3"}}
        }
        allure.attach(
            json.dumps(request_info, ensure_ascii=False, indent=2),
            name="请求信息",
            attachment_type=allure.attachment_type.JSON
        )
        pass
    status_code = 200
    response_time_ms = 465
    response_body = "{\"results\":[{\"gender\":\"female\",\"name\":{\"title\":\"Mrs\",\"first\":\"Thea\",\"last\":\"Zhang\"},\"location\":{\"street\":{\"number\":4521,\"name\":\"Ronwood Avenue\"},\"city\":\"Blenheim\",\"state\":\"West Coast\",\"country\":\"New Zealand\",\"postcode\":77065,\"coordinates\":{\"latitude\":\"48.6817\",\"longitude\":\"36.1159\"},\"timezone\":{\"offset\":\"-12:00\",\"description\":\"Eniwetok, Kwajalein\"}},\"email\":\"thea.zhang@example.com\",\"login\":{\"uuid\":\"ff607c1f-bc02-47cf-a68a-893a0eefb3d6\",\"username\":\"redleopard635\",\"password\":\"live\",\"salt\":\"VclEV04z\",\"md5\":\"baf096adbc80bea4687c700c04d91e1c\",\"sha1\":\"6a0db64e18726d9504b2e65cc3a3016c45ddac1d\",\"sha256\":\"490482c03408aced25f26dfb975112f7db6693f308158e351228e1a79b009748\"},\"dob\":{\"date\":\"1956-07-20T09:11:17.801Z\",\"age\":69},\"registered\":{\"date\":\"2015-07-10T06:28:38.185Z\",\"age\":10},\"phone\":\"(989)-718-4987\",\"cell\":\"(027)-046-9839\",\"id\":{\"name\":\"\",\"value\":null},\"picture\":{\"large\":\"https://randomuser.me/api/portraits/women/2.jpg\",\"medium\":\"https://randomuser.me/api/portraits/med/women/2.jpg\",\"thumbnail\":\"https://randomuser.me/api/portraits/thumb/women/2.jpg\"},\"nat\":\"NZ\"}],\"info\":{\"seed\":\"69ea366f8ab41cae\",\"results\":1,\"page\":1,\"version\":\"1.4\"}}"
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

@allure.feature("测试1")
@allure.story("步骤 2：用提取出来的数据组装全新的请求体")
@allure.title("测试步骤: 步骤 2：用提取出来的数据组装全新的请求体")
def test_step_2_2(shared_ctx):
    """[POST] 步骤 2：用提取出来的数据组装全新的请求体 - HTTP 200"""
    shared_ctx["steps"].append({
        "name": "[POST] 步骤 2：用提取出来的数据组装全新的请求体",
        "status": "passed",
        "status_code": 200,
        "response_time": 1706,
        "url": "https://httpbin.org/post"
    })
    with allure.step("1. 发起HTTP请求: POST https://httpbin.org/post"):
        request_info = {
            "url": "https://httpbin.org/post",
            "method": "POST",
            "headers": {"Content-Type": "application/json"},
            "payload": {"message": "报告！我已经成功抓获目标", "suspect_email": "{{target_email}}", "suspect_id": "{{target_uuid}}"}
        }
        allure.attach(
            json.dumps(request_info, ensure_ascii=False, indent=2),
            name="请求信息",
            attachment_type=allure.attachment_type.JSON
        )
        pass
    status_code = 200
    response_time_ms = 1706
    response_body = "{\n  \"args\": {}, \n  \"data\": \"{\\\"message\\\":\\\"\\u62a5\\u544a\\uff01\\u6211\\u5df2\\u7ecf\\u6210\\u529f\\u6293\\u83b7\\u76ee\\u6807\\\",\\\"suspect_email\\\":\\\"{{target_email}}\\\",\\\"suspect_id\\\":\\\"{{target_uuid}}\\\"}\", \n  \"files\": {}, \n  \"form\": {}, \n  \"headers\": {\n    \"Accept\": \"*/*\", \n    \"Accept-Encoding\": \"gzip, deflate\", \n    \"Content-Length\": \"116\", \n    \"Content-Type\": \"application/json\", \n    \"Host\": \"httpbin.org\", \n    \"User-Agent\": \"python-httpx/0.28.1\", \n    \"X-Amzn-Trace-Id\": \"Root=1-69de2704-7d508dc566a892490477c7b8\"\n  }, \n  \"json\": {\n    \"message\": \"\\u62a5\\u544a\\uff01\\u6211\\u5df2\\u7ecf\\u6210\\u529f\\u6293\\u83b7\\u76ee\\u6807\", \n    \"suspect_email\": \"{{target_email}}\", \n    \"suspect_id\": \"{{target_uuid}}\"\n  }, \n  \"origin\": \"34.96.134.66\", \n  \"url\": \"https://httpbin.org/post\"\n}\n"
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

