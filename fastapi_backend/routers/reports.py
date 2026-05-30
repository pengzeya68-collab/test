"""
学习报告导出路由
"""

import io
from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import (
    User,
    Progress,
    ProjectSubmission,
    ExamAttempt,
    Note,
)

router = APIRouter(prefix="/api/v1/report", tags=["学习报告"])


@router.get("/summary")
async def get_learning_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取学习数据摘要"""
    # 做过的题目
    ex_count = (
        await db.scalar(select(func.count(Progress.id)).where(Progress.user_id == current_user.id, Progress.completed))
        or 0
    )

    # 提交的项目任务
    sub_count = (
        await db.scalar(select(func.count(ProjectSubmission.id)).where(ProjectSubmission.user_id == current_user.id))
        or 0
    )

    # 完成的考试
    exam_count = (
        await db.scalar(
            select(func.count(ExamAttempt.id)).where(ExamAttempt.user_id == current_user.id, ExamAttempt.is_completed)
        )
        or 0
    )

    # 笔记
    note_count = await db.scalar(select(func.count(Note.id)).where(Note.user_id == current_user.id)) or 0

    return {
        "exercises_completed": ex_count,
        "project_submissions": sub_count,
        "exams_completed": exam_count,
        "notes_count": note_count,
        "score": current_user.score or 0,
        "level": current_user.level or 1,
        "study_time_hours": round((current_user.study_time or 0) / 3600, 1),
    }


@router.get("/export")
async def export_learning_report(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """导出学习报告为文本文件"""
    summary = await get_learning_summary(current_user=current_user, db=db)

    content = f"""
╔══════════════════════════════════════════╗
║         TestMaster 学习报告             ║
╠══════════════════════════════════════════╣
║                                          ║
║  用户: {current_user.username:<30s} ║
║  等级: Lv.{summary["level"]:<30s} ║
║  积分: {summary["score"]:<30s} ║
║  学习时长: {summary["study_time_hours"]}小时{"":<24s} ║
║                                          ║
╠══════════════════════════════════════════╣
║  完成习题: {summary["exercises_completed"]:<28s} ║
║  项目提交: {summary["project_submissions"]:<28s} ║
║  完成考试: {summary["exams_completed"]:<28s} ║
║  学习笔记: {summary["notes_count"]:<28s} ║
║                                          ║
╚══════════════════════════════════════════╝

生成时间: {datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")} UTC
    """.strip()

    buf = io.BytesIO(content.encode("utf-8"))
    return StreamingResponse(
        buf,
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f"attachment; filename=TestMaster_Report_{current_user.username}.txt"},
    )
