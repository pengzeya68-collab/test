"""
AI API 速率限制中间件

使用滑动窗口算法限制 AI 接口调用频率，防止 API Key 被刷爆

注意：当前实现使用内存存储，仅适用于单实例部署。
生产环境多实例部署时，应使用 Redis + 滑动窗口算法实现分布式速率限制。
"""

import time
import logging
from collections import defaultdict
from typing import Dict, List

from fastapi import Request
from fastapi.responses import JSONResponse

_logger = logging.getLogger(__name__)

# 注意：内存存储仅适用于单实例部署，多实例时每个 worker 独立计数
_user_request_timestamps: Dict[str, List[float]] = defaultdict(list)
_lock = __import__("threading").Lock()


def check_rate_limit(user_id: str, max_requests: int, window_seconds: int) -> bool:
    """
    检查用户是否超过速率限制

    Args:
        user_id: 用户ID
        max_requests: 窗口内最大请求数
        window_seconds: 时间窗口（秒）

    Returns:
        True 如果未超过限制，False 如果超过限制
    """
    now = time.time()
    cutoff = now - window_seconds

    with _lock:
        timestamps = _user_request_timestamps[user_id]
        timestamps[:] = [t for t in timestamps if t > cutoff]

        if len(timestamps) >= max_requests:
            return False

        timestamps.append(now)
        return True


def get_remaining_requests(user_id: str, max_requests: int, window_seconds: int) -> int:
    """获取用户剩余可用请求数"""
    now = time.time()
    cutoff = now - window_seconds

    with _lock:
        timestamps = _user_request_timestamps[user_id]
        timestamps[:] = [t for t in timestamps if t > cutoff]
        return max(0, max_requests - len(timestamps))


async def ai_rate_limit_middleware(request: Request, call_next):
    """
    FastAPI 中间件：对 AI 相关接口进行速率限制

    只限制真正调用 AI 的接口：
    - /api/v1/ai/* (AI Tutor — 所有请求)
    - /api/v1/interview/ 中的 POST 接口（提交答案、代码评测、追问生成）
    - 不限制面试模块的 GET 请求（轮询结果、列表查询等）

    优化：解析 JWT 后将 payload 存入 request.state，后续路由可复用，避免重复解码
    """
    path = request.url.path
    method = request.method

    # /api/v1/ai/ 全部限制
    if path.startswith("/api/v1/ai/"):
        pass
    # /api/v1/interview/ 只限制 POST（真正调用 AI 的接口）
    elif path.startswith("/api/v1/interview/") and method == "POST":
        pass
    else:
        return await call_next(request)

    from fastapi_backend.core.config import settings

    user_id = "anonymous"
    jwt_payload = None
    try:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            from fastapi_backend.services.auth_service import AuthService

            token = auth_header[7:]
            auth_service = AuthService()
            jwt_payload = await auth_service.decode_token(token, expected_type="access")
            user_id = jwt_payload.get("sub", "anonymous")
            # 将解析后的 payload 存入 request.state，供后续路由复用
            request.state.jwt_payload = jwt_payload
    except Exception:
        pass

    if user_id == "anonymous":
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            user_id = forwarded.split(",")[0].strip()
        elif request.client:
            user_id = request.client.host

    max_requests = settings.AI_RATE_LIMIT_REQUESTS
    window_seconds = settings.AI_RATE_LIMIT_WINDOW_SECONDS

    if not check_rate_limit(user_id, max_requests, window_seconds):
        remaining = 0
        retry_after = window_seconds
        _logger.warning(f"用户 {user_id} AI 接口调用超过速率限制: {path}")

        return JSONResponse(
            status_code=429,
            content={
                "detail": "AI 接口调用频率过高，请稍后再试",
                "code": "RATE_LIMIT_EXCEEDED",
                "retry_after": retry_after,
            },
            headers={
                "X-RateLimit-Limit": str(max_requests),
                "X-RateLimit-Remaining": str(remaining),
                "Retry-After": str(retry_after),
            },
        )

    response = await call_next(request)

    remaining = get_remaining_requests(user_id, max_requests, window_seconds)
    response.headers["X-RateLimit-Limit"] = str(max_requests)
    response.headers["X-RateLimit-Remaining"] = str(remaining)

    return response
