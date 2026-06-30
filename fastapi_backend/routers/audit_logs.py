"""
审计日志查询路由

路径前缀: /api/v1/admin/audit-logs
提供审计日志的分页查询、详情、统计、CSV 导出能力（管理员可见）。
"""

import csv
import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.models.models import User
from fastapi_backend.services.audit_service import AuditService

router = APIRouter(prefix="/api/v1/admin/audit-logs", tags=["审计日志"])


def _parse_time(value: Optional[str]) -> Optional[datetime]:
    """解析 ISO 格式时间字符串，失败返回 None。"""
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


@router.get("")
async def list_audit_logs(
    user_id: Optional[int] = Query(None, description="按操作者用户ID过滤"),
    resource_type: Optional[str] = Query(None, description="按资源类型过滤"),
    resource_id: Optional[int] = Query(None, description="按资源ID过滤"),
    action: Optional[str] = Query(None, description="按操作类型过滤"),
    status: Optional[str] = Query(None, description="按状态过滤(success/failed)"),
    start_time: Optional[str] = Query(None, description="起始时间(ISO格式)"),
    end_time: Optional[str] = Query(None, description="结束时间(ISO格式)"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=200, description="每页条数"),
    current_user: User = Depends(require_permissions("audit:read")),
    db: AsyncSession = Depends(get_db),
):
    """分页查询审计日志（支持多维度过滤）"""
    result = await AuditService.query_logs(
        db=db,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        status=status,
        start_time=_parse_time(start_time),
        end_time=_parse_time(end_time),
        page=page,
        page_size=page_size,
    )
    return result


@router.get("/stats")
async def audit_log_stats(
    start_time: Optional[str] = Query(None, description="起始时间(ISO格式)"),
    end_time: Optional[str] = Query(None, description="结束时间(ISO格式)"),
    current_user: User = Depends(require_permissions("audit:read")),
    db: AsyncSession = Depends(get_db),
):
    """审计日志统计信息（按操作类型/资源类型/用户分组）"""
    return await AuditService.stats(
        db=db,
        start_time=_parse_time(start_time),
        end_time=_parse_time(end_time),
    )


@router.get("/export")
async def export_audit_logs(
    user_id: Optional[int] = Query(None),
    resource_type: Optional[str] = Query(None),
    resource_id: Optional[int] = Query(None),
    action: Optional[str] = Query(None),
    start_time: Optional[str] = Query(None),
    end_time: Optional[str] = Query(None),
    current_user: User = Depends(require_permissions("audit:export")),
    db: AsyncSession = Depends(get_db),
):
    """导出审计日志为 CSV（最多导出 10000 条）"""
    result = await AuditService.query_logs(
        db=db,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        action=action,
        start_time=_parse_time(start_time),
        end_time=_parse_time(end_time),
        page=1,
        page_size=10000,
    )

    output = io.StringIO()
    output.write("\ufeff")  # BOM，便于 Excel 正确识别 UTF-8
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "user_id",
            "username",
            "action",
            "resource_type",
            "resource_id",
            "resource_name",
            "status",
            "ip_address",
            "request_method",
            "request_path",
            "error_message",
            "created_at",
        ]
    )
    for item in result["items"]:
        writer.writerow(
            [
                item.get("id"),
                item.get("user_id"),
                item.get("username"),
                item.get("action"),
                item.get("resource_type"),
                item.get("resource_id"),
                item.get("resource_name"),
                item.get("status"),
                item.get("ip_address"),
                item.get("request_method"),
                item.get("request_path"),
                item.get("error_message"),
                item.get("created_at"),
            ]
        )

    content = output.getvalue().encode("utf-8")
    headers = {
        "Content-Disposition": 'attachment; filename="audit_logs.csv"',
    }
    return StreamingResponse(io.BytesIO(content), media_type="text/csv", headers=headers)


@router.get("/{log_id}")
async def get_audit_log(
    log_id: int,
    current_user: User = Depends(require_permissions("audit:read")),
    db: AsyncSession = Depends(get_db),
):
    """查询单条审计日志详情"""
    item = await AuditService.get_log(db, log_id)
    if not item:
        raise HTTPException(status_code=404, detail="审计日志不存在")
    return item
