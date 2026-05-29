"""
AutoTest HTTP 请求服务
从 routers/autotest_execution.py 的 send_request 端点下沉的业务逻辑
"""

import json
import logging
import time
from typing import Any, Dict, Optional

import httpx
from sqlalchemy import select

from fastapi_backend.core.ssrf_guard import validate_url_safety
from fastapi_backend.utils.autotest_helpers import convert_to_dict

_logger = logging.getLogger(__name__)

_http_client: Optional[httpx.AsyncClient] = None


def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient(timeout=30, verify=True)
    return _http_client


async def resolve_variables(env_id: Optional[int], variables: Dict[str, Any]) -> Dict[str, Any]:
    """
    加载全局变量和环境变量，合并到 variables 中
    """
    from fastapi_backend.core.autotest_database import AsyncSessionLocal
    from fastapi_backend.models.autotest import (
        AutoTestGlobalVariable,
        AutoTestEnvironment,
    )
    from fastapi_backend.utils.encryption import decrypt

    variables = dict(variables)

    async with AsyncSessionLocal() as session:
        global_vars_result = await session.execute(select(AutoTestGlobalVariable))
        global_vars = {}
        for var in global_vars_result.scalars().all():
            value = var.value
            if var.is_encrypted:
                value = decrypt(value)
            global_vars[var.name] = value
        variables.update(global_vars)

        if env_id:
            result = await session.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.id == env_id))
            env = result.scalar_one_or_none()
            if env and env.variables and isinstance(env.variables, dict):
                variables.update(env.variables)

    return variables


def apply_variable_substitution(
    url: str,
    headers: Dict,
    params: Dict,
    body: Any,
    variables: Dict[str, Any],
) -> tuple:
    """
    对 url/headers/params/body 执行变量替换
    Returns:
        (url, headers, params, body) 替换后的元组
    """
    from fastapi_backend.utils.parser import replace_variables as rv

    if variables:
        url = rv(url, variables)
        if isinstance(headers, dict):
            headers = {k: rv(str(v), variables) for k, v in headers.items()}
        if isinstance(params, dict):
            params = {k: rv(str(v), variables) for k, v in params.items()}
        if body and isinstance(body, str):
            body = rv(body, variables)
        elif body and isinstance(body, dict):
            body_str = json.dumps(body, ensure_ascii=False)
            body_str = rv(body_str, variables)
            try:
                body = json.loads(body_str)
            except Exception:
                body = body_str

    return url, headers, params, body


async def execute_http_request(
    method: str,
    url: str,
    headers: Dict,
    params: Dict,
    body: Any,
    body_type: str = "json",
    env_id: Optional[int] = None,
    variables: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    执行 HTTP 请求的完整流程：
    1. SSRF 安全校验
    2. 加载全局变量/环境变量
    3. 变量替换
    4. 请求体格式处理
    5. 发送请求并返回结果
    """
    if variables is None:
        variables = {}

    safe, reason = validate_url_safety(url)
    if not safe:
        return {"success": False, "error": reason, "execution_time": 0}

    variables = await resolve_variables(env_id, variables)

    url, headers, params, body = apply_variable_substitution(url, headers, params, body, variables)

    start_time = time.time()
    try:
        req_kwargs: Dict[str, Any] = {"headers": headers, "params": params}
        processed_body = convert_to_dict(body) if body_type in ("form", "form-data") else body
        if body_type == "json" and processed_body:
            if isinstance(processed_body, str):
                try:
                    processed_body = json.loads(processed_body)
                except json.JSONDecodeError as e:
                    return {
                        "error": f"请求体 JSON 格式校验失败: {e}",
                        "execution_time": 0,
                    }
            req_kwargs["json"] = processed_body
        elif body_type in ("form", "form-data") and processed_body:
            req_kwargs["data"] = processed_body
        elif processed_body:
            if isinstance(processed_body, str):
                try:
                    processed_body = json.loads(processed_body)
                except json.JSONDecodeError as e:
                    return {
                        "error": f"请求体 JSON 格式校验失败: {e}",
                        "execution_time": 0,
                    }
            req_kwargs["json"] = processed_body

        client = _get_http_client()
        resp = await client.request(method, url, **req_kwargs)

        execution_time = int((time.time() - start_time) * 1000)
        try:
            response_content = resp.json()
        except Exception:
            response_content = resp.text

        return {
            "status_code": resp.status_code,
            "response_content": response_content,
            "data": response_content,
            "body": response_content,
            "headers": dict(resp.headers),
            "content_length": len(resp.content or b""),
            "execution_time": execution_time,
            "elapsed_ms": execution_time,
            "success": 200 <= resp.status_code < 400,
        }
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "请求超时",
            "execution_time": int((time.time() - start_time) * 1000),
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "error": "连接失败，请检查网络或服务地址",
            "execution_time": int((time.time() - start_time) * 1000),
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time": int((time.time() - start_time) * 1000),
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time": int((time.time() - start_time) * 1000),
        }
