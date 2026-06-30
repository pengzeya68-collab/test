"""
审计日志服务

提供审计日志的记录与查询能力。

设计要点：
1. 写入使用独立 session（与业务事务隔离），保证审计失败不影响主业务流程，
   且业务失败时仍可记录审计日志。
2. detail 字段做大小限制（10KB），避免存储超大变更内容。
3. 查询支持多维度过滤与分页。
"""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime
from typing import Any, Optional

from fastapi import Request
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from fastapi_backend.core.database import AsyncSessionLocal
from fastapi_backend.models.models import AuditLog

_logger = logging.getLogger(__name__)

# detail 字段最大长度（字符数），超出则截断
_DETAIL_MAX_LENGTH = 10 * 1024

# 敏感字段名匹配模式（密码、密钥、令牌等），审计日志中需脱敏
_SENSITIVE_KEY_PATTERN = re.compile(r"(password|passwd|secret|token|api[_-]?key|access[_-]?key|private[_-]?key|credential|authorization)", re.IGNORECASE)
_MASKED_VALUE = "****"


def _mask_sensitive_values(data: Any) -> Any:
    """递归脱敏 dict/list 中的敏感字段值（password/token/secret 等）。"""
    if isinstance(data, dict):
        masked = {}
        for k, v in data.items():
            if isinstance(k, str) and _SENSITIVE_KEY_PATTERN.search(k):
                masked[k] = _MASKED_VALUE
            else:
                masked[k] = _mask_sensitive_values(v)
        return masked
    if isinstance(data, list):
        return [_mask_sensitive_values(item) for item in data]
    return data


def _truncate_detail(detail: Any) -> Optional[str]:
    """将 detail 序列化为 JSON 字符串并限制大小，防止存储超大内容。同时对敏感字段脱敏。"""
    if detail is None:
        return None
    masked = _mask_sensitive_values(detail)
    try:
        text = json.dumps(masked, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = str(masked)
    if len(text) > _DETAIL_MAX_LENGTH:
        text = text[:_DETAIL_MAX_LENGTH] + "...[truncated]"
    return text


def _extract_request_info(request: Optional[Request]) -> dict:
    """从 Request 对象中提取 IP、User-Agent、路径、方法。"""
    info: dict[str, Optional[str]] = {
        "ip_address": None,
        "user_agent": None,
        "request_path": None,
        "request_method": None,
    }
    if request is None:
        return info
    info["request_path"] = str(request.url.path)
    info["request_method"] = request.method
    info["user_agent"] = request.headers.get("user-agent")
    # 优先取 X-Forwarded-For（反向代理场景），否则取 client.host
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        info["ip_address"] = forwarded.split(",")[0].strip()
    elif request.client:
        info["ip_address"] = request.client.host
    return info


class AuditService:
    """审计日志服务"""

    # 会话工厂（写入时使用独立 session），可被测试覆盖
    _session_factory: async_sessionmaker[AsyncSession] = AsyncSessionLocal

    @staticmethod
    async def log(
        db: AsyncSession,
        user_id: Optional[int],
        username: Optional[str],
        action: str,
        resource_type: str,
        resource_id: Optional[int] = None,
        resource_name: Optional[str] = None,
        detail: Optional[dict] = None,
        request: Optional[Request] = None,
        status: str = "success",
        error_message: Optional[str] = None,
    ) -> None:
        """记录审计日志（非阻塞，失败不影响主流程）。

        db 参数保留以兼容调用方与未来读操作；实际写入使用独立 session，
        以隔离业务事务（业务回滚/失败时审计日志仍可独立提交）。
        """
        req_info = _extract_request_info(request)
        # 资源名称限制长度，避免超长
        if resource_name is not None:
            resource_name = str(resource_name)[:500]
        if error_message is not None:
            error_message = str(error_message)[:2000]

        entry = AuditLog(
            user_id=user_id,
            username=username,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            resource_name=resource_name,
            detail=_truncate_detail(detail),
            ip_address=req_info["ip_address"],
            user_agent=req_info["user_agent"],
            request_path=req_info["request_path"],
            request_method=req_info["request_method"],
            status=status,
            error_message=error_message,
        )

        try:
            # 使用独立 session 写入，保证与业务事务隔离
            async with AuditService._session_factory() as session:
                session.add(entry)
                await session.commit()
        except Exception as exc:  # noqa: BLE001 - 审计日志失败不能影响主业务
            _logger.warning("记录审计日志失败: %s", exc, exc_info=True)

    @staticmethod
    async def query_logs(
        db: AsyncSession,
        user_id: Optional[int] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[int] = None,
        action: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """查询审计日志（带分页和多维度过滤）。"""
        filters = []
        if user_id is not None:
            filters.append(AuditLog.user_id == user_id)
        if resource_type is not None:
            filters.append(AuditLog.resource_type == resource_type)
        if resource_id is not None:
            filters.append(AuditLog.resource_id == resource_id)
        if action is not None:
            filters.append(AuditLog.action == action)
        if status is not None:
            filters.append(AuditLog.status == status)
        if start_time is not None:
            filters.append(AuditLog.created_at >= start_time)
        if end_time is not None:
            filters.append(AuditLog.created_at <= end_time)

        base_query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))
        for f in filters:
            base_query = base_query.where(f)
            count_query = count_query.where(f)

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        page = max(page, 1)
        page_size = max(min(page_size, 200), 1)
        offset = (page - 1) * page_size

        rows_query = (
            base_query.order_by(AuditLog.created_at.desc()).offset(offset).limit(page_size)
        )
        result = await db.execute(rows_query)
        items = [AuditService._to_dict(row) for row in result.scalars().all()]

        return {"items": items, "total": total, "page": page, "page_size": page_size}

    @staticmethod
    async def get_log(db: AsyncSession, log_id: int) -> Optional[dict]:
        """查询单条审计日志详情。"""
        result = await db.execute(select(AuditLog).where(AuditLog.id == log_id))
        entry = result.scalar_one_or_none()
        return AuditService._to_dict(entry) if entry else None

    @staticmethod
    async def stats(
        db: AsyncSession,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> dict:
        """统计信息：按 action / resource_type / user 分组统计。"""
        filters = []
        if start_time is not None:
            filters.append(AuditLog.created_at >= start_time)
        if end_time is not None:
            filters.append(AuditLog.created_at <= end_time)

        async def _group_count(group_col):
            q = select(group_col, func.count(AuditLog.id)).group_by(group_col)
            for f in filters:
                q = q.where(f)
            res = await db.execute(q)
            return {str(key): count for key, count in res.all() if key is not None}

        return {
            "by_action": await _group_count(AuditLog.action),
            "by_resource_type": await _group_count(AuditLog.resource_type),
            "by_user": await _group_count(AuditLog.username),
        }

    @staticmethod
    def _to_dict(entry: AuditLog) -> dict:
        """将 AuditLog 对象序列化为字典。"""
        detail = None
        if entry.detail:
            try:
                detail = json.loads(entry.detail)
            except (TypeError, ValueError):
                detail = entry.detail
        return {
            "id": entry.id,
            "user_id": entry.user_id,
            "username": entry.username,
            "action": entry.action,
            "resource_type": entry.resource_type,
            "resource_id": entry.resource_id,
            "resource_name": entry.resource_name,
            "detail": detail,
            "ip_address": entry.ip_address,
            "user_agent": entry.user_agent,
            "request_path": entry.request_path,
            "request_method": entry.request_method,
            "status": entry.status,
            "error_message": entry.error_message,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        }
