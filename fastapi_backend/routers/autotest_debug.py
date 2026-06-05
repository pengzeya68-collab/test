"""
JMeter 调试执行器 - 后端代理 HTTP 请求

解决跨域问题：前端通过后端代理发请求，不在浏览器直接发
返回完整的请求/响应详情，作为 JMeter 调试器的执行引擎
"""
import time
import json
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestCase
from fastapi_backend.models.models import User
from fastapi_backend.core.ssrf_guard import validate_url_safety

router = APIRouter(prefix="/api/auto-test/debug", tags=["JMeter调试器"])


@router.post("/execute")
async def debug_execute_request(
    body: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
):
    """
    代理执行 HTTP 请求并返回详细结果
    
    用于 JMeter 调试器：前端发送请求参数 → 后端代理执行 → 返回完整响应
    
    Request Body:
        method: "GET" | "POST" | "PUT" | "DELETE" | "PATCH"
        url: "https://api.example.com/users"
        headers: {"Content-Type": "application/json"}
        body: "..."  (请求体字符串)
        timeout: 30  (超时秒数，默认 30)
    
    Response:
        status_code, headers, body, elapsed_ms, size_bytes, error
    """
    import aiohttp
    
    method = body.get("method", "GET").upper()
    url = body.get("url", "")
    headers = body.get("headers", {}) or {}
    request_body = body.get("body", "")
    timeout = body.get("timeout", 30)

    # 校验 HTTP 方法
    allowed_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
    if method not in allowed_methods:
        raise HTTPException(status_code=400, detail=f"不支持的 HTTP 方法: {method}，仅支持 {', '.join(sorted(allowed_methods))}")

    # 校验超时范围
    try:
        timeout = float(timeout)
        if timeout <= 0 or timeout > 120:
            timeout = 30
    except (TypeError, ValueError):
        timeout = 30
    
    if not url:
        raise HTTPException(status_code=400, detail="请提供 URL")
    
    safe, reason = validate_url_safety(url)
    if not safe:
        raise HTTPException(status_code=400, detail=reason)
    
    start = time.time()
    result = {
        "request": {
            "method": method,
            "url": url,
            "headers": headers,
            "body": request_body[:5000],
        },
        "response": {}
    }
    
    try:
        timeout_obj = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession() as session:
            request_kw = {"headers": headers, "timeout": timeout_obj}
            if request_body and method in ("POST", "PUT", "PATCH", "DELETE"):
                request_kw["data"] = request_body
            
            async with session.request(method, url, **request_kw) as resp:
                elapsed = round((time.time() - start) * 1000)
                resp_body = await resp.text()
                
                result["response"] = {
                    "status_code": resp.status,
                    "status_text": resp.reason,
                    "headers": dict(resp.headers),
                    "body": resp_body[:50000],
                    "body_size": len(resp_body),
                    "elapsed_ms": elapsed,
                }
    except aiohttp.ClientConnectorError as e:
        elapsed = round((time.time() - start) * 1000)
        result["response"] = {
            "status_code": 0,
            "status_text": "Connection Error",
            "error": f"无法连接到服务器: {str(e)}",
            "elapsed_ms": elapsed,
        }
    except aiohttp.ClientError as e:
        elapsed = round((time.time() - start) * 1000)
        result["response"] = {
            "status_code": 0,
            "status_text": "Request Error",
            "error": str(e),
            "elapsed_ms": elapsed,
        }
    except Exception as e:
        elapsed = round((time.time() - start) * 1000)
        result["response"] = {
            "status_code": 0,
            "status_text": "Error",
            "error": str(e),
            "elapsed_ms": elapsed,
        }
    
    return result


@router.post("/execute/case/{case_id}")
async def debug_execute_from_case(
    case_id: int,
    env_id: Optional[int] = None,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_autotest_db),
):
    """从已有接口用例执行调试请求，支持变量替换和环境URL拼接"""
    from fastapi_backend.models.autotest import AutoTestEnvironment
    from fastapi_backend.utils.parser import replace_variables

    result = await db.execute(select(AutoTestCase).where(AutoTestCase.id == case_id, AutoTestCase.user_id == current_user.id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    # 加载环境配置
    env = None
    base_url = ""
    env_vars = {}
    if env_id:
        result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.id == env_id, AutoTestEnvironment.user_id == current_user.id))
        env = result.scalar_one_or_none()
    if env is None:
        result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.is_default.is_(True), AutoTestEnvironment.user_id == current_user.id))
        env = result.scalars().first()

    if env:
        base_url = env.base_url or ""
        if isinstance(env.variables, dict):
            env_vars = env.variables

    # 构造请求参数
    headers = case.headers or {}
    if case.content_type:
        headers.setdefault("Content-Type", case.content_type)

    # 变量替换
    url = replace_variables(case.url, env_vars)
    headers = replace_variables(headers, env_vars)

    # 环境URL拼接：如果 URL 不是完整路径，拼接 base_url
    if not url.startswith(("http://", "https://")) and base_url:
        url = base_url.rstrip("/") + "/" + url.lstrip("/")

    body_str = ""
    raw_payload = case.payload
    if raw_payload:
        # 变量替换 payload
        raw_payload = replace_variables(raw_payload, env_vars)
        if isinstance(raw_payload, dict):
            body_str = json.dumps(raw_payload, ensure_ascii=False)
        else:
            body_str = str(raw_payload)

    # SSRF 安全校验
    safe, reason = validate_url_safety(url)
    if not safe:
        raise HTTPException(status_code=400, detail=reason)

    # 直接构造请求结果，避免调用路由函数时缺少 Depends 注入
    from fastapi_backend.services.autotest_request_service import execute_http_request
    from fastapi_backend.utils.autotest_helpers import convert_to_dict

    try:
        result = await execute_http_request(
            method=case.method or "GET",
            url=url,
            headers=convert_to_dict(headers),
            body=body_str or None,
            body_type=getattr(case, 'body_type', 'json') or 'json',
            env_id=env_id,
            user_id=current_user.id,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
