"""
后台管理子路由 - 考试管理
从 admin_manage.py 拆分
"""

import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, desc, delete, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import User, Exam, ExamQuestion, ExamAttempt, ExamAnswer
from fastapi_backend.schemas.admin import AdminExamCreate, AdminExamUpdate, AdminExamPublishToggle

router = APIRouter(prefix="/api/v1/admin", tags=["Admin-考试管理"])


@router.get("/exams")
async def list_exams(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    exam_type: Optional[str] = Query(None),
    is_published: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
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

        # 真实统计：批量查询当前页考试的尝试数与通过数
        exam_ids = [e.id for e in exams]
        stats = {}
        if exam_ids:
            stats_result = await db.execute(
                select(
                    ExamAttempt.exam_id,
                    func.count(ExamAttempt.id),
                    func.coalesce(func.sum(ExamAttempt.is_passed.cast(Integer)), 0),
                )
                .where(ExamAttempt.exam_id.in_(exam_ids))
                .group_by(ExamAttempt.exam_id)
            )
            for row in stats_result.all():
                stats[row[0]] = {"attempt_count": row[1], "pass_count": row[2]}

        exam_list = []
        for e in exams:
            try:
                stat = stats.get(e.id, {"attempt_count": 0, "pass_count": 0})
                attempt_count = stat["attempt_count"]
                pass_count = stat["pass_count"]
                pass_rate = round(pass_count * 100 / attempt_count, 1) if attempt_count else 0
                exam_list.append(
                    {
                        "id": e.id,
                        "title": e.title,
                        "exam_type": getattr(e, "exam_type", ""),
                        "difficulty": getattr(e, "difficulty", "medium"),
                        "duration": getattr(e, "duration", 60),
                        "total_score": getattr(e, "total_score", 100),
                        "pass_score": getattr(e, "pass_score", 60),
                        "is_published": getattr(e, "is_published", False),
                        "question_count": len(getattr(e, "questions", []) or []),
                        "attempt_count": attempt_count,
                        "pass_rate": pass_rate,
                        "created_at": e.created_at.isoformat() if e.created_at else "",
                    }
                )
            except Exception:
                exam_list.append(
                    {
                        "id": getattr(e, "id", 0),
                        "title": getattr(e, "title", "(数据异常)"),
                        "exam_type": "",
                        "created_at": "",
                    }
                )

        return {"list": exam_list, "total": total or 0}
    except Exception as exc:
        import logging

        logging.getLogger(__name__).error(f"获取考试列表失败: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取考试列表失败")


@router.get("/exams/{exam_id}")
async def get_exam(
    exam_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取考试详情"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    # 获取题目
    q_result = await db.execute(select(ExamQuestion).where(ExamQuestion.exam_id == exam_id))
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
    data: AdminExamCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建考试"""
    new_exam = Exam(
        title=data.title,
        description=data.description,
        exam_type=data.exam_type,
        difficulty=data.difficulty,
        duration=data.duration,
        total_score=data.total_score,
        pass_score=data.pass_score,
        is_published=data.is_published,
        start_time=data.start_time,
        end_time=data.end_time,
        user_id=current_user.id,
    )

    db.add(new_exam)
    await db.flush()

    # 添加题目
    for q_data in data.questions:
        new_q = ExamQuestion(
            exam_id=new_exam.id,
            question_type=q_data.question_type,
            content=q_data.content,
            correct_answer=q_data.correct_answer,
            score=q_data.score,
            analysis=q_data.analysis,
            options=json.dumps(q_data.options, ensure_ascii=False) if q_data.options else None,
        )
        db.add(new_q)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error(f"创建考试失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="考试创建失败，事务已回滚")
    return {"message": "考试创建成功", "id": new_exam.id}


@router.put("/exams/{exam_id}")
async def update_exam(
    exam_id: int,
    data: AdminExamUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新考试"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    update_data = data.model_dump(exclude_unset=True)
    for field in [
        "title",
        "description",
        "difficulty",
        "exam_type",
        "duration",
        "total_score",
        "pass_score",
        "start_time",
        "end_time",
    ]:
        if field in update_data and hasattr(exam, field):
            setattr(exam, field, update_data[field])
    if "is_published" in update_data and hasattr(exam, "is_published"):
        exam.is_published = update_data["is_published"]

    # 更新题目（diff 策略：仅删除真正不再需要且无答题记录的题目，保留 ExamAnswer FK）
    if data.questions is not None:
        existing_result = await db.execute(select(ExamQuestion).where(ExamQuestion.exam_id == exam_id))
        existing_questions = {q.id: q for q in existing_result.scalars().all()}
        new_question_ids = {q.id for q in data.questions if q.id is not None}

        # 删除被移除且无答题记录的题目
        for q_id, q in existing_questions.items():
            if q_id not in new_question_ids:
                answer_count_result = await db.execute(
                    select(func.count(ExamAnswer.id)).where(ExamAnswer.question_id == q_id)
                )
                if answer_count_result.scalar() == 0:
                    await db.delete(q)
                # 否则保留题目（已有答题记录，不能删除以免破坏 FK）

        # 更新或创建题目
        for q_data in data.questions:
            if q_data.id is not None:
                # 更新已有题目
                q = existing_questions.get(q_data.id)
                if q is not None:
                    q.question_type = q_data.question_type
                    q.content = q_data.content
                    q.correct_answer = q_data.correct_answer
                    q.score = q_data.score
                    q.analysis = q_data.analysis
                    if q_data.options is not None:
                        q.options = json.dumps(q_data.options, ensure_ascii=False)
            else:
                # 新建题目
                new_q = ExamQuestion(
                    exam_id=exam_id,
                    question_type=q_data.question_type,
                    content=q_data.content,
                    correct_answer=q_data.correct_answer,
                    score=q_data.score,
                    analysis=q_data.analysis,
                    options=json.dumps(q_data.options, ensure_ascii=False) if q_data.options else None,
                )
                db.add(new_q)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error(f"更新考试失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="考试更新失败，事务已回滚")
    return {"message": "考试更新成功"}


@router.delete("/exams/{exam_id}")
async def delete_exam(
    exam_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除考试"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    # 先查所有 ExamQuestion.id，按顺序清理关联数据以保护外键
    q_ids_result = await db.execute(select(ExamQuestion.id).where(ExamQuestion.exam_id == exam_id))
    question_ids = [row[0] for row in q_ids_result.all()]
    if question_ids:
        await db.execute(delete(ExamAnswer).where(ExamAnswer.question_id.in_(question_ids)))
    await db.execute(delete(ExamQuestion).where(ExamQuestion.exam_id == exam_id))
    await db.execute(delete(ExamAttempt).where(ExamAttempt.exam_id == exam_id))
    await db.delete(exam)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error(f"删除考试失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="考试删除失败，事务已回滚")
    return {"message": "删除成功"}


@router.put("/exams/{exam_id}/publish")
async def toggle_exam_publish(
    exam_id: int,
    data: AdminExamPublishToggle,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """切换考试发布状态"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    if hasattr(exam, "is_published"):
        exam.is_published = data.is_published if data.is_published is not None else not exam.is_published
        try:
            await db.commit()
        except Exception as e:
            await db.rollback()
            logging.getLogger(__name__).error(f"切换考试发布状态失败: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="操作失败")
    return {"message": "操作成功"}
