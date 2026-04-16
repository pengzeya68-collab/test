"""
Interview 统计与报告服务
从 routers/interview.py 下沉的业务逻辑
"""
import logging
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

from sqlalchemy import select, func, case, or_
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.models import Submission, InterviewQuestion, InterviewSession

_logger = logging.getLogger(__name__)


async def get_user_interview_statistics(user_id: int, db: AsyncSession) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    today_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    seven_days_ago = now - timedelta(days=7)

    total_result = await db.execute(
        select(func.count(Submission.id)).where(Submission.user_id == user_id)
    )
    total_submissions = total_result.scalar_one() or 0

    completed_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.user_id == user_id,
            Submission.score.is_not(None)
        )
    )
    completed_submissions = completed_result.scalar_one() or 0

    score_stats_result = await db.execute(
        select(
            func.avg(Submission.score).label("avg_score"),
            func.max(Submission.score).label("max_score"),
            func.min(Submission.score).label("min_score")
        ).where(
            Submission.user_id == user_id,
            Submission.score.is_not(None)
        )
    )
    score_stats = score_stats_result.first()
    average_score = float(score_stats.avg_score) if score_stats.avg_score else None
    highest_score = score_stats.max_score
    lowest_score = score_stats.min_score

    pass_stats_result = await db.execute(
        select(
            func.count(Submission.id).label("total"),
            func.sum(case((Submission.score >= 80, 1), else_=0)).label("passed")
        ).where(
            Submission.user_id == user_id,
            Submission.score.is_not(None)
        )
    )
    pass_stats = pass_stats_result.first()
    total_with_score = pass_stats.total or 0
    passed_count = pass_stats.passed or 0 if pass_stats.passed else 0
    failed_count = total_with_score - passed_count
    pass_rate = (passed_count / total_with_score * 100) if total_with_score > 0 else 0.0

    recent_7_days_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.user_id == user_id,
            Submission.created_at >= seven_days_ago
        )
    )
    recent_7_days_submissions = recent_7_days_result.scalar_one() or 0

    today_result = await db.execute(
        select(func.count(Submission.id)).where(
            Submission.user_id == user_id,
            Submission.created_at >= today_start
        )
    )
    today_submissions = today_result.scalar_one() or 0

    difficulty_result = await db.execute(
        select(
            InterviewQuestion.difficulty,
            func.count(Submission.id).label("count")
        )
        .join(InterviewQuestion, Submission.question_id == InterviewQuestion.id)
        .where(Submission.user_id == user_id)
        .group_by(InterviewQuestion.difficulty)
    )
    difficulty_distribution = {}
    for difficulty, count in difficulty_result.all():
        if difficulty:
            difficulty_distribution[difficulty] = count

    daily_submissions = []
    for i in range(6, -1, -1):
        day_start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc) - timedelta(days=i)
        day_end = day_start + timedelta(days=1)
        day_result = await db.execute(
            select(func.count(Submission.id)).where(
                Submission.user_id == user_id,
                Submission.created_at >= day_start,
                Submission.created_at < day_end
            )
        )
        day_count = day_result.scalar_one() or 0
        daily_submissions.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": day_count
        })

    last_submission_result = await db.execute(
        select(Submission.created_at).where(
            Submission.user_id == user_id
        ).order_by(Submission.created_at.desc()).limit(1)
    )
    last_submission_time = last_submission_result.scalar_one_or_none()

    return {
        "total_submissions": total_submissions,
        "completed_submissions": completed_submissions,
        "average_score": average_score,
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "pass_rate": pass_rate,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "recent_7_days_submissions": recent_7_days_submissions,
        "today_submissions": today_submissions,
        "difficulty_distribution": difficulty_distribution,
        "daily_submissions_last_7_days": daily_submissions,
        "weak_tags": [],
        "last_submission_time": last_submission_time
    }


async def generate_interview_report(session_id: int, user_id: int, db: AsyncSession) -> Dict[str, Any]:
    session_result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        return None

    submissions_result = await db.execute(
        select(Submission)
        .where(Submission.session_id == session_id)
        .order_by(Submission.created_at)
    )
    submissions = submissions_result.scalars().all()

    total_questions = len(submissions)
    if total_questions == 0:
        return {
            "overall_score": 0,
            "overall_level": "未评估",
            "summary": "本次面试未提交任何回答",
            "dimensions": [],
            "strengths": [],
            "weaknesses": [],
            "improvement_plan": [],
        }

    scores = [s.score for s in submissions if s.score is not None]
    avg_score = sum(scores) / len(scores) if scores else 0
    max_score = max(scores) if scores else 0
    min_score = min(scores) if scores else 0
    pass_count = sum(1 for s in scores if s >= 60)

    level = "专家" if avg_score >= 90 else "精通" if avg_score >= 80 else "熟练" if avg_score >= 70 else "掌握" if avg_score >= 60 else "了解" if avg_score >= 40 else "入门"

    high_score_submissions = [s for s in submissions if s.score and s.score >= 80]
    low_score_submissions = [s for s in submissions if s.score and s.score < 60]

    strengths = []
    for s in high_score_submissions[:3]:
        q_result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == s.question_id))
        q = q_result.scalar_one_or_none()
        if q:
            strengths.append(f"{q.title}（{s.score}分）")

    weaknesses = []
    for s in low_score_submissions[:3]:
        q_result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == s.question_id))
        q = q_result.scalar_one_or_none()
        if q:
            weaknesses.append(f"{q.title}（{s.score}分）")

    improvement_plan = []
    if avg_score < 60:
        improvement_plan = [
            "建议先巩固基础知识，重点复习测试理论和测试用例设计方法",
            "每天至少完成3道练习题，建立知识体系",
            "关注薄弱环节，针对性练习",
        ]
    elif avg_score < 80:
        improvement_plan = [
            "基础已较扎实，建议深入学习自动化测试和接口测试",
            "尝试参与实际项目，积累实战经验",
            "学习CI/CD和云原生相关技能，提升综合能力",
        ]
    else:
        improvement_plan = [
            "你已经具备较强的测试开发能力",
            "建议向测试架构师方向发展，学习测试平台开发",
            "可以尝试指导新人，提升技术影响力",
        ]

    return {
        "overall_score": round(avg_score, 1),
        "overall_level": level,
        "summary": f"本次面试共 {total_questions} 题，平均得分 {round(avg_score, 1)} 分，通过 {pass_count}/{total_questions} 题",
        "score_range": {"max": max_score, "min": min_score, "avg": round(avg_score, 1)},
        "pass_rate": round(pass_count / total_questions * 100, 1) if total_questions > 0 else 0,
        "strengths": strengths[:5],
        "weaknesses": weaknesses[:5],
        "improvement_plan": improvement_plan,
    }


