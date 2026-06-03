"""
测试执行引擎

功能：
- 根据 case_id 和 env_id 执行单个用例
- 使用 replace_variables 替换变量
- 动态生成 YAML 测试数据
- 调用 Pytest 执行测试
- 返回执行结果
"""
import json
import time
import subprocess
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import requests

from fastapi_backend.utils.autotest_helpers import extract_jsonpath_value
from fastapi_backend.services.autotest_assertion_engine import (
    execute_assertions as _engine_execute,
    get_field_value as _engine_get_field_value,
    compare_values as _engine_compare_values,
    get_operator_text as _engine_get_operator_text,
    extract_variables_from_response as _engine_extract_variables,
)
# from fastapi_backend.services.autotest_variable_service import save_variables_to_db
from fastapi_backend.utils.parser import replace_variables
from fastapi_backend.models.autotest import AutoTestCase, AutoTestEnvironment, AutoTestGlobalVariable
from fastapi_backend.core.autotest_database import AsyncSessionLocal
from sqlalchemy import select
from fastapi_backend.utils.encryption import decrypt

_logger = logging.getLogger(__name__)

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"
BASE_DIR = AUTOTEST_DATA_DIR

# 全局变量缓存（5分钟过期，按 user_id 隔离）
_global_vars_cache: Dict[int, Dict] = {}  # {user_id: {"vars": {}, "timestamp": 0}}
_GLOBAL_VARS_CACHE_TTL = 300  # 5分钟


async def _get_global_variables_cached(user_id: int = None) -> Dict[str, Any]:
    """获取全局变量（带缓存，按用户隔离）"""
    now = time.time()
    cache_key = user_id or 0
    cached = _global_vars_cache.get(cache_key)
    if cached and now - cached["timestamp"] < _GLOBAL_VARS_CACHE_TTL:
        return cached["vars"]

    async with AsyncSessionLocal() as session:
        query = select(AutoTestGlobalVariable)
        if user_id is not None:
            query = query.where(AutoTestGlobalVariable.user_id == user_id)
        result = await session.execute(query)
        global_vars = {}
        for var in result.scalars().all():
            value = var.value
            if var.is_encrypted:
                value = decrypt(value)
            global_vars[var.name] = value

    _global_vars_cache[cache_key] = {"vars": global_vars, "timestamp": now}
    return global_vars


def _invalidate_global_vars_cache(user_id: int = None):
    """使全局变量缓存失效"""
    if user_id is not None:
        _global_vars_cache.pop(user_id, None)
    else:
        _global_vars_cache.clear()


async def _save_variables_to_db_safe(extracted_vars: Dict[str, Any], user_id: int = None):
    """保存变量到数据库（带异常处理）"""
    if not extracted_vars:
        return
    try:
        from fastapi_backend.services.autotest_variable_service import save_variables_to_db
        await save_variables_to_db(extracted_vars, user_id=user_id)
        _invalidate_global_vars_cache(user_id)
    except Exception as e:
        _logger.warning(f"保存变量失败: {e}")


def _validate_url(url: str) -> bool:
    """验证URL格式"""
    if not url:
        return False
    if url.startswith(("http://", "https://")):
        return True
    if url.startswith("/"):
        return True
    return False


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


