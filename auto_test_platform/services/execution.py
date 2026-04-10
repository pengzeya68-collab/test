"""
测试执行引擎
按照用户 Prompt 3 要求实现

功能：
- 根据 case_id 和 env_id 执行单个用例
- 使用 replace_variables 替换变量
- 动态生成 YAML 测试数据
- 调用 Pytest 执行测试
- 返回执行结果
"""
import os
import json
import time
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any
import requests

from auto_test_platform.models import ApiCase, Environment
from auto_test_platform.utils.parser import replace_variables


# 获取当前目录
BASE_DIR = Path(__file__).parent.parent.absolute()


def replace_case_variables(case: ApiCase, env: Optional[Environment]) -> Dict[str, Any]:
    """
    替换用例中的变量占位符

    Args:
        case: 用例对象
        env: 环境对象（可选）

    Returns:
        替换后的用例数据字典
    """
    # 合并变量：环境变量 + 内置变量
    variables = {}

    # 添加内置变量：base_url 和 api_prefix
    if env:
        # 从 base_url 中提取 host:port 作为 base_url 变量的值
        if env.base_url:
            variables["base_url"] = env.base_url.rstrip("/")
        # 默认 api_prefix 为空字符串（如果 URL 是完整路径则不需要）
        variables["api_prefix"] = ""

    # 添加环境变量（会覆盖内置变量）
    if env and env.variables:
        variables.update(env.variables)

    # 获取完整 URL
    url = case.url

    # 先替换 URL 中的变量
    url = replace_variables(url, variables)

    # 如果 URL 不是以 http 开头，则拼接 base_url
    if env and env.base_url and not url.startswith(("http://", "https://")):
        url = env.base_url.rstrip("/") + "/" + url.lstrip("/")

    # 替换请求头中的变量
    headers = case.headers
    if headers:
        headers = replace_variables(headers, variables)

    # 替换请求体中的变量
    payload = case.payload
    if payload:
        payload = replace_variables(payload, variables)

    return {
        "name": case.name,
        "method": case.method,
        "url": url,
        "headers": headers or {},
        "payload": payload,
        "assert_rules": case.assert_rules or {}
    }


async def quick_run_case(case: ApiCase, env: Optional[Environment]) -> Dict[str, Any]:
    """
    快速执行用例（不保存历史记录）

    Args:
        case: 用例对象
        env: 环境对象（可选）

    Returns:
        执行结果字典
    """
    start_time = time.time()

    try:
        # 替换变量
        case_data = replace_case_variables(case, env)

        # 发送请求
        method = case_data["method"].upper()
        url = case_data["url"]
        headers = case_data["headers"]
        payload = case_data["payload"]

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
            return {
                "success": False,
                "status_code": None,
                "response": None,
                "execution_time": 0,
                "error": f"不支持的请求方法: {method}",
                "assert_result": None
            }

        execution_time = int((time.time() - start_time) * 1000)

        # ========== Bug 1 修复：状态码拦截 - 发起请求后立即检查 ==========
        # 只要状态码 >= 400，强制标记失败，不需要后续断言检查
        if response.status_code >= 400:
            # 解析响应
            try:
                response_data = response.json()
            except:
                response_data = {"raw": response.text}
            return {
                "success": False,
                "status_code": response.status_code,
                "response": response_data,
                "execution_time": execution_time,
                "error": f"状态码错误: 期望 2xx/3xx, 实际返回 {response.status_code}",
                "assert_result": {
                    "passed": False,
                    "message": f"默认断言失败: 状态码 {response.status_code} >= 400",
                    "details": [{
                        "type": "status_code_intercept",
                        "expected": "2xx/3xx (< 400)",
                        "actual": response.status_code,
                        "passed": False
                    }]
                }
            }
        # ========== Bug 1 修复结束 ==========

        # 解析响应
        try:
            response_data = response.json()
        except:
            response_data = {"raw": response.text}

        # 执行断言
        assert_result = execute_assertions(case_data["assert_rules"], response.status_code, response_data)

        return {
            "success": assert_result["passed"],
            "status_code": response.status_code,
            "response": response_data,
            "execution_time": execution_time,
            "error": None if assert_result["passed"] else assert_result["message"],
            "assert_result": assert_result
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "status_code": None,
            "response": None,
            "execution_time": int((time.time() - start_time) * 1000),
            "error": "请求超时",
            "assert_result": None
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "status_code": None,
            "response": None,
            "execution_time": int((time.time() - start_time) * 1000),
            "error": "连接失败，请检查网络或服务地址",
            "assert_result": None
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "response": None,
            "execution_time": int((time.time() - start_time) * 1000),
            "error": str(e),
            "assert_result": None
        }


