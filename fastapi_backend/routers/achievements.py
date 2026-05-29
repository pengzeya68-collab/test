"""成就系统路由 - 经验值 + 徽章 + 成长"""
from __future__ import annotations


from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User, Achievement, UserAchievement, Progress

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

    # 只查询未解锁的成就，减少数据量
    all_achievements_stmt = select(Achievement).where(
        Achievement.id.notin_(unlocked_ids) if unlocked_ids else True
    )
    all_result = await db.execute(all_achievements_stmt)
    all_achievements = all_result.scalars().all()

    if not all_achievements:
        return []

    # 批量预查询用户统计数据，避免N+1查询
    from fastapi_backend.models.models import ExamAttempt, InterviewSession, DailyCheckin, Exam

    progress_count_stmt = select(func.count()).select_from(Progress).where(
        Progress.user_id == user_id, Progress.completed == True  # noqa: E712
    )
    progress_count_result = await db.execute(progress_count_stmt)
    total_completed_exercises = progress_count_result.scalar_one()

    exam_count_stmt = select(func.count()).select_from(ExamAttempt).where(
        ExamAttempt.user_id == user_id
    )
    exam_count_result = await db.execute(exam_count_stmt)
    exam_count = exam_count_result.scalar_one()

    perfect_stmt = select(func.count()).select_from(ExamAttempt).join(
        Exam, and_(ExamAttempt.exam_id == Exam.id, ExamAttempt.score == Exam.total_score)
    ).where(
        ExamAttempt.user_id == user_id
    )
    perfect_result = await db.execute(perfect_stmt)
    perfect_count = perfect_result.scalar_one()

    interview_count_stmt = select(func.count()).select_from(InterviewSession).where(
        InterviewSession.user_id == user_id
    )
    interview_count_result = await db.execute(interview_count_stmt)
    interview_count = interview_count_result.scalar_one()

    streak_stmt = select(func.max(DailyCheckin.streak_count)).where(
        DailyCheckin.user_id == user_id
    )
    streak_result = await db.execute(streak_stmt)
    max_streak = streak_result.scalar_one_or_none() or 0

    user_stmt = select(User.assessment_score).where(User.id == user_id)
    user_result = await db.execute(user_stmt)
    assessment_score = user_result.scalar_one_or_none()

    new_unlocks = []

    for ach in all_achievements:
        should_unlock = False

        if ach.key == "first_login":
            should_unlock = not unlocked_ids
        elif ach.key in ("first_exercise", "exercises_10", "exercises_50"):
            if ach.key == "first_exercise" and total_completed_exercises >= 1:
                should_unlock = True
            elif ach.key == "exercises_10" and total_completed_exercises >= 10:
                should_unlock = True
            elif ach.key == "exercises_50" and total_completed_exercises >= 50:
                should_unlock = True
        elif ach.key == "assessment_done":
            if assessment_score is not None:
                should_unlock = True
        elif ach.key == "first_exam":
            if exam_count >= 1:
                should_unlock = True
        elif ach.key == "first_interview":
            if interview_count >= 1:
                should_unlock = True
        elif ach.key == "perfect_score":
            if perfect_count >= 1:
                should_unlock = True
        elif ach.key == "interview_5":
            if interview_count >= 5:
                should_unlock = True
        elif ach.key == "streak_7":
            if max_streak >= 7:
                should_unlock = True
        elif ach.key in ("skill_80", "all_rounder"):
            pass

        if should_unlock:
            ua = UserAchievement(user_id=user_id, achievement_id=ach.id)
            db.add(ua)
            new_unlocks.append(ach)

    if new_unlocks:
        await db.commit()

    return new_unlocks


@router.get("")
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
