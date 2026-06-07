"""AI 积分依赖注入 — require_ai_points"""

import logging
from typing import Callable, Awaitable
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User
from fastapi_backend.services.points_service import (
    check_and_deduct_points,
    get_feature_cost,
    deduct_points_direct,
)

_logger = logging.getLogger(__name__)

# HTTP 402 Payment Required
PAYMENT_REQUIRED = 402


def require_ai_points(feature: str):
    """
    FastAPI 依赖：检查并扣除 AI 功能积分。

    用法：
        @router.post("/ai/chat")
        async def chat(..., _ai=Depends(require_ai_points("ai_chat"))):
            try:
                result = await do_ai_call()
            except Exception:
                await db.rollback()  # 回滚扣费
                raise
            await _ai()  # 成功 → 提交扣费
            return result

    返回的 _ai 回调：
    - await _ai() = 确认成功，提交扣费事务
    - 不调用 = 请求结束时事务自动回滚，积分不扣
    """

    async def _check(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ) -> Callable[[], Awaitable[None]]:
        cost = await get_feature_cost(db, feature)
        if cost is None:
            # 功能未配置 → 视为免费，不扣费
            async def _noop():
                pass

            return _noop
        if cost <= 0:
            # 功能费用为0 → 免费，不扣费
            async def _noop():
                pass

            return _noop

        success = await check_and_deduct_points(db, current_user, feature)
        if not success:
            raise HTTPException(
                status_code=PAYMENT_REQUIRED,
                detail=f"积分不足，需要 {cost} 积分。请通过签到、项目实战或购买获取积分。",
            )

        # 不在这里 commit！只 flush 确保 SQL 发送到数据库
        # 由调用方通过 _ai() 确认后才 commit

        async def _confirm():
            """确认成功 → 提交扣费。不调用则事务回滚，积分不扣。"""
            await db.commit()

        return _confirm

    return _check


def require_ai_points_batch(feature: str, batch_desc: str = "批次"):
    """
    按批次扣费的依赖（用于 AI 生成测试用例等场景）。
    返回 (check_batch, confirm) 元组：
    - check_batch(n): 检查并扣除 n 个批次的积分
    - confirm(): 确认成功，提交扣费事务；不调用则回滚
    """

    async def _check(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
    ):
        cost_per_batch = await get_feature_cost(db, feature)

        async def check_batch(batch_count: int) -> bool:
            """检查并扣除 batch_count 个批次的积分。返回 True=成功"""
            if batch_count <= 0:
                return True
            nonlocal cost_per_batch
            if cost_per_batch is None or cost_per_batch <= 0:
                return True
            total_cost = cost_per_batch * batch_count
            success = await deduct_points_direct(
                db,
                current_user,
                total_cost,
                feature,
                note=f"{batch_desc} x{batch_count}",
            )
            if not success:
                raise HTTPException(
                    status_code=PAYMENT_REQUIRED,
                    detail=f"积分不足，需要 {total_cost} 积分（{batch_count}个{batch_desc}，每个{cost_per_batch}积分）。",
                )
            return True

        async def confirm():
            """确认成功 → 提交扣费。不调用则事务回滚，积分不扣。"""
            await db.commit()

        return check_batch, confirm

    return _check