async def replace_case_variables(case: AutoTestCase, env: Optional[AutoTestEnvironment], user_id: int = None) -> Dict[str, Any]:
    """
    替换用例中的变量占位符
    """
    variables = {}

    # 使用缓存的全局变量（按用户隔离）
    global_vars = await _get_global_variables_cached(user_id)
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
    override_params: Optional[Dict[str, Any]] = None,
    user_id: int = None,
) -> Dict[str, Any]:
    """
    快速执行用例（不保存历史记录）
    override_params: 前端传来的已替换变量后的 params，会覆盖 case 自带的 params
    """
    start_time = time.time()

    try:
        case_data = await replace_case_variables(case, env, user_id=user_id)

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
        extracted_vars = await extract_variables_from_response(extractors, response_data, response.text, dict(response.headers))
        if extracted_vars:
            await _save_variables_to_db_safe(extracted_vars, user_id=user_id)

        # 执行断言（不再提前拦截 status_code >= 400，让断言引擎根据用户配置判断）
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
    执行断言，委托给统一断言引擎
    """
    return _engine_execute(
        assert_rules=assert_rules,
        status_code=status_code,
        response_body=response,
        response_time_ms=0,
        response_headers=None,
    )


def get_field_value(field: str, status_code: int, response: Any) -> Any:
    """根据字段名获取实际值，委托给统一断言引擎"""
    return _engine_get_field_value(field, status_code, response)


def compare_values(actual: Any, operator: str, expected: Any) -> bool:
    """比较值，委托给统一断言引擎"""
    return _engine_compare_values(actual, operator, expected)


def get_operator_text(operator: str) -> str:
    """获取操作符的中文描述，委托给统一断言引擎"""
    return _engine_get_operator_text(operator)


async def extract_variables_from_response(extractors: Any, response_data: Any, response_text: str, response_headers: Optional[Dict] = None) -> Dict[str, str]:
    """
    从响应中提取变量，委托给统一断言引擎
    """
    return _engine_extract_variables(
        extractors=extractors,
        response_body=response_data,
        response_text=response_text,
        response_headers=response_headers,
    )



async def save_variables_to_db(variables: Dict[str, str], user_id: int = None) -> bool:
    """
    将提取的变量保存到全局变量表
    Args:
        variables: 变量字典 {变量名: 变量值}
        user_id: 用户ID，用于数据隔离
    Returns:
        是否保存成功
    """
    if not variables:
        return False

    from fastapi_backend.core.autotest_database import AsyncSessionLocal
    from sqlalchemy import select

    try:
        async with AsyncSessionLocal() as session:
            for var_name, var_value in variables.items():
                query = select(AutoTestGlobalVariable).where(AutoTestGlobalVariable.name == var_name)
                if user_id is not None:
                    query = query.where(AutoTestGlobalVariable.user_id == user_id)
                result = await session.execute(query)
                existing_var = result.scalar_one_or_none()

                if existing_var:
                    existing_var.value = str(var_value)
                    existing_var.updated_at = datetime.now(timezone.utc)
                else:
                    new_var = AutoTestGlobalVariable(
                        name=var_name,
                        value=str(var_value),
                        description="从测试用例提取",
                        is_encrypted=False,
                        user_id=user_id,
                    )
                    session.add(new_var)

            await session.commit()
            return True
    except Exception as e:
        _logger.info(f"保存变量失败: {str(e)}")
        return False


def generate_test_yaml(case_data: Dict[str, Any], output_path: Path) -> None:
    """将用例数据生成 YAML 文件供 Pytest 使用"""
    import yaml

    yaml_content = {"test_cases": [case_data]}

    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f, allow_unicode=True, default_flow_style=False)


async def run_case_with_pytest(case: AutoTestCase, env: Optional[AutoTestEnvironment], history_id: int, user_id: int = None) -> Dict[str, Any]:
    """使用 Pytest 执行用例（生成 Allure 报告）"""
    from fastapi_backend.models.autotest import AutoTestHistory

    start_time = time.time()

    try:
        case_data = await replace_case_variables(case, env, user_id=user_id)

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

        _logger.info(f"[Execution] 尝试方式1: {' '.join(cmd1)}")
        result = await asyncio.to_thread(
            subprocess.run, cmd1, capture_output=True, text=True, timeout=60, 
        )

        result_files = list(allure_results_dir.glob("*.json"))
        _logger.info(f"[Execution] 方式1 后 JSON 结果文件数量: {len(result_files)}")

        if len(result_files) == 0 and result.returncode != 0 and "No module named pytest" in result.stderr:
            _logger.info("[Execution] 方式1失败，尝试其他方式")

            python_dir = Path(sys.executable).parent
            pytest_exe = python_dir / "Scripts" / "pytest.exe"

            if pytest_exe.exists():
                cmd2 = [str(pytest_exe), str(runner_script), f"--data_path={yaml_file}", f"--alluredir={allure_results_dir_abs}", "-v"]
                _logger.info(f"[Execution] 尝试方式2 (Python Scripts): {' '.join(cmd2)}")
                result = await asyncio.to_thread(
                    subprocess.run, cmd2, capture_output=True, text=True, timeout=60, 
                )
                result_files = list(allure_results_dir.glob("*.json"))

            if len(result_files) == 0:
                cmd3 = ["pytest", str(runner_script), f"--data_path={yaml_file}", f"--alluredir={allure_results_dir_abs}", "-v"]
                _logger.info(f"[Execution] 尝试方式3: {' '.join(cmd3)}")
                result = await asyncio.to_thread(
                    subprocess.run, cmd3, capture_output=True, text=True, timeout=60, 
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
                capture_output=True, 
            )
            report_url = f"/reports/report_{history_id}/index.html" if cmd_result.returncode == 0 else None
        except (FileNotFoundError, Exception):
            report_url = None

        success = result.returncode == 0

        # 更新历史记录
        async with AsyncSessionLocal() as session:
            from sqlalchemy import update
            stmt = update(AutoTestHistory).where(AutoTestHistory.id == history_id)
            if user_id is not None:
                stmt = stmt.where(AutoTestHistory.user_id == user_id)
            await session.execute(
                stmt.values(status="success" if success else "failed", execution_time=execution_time, report_url=report_url)
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
            stmt = update(AutoTestHistory).where(AutoTestHistory.id == history_id)
            if user_id is not None:
                stmt = stmt.where(AutoTestHistory.user_id == user_id)
            await session.execute(
                stmt.values(status="error", execution_time=execution_time, error_message="执行超时")
            )
            await session.commit()
        return {"success": False, "execution_time": execution_time, "error": "执行超时（60秒）", "report_url": None}

    except Exception as e:
        execution_time = int((time.time() - start_time) * 1000)
        async with AsyncSessionLocal() as session:
            from sqlalchemy import update
            stmt = update(AutoTestHistory).where(AutoTestHistory.id == history_id)
            if user_id is not None:
                stmt = stmt.where(AutoTestHistory.user_id == user_id)
            await session.execute(
                stmt.values(status="error", execution_time=execution_time, error_message=str(e))
            )
            await session.commit()
        return {"success": False, "execution_time": execution_time, "error": str(e), "report_url": None}
