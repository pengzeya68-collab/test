"""成就系统路由 - 经验值 + 徽章 + 成长"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User, Achievement, UserAchievement, Submission, Progress

router = APIRouter(prefix="/api/v1/achievements", tags=["成就系统"])

ACHIEVEMENT_DEFINITIONS = [
    {"key": "first_login", "name": "初来乍到", "description": "首次登录平台", "icon": "🚀", "category": "入门", "threshold": 1, "exp_reward": 5},
    {"key": "first_exercise", "name": "初试锋芒", "description": "完成第一道练习题", "icon": "✏️", "category": "练习", "threshold": 1, "exp_reward": 10},
    {"key": "first_exam", "name": "考场新秀", "description": "参加第一次考试", "icon": "📝", "category": "考试", "threshold": 1, "exp_reward": 15},
    {"key": "first_interview", "name": "面试初体验", "description": "完成第一次模拟面试", "icon": "🎤", "category": "面试", "threshold": 1, "exp_reward": 15},
    {"key": "assessment_done", "name": "知己知彼", "description": "完成入学能力测评", "icon": "🎯", "category": "入门", "threshold": 1, "exp_reward": 10},
    {"key": "exercises_10", "name": "勤学苦练", "description": "完成 10 道练习题", "icon": "💪", "category": "练习", "threshold": 10, "exp_reward": 25},
    {"key": "exercises_50", "name": "题海战术", "description": "完成 50 道练习题", "icon": "📚", "category": "练习", "threshold": 50, "exp_reward": 50},
    {"key": "perfect_score", "name": "完美答卷", "description": "考试获得满分", "icon": "💯", "category": "考试", "threshold": 1, "exp_reward": 30},
    {"key": "interview_5", "name": "面试达人", "description": "完成 5 次模拟面试", "icon": "🏆", "category": "面试", "threshold": 5, "exp_reward": 40},
    {"key": "streak_7", "name": "七日之约", "description": "连续 7 天学习", "icon": "🔥", "category": "坚持", "threshold": 7, "exp_reward": 35},
    {"key": "skill_80", "name": "技能精通", "description": "任一技能维度达到 80 分", "icon": "⭐", "category": "技能", "threshold": 1, "exp_reward": 50},
    {"key": "all_rounder", "name": "全面发展", "description": "所有技能维度均达到 60 分", "icon": "🌟", "category": "技能", "threshold": 1, "exp_reward": 100},
]


async def _ensure_achievements(db: AsyncSession):
    stmt = select(func.count()).select_from(Achievement)
    result = await db.execute(stmt)
    count = result.scalar_one()
    if count == 0:
        for ach_def in ACHIEVEMENT_DEFINITIONS:
            ach = Achievement(**ach_def)
            db.add(ach)
        await db.commit()


async def check_and_unlock_achievements(user_id: int, db: AsyncSession):
    """检查并解锁用户成就（在关键操作后调用）"""
    await _ensure_achievements(db)

    unlocked_stmt = select(UserAchievement.achievement_id).where(
        UserAchievement.user_id == user_id
    )
    unlocked_result = await db.execute(unlocked_stmt)
    unlocked_ids = {row[0] for row in unlocked_result.all()}

    all_achievements_stmt = select(Achievement)
    all_result = await db.execute(all_achievements_stmt)
    all_achievements = all_result.scalars().all()

    new_unlocks = []

    for ach in all_achievements:
        if ach.id in unlocked_ids:
            continue

        should_unlock = False

        if ach.key == "first_login":
            should_unlock = True
        elif ach.key == "first_exercise":
            count_stmt = select(func.count()).select_from(Progress).where(
                Progress.user_id == user_id, Progress.completed == True  # noqa: E712
            )
            count_result = await db.execute(count_stmt)
            if count_result.scalar_one() >= 1:
                should_unlock = True
        elif ach.key == "exercises_10":
            count_stmt = select(func.count()).select_from(Progress).where(
                Progress.user_id == user_id, Progress.completed == True  # noqa: E712
            )
            count_result = await db.execute(count_stmt)
            if count_result.scalar_one() >= 10:
                should_unlock = True
        elif ach.key == "exercises_50":
            count_stmt = select(func.count()).select_from(Progress).where(
                Progress.user_id == user_id, Progress.completed == True  # noqa: E712
            )
            count_result = await db.execute(count_stmt)
            if count_result.scalar_one() >= 50:
                should_unlock = True
        elif ach.key == "assessment_done":
            user_stmt = select(User.score).where(User.id == user_id)
            user_result = await db.execute(user_stmt)
            score = user_result.scalar_one_or_none()
            if score and score > 0:
                should_unlock = True

        if should_unlock:
            ua = UserAchievement(user_id=user_id, achievement_id=ach.id)
            db.add(ua)
            new_unlocks.append(ach)

    if new_unlocks:
        await db.commit()

    return new_unlocks


@router.get("/")
async def get_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的成就列表（含解锁状态）"""
    await _ensure_achievements(db)

    all_stmt = select(Achievement).order_by(Achievement.id)
    all_result = await db.execute(all_stmt)
    all_achs = all_result.scalars().all()

    unlocked_stmt = select(UserAchievement).where(
        UserAchievement.user_id == current_user.id
    )
    unlocked_result = await db.execute(unlocked_stmt)
    unlocked_map = {ua.achievement_id: ua for ua in unlocked_result.scalars().all()}

    total_exp = sum(ach.exp_reward for ach in all_achs if ach.id in unlocked_map)
    total_count = len(all_achs)
    unlocked_count = len(unlocked_map)

    achievements = []
    for ach in all_achs:
        ua = unlocked_map.get(ach.id)
        achievements.append({
            "id": ach.id,
            "key": ach.key,
            "name": ach.name,
            "description": ach.description,
            "icon": ach.icon,
            "category": ach.category,
            "threshold": ach.threshold,
            "exp_reward": ach.exp_reward,
            "unlocked": ua is not None,
            "unlocked_at": str(ua.unlocked_at) if ua else None,
            "progress": ua.progress if ua else 0,
        })

    return {
        "achievements": achievements,
        "total_exp": total_exp,
        "total_count": total_count,
        "unlocked_count": unlocked_count,
        "level": current_user.level or 1,
        "exp": current_user.score or 0,
    }


@router.post("/check")
async def check_achievements(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """手动触发成就检查，返回新解锁的成就"""
    new_unlocks = await check_and_unlock_achievements(current_user.id, db)

    return {
        "new_unlocks": [
            {
                "key": ach.key,
                "name": ach.name,
                "description": ach.description,
                "icon": ach.icon,
                "exp_reward": ach.exp_reward,
            }
            for ach in new_unlocks
        ],
        "count": len(new_unlocks),
    }
