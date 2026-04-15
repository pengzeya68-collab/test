"""
测试执行引擎

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
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime
import requests

from fastapi_backend.utils.parser import replace_variables
from fastapi_backend.models.autotest import AutoTestCase, AutoTestEnvironment, AutoTestGlobalVariable
from fastapi_backend.core.autotest_database import AsyncSessionLocal
from sqlalchemy import select
from fastapi_backend.utils.encryption import decrypt

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"
BASE_DIR = AUTOTEST_DATA_DIR


def _smart_type_convert(obj: Any) -> Any:
    """递归地将 dict/list 中看起来像数字的字符串值转换为数字类型"""
    if isinstance(obj, dict):
        return {k: _smart_type_convert(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_smart_type_convert(item) for item in obj]
    elif isinstance(obj, str):
        if obj.isdigit():
            return int(obj)
        try:
            float_val = float(obj)
            if str(float_val) == obj or obj.count('.') == 1:
                return float_val
        except (ValueError, OverflowError):
            pass
        if obj.lower() == 'true':
            return True
        if obj.lower() == 'false':
            return False
        if obj.lower() == 'null' or obj.lower() == 'none':
            return None
    return obj


async def replace_case_variables(case: AutoTestCase, env: Optional[AutoTestEnvironment]) -> Dict[str, Any]:
    """
    替换用例中的变量占位符
    """
    variables = {}

    # 加载全局变量
    from fastapi_backend.models.autotest import AutoTestGlobalVariable
    async def load_global_variables():
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(AutoTestGlobalVariable))
            global_vars = {}
            for var in result.scalars().all():
                value = var.value
                if var.is_encrypted:
                    value = decrypt(value)
                global_vars[var.name] = value
            return global_vars
    
    global_vars = await load_global_variables()
    variables.update(global_vars)

    if env:
        if env.base_url:
            variables["base_url"] = env.base_url.rstrip("/")
        variables["api_prefix"] = ""

    if env and env.variables and isinstance(env.variables, dict):
        variables.update(env.variables)

    url = case.url
    url = replace_variables(url, variables)

    if env and env.base_url and not url.startswith(("http://", "https://")):
        url = env.base_url.rstrip("/") + "/" + url.lstrip("/")

    headers = case.headers
    if headers:
        if isinstance(headers, dict):
            headers_str = json.dumps(headers, ensure_ascii=False)
            headers_str = replace_variables(headers_str, variables)
            headers = json.loads(headers_str)
            headers = _smart_type_convert(headers)
        else:
            headers = replace_variables(headers, variables)

    payload = case.payload
    if payload:
        if isinstance(payload, dict):
            payload_str = json.dumps(payload, ensure_ascii=False)
            payload_str = replace_variables(payload_str, variables)
            payload = json.loads(payload_str)
            payload = _smart_type_convert(payload)
        else:
            payload = replace_variables(payload, variables)

    params = getattr(case, 'params', None)
    if params:
        if isinstance(params, dict):
            params_str = json.dumps(params, ensure_ascii=False)
            params_str = replace_variables(params_str, variables)
            params = json.loads(params_str)
            params = _smart_type_convert(params)
        elif isinstance(params, str):
            params = replace_variables(params, variables)
            try:
                params = json.loads(params)
                params = _smart_type_convert(params)
            except (json.JSONDecodeError, TypeError):
                pass
    else:
        params = {}

    # 处理 body_type 和 content_type
    body_type = getattr(case, 'body_type', 'none') or 'none'
    content_type = getattr(case, 'content_type', 'application/json') or 'application/json'

    return {
        "name": case.name,
        "method": case.method,
        "url": url,
        "headers": headers or {},
        "params": params,
        "body_type": body_type,
        "content_type": content_type,
        "payload": payload,
        "assert_rules": case.assert_rules or {}
    }


async def quick_run_case(
    case: AutoTestCase,
    env: Optional[AutoTestEnvironment],
    override_params: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    快速执行用例（不保存历史记录）
    override_params: 前端传来的已替换变量后的 params，会覆盖 case 自带的 params
    """
    start_time = time.time()

    try:
        case_data = await replace_case_variables(case, env)

        method = case_data["method"].upper()
        url = case_data["url"]
        headers = case_data["headers"]
        # 🔥 优先使用前端传来的 params（已替换变量），否则用 case 自带的
        params = override_params if override_params is not None else case_data.get("params", {})
        payload = case_data["payload"]
        body_type = case_data.get("body_type", "none")
        content_type = case_data.get("content_type", "application/json")

        # 处理 payload 为字符串的情况
        if isinstance(payload, str) and payload:
            import json
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                pass

        # 构建请求 kwargs
        req_kwargs = {
            "headers": headers,
            "timeout": 30
        }

        if params:
            req_kwargs["params"] = params

        if method in ("POST", "PUT", "PATCH"):
            if body_type == "none" or not payload:
                pass
            elif body_type == "raw":
                if content_type == "application/json":
                    req_kwargs["json"] = payload
                else:
                    req_kwargs["data"] = str(payload) if payload else ""
                    if headers and isinstance(headers, dict):
                        headers["Content-Type"] = content_type
                    else:
                        req_kwargs["headers"] = {**(headers or {}), "Content-Type": content_type}
            elif body_type == "form-data":
                req_kwargs["data"] = payload

        if method == "GET":
            response = await asyncio.to_thread(requests.get, url, **req_kwargs)
        elif method == "POST":
            response = await asyncio.to_thread(requests.post, url, **req_kwargs)
        elif method == "PUT":
            response = await asyncio.to_thread(requests.put, url, **req_kwargs)
        elif method == "DELETE":
            response = await asyncio.to_thread(requests.delete, url, **req_kwargs)
        elif method == "PATCH":
            response = await asyncio.to_thread(requests.patch, url, **req_kwargs)
        else:
            return {
                "success": False,
                "status_code": 400,
                "response": None,
                "execution_time": 0,
                "error": f"不支持的请求方法: {method}",
                "assert_result": None,
                "request_body": payload
            }

        execution_time = int((time.time() - start_time) * 1000)

        try:
            response_data = response.json()
        except Exception:
            response_data = {"raw": response.text}

        # 🔥 修复：无论状态码如何，都执行变量提取
        extractors = None
        if hasattr(case, 'extractors'):
            extractors = case.extractors
        extracted_vars = await extract_variables_from_response(extractors, response_data, response.text)
        if extracted_vars:
            await save_extracted_variables(extracted_vars)

        # Bug 1 修复：状态码拦截
        if response.status_code >= 400:
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
                },
                "request_body": payload,
                "request_url": url,
                "request_method": method,
            "request_headers": headers,
            "request_params": params,
            "extracted_variables": extracted_vars
        }

        assert_result = execute_assertions(case_data["assert_rules"], response.status_code, response_data)

        return {
            "success": assert_result["passed"],
            "status_code": response.status_code,
            "response": response_data,
            "execution_time": execution_time,
            "error": None if assert_result["passed"] else assert_result["message"],
            "assert_result": assert_result,
            "request_body": payload,
            "request_url": url,
            "request_method": method,
            "request_headers": headers,
            "request_params": params,
            "extracted_variables": extracted_vars
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "status_code": 408,
            "response": None,
            "execution_time": int((time.time() - start_time) * 1000),
            "error": "请求超时",
            "assert_result": None,
            "request_body": case.payload,
            "request_url": case.url if hasattr(case, 'url') else None,
            "request_method": case.method if hasattr(case, 'method') else None,
            "request_headers": None,
            "request_params": None
        }
    except requests.exceptions.ConnectionError:
        return {
            "success": False,
            "status_code": 503,
            "response": None,
            "execution_time": int((time.time() - start_time) * 1000),
            "error": "连接失败，请检查网络或服务地址",
            "assert_result": None,
            "request_body": case.payload,
            "request_url": case.url if hasattr(case, 'url') else None,
            "request_method": case.method if hasattr(case, 'method') else None,
            "request_headers": None,
            "request_params": None
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": 500,
            "response": None,
            "execution_time": int((time.time() - start_time) * 1000),
            "error": str(e),
            "assert_result": None,
            "request_body": case.payload,
            "request_url": case.url if hasattr(case, 'url') else None,
            "request_method": case.method if hasattr(case, 'method') else None,
            "request_headers": None,
            "request_params": None
        }


