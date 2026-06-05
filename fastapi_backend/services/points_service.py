"""积分服务 — 账本逻辑：检查、扣除、退还、记录流水"""

import logging
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.models import User, AIPointsConfig, AIUsageLog, PointsTransaction

_logger = logging.getLogger(__name__)


# ──────────── 积分配置查询 ────────────

async def get_feature_cost(db: AsyncSession, feature: str) -> int | None:
    """获取某功能的积分消耗，不存在则返回 None"""
    result = await db.execute(
        select(AIPointsConfig.points_cost).where(AIPointsConfig.feature == feature)
    )
    return result.scalar_one_or_none()


async def get_all_ai_costs(db: AsyncSession) -> list[AIPointsConfig]:
    """获取所有 AI 功能的积分配置"""
    result = await db.execute(
        select(AIPointsConfig).order_by(AIPointsConfig.points_cost.desc())
    )
    return list(result.scalars().all())


# ──────────── 积分余额查询 ────────────

async def get_user_balance(db: AsyncSession, user_id: int) -> int:
    """查询用户积分余额"""
    result = await db.execute(
        select(User.score).where(User.id == user_id)
    )
    return result.scalar_one_or_none() or 0


# ──────────── 核心扣费（带账本） ────────────

async def check_and_deduct_points(
    db: AsyncSession,
    user: User,
    feature: str,
    note: str = None,
) -> bool:
    """
    检查积分是否足够，足够则扣除并记录流水。
    使用 SELECT ... FOR UPDATE 防止并发超扣。
    返回 True = 扣费成功，False = 余额不足。
    """
    cost = await get_feature_cost(db, feature)
    if cost is None:
        _logger.error(f"未找到功能 {feature} 的积分配置，拒绝扣费")
        return False
    if cost <= 0:
        return True

    # 锁定用户行
    result = await db.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = result.scalar_one()
    current = locked_user.score or 0

    if current < cost:
        return False

    new_balance = current - cost
    locked_user.score = new_balance

    # 记录流水
    tx = PointsTransaction(
        user_id=user.id,
        amount=-cost,
        balance_after=new_balance,
        tx_type="ai_usage",
        source=_feature_display_name(feature),
        related_feature=feature,
        note=note,
    )
    db.add(tx)

    # 记录 AI 使用日志
    log = AIUsageLog(
        user_id=user.id,
        feature=feature,
        points_cost=cost,
    )
    db.add(log)

    await db.flush()
    return True


async def deduct_points_direct(
    db: AsyncSession,
    user: User,
    cost: int,
    feature: str,
    note: str = None,
) -> bool:
    """直接扣指定积分数（用于按批次扣费等场景）"""
    if cost <= 0:
        return True

    result = await db.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = result.scalar_one()
    current = locked_user.score or 0

    if current < cost:
        return False

    new_balance = current - cost
    locked_user.score = new_balance

    tx = PointsTransaction(
        user_id=user.id,
        amount=-cost,
        balance_after=new_balance,
        tx_type="ai_usage",
        source=_feature_display_name(feature),
        related_feature=feature,
        note=note,
    )
    db.add(tx)

    log = AIUsageLog(
        user_id=user.id,
        feature=feature,
        points_cost=cost,
    )
    db.add(log)

    await db.flush()
    return True


# ──────────── 退还积分 ────────────

async def refund_points(
    db: AsyncSession,
    user: User,
    feature: str,
    amount: int = None,
    note: str = None,
) -> None:
    """退还积分（AI 调用失败时）。amount 为空则按配置退还全额。"""
    if amount is None:
        amount = await get_feature_cost(db, feature)
    if amount is None or amount <= 0:
        return

    result = await db.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = result.scalar_one()
    new_balance = (locked_user.score or 0) + amount
    locked_user.score = new_balance

    tx = PointsTransaction(
        user_id=user.id,
        amount=amount,
        balance_after=new_balance,
        tx_type="refund",
        source=f"退还-{_feature_display_name(feature)}",
        related_feature=feature,
        note=note or f"AI调用失败退还",
    )
    db.add(tx)
    await db.flush()
    _logger.info(f"已退还用户 {user.id} {amount} 积分（功能: {feature}）")