def execute_assertions(assert_rules: Any, status_code: int, response: Any) -> Dict[str, Any]:
    """
    执行断言

    支持两种格式:

    格式1 - 对象格式 (旧版):
    {
        "status_code": 200,
        "json_path": {"$.code": {"eq": 0}}
    }

    格式2 - 数组格式 (新版，前端编辑器的格式):
    [
        {"field": "status_code", "operator": "equals", "expectedValue": 200},
        {"field": "body.code", "operator": "equals", "expectedValue": 0}
    ]

    Args:
        assert_rules: 断言规则
        status_code: 实际状态码
        response: 响应数据

    Returns:
        {
            "passed": bool,
            "message": str,
            "details": []
        }
    """
    details = []
    all_passed = True
    error_messages = []
    has_status_code_assertion = False

    # 如果没有断言规则，默认检查 2xx/3xx 状态码
    if not assert_rules:
        # 默认兜底校验：检查状态码是否为 2xx 或 3xx
        if not (200 <= status_code < 400):
            all_passed = False
            error_messages.append(f"默认断言失败: 期望 2xx/3xx, 实际返回 {status_code}")
            details.append({
                "type": "default_status_code",
                "expected": "2xx/3xx",
                "actual": status_code,
                "passed": False
            })
        else:
            details.append({
                "type": "default_status_code",
                "expected": "2xx/3xx",
                "actual": status_code,
                "passed": True
            })
        return {
            "passed": all_passed,
            "message": "; ".join(error_messages) if error_messages else "默认状态码检查通过",
            "details": details
        }

    # 格式2: 数组格式 (前端编辑器的格式)
    if isinstance(assert_rules, list):
        for rule in assert_rules:
            if not isinstance(rule, dict):
                continue

            field = rule.get("field", "") or rule.get("target", "")

            # 检查是否配置了 status_code 断言
            if field == "status_code":
                has_status_code_assertion = True

            operator = rule.get("operator", "") or rule.get("condition", "equals")
            expected = rule.get("expectedValue") or rule.get("value", "")

            # 获取实际值
            actual = get_field_value(field, status_code, response)

            # 执行断言
            passed = compare_values(actual, operator, expected)

            if not passed:
                all_passed = False
                error_messages.append(f"字段 {field} {get_operator_text(operator)} {expected}，实际: {actual}")

            details.append({
                "type": "assertion",
                "field": field,
                "operator": operator,
                "expected": expected,
                "actual": actual,
                "passed": passed
            })

    # 格式1: 对象格式 (旧版)
    elif isinstance(assert_rules, dict):
        # 断言状态码
        if "status_code" in assert_rules:
            has_status_code_assertion = True
            expected = assert_rules["status_code"]

            # 处理多种格式的状态码断言
            if isinstance(expected, dict):
                # 新格式: {"operator": "range", "expectedValue": "2xx/3xx"} 或 {"eq": 200}
                operator = expected.get("operator", "equals")
                expected_value = expected.get("expectedValue") or expected.get("eq")

                if operator == "range":
                    # 处理范围格式，如 "2xx/3xx"
                    range_text = str(expected_value).lower()
                    if "2xx" in range_text or "2xx/3xx" == range_text:
                        passed = (200 <= status_code < 400)
                    elif "3xx" in range_text:
                        passed = (300 <= status_code < 400)
                    elif "2xx" == range_text:
                        passed = (200 <= status_code < 300)
                    else:
                        # 尝试解析范围值
                        passed = (200 <= status_code < 400)
                else:
                    passed = compare_values(status_code, operator, expected_value)
            else:
                # 旧格式: 直接是数字，如 200
                passed = (status_code == expected)

            if not passed:
                all_passed = False
                error_messages.append(f"状态码断言失败: 期望 {expected}, 实际 {status_code}")
            details.append({
                "type": "status_code",
                "expected": expected,
                "actual": status_code,
                "passed": passed
            })

        # JSON 路径断言
        if "json_path" in assert_rules and isinstance(response, dict):
            for path, rule in assert_rules["json_path"].items():
                keys = path.replace("$.", "").split(".")
                value = response
                for key in keys:
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break

                if "eq" in rule:
                    passed = (value == rule["eq"])
                    if not passed:
                        all_passed = False
                        error_messages.append(f"JSON路径 {path} 断言失败: 期望 {rule['eq']}, 实际 {value}")
                    details.append({
                        "type": "json_path",
                        "path": path,
                        "assertion": "eq",
                        "expected": rule["eq"],
                        "actual": value,
                        "passed": passed
                    })
                elif "contains" in rule:
                    passed = (value is not None and rule["contains"] in str(value))
                    if not passed:
                        all_passed = False
                        error_messages.append(f"JSON路径 {path} 不包含: {rule['contains']}")
                    details.append({
                        "type": "json_path",
                        "path": path,
                        "assertion": "contains",
                        "expected": rule["contains"],
                        "actual": value,
                        "passed": passed
                    })

    # 其他格式，默认通过
    else:
        pass

    # 如果没有配置 status_code 断言，添加默认兜底校验
    if not has_status_code_assertion:
        if not (200 <= status_code < 400):
            all_passed = False
            error_messages.append(f"默认断言失败: 期望 2xx/3xx, 实际返回 {status_code}")
            details.append({
                "type": "default_status_code",
                "expected": "2xx/3xx",
                "actual": status_code,
                "passed": False
            })

    if all_passed:
        return {"passed": True, "message": "所有断言通过", "details": details}
    else:
        return {"passed": False, "message": "; ".join(error_messages), "details": details}