def execute_assertions(assert_rules: Any, status_code: int, response: Any) -> Dict[str, Any]:
    """
    执行断言，支持对象格式和数组格式
    """
    details = []
    all_passed = True
    error_messages = []
    has_status_code_assertion = False

    if not assert_rules:
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

    # 格式2: 数组格式
    if isinstance(assert_rules, list):
        for rule in assert_rules:
            if not isinstance(rule, dict):
                continue

            field = rule.get("field", "") or rule.get("target", "")
            if field == "status_code":
                has_status_code_assertion = True

            operator = rule.get("operator", "") or rule.get("condition", "equals")
            expected = rule.get("expectedValue") or rule.get("value", "")

            actual = get_field_value(field, status_code, response)
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

    # 格式1: 对象格式
    elif isinstance(assert_rules, dict):
        if "status_code" in assert_rules:
            has_status_code_assertion = True
            expected = assert_rules["status_code"]

            if isinstance(expected, dict):
                operator = expected.get("operator", "equals")
                expected_value = expected.get("expectedValue") or expected.get("eq")

                if operator == "range":
                    range_text = str(expected_value).lower()
                    if "2xx" in range_text or "2xx/3xx" == range_text:
                        passed = (200 <= status_code < 400)
                    elif "3xx" in range_text:
                        passed = (300 <= status_code < 400)
                    elif "2xx" == range_text:
                        passed = (200 <= status_code < 300)
                    else:
                        passed = (200 <= status_code < 400)
                else:
                    passed = compare_values(status_code, operator, expected_value)
            else:
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
        return None
    elif field == "body" or field == "response_body":
        return response
    elif field == "headers":
        return None
    elif field.startswith("body.") or field.startswith("response."):
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

    if operator in ("equals", "eq"):
        return str(actual) == str(expected)
    elif operator in ("not_equals", "ne"):
        return str(actual) != str(expected)
    elif operator == "contains":
        return str(expected) in str(actual)
    elif operator == "not_contains":
        return str(expected) not in str(actual)
    elif operator == "gt":
        try:
            return float(actual) > float(expected)
        except Exception:
            return False
    elif operator == "lt":
        try:
            return float(actual) < float(expected)
        except Exception:
            return False
    elif operator == "gte":
        try:
            return float(actual) >= float(expected)
        except Exception:
            return False
    elif operator == "lte":
        try:
            return float(actual) <= float(expected)
        except Exception:
            return False
    elif operator == "regex":
        import re
        try:
            return bool(re.search(str(expected), str(actual)))
        except Exception:
            return False
    elif operator == "json_exists":
        return actual is not None
    return True


