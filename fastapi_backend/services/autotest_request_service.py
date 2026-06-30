"""
AutoTest HTTP 请求服务
从 routers/autotest_execution.py 的 send_request 端点下沉的业务逻辑
"""

import json
import logging
import threading
import time
from typing import Any, Dict, Optional

import httpx
from sqlalchemy import select

from fastapi_backend.core.ssrf_guard import validate_url_safety
from fastapi_backend.utils.autotest_helpers import convert_to_dict

_logger = logging.getLogger(__name__)

_http_client: Optional[httpx.AsyncClient] = None
_client_lock = threading.Lock()


def _get_http_client() -> httpx.AsyncClient:
    """获取 HTTP 客户端单例，线程安全"""
    global _http_client
    if _http_client is None or _http_client.is_closed:
        with _client_lock:
            if _http_client is None or _http_client.is_closed:
                from fastapi_backend.core.config import settings
                _http_client = httpx.AsyncClient(
                    timeout=30,
                    verify=not settings.DISABLE_SSL_VERIFY,
                    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
                )
    return _http_client


async def shutdown_http_client():
    global _http_client
    with _client_lock:
        client = _http_client
        _http_client = None
    if client is not None:
        await client.aclose()


async def resolve_variables(env_id: Optional[int], variables: Dict[str, Any], user_id: int = None) -> Dict[str, Any]:
    """
    加载全局变量和环境变量，合并到 variables 中
    """
    from fastapi_backend.core.autotest_database import AsyncSessionLocal
    from fastapi_backend.models.autotest import AutoTestGlobalVariable, AutoTestEnvironment
    from fastapi_backend.utils.encryption import decrypt
    from fastapi_backend.services.autotest_variable_service import deserialize_var_value

    variables = dict(variables)

    async with AsyncSessionLocal() as session:
        query = select(AutoTestGlobalVariable)
        if user_id is not None:
            query = query.where(AutoTestGlobalVariable.user_id == user_id)
        global_vars_result = await session.execute(query)
        global_vars = {}
        for var in global_vars_result.scalars().all():
            value = var.value
            if var.is_encrypted:
                value = decrypt(value)
            # 反序列化以还原原始类型（int/float/bool/dict/list 等）
            value = deserialize_var_value(value)
            global_vars[var.name] = value
        variables.update(global_vars)

        if env_id:
            env_query = select(AutoTestEnvironment).where(AutoTestEnvironment.id == env_id)
            if user_id is not None:
                env_query = env_query.where(AutoTestEnvironment.user_id == user_id)
            result = await session.execute(env_query)
            env = result.scalar_one_or_none()
            if env:
                # 🔥 修复：环境变量继承——当 env 设置了 parent_id 时，合并整条继承链上的变量
                # （子环境覆盖父环境同名变量），与 replace_case_variables 保持一致
                if getattr(env, "parent_id", None) is not None:
                    try:
                        from fastapi_backend.services.autotest_variable_service import (
                            get_effective_variables,
                        )

                        effective_vars = await get_effective_variables(session, env.id)
                        for v in effective_vars:
                            variables[v["name"]] = v["value"]
                    except Exception:
                        if env.variables and isinstance(env.variables, dict):
                            variables.update(env.variables)
                elif env.variables and isinstance(env.variables, dict):
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
    user_id: int = None,
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

    variables = await resolve_variables(env_id, variables, user_id=user_id)

    url, headers, params, body = apply_variable_substitution(url, headers, params, body, variables)

    # 变量替换后再次校验 SSRF（防止通过变量注入内网地址）
    safe, reason = validate_url_safety(url)
    if not safe:
        return {"success": False, "error": reason, "execution_time": 0}

    start_time = time.time()
    try:
        req_kwargs: Dict[str, Any] = {"headers": headers, "params": params}
        processed_body = convert_to_dict(body) if body_type in ("form", "form-data") else body
        if body_type == "json" and processed_body:
            if isinstance(processed_body, str):
                try:
                    processed_body = json.loads(processed_body)
                except json.JSONDecodeError as e:
                    return {"success": False, "error": f"请求体 JSON 格式校验失败: {e}", "execution_time": 0}
            req_kwargs["json"] = processed_body
        elif body_type in ("form", "form-data") and processed_body:
            req_kwargs["data"] = processed_body
        elif body_type == "raw" and processed_body:
            # raw 模式：直接发送原始字符串
            if isinstance(processed_body, str):
                req_kwargs["content"] = processed_body.encode("utf-8")
            else:
                req_kwargs["content"] = str(processed_body).encode("utf-8")
        elif processed_body:
            if isinstance(processed_body, str):
                try:
                    processed_body = json.loads(processed_body)
                except json.JSONDecodeError as e:
                    return {"success": False, "error": f"请求体 JSON 格式校验失败: {e}", "execution_time": 0}
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
            "status_code": None,
            "response_content": None,
            "headers": {},
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "error": "连接失败，请检查网络或服务地址",
            "execution_time": int((time.time() - start_time) * 1000),
            "status_code": None,
            "response_content": None,
            "headers": {},
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time": int((time.time() - start_time) * 1000),
            "status_code": None,
            "response_content": None,
            "headers": {},
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time": int((time.time() - start_time) * 1000),
            "status_code": None,
            "response_content": None,
            "headers": {},
        }
