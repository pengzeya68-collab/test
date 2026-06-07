"""后管 — AI 积分配置管理 + 使用日志 + 流水查询"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import User, AIPointsConfig, AIUsageLog, PointsTransaction
from fastapi_backend.schemas.ai_points import (
    AIPointsConfigResponse,
    AIPointsConfigUpdate,
    AIUsageStatsResponse,
    PointsPurchaseRequest,
)
from fastapi_backend.services.points_service import (
    get_all_ai_costs,
    grant_points,
    get_tx_type_name,
    _feature_display_name,
)

router = APIRouter(prefix="/api/v1/admin/ai-points", tags=["AI积分管理"])


# ──────────── 积分配置管理 ────────────


@router.get("/config", response_model=list[AIPointsConfigResponse])
async def list_configs(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    return await get_all_ai_costs(db)


@router.put("/config/{feature}", response_model=AIPointsConfigResponse)
async def update_config(
    feature: str,
    data: AIPointsConfigUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(select(AIPointsConfig).where(AIPointsConfig.feature == feature))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="功能配置不存在")

    if data.points_cost is not None:
        config.points_cost = data.points_cost
    if data.display_name is not None:
        config.display_name = data.display_name
    if data.description is not None:
        config.description = data.description

    from datetime import datetime, timezone

    config.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(config)
    return config


# ──────────── AI 使用日志 ────────────


@router.get("/logs")
async def list_usage_logs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Query(None),
    feature: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = select(AIUsageLog)
    count_query = select(func.count()).select_from(AIUsageLog)

    if user_id:
        query = query.where(AIUsageLog.user_id == user_id)
        count_query = count_query.where(AIUsageLog.user_id == user_id)
    if feature:
        query = query.where(AIUsageLog.feature == feature)
        count_query = count_query.where(AIUsageLog.feature == feature)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(AIUsageLog.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    logs = result.scalars().all()

    # 批量查用户名
    user_ids = list(set(l.user_id for l in logs))
    users = {}
    if user_ids:
        uresult = await db.execute(select(User.id, User.username).where(User.id.in_(user_ids)))
        users = {r.id: r.username for r in uresult.all()}

    items = []
    for l in logs:
        items.append(
            {
                "id": l.id,
                "user_id": l.user_id,
                "username": users.get(l.user_id, ""),
                "feature": l.feature,
                "feature_name": _feature_display_name(l.feature),
                "points_cost": l.points_cost,
                "created_at": l.created_at,
            }
        )

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/logs/stats", response_model=list[AIUsageStatsResponse])
async def usage_stats(
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    result = await db.execute(
        select(
            AIUsageLog.feature,
            func.count().label("total_calls"),
            func.sum(AIUsageLog.points_cost).label("total_points"),
        )
        .group_by(AIUsageLog.feature)
        .order_by(func.sum(AIUsageLog.points_cost).desc())
    )
    rows = result.all()
    return [
        AIUsageStatsResponse(
            feature=r.feature,
            display_name=_feature_display_name(r.feature),
            total_calls=r.total_calls,
            total_points=r.total_points or 0,
        )
        for r in rows
    ]


# ──────────── 积分流水查询 ────────────


@router.get("/transactions")
async def list_all_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Query(None),
    tx_type: str = Query(None),
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_admin),
):
    query = select(PointsTransaction)
    count_query = select(func.count()).select_from(PointsTransaction)

    if user_id:
        query = query.where(PointsTransaction.user_id == user_id)
        count_query = count_query.where(PointsTransaction.user_id == user_id)
    if tx_type:
        query = query.where(PointsTransaction.tx_type == tx_type)
        count_query = count_query.where(PointsTransaction.tx_type == tx_type)

    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(PointsTransaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    txs = result.scalars().all()

    user_ids = list(set(t.user_id for t in txs))
    users = {}
    if user_ids:
        uresult = await db.execute(select(User.id, User.username).where(User.id.in_(user_ids)))
        users = {r.id: r.username for r in uresult.all()}

    items = []
    for t in txs:
        items.append(
            {
                "id": t.id,
                "user_id": t.user_id,
                "username": users.get(t.user_id, ""),
                "amount": t.amount,
                "balance_after": t.balance_after,
                "tx_type": t.tx_type,
                "tx_type_name": get_tx_type_name(t.tx_type),
                "source": t.source,
                "related_feature": t.related_feature,
                "note": t.note,
                "created_at": t.created_at,
            }
        )

    return {"items": items, "total": total, "page": page, "page_size": page_size}


# ──────────── 管理员手动充值 ────────────


@router.post("/grant")
async def grant_points_to_user(
    data: PointsPurchaseRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == data.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_balance = await grant_points(
        db,
        user,
        data.amount,
        tx_type="admin_grant",
        source="管理员充值",
        note=data.note or f"管理员 {admin.username} 充值 {data.amount} 积分",
    )
    await db.commit()

    return {"message": f"充值成功，用户 {user.username} 当前积分: {new_balance}", "balance": new_balance}


# ──────────── 管理员扣减积分 ────────────


@router.post("/deduct")
async def deduct_points_from_user(
    data: PointsPurchaseRequest,
    db: AsyncSession = Depends(get_db),
    admin: User = Depends(require_admin),
):
    result = await db.execute(select(User).where(User.id == data.user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    try:
        new_balance = await grant_points(
            db,
            user,
            -abs(data.amount),
            tx_type="admin_deduct",
            source="管理员扣减",
            note=data.note or f"管理员 {admin.username} 扣减 {data.amount} 积分",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await db.commit()

    return {"message": f"扣减成功，用户 {user.username} 当前积分: {new_balance}", "balance": new_balance}
