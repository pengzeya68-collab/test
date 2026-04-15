"""每日签到路由 - 连续学习激励系统"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User, DailyCheckin

router = APIRouter(prefix="/api/v1/checkin", tags=["每日签到"])

STREAK_REWARDS = {
    1: 5,
    2: 5,
    3: 8,
    4: 8,
    5: 10,
    6: 10,
    7: 20,
}

MAX_DAILY_EXP = 20


def _get_streak_exp(streak: int) -> int:
    if streak >= 7:
        return STREAK_REWARDS[7]
    return STREAK_REWARDS.get(streak, 5)


@router.post("/")
async def daily_checkin(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """执行每日签到"""
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    existing_stmt = select(DailyCheckin).where(
        DailyCheckin.user_id == current_user.id,
        DailyCheckin.checkin_date >= today,
    )
    existing_result = await db.execute(existing_stmt)
    if existing_result.scalar_one_or_none():
        return {
            "checked_in": False,
            "message": "今日已签到",
            "streak": 0,
            "exp_earned": 0,
        }

    yesterday = today - timedelta(days=1)
    yesterday_stmt = select(DailyCheckin).where(
        DailyCheckin.user_id == current_user.id,
        DailyCheckin.checkin_date >= yesterday,
        DailyCheckin.checkin_date < today,
    )
    yesterday_result = await db.execute(yesterday_stmt)
    yesterday_checkin = yesterday_result.scalar_one_or_none()

    if yesterday_checkin:
        streak = yesterday_checkin.streak_count + 1
    else:
        streak = 1

    exp_earned = _get_streak_exp(streak)

    checkin = DailyCheckin(
        user_id=current_user.id,
        checkin_date=today,
        streak_count=streak,
        exp_earned=exp_earned,
    )
    db.add(checkin)

    current_user.score = (current_user.score or 0) + exp_earned
    await db.commit()

    return {
        "checked_in": True,
        "message": f"签到成功！连续{streak}天",
        "streak": streak,
        "exp_earned": exp_earned,
        "total_score": current_user.score,
    }


@router.get("/status")
async def checkin_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取签到状态"""
    now = datetime.utcnow()
    today = now.replace(hour=0, minute=0, second=0, microsecond=0)

    today_stmt = select(DailyCheckin).where(
        DailyCheckin.user_id == current_user.id,
        DailyCheckin.checkin_date >= today,
    )
    today_result = await db.execute(today_stmt)
    today_checkin = today_result.scalar_one_or_none()

    latest_stmt = select(DailyCheckin).where(
        DailyCheckin.user_id == current_user.id,
    ).order_by(DailyCheckin.checkin_date.desc()).limit(1)
    latest_result = await db.execute(latest_stmt)
    latest_checkin = latest_result.scalar_one_or_none()

    current_streak = 0
    if today_checkin:
        current_streak = today_checkin.streak_count
    elif latest_checkin:
        yesterday = today - timedelta(days=1)
        if latest_checkin.checkin_date >= yesterday:
            current_streak = latest_checkin.streak_count

    total_checkins_stmt = select(func.count()).select_from(DailyCheckin).where(
        DailyCheckin.user_id == current_user.id,
    )
    total_result = await db.execute(total_checkins_stmt)
    total_checkins = total_result.scalar_one()

    last_7_days = []
    for i in range(6, -1, -1):
        d = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        day_start = today - timedelta(days=i)
        day_end = today - timedelta(days=i - 1) if i > 0 else today + timedelta(days=1)
        check_stmt = select(DailyCheckin).where(
            DailyCheckin.user_id == current_user.id,
            DailyCheckin.checkin_date >= day_start,
            DailyCheckin.checkin_date < day_end,
        )
        check_result = await db.execute(check_stmt)
        checked = check_result.scalar_one_or_none() is not None
        last_7_days.append({"date": d, "checked": checked})

    return {
        "checked_in_today": today_checkin is not None,
        "current_streak": current_streak,
        "total_checkins": total_checkins,
        "next_reward": _get_streak_exp(current_streak + 1) if current_streak < 7 else STREAK_REWARDS[7],
        "last_7_days": last_7_days,
    }
