"""
通知系统路由

路径前缀: /api/v1/notifications
"""
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User, Notification

router = APIRouter(prefix="/api/v1/notifications", tags=["通知"])


def _notify_create(db, user_id, title, content, ntype="system", link=None):
    """辅助：创建通知（供其他服务调用）"""
    notif = Notification(
        user_id=user_id,
        title=title,
        content=content,
        type=ntype,
        link=link,
    )
    db.add(notif)
    return notif


@router.get("")
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的通知列表"""
    base = select(Notification).where(Notification.user_id == current_user.id)
    if unread_only:
        base = base.where(Notification.is_read == False)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    result = await db.execute(
        base.order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    notifications = result.scalars().all()

    return {
        "notifications": [n.to_dict() for n in notifications],
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
    }


@router.get("/unread-count")
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取未读通知数量"""
    result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    count = result.scalar() or 0
    return {"unread_count": count}


@router.post("/{notification_id}/read")
async def mark_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记单条通知为已读"""
    result = await db.execute(
        select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
    )
    notif = result.scalar_one_or_none()
    if not notif:
        raise HTTPException(status_code=404, detail="通知不存在")
    notif.is_read = True
    await db.commit()
    return {"message": "已标记为已读"}


@router.post("/read-all")
async def mark_all_as_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """标记所有通知为已读"""
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .values(is_read=True)
    )
    await db.commit()
    return {"message": "已全部标记为已读"}


@router.post("/send")
@router.post("/send/{user_id}")
async def send_notification(
    user_id: int,
    body: Dict[str, Any],
    db: AsyncSession = Depends(get_db),
):
    """发送通知（内部调用）"""
    notif = _notify_create(
        db,
        user_id=user_id,
        title=body.get("title", ""),
        content=body.get("content", ""),
        ntype=body.get("type", "system"),
        link=body.get("link"),
    )
    await db.commit()
    await db.refresh(notif)
    return {"message": "发送成功", "notification": notif.to_dict()}
