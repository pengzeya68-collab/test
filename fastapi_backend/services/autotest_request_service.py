"""
AutoTest HTTP 请求服务
从 routers/autotest_execution.py 的 send_request 端点下沉的业务逻辑
"""

import base64
import copy
import json
import logging
import time
from typing import Any, Dict, Optional
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

import httpx
from sqlalchemy import select

from fastapi_backend.core.ssrf_guard import validate_url_safety
from fastapi_backend.core.config import settings
from fastapi_backend.utils.autotest_helpers import convert_to_dict

_logger = logging.getLogger(__name__)


async def shutdown_http_client():
    """保留启动/关闭契约；请求客户端现在按运行隔离，不再全局共享 Cookie。"""
    return None


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

                        effective_vars = await get_effective_variables(session, env.id, user_id=user_id)
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


def _substitute_config_values(value: Any, variables: Dict[str, Any]) -> Any:
    from fastapi_backend.utils.parser import replace_variables

    if isinstance(value, dict):
        return {key: _substitute_config_values(item, variables) for key, item in value.items()}
    if isinstance(value, list):
        return [_substitute_config_values(item, variables) for item in value]
    if isinstance(value, str):
        return replace_variables(value, variables)
    return value


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
    request_config: Optional[Dict[str, Any]] = None,
    http_client: Optional[httpx.AsyncClient] = None,
    http_client_verify_ssl: Optional[bool] = None,
    resolve_persisted_variables: bool = True,
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

    if resolve_persisted_variables:
        variables = await resolve_variables(env_id, variables, user_id=user_id)
    else:
        variables = dict(variables)

    url, headers, params, body = apply_variable_substitution(url, headers, params, body, variables)

    # 变量替换后再次校验 SSRF（防止通过变量注入内网地址）
    safe, reason = validate_url_safety(url)
    if not safe:
        return {"success": False, "error": reason, "execution_time": 0}

    config = dict(request_config) if isinstance(request_config, dict) else {}
    verify_ssl_explicit = "verify_ssl" in config
    if config and variables:
        config = _substitute_config_values(config, variables)
    try:
        from fastapi_backend.schemas.autotest import AutoTestRequestConfig

        config = AutoTestRequestConfig.model_validate(config).model_dump(by_alias=True)
    except Exception as exc:
        return {
            "success": False,
            "error": f"请求配置无效: {exc}",
            "execution_time": 0,
            "status_code": None,
            "response_content": None,
            "headers": {},
            "attempts": [],
        }
    auth_config = config.get("auth") if isinstance(config.get("auth"), dict) else {}
    auth_type = str(auth_config.get("type") or "none").lower()
    headers = dict(headers or {})
    params = dict(params or {})

    if auth_type == "bearer" and auth_config.get("token"):
        headers.setdefault("Authorization", f"Bearer {auth_config['token']}")
    elif auth_type == "basic":
        username = str(auth_config.get("username") or "")
        password = str(auth_config.get("password") or "")
        token = base64.b64encode(f"{username}:{password}".encode()).decode()
        headers.setdefault("Authorization", f"Basic {token}")
    elif auth_type == "api_key" and auth_config.get("key"):
        location = str(auth_config.get("in") or "header").lower()
        if location == "query":
            params.setdefault(str(auth_config["key"]), auth_config.get("value", ""))
        else:
            headers.setdefault(str(auth_config["key"]), str(auth_config.get("value", "")))

    timeout_ms = max(100, min(int(config.get("timeout_ms") or 30000), 600000))
    retry_config = config.get("retry") if isinstance(config.get("retry"), dict) else {}
    retry_count = max(0, min(int(retry_config.get("count") or 0), 10))
    if method.upper() not in {"GET", "HEAD", "OPTIONS", "PUT", "DELETE"} and not retry_config.get(
        "retry_non_idempotent"
    ):
        retry_count = 0
    retry_interval_ms = max(0, min(int(retry_config.get("interval_ms") or 0), 60000))
    retry_statuses = {
        int(value) for value in retry_config.get("status_codes", [408, 429, 500, 502, 503, 504]) if str(value).isdigit()
    }
    follow_redirects = bool(config.get("follow_redirects", True))
    max_redirects = max(0, min(int(config.get("max_redirects") or 10), 20))
    verify_ssl = bool(config["verify_ssl"]) if verify_ssl_explicit else not settings.DISABLE_SSL_VERIFY
    cookies = config.get("cookies") if isinstance(config.get("cookies"), dict) else {}
    attempts = []
    started_at = time.time()

    owned_client = None
    try:
        req_kwargs: Dict[str, Any] = {
            "headers": headers,
            "follow_redirects": False,
            "timeout": timeout_ms / 1000,
        }
        if params:
            req_kwargs["params"] = params
        processed_body = (
            convert_to_dict(body) if body_type in ("form", "form-data", "x-www-form-urlencoded", "urlencoded") else body
        )
        # An empty JSON editor means "no request body". Parsing an empty string as
        # JSON makes ordinary GET requests fail before they reach the target.
        if body_type == "json" and isinstance(processed_body, str) and not processed_body.strip():
            processed_body = None
        if body_type == "json" and processed_body is not None:
            if isinstance(processed_body, str):
                try:
                    processed_body = json.loads(processed_body)
                except json.JSONDecodeError as e:
                    return {"success": False, "error": f"请求体 JSON 格式校验失败: {e}", "execution_time": 0}
            req_kwargs["json"] = processed_body
        elif body_type in ("x-www-form-urlencoded", "urlencoded", "form") and processed_body is not None:
            req_kwargs["data"] = processed_body
        elif body_type == "form-data" and processed_body is not None:
            form_fields = {}
            files = {}
            total_file_bytes = 0
            for key, value in processed_body.items() if isinstance(processed_body, dict) else []:
                if isinstance(value, dict) and value.get("type") == "file":
                    encoded = value.get("content_base64") or ""
                    if len(files) >= 20:
                        raise ValueError("单次请求最多上传 20 个文件")
                    if len(encoded) > 28 * 1024 * 1024:
                        raise ValueError(f"文件 {value.get('filename') or key} 超过 20 MB 限制")
                    decoded = base64.b64decode(encoded, validate=True)
                    total_file_bytes += len(decoded)
                    if total_file_bytes > 50 * 1024 * 1024:
                        raise ValueError("单次请求文件总大小不能超过 50 MB")
                    files[key] = (
                        value.get("filename") or "upload.bin",
                        decoded,
                        value.get("content_type") or "application/octet-stream",
                    )
                else:
                    form_fields[key] = (
                        json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else str(value)
                    )
            req_kwargs["data"] = form_fields
            if files:
                req_kwargs["files"] = files
        elif body_type == "graphql" and processed_body is not None:
            req_kwargs["json"] = {
                "query": processed_body if isinstance(processed_body, str) else processed_body.get("query", ""),
                "variables": config.get("graphql_variables", {}),
            }
        elif body_type == "binary" and processed_body is not None:
            if config.get("binary_encoding") == "base64" and isinstance(processed_body, str):
                req_kwargs["content"] = base64.b64decode(processed_body, validate=True)
            elif isinstance(processed_body, str):
                req_kwargs["content"] = processed_body.encode("utf-8")
            else:
                req_kwargs["content"] = bytes(processed_body)
        elif body_type == "raw" and processed_body is not None:
            # raw 模式：直接发送原始字符串
            if isinstance(processed_body, str):
                req_kwargs["content"] = processed_body.encode("utf-8")
            else:
                req_kwargs["content"] = str(processed_body).encode("utf-8")
        elif processed_body is not None and body_type != "none":
            if isinstance(processed_body, str):
                try:
                    processed_body = json.loads(processed_body)
                except json.JSONDecodeError as e:
                    return {"success": False, "error": f"请求体 JSON 格式校验失败: {e}", "execution_time": 0}
            req_kwargs["json"] = processed_body

        response = None
        if http_client is None:
            owned_client = httpx.AsyncClient(
                verify=verify_ssl,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
            active_client = owned_client
        else:
            if http_client_verify_ssl is not None and http_client_verify_ssl != verify_ssl:
                owned_client = httpx.AsyncClient(verify=verify_ssl)
                for scoped_cookie in http_client.cookies.jar:
                    owned_client.cookies.jar.set_cookie(copy.copy(scoped_cookie))
                active_client = owned_client
            else:
                active_client = http_client
        for attempt in range(retry_count + 1):
            attempt_started = time.time()
            try:
                current_method = method.upper()
                current_url = url
                current_kwargs = dict(req_kwargs)
                for redirect_index in range(max_redirects + 1):
                    request_headers = dict(current_kwargs.get("headers") or {})
                    cookie_probe = httpx.Request(current_method, current_url)
                    active_client.cookies.set_cookie_header(cookie_probe)
                    merged_cookie_values = {}
                    jar_header = cookie_probe.headers.get("cookie", "")
                    for item in jar_header.split(";"):
                        if "=" in item:
                            key, value = item.strip().split("=", 1)
                            merged_cookie_values[key] = value
                    if redirect_index == 0:
                        merged_cookie_values.update({str(key): str(value) for key, value in cookies.items()})
                    if merged_cookie_values:
                        request_headers["Cookie"] = "; ".join(
                            f"{key}={value}" for key, value in merged_cookie_values.items()
                        )
                    else:
                        request_headers.pop("Cookie", None)
                    current_kwargs["headers"] = request_headers
                    response = await active_client.request(current_method, current_url, **current_kwargs)
                    if not follow_redirects or response.status_code not in {301, 302, 303, 307, 308}:
                        break
                    location = response.headers.get("location")
                    if not location:
                        break
                    if redirect_index >= max_redirects:
                        raise ValueError(f"重定向次数超过限制（{max_redirects}）")
                    next_url = urljoin(str(response.request.url), location)
                    current_kwargs.pop("params", None)
                    safe, reason = validate_url_safety(next_url)
                    if not safe:
                        raise ValueError(f"重定向目标被安全策略拦截: {reason}")
                    current_origin = urlsplit(current_url)
                    next_origin = urlsplit(next_url)
                    if current_origin.scheme == "https" and next_origin.scheme == "http":
                        raise ValueError("禁止从 HTTPS 重定向降级到 HTTP")
                    if (current_origin.scheme, current_origin.hostname, current_origin.port) != (
                        next_origin.scheme,
                        next_origin.hostname,
                        next_origin.port,
                    ):
                        redirect_headers = dict(current_kwargs.get("headers") or {})
                        sensitive_redirect_headers = {"authorization", "proxy-authorization", "cookie"}
                        if auth_type == "api_key" and str(auth_config.get("in") or "header").lower() != "query":
                            sensitive_redirect_headers.add(str(auth_config.get("key") or "").lower())
                        current_kwargs["headers"] = {
                            key: value
                            for key, value in redirect_headers.items()
                            if key.lower() not in sensitive_redirect_headers
                        }
                        if auth_type == "api_key" and str(auth_config.get("in") or "header").lower() == "query":
                            api_key_name = str(auth_config.get("key") or "")
                            current_kwargs["params"] = {
                                key: value
                                for key, value in (current_kwargs.get("params") or {}).items()
                                if key != api_key_name
                            }
                    if response.status_code == 303 or (
                        response.status_code in {301, 302} and current_method not in {"GET", "HEAD"}
                    ):
                        current_method = "GET"
                        current_kwargs = {
                            key: value
                            for key, value in current_kwargs.items()
                            if key not in {"json", "data", "content", "files"}
                        }
                    current_url = next_url
                attempts.append(
                    {
                        "attempt": attempt + 1,
                        "status_code": response.status_code,
                        "elapsed_ms": int((time.time() - attempt_started) * 1000),
                    }
                )
                if response.status_code not in retry_statuses or attempt >= retry_count:
                    break
            except (httpx.TimeoutException, httpx.ConnectError) as exc:
                attempts.append(
                    {
                        "attempt": attempt + 1,
                        "error": type(exc).__name__,
                        "elapsed_ms": int((time.time() - attempt_started) * 1000),
                    }
                )
                if attempt >= retry_count:
                    raise
            except httpx.DecodingError:
                attempts.append(
                    {
                        "attempt": attempt + 1,
                        "error": "DecodingError",
                        "elapsed_ms": int((time.time() - attempt_started) * 1000),
                    }
                )
                fallback_headers = dict(req_kwargs.get("headers") or {})
                fallback_headers["Accept-Encoding"] = "identity"
                req_kwargs["headers"] = fallback_headers
                if attempt >= retry_count:
                    response = await active_client.request(method, url, **req_kwargs)
                    attempts.append(
                        {
                            "attempt": attempt + 2,
                            "status_code": response.status_code,
                            "elapsed_ms": int((time.time() - attempt_started) * 1000),
                            "recovery": "identity_encoding",
                        }
                    )
                    break
            if retry_interval_ms:
                import asyncio

                await asyncio.sleep(retry_interval_ms / 1000)

        resp = response
        if http_client is not None and active_client is not http_client:
            http_client.cookies.update(response.cookies)
        if owned_client is not None:
            await owned_client.aclose()
            owned_client = None
        execution_time = int((time.time() - started_at) * 1000)
        try:
            response_content = resp.json()
        except Exception:
            response_content = resp.text

        sensitive_header_names = {"authorization", "proxy-authorization", "cookie", "set-cookie"}
        if auth_type == "api_key" and str(auth_config.get("in") or "header").lower() != "query":
            sensitive_header_names.add(str(auth_config.get("key") or "").lower())
        request_url_parts = urlsplit(str(resp.request.url))
        sensitive_query_names = {"token", "access_token", "api_key", "apikey", "key", "secret", "password"}
        if auth_type == "api_key" and str(auth_config.get("in") or "header").lower() == "query":
            sensitive_query_names.add(str(auth_config.get("key") or "").lower())
        masked_query = urlencode(
            [
                (key, "******" if key.lower() in sensitive_query_names else value)
                for key, value in parse_qsl(request_url_parts.query, keep_blank_values=True)
            ]
        )
        masked_request_url = urlunsplit(request_url_parts._replace(query=masked_query))

        return {
            "status_code": resp.status_code,
            "response_content": response_content,
            "data": response_content,
            "body": response_content,
            "headers": {
                key: ("******" if key.lower() in sensitive_header_names else value)
                for key, value in resp.headers.items()
            },
            "_raw_headers": dict(resp.headers),
            "content_length": len(resp.content or b""),
            "execution_time": execution_time,
            "elapsed_ms": execution_time,
            "success": 200 <= resp.status_code < 400,
            "attempts": attempts,
            "request": {
                "method": method.upper(),
                "url": masked_request_url,
                "headers": {
                    key: ("******" if key.lower() in sensitive_header_names else value)
                    for key, value in resp.request.headers.items()
                },
                "body_type": body_type,
                "timeout_ms": timeout_ms,
                "follow_redirects": follow_redirects,
                "verify_ssl": verify_ssl,
            },
        }
    except httpx.TimeoutException:
        return {
            "success": False,
            "error": "请求超时",
            "execution_time": int((time.time() - started_at) * 1000),
            "status_code": None,
            "response_content": None,
            "headers": {},
            "attempts": attempts,
        }
    except httpx.ConnectError:
        return {
            "success": False,
            "error": "连接失败，请检查网络或服务地址",
            "execution_time": int((time.time() - started_at) * 1000),
            "status_code": None,
            "response_content": None,
            "headers": {},
            "attempts": attempts,
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time": int((time.time() - started_at) * 1000),
            "status_code": None,
            "response_content": None,
            "headers": {},
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_time": int((time.time() - started_at) * 1000),
            "status_code": None,
            "response_content": None,
            "headers": {},
        }
    finally:
        if owned_client is not None:
            await owned_client.aclose()