def get_field_value(field: str, status_code: int, response: Any) -> Any:
    """根据字段名获取实际值"""
    if field == "status_code":
        return status_code
    elif field == "response_time":
        return None  # 需要在请求时测量
    elif field == "body" or field == "response_body":
        return response
    elif field == "headers":
        return None
    elif field.startswith("body.") or field.startswith("response."):
        # 支持 body.code, response.data.token 等
        keys = field.replace("body.", "").replace("response.", "").split(".")
        value = response
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    return None


def compare_values(actual: Any, operator: str, expected: Any) -> bool:
    """比较值"""
    if actual is None:
        return False

    if operator == "equals" or operator == "eq":
        return str(actual) == str(expected)
    elif operator == "not_equals" or operator == "ne":
        return str(actual) != str(expected)
    elif operator == "contains":
        return str(expected) in str(actual)
    elif operator == "not_contains":
        return str(expected) not in str(actual)
    elif operator == "gt":
        try:
            return float(actual) > float(expected)
        except:
            return False
    elif operator == "lt":
        try:
            return float(actual) < float(expected)
        except:
            return False
    elif operator == "gte":
        try:
            return float(actual) >= float(expected)
        except:
            return False
    elif operator == "lte":
        try:
            return float(actual) <= float(expected)
        except:
            return False
    elif operator == "regex":
        import re
        try:
            return bool(re.search(str(expected), str(actual)))
        except:
            return False
    elif operator == "json_exists":
        return actual is not None
    return True