async def complete_session(session_id: int, user_id: int, db: AsyncSession) -> Optional[Dict[str, Any]]:
    session_result = await db.execute(
        select(InterviewSession).where(
            InterviewSession.id == session_id,
            InterviewSession.user_id == user_id,
        )
    )
    session = session_result.scalar_one_or_none()
    if not session:
        return None

    now = datetime.now(timezone.utc)
    session.status = "finished"
    session.finished_at = now
    session.end_time = now

    sub_result = await db.execute(
        select(Submission).where(Submission.session_id == session_id)
    )
    submissions = sub_result.scalars().all()
    scores = [s.score for s in submissions if s.score is not None]
    if scores:
        avg = sum(scores) / len(scores)
        session.latest_score = int(avg)
        session.user_score = int(avg)
        session.total_score = 100

    await db.commit()
    await db.refresh(session)

    return {
        "session_id": session.id,
        "status": session.status,
        "score": session.latest_score,
        "total_questions": len(submissions),
        "answered_questions": len(submissions),
    }


async def get_interview_history(
    user_id: int,
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    question_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    query = (
        select(
            Submission,
            InterviewQuestion.title.label("question_title"),
            InterviewQuestion.difficulty.label("question_difficulty"),
        )
        .outerjoin(InterviewQuestion, Submission.question_id == InterviewQuestion.id)
        .where(Submission.user_id == user_id)
        .order_by(Submission.created_at.desc())
    )

    if question_id is not None:
        query = query.where(Submission.question_id == question_id)

    if status_filter is not None:
        query = query.where(
            or_(
                Submission.execution_status == status_filter,
                Submission.ai_evaluation_status == status_filter,
            )
        )

    if start_date is not None:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.where(Submission.created_at >= start_dt)
        except ValueError:
            return {"error": "开始日期格式无效，请使用 YYYY-MM-DD 格式"}

    if end_date is not None:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
            query = query.where(Submission.created_at < end_dt)
        except ValueError:
            return {"error": "结束日期格式无效，请使用 YYYY-MM-DD 格式"}

    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    pages = (total + size - 1) // size if size > 0 else 0
    offset = (page - 1) * size

    query = query.offset(offset).limit(size)
    result = await db.execute(query)
    rows = result.all()

    history_items = []
    for submission, question_title, question_difficulty in rows:
        history_items.append({
            "id": submission.id,
            "session_id": submission.session_id,
            "question_id": submission.question_id,
            "question_title": question_title,
            "question_difficulty": question_difficulty,
            "language": submission.language,
            "execution_status": submission.execution_status,
            "ai_evaluation_status": submission.ai_evaluation_status,
            "score": submission.score,
            "created_at": submission.created_at,
            "updated_at": submission.updated_at,
        })

    return {
        "items": history_items,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages,
    }


async def get_submission_result_detail(submission_id: int, user_id: int, db: AsyncSession) -> Optional[Dict[str, Any]]:
    query = (
        select(
            Submission,
            InterviewSession.status.label("session_status"),
            InterviewQuestion.title.label("question_title"),
            InterviewQuestion.difficulty.label("question_difficulty"),
            InterviewQuestion.description.label("question_description"),
            InterviewQuestion.prompt.label("question_prompt"),
            InterviewQuestion.test_cases.label("question_test_cases"),
        )
        .join(InterviewSession, Submission.session_id == InterviewSession.id)
        .join(InterviewQuestion, Submission.question_id == InterviewQuestion.id)
        .where(
            Submission.id == submission_id,
            Submission.user_id == user_id,
        )
    )

    result = await db.execute(query)
    row = result.first()

    if not row:
        return None

    submission, session_status, question_title, question_difficulty, \
        question_description, question_prompt, question_test_cases = row

    return {
        "id": submission.id,
        "session_id": submission.session_id,
        "user_id": submission.user_id,
        "question_id": submission.question_id,
        "language": submission.language,
        "source_code": submission.source_code,
        "execution_status": submission.execution_status,
        "ai_evaluation_status": submission.ai_evaluation_status,
        "score": submission.score,
        "feedback": submission.feedback,
        "execution_result": submission.execution_result,
        "created_at": submission.created_at,
        "updated_at": submission.updated_at,
        "session_status": session_status,
        "question_title": question_title,
        "question_difficulty": question_difficulty,
        "question_description": question_description,
        "question_prompt": question_prompt,
        "question_test_cases": question_test_cases,
    }