async def refund_points_direct(
    db: AsyncSession,
    user: User,
    amount: int,
    feature: str,
    note: str = None,
) -> None:
    """直接退还指定积分数（不查询配置，用于已知金额的退还）"""
    if not amount or amount <= 0:
        return

    result = await db.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = result.scalar_one()
    new_balance = (locked_user.score or 0) + amount
    locked_user.score = new_balance

    tx = PointsTransaction(
        user_id=user.id,
        amount=amount,
        balance_after=new_balance,
        tx_type="refund",
        source=f"退还-{_feature_display_name(feature)}",
        related_feature=feature,
        note=note or "AI调用失败退还",
    )
    db.add(tx)
    await db.flush()
    _logger.info(f"已退还用户 {user.id} {amount} 积分（功能: {feature}）")


# ──────────── 积分充值 ────────────

async def grant_points(
    db: AsyncSession,
    user: User,
    amount: int,
    tx_type: str,
    source: str,
    note: str = None,
) -> int:
    """
    给用户增加积分并记录流水。
    tx_type: checkin / project / purchase / admin_grant / admin_deduct
    返回变动后余额。
    如果是扣减（amount<0）且余额不足，抛出 ValueError。
    """
    result = await db.execute(
        select(User).where(User.id == user.id).with_for_update()
    )
    locked_user = result.scalar_one()
    current = locked_user.score or 0
    new_balance = current + amount

    if amount < 0 and new_balance < 0:
        raise ValueError(f"积分不足，当前 {current}，需要扣除 {abs(amount)}")

    locked_user.score = new_balance

    tx = PointsTransaction(
        user_id=user.id,
        amount=amount,
        balance_after=new_balance,
        tx_type=tx_type,
        source=source,
        note=note,
    )
    db.add(tx)
    await db.flush()
    return new_balance


# ──────────── 流水查询 ────────────

async def get_user_transactions(
    db: AsyncSession,
    user_id: int,
    tx_type: str = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[PointsTransaction], int]:
    """查询用户积分流水（分页）"""
    query = select(PointsTransaction).where(PointsTransaction.user_id == user_id)
    count_query = select(func.count()).select_from(PointsTransaction).where(PointsTransaction.user_id == user_id)

    if tx_type:
        query = query.where(PointsTransaction.tx_type == tx_type)
        count_query = count_query.where(PointsTransaction.tx_type == tx_type)

    query = query.order_by(PointsTransaction.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    count_result = await db.execute(count_query)

    return list(result.scalars().all()), count_result.scalar_one()


async def get_user_usage_stats(db: AsyncSession, user_id: int) -> list[dict]:
    """按功能统计用户 AI 使用次数和积分消耗"""
    result = await db.execute(
        select(
            AIUsageLog.feature,
            func.count().label("count"),
            func.sum(AIUsageLog.points_cost).label("total_cost"),
        )
        .where(AIUsageLog.user_id == user_id)
        .group_by(AIUsageLog.feature)
        .order_by(func.sum(AIUsageLog.points_cost).desc())
    )
    return [
        {"feature": row.feature, "count": row.count, "total_cost": row.total_cost}
        for row in result.all()
    ]


# ──────────── 辅助函数 ────────────

_FEATURE_NAMES = {
    "ai_chat": "AI 导师对话",
    "ai_code_review": "AI 代码评审",
    "ai_learning_advice": "AI 学习建议",
    "ai_explain_exercise": "AI 解题讲解",
    "interview_code_eval": "面试代码评测",
    "interview_text_eval": "面试文本评测",
    "interview_follow_up": "面试追问生成",
    "exercise_code_eval": "习题代码评测",
    "ai_generate_cases": "AI 生成测试用例",
    "bench_ai_analysis": "性能 AI 分析",
    "report_ai_suggestions": "报告优化建议",
    "jmeter_ai_assertions": "JMeter AI 断言",
}


def _feature_display_name(feature: str) -> str:
    return _FEATURE_NAMES.get(feature, feature)


_TX_TYPE_NAMES = {
    "checkin": "每日签到",
    "project": "项目实战",
    "purchase": "积分购买",
    "admin_grant": "管理员充值",
    "admin_deduct": "管理员扣减",
    "ai_usage": "AI 功能使用",
    "refund": "积分退还",
}


def get_tx_type_name(tx_type: str) -> str:
    return _TX_TYPE_NAMES.get(tx_type, tx_type)