def get_operator_text(operator: str) -> str:
    """获取操作符的中文描述"""
    mapping = {
        "equals": "等于", "eq": "等于", "not_equals": "不等于", "ne": "不等于",
        "contains": "包含", "not_contains": "不包含", "gt": "大于",
        "lt": "小于", "gte": "大于等于", "lte": "小于等于",
        "regex": "正则匹配", "json_exists": "存在"
    }
    return mapping.get(operator, operator)


async def extract_variables_from_response(extractors: Any, response_data: Any, response_text: str) -> Dict[str, str]:
    """
    从响应中提取变量
    Args:
        extractors: 提取规则列表
        response_data: 解析后的响应数据（dict/list）
        response_text: 原始响应文本
    Returns:
        提取的变量字典 {变量名: 变量值}
    """
    if not extractors:
        return {}

    extracted = {}

    for extractor in extractors:
        if not isinstance(extractor, dict):
            continue

        var_name = extractor.get("variableName") or extractor.get("var_name")
        extractor_type = extractor.get("extractorType") or extractor.get("type", "jsonpath")
        expression = extractor.get("expression") or extractor.get("path", "")
        default_value = extractor.get("defaultValue") or extractor.get("default", "")

        if not var_name or not expression:
            continue

        value = default_value

        try:
            if extractor_type == "jsonpath":
                value = extract_jsonpath_value(response_data, expression, default_value)
            elif extractor_type == "regex":
                import re
                match = re.search(expression, response_text)
                if match:
                    value = match.group(1) if match.groups() else match.group(0)
                else:
                    value = default_value
            elif extractor_type == "header":
                pass
        except Exception as e:
            print(f"变量提取失败 {var_name}: {str(e)}")
            value = default_value

        extracted[var_name] = value

    return extracted


