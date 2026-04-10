"""
Pytest 通用测试脚本
按照用户 Prompt 3 要求编写

这个脚本被设计为读取指定的 YAML 文件并执行 HTTP 请求测试

使用方式:
    pytest runner/test_core.py --data_path=temp_run_data/case_1.yaml --alluredir=./allure-results

YAML 文件格式:
    test_cases:
      - name: 用例名称
        method: GET/POST/PUT/DELETE/PATCH
        url: http://example.com/api
        headers:
          Content-Type: application/json
        payload:
          key: value
        assert_rules:
          status_code: 200
          json_path:
            $.code: {"eq": 0}
"""
import pytest
import yaml
import requests
import allure
import time
from pathlib import Path


def load_test_data(data_path: str) -> dict:
    """
    加载 YAML 测试数据文件

    Args:
        data_path: YAML 文件路径

    Returns:
        测试数据字典
    """
    with open(data_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="session")
def test_cases(request):
    """
    从命令行参数加载测试数据
    """
    data_path = request.config.getoption("--data_path")
    if not data_path:
        pytest.fail("必须指定 --data_path 参数")

    data = load_test_data(data_path)
    return data.get("test_cases", [])


@pytest.fixture(scope="session")
def allure_dir(request):
    """
    获取 Allure 结果目录
    """
    return request.config.getoption("--alluredir")


def test_api_case(test_cases, allure_dir):
    """
    执行 API 测试用例

    这个测试函数会：
    1. 从 YAML 文件加载测试数据
    2. 发送 HTTP 请求
    3. 执行断言
    4. 生成 Allure 报告
    """
    for case_data in test_cases:
        name = case_data.get("name", "未命名用例")
        method = case_data.get("method", "GET").upper()
        url = case_data.get("url", "")
        headers = case_data.get("headers", {})
        payload = case_data.get("payload", {})
        assert_rules = case_data.get("assert_rules", {})

        with allure.step(f"执行用例: {name}"):
            with allure.step(f"发送 {method} 请求到 {url}"):
                allure.attach(
                    str(headers),
                    name="请求头",
                    attachment_type=allure.attachment_type.JSON
                )

                if payload:
                    allure.attach(
                        str(payload),
                        name="请求体",
                        attachment_type=allure.attachment_type.JSON
                    )

            start_time = time.time()

            try:
                # 发送请求
                if method == "GET":
                    response = requests.get(url, headers=headers, timeout=30)
                elif method == "POST":
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                elif method == "PUT":
                    response = requests.put(url, headers=headers, json=payload, timeout=30)
                elif method == "DELETE":
                    response = requests.delete(url, headers=headers, timeout=30)
                elif method == "PATCH":
                    response = requests.patch(url, headers=headers, json=payload, timeout=30)
                else:
                    pytest.fail(f"不支持的请求方法: {method}")

                execution_time = int((time.time() - start_time) * 1000)

                # ========== Bug 1 修复：状态码拦截 - 发起请求后立即检查 ==========
                # 只要状态码 >= 400，强制抛出异常标记为失败
                if response.status_code >= 400:
                    # 记录响应
                    with allure.step("记录响应"):
                        allure.attach(
                            str(response.status_code),
                            name="状态码",
                            attachment_type=allure.attachment_type.TEXT
                        )
                        try:
                            response_json = response.json()
                            allure.attach(
                                yaml.dump(response_json, allow_unicode=True),
                                name="响应体",
                                attachment_type=allure.attachment_type.JSON
                            )
                        except:
                            allure.attach(
                                response.text[:1000],
                                name="响应体",
                                attachment_type=allure.attachment_type.TEXT
                            )
                    # 强制抛出异常，标记测试失败
                    raise AssertionError(f"默认断言失败: 期望 2xx/3xx (< 400), 实际返回 {response.status_code}")
                # ========== Bug 1 修复结束 ==========

                # 记录响应
                with allure.step("记录响应"):
                    allure.attach(
                        str(response.status_code),
                        name="状态码",
                        attachment_type=allure.attachment_type.TEXT
                    )

                    try:
                        response_json = response.json()
                        allure.attach(
                            yaml.dump(response_json, allow_unicode=True),
                            name="响应体",
                            attachment_type=allure.attachment_type.JSON
                        )
                    except:
                        allure.attach(
                            response.text[:1000],
                            name="响应体",
                            attachment_type=allure.attachment_type.TEXT
                        )

                    allure.attach(
                        f"{execution_time}ms",
                        name="响应时间",
                        attachment_type=allure.attachment_type.TEXT
                    )

                # 执行断言
                with allure.step("执行断言"):
                    if "status_code" in assert_rules:
                        expected_status = assert_rules["status_code"]
                        assert response.status_code == expected_status, \
                            f"状态码断言失败: 期望 {expected_status}, 实际 {response.status_code}"
                        allure.attach(
                            f"状态码 {response.status_code} == {expected_status}",
                            name="状态码断言",
                            attachment_type=allure.attachment_type.TEXT
                        )

                    # JSON 路径断言
                    if "json_path" in assert_rules and isinstance(response_json, dict):
                        for path, rule in assert_rules["json_path"].items():
                            keys = path.replace("$.", "").split(".")
                            value = response_json
                            for key in keys:
                                if isinstance(value, dict) and key in value:
                                    value = value[key]
                                else:
                                    value = None
                                    break

                            if "eq" in rule:
                                assert value == rule["eq"], \
                                    f"JSON路径 {path} 断言失败: 期望 {rule['eq']}, 实际 {value}"
                            elif "contains" in rule:
                                assert value is not None and rule["contains"] in str(value), \
                                    f"JSON路径 {path} 不包含: {rule['contains']}"

            except requests.exceptions.Timeout:
                pytest.fail(f"请求超时: {url}")
            except requests.exceptions.ConnectionError as e:
                pytest.fail(f"连接失败: {str(e)}")


def pytest_addoption(parser):
    """
    添加自定义命令行参数
    """
    parser.addoption(
        "--data_path",
        action="store",
        default=None,
        help="YAML 测试数据文件路径"
    )
    parser.addoption(
        "--alluredir",
        action="store",
        default=None,
        help="Allure 结果目录"
    )
