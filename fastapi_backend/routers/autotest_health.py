"""
测试环境健康检查路由

一键 Ping 所有配置的环境，快速定位环境问题
"""
import time
import asyncio
from urllib.parse import urlparse
from typing import Dict, Any, List

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.autotest import AutoTestEnvironment

router = APIRouter(prefix="/api/auto-test/health-check", tags=["环境健康检查"], dependencies=[Depends(get_current_user)])


def _parse_env_url(env: AutoTestEnvironment) -> str:
    """从环境配置中提取可用于健康检查的 URL"""
    config = env.config or {}
    if isinstance(config, str):
        import json
        try:
            config = json.loads(config)
        except:
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

    start = time.time()
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=timeout)) as resp:
                elapsed = round((time.time() - start) * 1000)
                return {
                    "url": url,
                    "status": "healthy" if 200 <= resp.status < 500 else "degraded",
                    "status_code": resp.status,
                    "response_time_ms": elapsed,
                    "error": None,
                }
    except asyncio.TimeoutError:
        elapsed = round((time.time() - start) * 1000)
        return {"url": url, "status": "unhealthy", "status_code": None, "response_time_ms": elapsed, "error": "连接超时"}
    except Exception as e:
        elapsed = round((time.time() - start) * 1000)
        return {"url": url, "status": "unhealthy", "status_code": None, "response_time_ms": elapsed, "error": str(e)}


@router.get("")
async def health_check_all(db=Depends(get_autotest_db)):
    """一键检查所有环境的健康状态"""
    results: List[Dict] = []

    async for session in db():
        result = await session.execute(select(AutoTestEnvironment))
        envs = result.scalars().all()

        for env in envs:
            url = _parse_env_url(env)
            if not url:
                results.append({
                    "env_id": env.id,
                    "env_name": env.name,
                    "status": "unknown",
                    "url": "未配置",
                    "status_code": None,
                    "response_time_ms": 0,
                    "error": "该环境未配置 base_url",
                })
            else:
                check = await _check_single(url)
                check["env_id"] = env.id
                check["env_name"] = env.name
                results.append(check)
        break

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
async def health_check_single(env_id: int, db=Depends(get_autotest_db)):
    """检查单个环境"""
    async for session in db():
        result = await session.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.id == env_id))
        env = result.scalar_one_or_none()
        if not env:
            return {"error": "环境不存在"}

        url = _parse_env_url(env)
        if not url:
            return {"env_id": env.id, "env_name": env.name, "status": "unknown", "error": "未配置 base_url"}

        check = await _check_single(url)
        check["env_id"] = env.id
        check["env_name"] = env.name
        return check
