"""
测试环境健康检查路由

一键 Ping 所有配置的环境，快速定位环境问题
"""

import time
import asyncio
from typing import Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestEnvironment
from fastapi_backend.models.models import User

router = APIRouter(prefix="/api/auto-test/health-check", tags=["环境健康检查"])


def _parse_env_url(env: AutoTestEnvironment) -> str:
    """从环境配置中提取可用于健康检查的 URL"""
    config = env.config or {}
    if isinstance(config, str):
        import json

        try:
            config = json.loads(config)
        except Exception:
            config = {}

    base_url = config.get("base_url", "") or env.base_url or ""
    if base_url:
        # 确保 URL 有 scheme
        if not base_url.startswith("http"):
            base_url = f"https://{base_url}"
        return f"{base_url.rstrip('/')}/"

    return ""


async def _check_single(url: str, timeout: float = 5.0) -> Dict:
    """检查单个 URL 的可用性"""
    import aiohttp

    # SSRF 安全校验
    from fastapi_backend.core.ssrf_guard import validate_url_safety

    safe, reason = validate_url_safety(url)
    if not safe:
        return {
            "url": url,
            "status": "unhealthy",
            "status_code": None,
            "response_time_ms": 0,
            "error": f"URL安全校验失败: {reason}",
        }

    start = time.time()
    try:
        from fastapi_backend.core.config import settings
        import ssl as ssl_module

        ssl_context = None if settings.DISABLE_SSL_VERIFY else ssl_module.create_default_context()
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        async with aiohttp.ClientSession(connector=connector) as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                elapsed = round((time.time() - start) * 1000)
                return {
                    "url": url,
                    "status": "healthy"
                    if 200 <= resp.status < 300
                    else ("degraded" if 300 <= resp.status < 400 else "unhealthy"),
                    "status_code": resp.status,
                    "response_time_ms": elapsed,
                    "error": None,
                }
    except asyncio.TimeoutError:
        elapsed = round((time.time() - start) * 1000)
        return {
            "url": url,
            "status": "unhealthy",
            "status_code": None,
            "response_time_ms": elapsed,
            "error": "连接超时",
        }
    except Exception as e:
        elapsed = round((time.time() - start) * 1000)
        return {"url": url, "status": "unhealthy", "status_code": None, "response_time_ms": elapsed, "error": str(e)}


@router.get("")
async def health_check_all(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_autotest_db),
):
    """一键检查所有环境的健康状态"""
    results: List[Dict] = []

    result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.user_id == current_user.id))
    envs = result.scalars().all()

    # 并发执行环境检查
    check_tasks = []
    env_info = []
    for env in envs:
        url = _parse_env_url(env)
        if not url:
            results.append(
                {
                    "env_id": env.id,
                    "env_name": env.env_name,
                    "status": "unknown",
                    "url": "未配置",
                    "status_code": None,
                    "response_time_ms": 0,
                    "error": "该环境未配置 base_url",
                }
            )
        else:
            check_tasks.append(_check_single(url))
            env_info.append(env)

    checks = await asyncio.gather(*check_tasks)
    for check, env in zip(checks, env_info):
        check["env_id"] = env.id
        check["env_name"] = env.env_name
        results.append(check)

    healthy = sum(1 for r in results if r["status"] == "healthy")
    unhealthy = sum(1 for r in results if r["status"] in ("unhealthy", "degraded"))
    unknown = sum(1 for r in results if r["status"] == "unknown")

    return {
        "results": results,
        "total": len(results),
        "summary": {
            "healthy": healthy,
            "unhealthy": unhealthy,
            "unknown": unknown,
            "overall": "healthy" if unhealthy == 0 and unknown == 0 else "degraded",
        },
    }


@router.get("/{env_id}")
async def health_check_single(
    env_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_autotest_db),
):
    """检查单个环境"""
    result = await db.execute(
        select(AutoTestEnvironment).where(
            AutoTestEnvironment.id == env_id,
            AutoTestEnvironment.user_id == current_user.id,
        )
    )
    env = result.scalar_one_or_none()
    if not env:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="环境不存在")

    url = _parse_env_url(env)
    if not url:
        return {"env_id": env.id, "env_name": env.env_name, "status": "unknown", "error": "未配置 base_url"}

    check = await _check_single(url)
    check["env_id"] = env.id
    check["env_name"] = env.env_name
    return check
