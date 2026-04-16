"""
后台管理子路由 - 考试管理
从 admin_manage.py 拆分
"""
from typing import Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db, AsyncSessionLocal
from fastapi_backend.core.exceptions import NotFoundException
from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import User, Exercise, LearningPath, Exam, ExamQuestion, Post, Comment, InterviewQuestion, Submission, Progress
from fastapi_backend.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/admin", tags=["Admin-考试管理"])

@router.get("/exams")
async def list_exams(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    exam_type: Optional[str] = Query(None),
    is_published: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(Exam)

        if keyword:
            query = query.where(Exam.title.contains(keyword))
        if exam_type:
            query = query.where(Exam.exam_type == exam_type) if hasattr(Exam, "exam_type") else query
        if is_published is not None and is_published != "":
            is_pub = is_published == "true"
            query = query.where(Exam.is_published == is_pub) if hasattr(Exam, "is_published") else query

        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        offset = (page - 1) * size
        query = query.order_by(desc(Exam.created_at)).offset(offset).limit(size)
        result = await db.execute(query)
        exams = result.scalars().all()

        exam_list = []
        for e in exams:
            try:
                exam_list.append({
                    "id": e.id,
                    "title": e.title,
                    "exam_type": getattr(e, "exam_type", ""),
                    "difficulty": getattr(e, "difficulty", "medium"),
                    "duration": getattr(e, "duration", 60),
                    "total_score": getattr(e, "total_score", 100),
                    "pass_score": getattr(e, "pass_score", 60),
                    "is_published": getattr(e, "is_published", False),
                    "question_count": len(getattr(e, 'questions', []) or []),
                    "attempt_count": 0,
                    "pass_rate": 0,
                    "created_at": e.created_at.isoformat() if e.created_at else "",
                })
            except Exception:
                exam_list.append({
                    "id": getattr(e, 'id', 0),
                    "title": getattr(e, 'title', '(数据异常)'),
                    "exam_type": "",
                    "created_at": "",
                })

        return {"list": exam_list, "total": total or 0}
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error(f"获取考试列表失败: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取考试列表失败")


@router.get("/exams/{exam_id}")
async def get_exam(
    exam_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取考试详情"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    # 获取题目
    q_result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam_id)
    )
    questions = q_result.scalars().all()

    return {
        "id": exam.id,
        "title": exam.title,
        "exam_type": getattr(exam, "exam_type", ""),
        "difficulty": getattr(exam, "difficulty", "medium"),
        "duration": getattr(exam, "duration", 60),
        "total_score": getattr(exam, "total_score", 100),
        "pass_score": getattr(exam, "pass_score", 60),
        "description": getattr(exam, "description", ""),
        "is_published": getattr(exam, "is_published", False),
        "start_time": getattr(exam, "start_time", None),
        "end_time": getattr(exam, "end_time", None),
        "questions": [
            {
                "id": q.id,
                "question_type": getattr(q, "question_type", "single_choice"),
                "content": getattr(q, "content", ""),
                "options": getattr(q, "options", []),
                "correct_answer": getattr(q, "correct_answer", ""),
                "score": getattr(q, "score", 10),
                "analysis": getattr(q, "analysis", ""),
            }
            for q in questions
        ],
    }


@router.post("/exams")
async def create_exam(
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建考试"""
    questions = data.pop("questions", [])
    new_exam = Exam(
        title=data.get("title", ""),
        description=data.get("description", ""),
        exam_type=data.get("exam_type", "模拟考试"),
        difficulty=data.get("difficulty", "medium"),
        duration=data.get("duration", 60),
        total_score=data.get("total_score", 100),
        pass_score=data.get("pass_score", 60),
        is_published=data.get("is_published", False),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
        user_id=current_user.id,
    )

    db.add(new_exam)
    await db.flush()

    # 添加题目
    for q_data in questions:
        new_q = ExamQuestion(
            exam_id=new_exam.id,
            question_type=q_data.get("question_type", "single_choice"),
            content=q_data.get("content", ""),
            correct_answer=q_data.get("correct_answer", ""),
            score=q_data.get("score", 10),
            analysis=q_data.get("analysis", ""),
            options=str(q_data.get("options", [])) if q_data.get("options") else None,
        )
        db.add(new_q)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="考试创建失败，事务已回滚")
    return {"message": "考试创建成功", "id": new_exam.id}


@router.put("/exams/{exam_id}")
async def update_exam(
    exam_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新考试"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    for field in ["title", "description", "difficulty", "exam_type", "duration", "total_score", "pass_score", "start_time", "end_time"]:
        if field in data and hasattr(exam, field):
            setattr(exam, field, data[field])
    if "is_published" in data and hasattr(exam, "is_published"):
        exam.is_published = data["is_published"]

    # 更新题目（简单策略：先删后加）
    questions = data.get("questions", None)
    if questions is not None:
        old_q_result = await db.execute(
            select(ExamQuestion).where(ExamQuestion.exam_id == exam_id)
        )
        for old_q in old_q_result.scalars().all():
            await db.delete(old_q)

        for q_data in questions:
            new_q = ExamQuestion(
                exam_id=exam_id,
                question_type=q_data.get("question_type", "single_choice"),
                content=q_data.get("content", ""),
                correct_answer=q_data.get("correct_answer", ""),
                score=q_data.get("score", 10),
                analysis=q_data.get("analysis", ""),
                options=str(q_data.get("options", [])) if q_data.get("options") else None,
            )
            db.add(new_q)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="考试更新失败，事务已回滚")
    return {"message": "考试更新成功"}


@router.delete("/exams/{exam_id}")
async def delete_exam(
    exam_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除考试"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    # 删除关联题目
    q_result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam_id)
    )
    for q in q_result.scalars().all():
        await db.delete(q)

    await db.delete(exam)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="考试删除失败，事务已回滚")
    return {"message": "删除成功"}


@router.put("/exams/{exam_id}/publish")
async def toggle_exam_publish(
    exam_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """切换考试发布状态"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    if hasattr(exam, "is_published"):
        exam.is_published = data.get("is_published", not exam.is_published)
        await db.commit()
    return {"message": "操作成功"}