def extract_jsonpath_value(data: Any, path: str, default: Any = None) -> Any:
    """
    从 JSON 数据中提取值（简化版 JSONPath）
    支持: $.data.id, $.items[0].name, data.id, items[0].name
    """
    if not path:
        return default

    path = path.replace("$.", "").replace("$", "")

    keys = []
    current = ""
    i = 0
    while i < len(path):
        char = path[i]
        if char == ".":
            if current:
                keys.append(current)
                current = ""
        elif char == "[":
            if current:
                keys.append(current)
                current = ""
            j = i + 1
            while j < len(path) and path[j] != "]":
                j += 1
            index_str = path[i+1:j]
            try:
                keys.append(int(index_str))
            except ValueError:
                pass
            i = j
        elif char == "]":
            pass
        else:
            current += char
        i += 1

    if current:
        keys.append(current)

    value = data
    for key in keys:
        if isinstance(key, int):
            if isinstance(value, list) and 0 <= key < len(value):
                value = value[key]
            else:
                return default
        elif isinstance(value, dict):
            value = value.get(key, default)
        else:
            return default

    return value


async def save_extracted_variables(variables: Dict[str, str]) -> bool:
    """
    将提取的变量保存到全局变量表
    Args:
        variables: 变量字典 {变量名: 变量值}
    Returns:
        是否保存成功
    """
    if not variables:
        return False

    from fastapi_backend.core.autotest_database import AsyncSessionLocal
    from fastapi_backend.models.autotest import AutoTestGlobalVariable
    from sqlalchemy import select

    try:
        async with AsyncSessionLocal() as session:
            for var_name, var_value in variables.items():
                result = await session.execute(
                    select(AutoTestGlobalVariable).where(AutoTestGlobalVariable.name == var_name)
                )
                existing_var = result.scalar_one_or_none()

                if existing_var:
                    existing_var.value = str(var_value)
                    existing_var.updated_at = datetime.utcnow()
                else:
                    new_var = AutoTestGlobalVariable(
                        name=var_name,
                        value=str(var_value),
                        description=f"从测试用例提取",
                        is_encrypted=False
                    )
                    session.add(new_var)

            await session.commit()
            return True
    except Exception as e:
        print(f"保存变量失败: {str(e)}")
        return False


def generate_test_yaml(case_data: Dict[str, Any], output_path: Path) -> None:
    """将用例数据生成 YAML 文件供 Pytest 使用"""
    import yaml

    yaml_content = {"test_cases": [case_data]}

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f, allow_unicode=True, default_flow_style=False)


