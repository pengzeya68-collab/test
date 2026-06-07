"""用户 — 积分余额、流水、使用统计"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User
from fastapi_backend.schemas.ai_points import (
    PointsBalanceResponse,
    AIPointsConfigResponse,
)
from fastapi_backend.services.points_service import (
    get_user_balance,
    get_user_transactions,
    get_user_usage_stats,
    get_all_ai_costs,
    get_tx_type_name,
    _feature_display_name,
)

router = APIRouter(prefix="/api/v1/user/points", tags=["用户积分"])


@router.get("", response_model=PointsBalanceResponse)
async def my_points(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户积分余额和等级"""
    balance = await get_user_balance(db, current_user.id)
    return PointsBalanceResponse(points=balance, level=current_user.level or 1)


@router.get("/transactions")
async def my_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    tx_type: str = Query(None, description="筛选类型: checkin/project/purchase/ai_usage/refund/admin_grant"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询当前用户积分流水"""
    txs, total = await get_user_transactions(db, current_user.id, tx_type=tx_type, page=page, page_size=page_size)
    items = []
    for t in txs:
        items.append(
            {
                "id": t.id,
                "amount": t.amount,
                "balance_after": t.balance_after,
                "tx_type": t.tx_type,
                "tx_type_name": get_tx_type_name(t.tx_type),
                "source": t.source,
                "related_feature": t.related_feature,
                "note": t.note,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
        )

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/usage-stats")
async def my_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """当前用户 AI 功能使用统计"""
    stats = await get_user_usage_stats(db, current_user.id)
    total_cost = sum(s["total_cost"] or 0 for s in stats)
    items = [
        {
            "feature": s["feature"],
            "display_name": _feature_display_name(s["feature"]),
            "count": s["count"],
            "total_cost": s["total_cost"],
        }
        for s in stats
    ]
    return {"items": items, "total_points_used": total_cost}


@router.get("/costs", response_model=list[AIPointsConfigResponse])
async def ai_feature_costs(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(get_current_user),
):
    """获取所有 AI 功能的积分消耗配置（用户可见）"""
    return await get_all_ai_costs(db)
