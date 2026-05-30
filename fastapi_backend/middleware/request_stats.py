"""
请求统计中间件

记录每个请求的响应时间和状态码，用于监控和统计
"""

import time
import logging
from fastapi import Request

from fastapi_backend.services.system_monitor import system_monitor

_logger = logging.getLogger(__name__)


async def request_stats_middleware(request: Request, call_next):
    """记录请求统计的中间件"""
    start_time = time.time()

    try:
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        # 记录请求统计
        system_monitor.request_stats.record_request(
            path=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )

        return response
    except Exception:
        duration_ms = (time.time() - start_time) * 1000

        # 记录异常请求
        system_monitor.request_stats.record_request(
            path=request.url.path,
            method=request.method,
            status_code=500,
            duration_ms=duration_ms,
        )

        raise