def get_operator_text(operator: str) -> str:
    """获取操作符的中文描述"""
    mapping = {
        "equals": "等于",
        "eq": "等于",
        "not_equals": "不等于",
        "ne": "不等于",
        "contains": "包含",
        "not_contains": "不包含",
        "gt": "大于",
        "lt": "小于",
        "gte": "大于等于",
        "lte": "小于等于",
        "regex": "正则匹配",
        "json_exists": "存在"
    }
    return mapping.get(operator, operator)


def generate_test_yaml(case_data: Dict[str, Any], output_path: Path) -> None:
    """
    将用例数据生成 YAML 文件供 Pytest 使用

    Args:
        case_data: 替换后的用例数据
        output_path: 输出文件路径
    """
    import yaml

    yaml_content = {
        "test_cases": [case_data]
    }

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f, allow_unicode=True, default_flow_style=False)


async def run_case_with_pytest(case: ApiCase, env: Optional[Environment], history_id: int) -> Dict[str, Any]:
    """
    使用 Pytest 执行用例（生成 Allure 报告）

    Args:
        case: 用例对象
        env: 环境对象
        history_id: 历史记录ID

    Returns:
        执行结果字典
    """
    from database import async_session
    from models import TestHistory

    start_time = time.time()

    try:
        # 1. 替换变量
        case_data = replace_case_variables(case, env)

        # 2. 生成临时 YAML 文件
        temp_dir = BASE_DIR / "temp_run_data"
        temp_dir.mkdir(exist_ok=True)

        yaml_file = temp_dir / f"case_{case.id}.yaml"
        generate_test_yaml(case_data, yaml_file)

        # 3. 生成 Allure 结果目录
        allure_results_dir = BASE_DIR / "allure-results" / f"case_{case.id}"
        allure_results_dir.mkdir(parents=True, exist_ok=True)

        # 4. 调用 Pytest 执行
        import sys
        runner_script = BASE_DIR / "runner" / "test_core.py"
        allure_results_dir_abs = str(allure_results_dir.absolute())

        # 兼容处理：尝试两种方式，保证在任何环境都能运行
        # 方式1: python -m pytest (使用当前 Python，能找到当前环境安装的 allure-pytest)
        # 方式2: 直接调用 pytest 命令 (当当前 Python 没有安装 pytest 但 PATH 中有时使用)

        # 尝试 1: 使用当前 Python 解释器执行 pytest
        python_executable = sys.executable
        cmd1 = [
            python_executable,
            "-m",
            "pytest",
            str(runner_script),
            f"--data_path={yaml_file}",
            f"--alluredir={allure_results_dir_abs}",
            "-v"
        ]

        print(f"[Execution] 尝试方式1: {' '.join(cmd1)}")
        result = subprocess.run(
            cmd1,
            capture_output=True,
            text=True,
            timeout=60,
            shell=True  # Windows 上需要 shell=True
        )

        # 检查是否生成了结果文件
        result_files = list(allure_results_dir.glob("*.json"))
        print(f"[Execution] 方式1 后 JSON 结果文件数量: {len(result_files)}")

        # 如果方式1失败（No module named pytest），尝试方式2和方式3
        if len(result_files) == 0 and result.returncode != 0 and "No module named pytest" in result.stderr:
            print(f"[Execution] 方式1失败，尝试其他方式")

            # 方式2: 尝试从 Python 的 Scripts 目录找到 pytest.exe (Windows 常见位置)
            python_dir = Path(sys.executable).parent
            pytest_exe = python_dir / "Scripts" / "pytest.exe"

            if pytest_exe.exists():
                cmd2 = [
                    str(pytest_exe),
                    str(runner_script),
                    f"--data_path={yaml_file}",
                    f"--alluredir={allure_results_dir_abs}",
                    "-v"
                ]
                print(f"[Execution] 尝试方式2 (Python Scripts): {' '.join(cmd2)}")
                result = subprocess.run(
                    cmd2,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    shell=True
                )
                print(f"[Execution] 方式2 结果: returncode={result.returncode}")
                if result.stdout:
                    print(f"[Execution] 方式2 stdout:\n{result.stdout}")
                if result.stderr:
                    print(f"[Execution] 方式2 stderr:\n{result.stderr}")
                result_files = list(allure_results_dir.glob("*.json"))
                print(f"[Execution] 方式2 后 JSON 结果文件数量: {len(result_files)}")
            else:
                print(f"[Execution] Scripts/pytest.exe 不存在: {pytest_exe}")

            # 如果方式2也失败，尝试方式3: 直接调用 pytest 命令 (PATH 中)
            if len(result_files) == 0:
                print(f"[Execution] 尝试方式3 (PATH 中): 直接调用 pytest 命令")
                cmd3 = [
                    "pytest",
                    str(runner_script),
                    f"--data_path={yaml_file}",
                    f"--alluredir={allure_results_dir_abs}",
                    "-v"
                ]
                print(f"[Execution] 尝试方式3: {' '.join(cmd3)}")
                result = subprocess.run(
                    cmd3,
                    capture_output=True,
                    text=True,
                    timeout=60,
                    shell=True
                )
                print(f"[Execution] 方式3 结果: returncode={result.returncode}")
                if result.stdout:
                    print(f"[Execution] 方式3 stdout:\n{result.stdout}")
                if result.stderr:
                    print(f"[Execution] 方式3 stderr:\n{result.stderr}")
                result_files = list(allure_results_dir.glob("*.json"))
                print(f"[Execution] 方式3 后 JSON 结果文件数量: {len(result_files)}")

        execution_time = int((time.time() - start_time) * 1000)

        # 5. 生成 Allure 报告
        report_dir = BASE_DIR / "reports" / f"report_{history_id}"
        report_dir.mkdir(parents=True, exist_ok=True)

        try:
            cmd_result = subprocess.run(
                ["allure", "generate", str(allure_results_dir), "-o", str(report_dir), "--clean"],
                capture_output=True,
                shell=True  # Windows 上需要 shell=True 才能运行 .cmd 文件
            )
            if cmd_result.returncode == 0:
                report_url = f"/reports/report_{history_id}/index.html"
                print(f"[Execution] Allure 报告生成成功: {report_url}")
            else:
                print(f"[Execution] Allure 报告生成失败, returncode={cmd_result.returncode}")
                print(f"[Execution] stderr: {cmd_result.stderr.decode('utf-8', errors='ignore')}")
                report_url = None
        except FileNotFoundError as e:
            print(f"[Execution] Allure 命令未找到，请安装 Allure: {e}")
            report_url = None
        except Exception as e:
            print(f"[Execution] Allure 报告生成异常: {e}")
            report_url = None

        # 6. 判断执行结果
        success = result.returncode == 0

        # 7. 更新历史记录
        async with async_session() as session:
            from sqlalchemy import update
            await session.execute(
                update(TestHistory)
                .where(TestHistory.id == history_id)
                .values(
                    status="success" if success else "failed",
                    execution_time=execution_time,
                    report_url=report_url
                )
            )
            await session.commit()

        return {
            "success": success,
            "execution_time": execution_time,
            "report_url": report_url,
            "output": result.stdout,
            "error": result.stderr if not success else None
        }

    except subprocess.TimeoutExpired:
        execution_time = int((time.time() - start_time) * 1000)

        # 更新历史记录为失败
        async with async_session() as session:
            from sqlalchemy import update
            await session.execute(
                update(TestHistory)
                .where(TestHistory.id == history_id)
                .values(
                    status="error",
                    execution_time=execution_time,
                    error_message="执行超时"
                )
            )
            await session.commit()

        return {
            "success": False,
            "execution_time": execution_time,
            "error": "执行超时（60秒）",
            "report_url": None
        }

    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)

        # 更新历史记录为失败
        async with async_session() as session:
            from sqlalchemy import update
            await session.execute(
                update(TestHistory)
                .where(TestHistory.id == history_id)
                .values(
                    status="error",
                    execution_time=execution_time,
                    error_message=str(e)
                )
            )
            await session.commit()

        return {
            "success": False,
            "execution_time": execution_time,
            "error": str(e),
            "report_url": None
        }
