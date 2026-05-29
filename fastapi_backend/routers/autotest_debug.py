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
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.autotest import AutoTestCase
from fastapi_backend.core.ssrf_guard import validate_url_safety

router = APIRouter(prefix="/api/auto-test/debug", tags=["JMeter调试器"], dependencies=[Depends(get_current_user)])


@router.post("/execute")
async def debug_execute_request(
    body: Dict[str, Any] = Body(...),
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
            if request_body:
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
    db: AsyncSession = Depends(get_autotest_db),
):
    """从已有接口用例执行调试请求"""
    result = await db.execute(select(AutoTestCase).where(AutoTestCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    
    # 构造请求
    headers = case.headers or {}
    if case.content_type:
        headers.setdefault("Content-Type", case.content_type)
    
    body_str = ""
    if case.payload:
        if isinstance(case.payload, dict):
            body_str = json.dumps(case.payload, ensure_ascii=False)
        else:
            body_str = str(case.payload)
    
    return await debug_execute_request(body={
        "method": case.method,
        "url": case.url,
        "headers": headers,
        "body": body_str,
    })
