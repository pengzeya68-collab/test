"""排行榜路由 - 竞争激励系统"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, desc, case
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User, Progress, ExerciseSubmissionRecord, DailyCheckin

router = APIRouter(prefix="/api/v1/leaderboard", tags=["排行榜"])


@router.get("/score")
async def get_score_leaderboard(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """综合积分排行榜"""
    total_stmt = select(func.count()).select_from(User)
    total_result = await db.execute(total_stmt)
    total = total_result.scalar_one()

    offset = (page - 1) * page_size
    stmt = (
        select(User)
        .order_by(desc(User.score))
        .offset(offset)
        .limit(page_size)
    )
    result = await db.execute(stmt)
    users = result.scalars().all()

    my_rank_stmt = select(func.count()).select_from(User).where(User.score > (current_user.score or 0))
    my_rank_result = await db.execute(my_rank_stmt)
    my_rank = my_rank_result.scalar_one() + 1

    leaderboard = []
    for idx, u in enumerate(users):
        rank = offset + idx + 1
        leaderboard.append({
            "rank": rank,
            "user_id": u.id,
            "username": u.username,
            "score": u.score or 0,
            "is_me": u.id == current_user.id,
        })

    return {
        "leaderboard": leaderboard,
        "my_rank": my_rank,
        "my_score": current_user.score or 0,
        "total": total,
        "page": page,
    }


@router.get("/weekly")
async def get_weekly_leaderboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """本周活跃排行榜（按本周完成习题数排名）"""
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)

    stmt = (
        select(
            ExerciseSubmissionRecord.user_id,
            func.count().label("submission_count"),
            func.sum(case((ExerciseSubmissionRecord.result == "pass", 1), else_=0)).label("correct_count"),
        )
        .where(ExerciseSubmissionRecord.created_at >= week_start)
        .group_by(ExerciseSubmissionRecord.user_id)
        .order_by(desc("correct_count"))
        .limit(20)
    )
    result = await db.execute(stmt)
    rows = result.all()

    user_ids = [r.user_id for r in rows]
    user_map = {}
    if user_ids:
        users_stmt = select(User).where(User.id.in_(user_ids))
        users_result = await db.execute(users_stmt)
        for u in users_result.scalars().all():
            user_map[u.id] = u.username

    my_weekly_stmt = select(
        func.count().label("total"),
        func.sum(case((ExerciseSubmissionRecord.result == "pass", 1), else_=0)).label("correct"),
    ).where(
        ExerciseSubmissionRecord.user_id == current_user.id,
        ExerciseSubmissionRecord.created_at >= week_start,
    )
    my_weekly_result = await db.execute(my_weekly_stmt)
    my_weekly = my_weekly_result.one()

    leaderboard = []
    for idx, r in enumerate(rows):
        leaderboard.append({
            "rank": idx + 1,
            "user_id": r.user_id,
            "username": user_map.get(r.user_id, f"用户{r.user_id}"),
            "weekly_correct": r.correct_count or 0,
            "weekly_total": r.submission_count,
            "is_me": r.user_id == current_user.id,
        })

    return {
        "leaderboard": leaderboard,
        "my_weekly_correct": my_weekly.correct or 0,
        "my_weekly_total": my_weekly.total or 0,
        "week_start": week_start.strftime("%Y-%m-%d"),
    }


@router.get("/streak")
async def get_streak_leaderboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """连续签到排行榜"""
    stmt = (
        select(
            DailyCheckin.user_id,
            func.max(DailyCheckin.streak_count).label("max_streak"),
        )
        .group_by(DailyCheckin.user_id)
        .order_by(desc("max_streak"))
        .limit(20)
    )
    result = await db.execute(stmt)
    rows = result.all()

    user_ids = [r.user_id for r in rows]
    user_map = {}
    if user_ids:
        users_stmt = select(User).where(User.id.in_(user_ids))
        users_result = await db.execute(users_stmt)
        for u in users_result.scalars().all():
            user_map[u.id] = u.username

    my_streak = 0
    my_checkin_stmt = select(DailyCheckin).where(
        DailyCheckin.user_id == current_user.id,
    ).order_by(desc(DailyCheckin.streak_count)).limit(1)
    my_checkin_result = await db.execute(my_checkin_stmt)
    my_checkin = my_checkin_result.scalar_one_or_none()
    if my_checkin:
        my_streak = my_checkin.streak_count

    leaderboard = []
    for idx, r in enumerate(rows):
        leaderboard.append({
            "rank": idx + 1,
            "user_id": r.user_id,
            "username": user_map.get(r.user_id, f"用户{r.user_id}"),
            "streak": r.max_streak,
            "is_me": r.user_id == current_user.id,
        })

    return {
        "leaderboard": leaderboard,
        "my_streak": my_streak,
    }