async def run_case_with_pytest(case: AutoTestCase, env: Optional[AutoTestEnvironment], history_id: int) -> Dict[str, Any]:
    """使用 Pytest 执行用例（生成 Allure 报告）"""
    from fastapi_backend.models.autotest import AutoTestHistory

    start_time = time.time()

    try:
        case_data = await replace_case_variables(case, env)

        temp_dir = BASE_DIR / "temp_run_data"
        temp_dir.mkdir(exist_ok=True)

        yaml_file = temp_dir / f"case_{case.id}.yaml"
        generate_test_yaml(case_data, yaml_file)

        allure_results_dir = BASE_DIR / "allure-results" / f"case_{case.id}"
        allure_results_dir.mkdir(parents=True, exist_ok=True)

        import sys
        runner_script = BASE_DIR / "runner" / "test_core.py"
        allure_results_dir_abs = str(allure_results_dir.absolute())

        python_executable = sys.executable
        cmd1 = [
            python_executable, "-m", "pytest", str(runner_script),
            f"--data_path={yaml_file}", f"--alluredir={allure_results_dir_abs}", "-v"
        ]

        print(f"[Execution] 尝试方式1: {' '.join(cmd1)}")
        result = await asyncio.to_thread(
            subprocess.run, cmd1, capture_output=True, text=True, timeout=60, shell=True
        )

        result_files = list(allure_results_dir.glob("*.json"))
        print(f"[Execution] 方式1 后 JSON 结果文件数量: {len(result_files)}")

        if len(result_files) == 0 and result.returncode != 0 and "No module named pytest" in result.stderr:
            print("[Execution] 方式1失败，尝试其他方式")

            python_dir = Path(sys.executable).parent
            pytest_exe = python_dir / "Scripts" / "pytest.exe"

            if pytest_exe.exists():
                cmd2 = [str(pytest_exe), str(runner_script), f"--data_path={yaml_file}", f"--alluredir={allure_results_dir_abs}", "-v"]
                print(f"[Execution] 尝试方式2 (Python Scripts): {' '.join(cmd2)}")
                result = await asyncio.to_thread(
                    subprocess.run, cmd2, capture_output=True, text=True, timeout=60, shell=True
                )
                result_files = list(allure_results_dir.glob("*.json"))

            if len(result_files) == 0:
                cmd3 = ["pytest", str(runner_script), f"--data_path={yaml_file}", f"--alluredir={allure_results_dir_abs}", "-v"]
                print(f"[Execution] 尝试方式3: {' '.join(cmd3)}")
                result = await asyncio.to_thread(
                    subprocess.run, cmd3, capture_output=True, text=True, timeout=60, shell=True
                )
                result_files = list(allure_results_dir.glob("*.json"))

        execution_time = int((time.time() - start_time) * 1000)

        report_dir = BASE_DIR / "reports" / f"report_{history_id}"
        report_dir.mkdir(parents=True, exist_ok=True)

        try:
            import shutil
            old_report_history = report_dir / "history"
            new_results_history = allure_results_dir / "history"
            if old_report_history.exists() and old_report_history.is_dir():
                if new_results_history.exists():
                    shutil.rmtree(str(new_results_history))
                shutil.copytree(str(old_report_history), str(new_results_history))

            cmd_result = await asyncio.to_thread(
                subprocess.run,
                ["allure", "generate", str(allure_results_dir), "-o", str(report_dir), "--clean"],
                capture_output=True, shell=True
            )
            report_url = f"/reports/report_{history_id}/index.html" if cmd_result.returncode == 0 else None
        except (FileNotFoundError, Exception):
            report_url = None

        success = result.returncode == 0

        # 更新历史记录
        async with AsyncSessionLocal() as session:
            from sqlalchemy import update
            await session.execute(
                update(AutoTestHistory)
                .where(AutoTestHistory.id == history_id)
                .values(status="success" if success else "failed", execution_time=execution_time, report_url=report_url)
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
        async with AsyncSessionLocal() as session:
            from sqlalchemy import update
            await session.execute(
                update(AutoTestHistory).where(AutoTestHistory.id == history_id)
                .values(status="error", execution_time=execution_time, error_message="执行超时")
            )
            await session.commit()
        return {"success": False, "execution_time": execution_time, "error": "执行超时（60秒）", "report_url": None}

    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        async with AsyncSessionLocal() as session:
            from sqlalchemy import update
            await session.execute(
                update(AutoTestHistory).where(AutoTestHistory.id == history_id)
                .values(status="error", execution_time=execution_time, error_message=str(e))
            )
            await session.commit()
        return {"success": False, "execution_time": execution_time, "error": str(e), "report_url": None}
