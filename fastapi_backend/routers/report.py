"""学习周报路由 - 学习数据复盘"""
from __future__ import annotations

from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_, case, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import (
    User, Progress, Exercise, ExerciseSubmissionRecord, DailyCheckin,
)

router = APIRouter(prefix="/api/v1/report", tags=["学习报告"])


@router.get("/weekly")
async def get_weekly_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取本周学习报告"""
    now = datetime.utcnow()
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    last_week_start = week_start - timedelta(days=7)

    # 本周提交
    this_week_stmt = select(ExerciseSubmissionRecord).where(
        ExerciseSubmissionRecord.user_id == current_user.id,
        ExerciseSubmissionRecord.created_at >= week_start,
    )
    this_week_result = await db.execute(this_week_stmt)
    this_week_subs = this_week_result.scalars().all()

    this_week_total = len(this_week_subs)
    this_week_correct = sum(1 for s in this_week_subs if s.result == "pass")
    this_week_wrong = this_week_total - this_week_correct

    # 上周提交
    last_week_stmt = select(ExerciseSubmissionRecord).where(
        ExerciseSubmissionRecord.user_id == current_user.id,
        ExerciseSubmissionRecord.created_at >= last_week_start,
        ExerciseSubmissionRecord.created_at < week_start,
    )
    last_week_result = await db.execute(last_week_stmt)
    last_week_subs = last_week_result.scalars().all()

    last_week_total = len(last_week_subs)
    last_week_correct = sum(1 for s in last_week_subs if s.result == "pass")

    # 本周每日分布
    daily_data = []
    for i in range(7):
        day_start = week_start + timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        day_stmt = select(
            func.count().label("total"),
            func.sum(case((ExerciseSubmissionRecord.result == "pass", 1), else_=0)).label("correct"),
        ).where(
            ExerciseSubmissionRecord.user_id == current_user.id,
            ExerciseSubmissionRecord.created_at >= day_start,
            ExerciseSubmissionRecord.created_at < day_end,
        )
        day_result = await db.execute(day_stmt)
        day_row = day_result.one()
        daily_data.append({
            "date": day_start.strftime("%m-%d"),
            "day_name": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][i],
            "total": day_row.total or 0,
            "correct": day_row.correct or 0,
        })

    # 本周知识点分布
    this_week_exercise_ids = list({s.exercise_id for s in this_week_subs})
    category_dist = {}
    if this_week_exercise_ids:
        ex_stmt = select(Exercise).where(Exercise.id.in_(this_week_exercise_ids))
        ex_result = await db.execute(ex_stmt)
        for ex in ex_result.scalars().all():
            cat = ex.category or "未分类"
            category_dist[cat] = category_dist.get(cat, 0) + 1

    # 本周签到
    checkin_stmt = select(DailyCheckin).where(
        DailyCheckin.user_id == current_user.id,
        DailyCheckin.checkin_date >= week_start,
    )
    checkin_result = await db.execute(checkin_stmt)
    checkins = checkin_result.scalars().all()
    checkin_count = len(checkins)
    max_streak = max((c.streak_count for c in checkins), default=0)

    # 变化率
    total_change = 0
    if last_week_total > 0:
        total_change = round((this_week_total - last_week_total) / last_week_total * 100, 1)
    elif this_week_total > 0:
        total_change = 100

    correct_rate = round(this_week_correct / this_week_total * 100, 1) if this_week_total > 0 else 0
    last_correct_rate = round(last_week_correct / last_week_total * 100, 1) if last_week_total > 0 else 0

    # 学习建议
    suggestions = []
    if this_week_total == 0:
        suggestions.append("本周还没有开始学习，赶快行动起来吧！")
    else:
        if correct_rate < 60:
            suggestions.append("正确率偏低，建议回顾基础知识点，从简单题目开始练习。")
        if this_week_total < 5:
            suggestions.append("练习量偏少，建议每天至少完成3道题，保持学习节奏。")
        if checkin_count < 3:
            suggestions.append("签到次数较少，坚持每日签到可以获取更多经验奖励。")
        if this_week_wrong > this_week_correct:
            suggestions.append("错题较多，建议使用错题本功能复习薄弱知识点。")
        if correct_rate >= 80 and this_week_total >= 10:
            suggestions.append("表现优秀！可以尝试更高难度的题目，挑战自我。")
        if not suggestions:
            suggestions.append("保持良好的学习节奏，继续加油！")

    return {
        "period": {
            "start": week_start.strftime("%Y-%m-%d"),
            "end": now.strftime("%Y-%m-%d"),
        },
        "summary": {
            "total_submissions": this_week_total,
            "correct_count": this_week_correct,
            "wrong_count": this_week_wrong,
            "correct_rate": correct_rate,
            "checkin_count": checkin_count,
            "max_streak": max_streak,
        },
        "comparison": {
            "last_week_total": last_week_total,
            "last_week_correct": last_week_correct,
            "last_correct_rate": last_correct_rate,
            "total_change_percent": total_change,
        },
        "daily_data": daily_data,
        "category_distribution": category_dist,
        "suggestions": suggestions,
    }


@router.get("/heatmap")
async def get_learning_heatmap(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学习热力图数据（过去365天）"""
    now = datetime.utcnow()
    start_date = now - timedelta(days=365)

    stmt = select(
        func.date(ExerciseSubmissionRecord.created_at).label("date"),
        func.count().label("total"),
        func.sum(case((ExerciseSubmissionRecord.result == "pass", 1), else_=0)).label("correct"),
    ).where(
        ExerciseSubmissionRecord.user_id == current_user.id,
        ExerciseSubmissionRecord.created_at >= start_date,
    ).group_by(func.date(ExerciseSubmissionRecord.created_at))

    result = await db.execute(stmt)
    rows = result.all()

    heatmap = {}
    for r in rows:
        date_str = str(r.date) if r.date else ""
        heatmap[date_str] = {
            "total": r.total or 0,
            "correct": r.correct or 0,
        }

    days = []
    for i in range(364, -1, -1):
        d = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        data = heatmap.get(d, {"total": 0, "correct": 0})
        days.append({
            "date": d,
            "total": data["total"],
            "correct": data["correct"],
            "level": min(data["total"], 4),
        })

    total_days = sum(1 for d in days if d["total"] > 0)
    total_submissions = sum(d["total"] for d in days)
    longest_streak = 0
    current_streak = 0
    for d in days:
        if d["total"] > 0:
            current_streak += 1
            longest_streak = max(longest_streak, current_streak)
        else:
            current_streak = 0

    return {
        "days": days,
        "total_days": total_days,
        "total_submissions": total_submissions,
        "longest_streak": longest_streak,
    }
