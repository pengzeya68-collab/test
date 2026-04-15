"""Exam system router – migrated from Flask backend/api/exam.py."""
from __future__ import annotations

import json
import random
import re
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user, require_admin
from fastapi_backend.models.models import (
    Exam,
    ExamAnswer,
    ExamAttempt,
    ExamQuestion,
    Exercise,
    User,
)
from fastapi_backend.schemas.exam import (
    ExamGenerateRequest,
    ExamSubmitRequest,
    ExamBrief,
    ExamListResponse,
    ExamDetailResponse,
    ExamStartResponse,
    ExamSubmitResponse,
    ExamResultResponse,
    MyAttemptsResponse,
    AttemptBrief,
    AuthorBrief,
    QuestionBrief,
    AnswerResult,
    AttemptInfo,
    ExamGenerateResponse,
)

router = APIRouter(prefix="/api/v1/exams", tags=["exams"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt_exam(exam: Exam, user_id: int | None = None) -> dict:
    data = {
        "id": exam.id,
        "title": exam.title,
        "description": exam.description,
        "exam_type": exam.exam_type,
        "difficulty": exam.difficulty,
        "duration": exam.duration,
        "total_score": exam.total_score,
        "pass_score": exam.pass_score,
        "is_published": exam.is_published,
        "start_time": exam.start_time.strftime("%Y-%m-%d %H:%M:%S") if exam.start_time else None,
        "end_time": exam.end_time.strftime("%Y-%m-%d %H:%M:%S") if exam.end_time else None,
        "created_at": exam.created_at.strftime("%Y-%m-%d %H:%M:%S") if exam.created_at else None,
        "question_count": len(exam.questions) if exam.questions else 0,
        "author": {
            "id": exam.user.id if exam.user else 0,
            "username": exam.user.username if exam.user else "unknown",
        },
    }
    # The caller may attach attempt info separately
    if hasattr(exam, "_attempt_status"):
        data["attempt_status"] = exam._attempt_status
        data["attempt_score"] = exam._attempt_score
        data["attempt_id"] = exam._attempt_id
    return data


def _fmt_question(q: ExamQuestion, show_answer: bool = False) -> dict:
    data = {
        "id": q.id,
        "question_type": q.question_type,
        "content": q.content,
        "score": q.score,
        "sort_order": q.sort_order,
    }
    if q.question_type in ("single_choice", "multiple_choice"):
        try:
            data["options"] = json.loads(q.options) if q.options else []
        except (json.JSONDecodeError, TypeError):
            data["options"] = []
    if show_answer:
        data["correct_answer"] = q.correct_answer
        data["analysis"] = q.analysis
    return data


def _simple_code_scoring(user_code: str, correct_answer: str | None, question_score: int) -> tuple[int, bool, str]:
    if not user_code:
        return 0, False, "未提交代码"

    user_normalized = "".join(user_code.split()).lower()
    score_ratio = 0.1  # base: just having code

    if correct_answer:
        func_pattern = r"def\s+(\w+)\s*\("
        correct_funcs = set(re.findall(func_pattern, correct_answer))
        user_funcs = set(re.findall(func_pattern, user_code))
        if correct_funcs and user_funcs:
            common = correct_funcs.intersection(user_funcs)
            score_ratio += 0.3 * (len(common) / len(correct_funcs))

        len_ratio = len(user_code) / len(correct_answer) if correct_answer else 0
        if 0.5 <= len_ratio <= 2.0:
            score_ratio += 0.2

        syntax_errors = ["syntax error", "indentationerror", "nameerror"]
        if not any(err in user_code.lower() for err in syntax_errors):
            score_ratio += 0.2

        correct_kw = set(re.findall(r"\b\w+\b", correct_answer.lower()))
        user_kw = set(re.findall(r"\b\w+\b", user_code.lower()))
        if correct_kw:
            score_ratio += 0.2 * (len(correct_kw.intersection(user_kw)) / len(correct_kw))

    score_ratio = min(1.0, max(0, score_ratio))
    score = int(question_score * score_ratio)
    is_correct = score >= question_score * 0.6
    return score, is_correct, f"代码相似度评分: {score_ratio * 100:.1f}%"


async def _calculate_score(attempt: ExamAttempt, db: AsyncSession) -> int:
    """Auto-grade all answers for an attempt."""
    total_score = 0
    ans_stmt = select(ExamAnswer).where(ExamAnswer.attempt_id == attempt.id)
    ans_result = await db.execute(ans_stmt)
    answers = ans_result.scalars().all()

    for answer in answers:
        q_stmt = select(ExamQuestion).where(ExamQuestion.id == answer.question_id)
        q_result = await db.execute(q_stmt)
        question = q_result.scalar_one_or_none()
        if not question:
            continue

        if question.question_type in ("single_choice", "multiple_choice", "true_false"):
            if answer.user_answer == question.correct_answer:
                answer.is_correct = True
                answer.score = question.score
                total_score += question.score
            else:
                answer.is_correct = False
                answer.score = 0
        elif question.question_type == "code":
            user_code = answer.user_answer or ""
            if not user_code:
                answer.is_correct = False
                answer.score = 0
            else:
                # Try test-case-based judging first (simplified – no sandbox here)
                if question.test_cases:
                    # For now, fall back to simple scoring.
                    # Full sandbox integration should use sandbox_service later.
                    try:
                        answer.score, answer.is_correct, answer.feedback = _simple_code_scoring(
                            user_code, question.correct_answer, question.score
                        )
                    except Exception as e:
                        answer.score, answer.is_correct, answer.feedback = _simple_code_scoring(
                            user_code, question.correct_answer, question.score
                        )
                        answer.feedback = (answer.feedback or "") + f" (判题异常: {e})"
                else:
                    answer.score, answer.is_correct, answer.feedback = _simple_code_scoring(
                        user_code, question.correct_answer, question.score
                    )
                total_score += answer.score
        else:
            answer.is_correct = None
            answer.score = 0

    # Update attempt
    exam_stmt = select(Exam).where(Exam.id == attempt.exam_id)
    exam_result = await db.execute(exam_stmt)
    exam = exam_result.scalar_one_or_none()

    attempt.score = total_score
    attempt.is_passed = total_score >= (exam.pass_score if exam else 60)
    attempt.status = "graded"
    await db.commit()
    return total_score


def _parse_options_from_content(content: str | None) -> list[str]:
    if not content:
        return ["选项A", "选项B", "选项C", "选项D"]
    options = []
    for line in content.split("\n"):
        line = line.strip()
        if line and line[0] in "ABCDEF" and len(line) > 1 and line[1] in ".。、)] ":
            text = line[2:].strip()
            if text:
                options.append(text)
    return options if len(options) >= 2 else ["选项A", "选项B", "选项C", "选项D"]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("", response_model=ExamListResponse)
async def get_exams(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    type: str = Query(""),
    difficulty: str = Query(""),
    search: str = Query(""),
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取考试列表"""
    stmt = select(Exam).where(Exam.is_published == True).options(selectinload(Exam.user), selectinload(Exam.questions))  # noqa: E712

    if type:
        stmt = stmt.where(Exam.exam_type == type)
    if difficulty:
        stmt = stmt.where(Exam.difficulty == difficulty)
    if search:
        stmt = stmt.where(or_(Exam.title.contains(search), Exam.description.contains(search)))

    stmt = stmt.order_by(Exam.created_at.desc())

    # Count total
    count_stmt = select(func.count()).select_from(Exam).where(Exam.is_published == True)  # noqa: E712
    if type:
        count_stmt = count_stmt.where(Exam.exam_type == type)
    if difficulty:
        count_stmt = count_stmt.where(Exam.difficulty == difficulty)
    if search:
        count_stmt = count_stmt.where(or_(Exam.title.contains(search), Exam.description.contains(search)))
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = stmt.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    exams = result.scalars().all()

    user_id = current_user.id if current_user else None
    items = []
    for exam in exams:
        d = _fmt_exam(exam, user_id)
        if user_id:
            att_stmt = select(ExamAttempt).where(
                ExamAttempt.user_id == user_id, ExamAttempt.exam_id == exam.id
            ).order_by(ExamAttempt.created_at.desc()).limit(1)
            att_result = await db.execute(att_stmt)
            att = att_result.scalar_one_or_none()
            if att:
                d["attempt_status"] = att.status
                d["attempt_score"] = att.score
                d["attempt_id"] = att.id
        items.append(d)

    return ExamListResponse(list=items, total=total, page=page, per_page=per_page)


@router.get("/{exam_id}")
async def get_exam_detail(
    exam_id: int,
    current_user: Optional[User] = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取考试详情（包含题目列表）"""
    stmt = select(Exam).where(Exam.id == exam_id).options(selectinload(Exam.user), selectinload(Exam.questions))
    result = await db.execute(stmt)
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not exam.is_published:
        raise HTTPException(status_code=403, detail="考试未发布")

    user_id = current_user.id if current_user else None
    data = _fmt_exam(exam, user_id)

    if user_id:
        att_stmt = select(ExamAttempt).where(
            ExamAttempt.user_id == user_id, ExamAttempt.exam_id == exam_id
        ).order_by(ExamAttempt.created_at.desc()).limit(1)
        att_result = await db.execute(att_stmt)
        att = att_result.scalar_one_or_none()
        if att:
            data["attempt_status"] = att.status
            data["attempt_score"] = att.score
            data["attempt_id"] = att.id

    questions = sorted(exam.questions, key=lambda q: q.sort_order)
    data["questions"] = [_fmt_question(q) for q in questions]
    return data


@router.delete("/{exam_id}")
async def delete_exam(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除考试"""
    stmt = select(Exam).where(Exam.id == exam_id)
    result = await db.execute(stmt)
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if exam.user_id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限删除此考试")

    # Check for in-progress attempts
    att_stmt = select(ExamAttempt).where(ExamAttempt.exam_id == exam_id, ExamAttempt.status == "in_progress")
    att_result = await db.execute(att_stmt)
    if att_result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="有用户正在进行此考试，无法删除")

    # Delete answers, attempts, questions, exam
    attempt_ids_stmt = select(ExamAttempt.id).where(ExamAttempt.exam_id == exam_id)
    attempt_ids_result = await db.execute(attempt_ids_stmt)
    attempt_ids = [row[0] for row in attempt_ids_result.all()]

    if attempt_ids:
        await db.execute(delete(ExamAnswer).where(ExamAnswer.attempt_id.in_(attempt_ids)))
    await db.execute(delete(ExamAttempt).where(ExamAttempt.exam_id == exam_id))
    await db.execute(delete(ExamQuestion).where(ExamQuestion.exam_id == exam_id))
    await db.execute(delete(Exam).where(Exam.id == exam_id))
    await db.commit()
    return {"message": "考试删除成功"}


@router.get("/{exam_id}/questions", response_model=ExamStartResponse)
async def get_exam_questions(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取考试题目（开始考试）"""
    stmt = select(Exam).where(Exam.id == exam_id).options(selectinload(Exam.user), selectinload(Exam.questions))
    result = await db.execute(stmt)
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")
    if not exam.is_published:
        raise HTTPException(status_code=403, detail="考试未发布")

    now = datetime.utcnow()
    if exam.start_time and now < exam.start_time:
        raise HTTPException(status_code=403, detail="考试尚未开始")
    if exam.end_time and now > exam.end_time:
        raise HTTPException(status_code=403, detail="考试已结束")

    user_id = current_user.id

    # Check for existing in-progress attempt
    att_stmt = select(ExamAttempt).where(
        ExamAttempt.user_id == user_id, ExamAttempt.exam_id == exam_id, ExamAttempt.status == "in_progress"
    )
    att_result = await db.execute(att_stmt)
    existing = att_result.scalar_one_or_none()

    if existing:
        attempt_id = existing.id
    else:
        attempt = ExamAttempt(user_id=user_id, exam_id=exam_id, start_time=now)
        db.add(attempt)
        await db.commit()
        await db.refresh(attempt)
        attempt_id = attempt.id

    questions = sorted(exam.questions, key=lambda q: q.sort_order)
    return ExamStartResponse(
        attempt_id=attempt_id,
        exam=ExamBrief(**_fmt_exam(exam)),
        questions=[QuestionBrief(**_fmt_question(q)) for q in questions],
    )


@router.post("/attempts/{attempt_id}/submit", response_model=ExamSubmitResponse)
async def submit_exam(
    attempt_id: int,
    body: ExamSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交考试"""
    stmt = select(ExamAttempt).where(ExamAttempt.id == attempt_id)
    result = await db.execute(stmt)
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="考试记录不存在")
    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限操作此考试")
    if attempt.status != "in_progress":
        raise HTTPException(status_code=400, detail="考试已经提交过了")

    # Save answers
    for ans in body.answers:
        answer = ExamAnswer(
            attempt_id=attempt_id,
            question_id=ans.question_id,
            user_answer=ans.answer,
        )
        db.add(answer)

    attempt.end_time = datetime.utcnow()
    attempt.status = "submitted"
    await db.commit()

    # Auto-grade
    total_score = await _calculate_score(attempt, db)
    return ExamSubmitResponse(
        message="考试提交成功",
        score=total_score,
        is_passed=attempt.is_passed,
        attempt_id=attempt_id,
    )


@router.get("/attempts/{attempt_id}/result")
async def get_exam_result(
    attempt_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取考试结果"""
    stmt = select(ExamAttempt).where(ExamAttempt.id == attempt_id)
    result = await db.execute(stmt)
    attempt = result.scalar_one_or_none()
    if not attempt:
        raise HTTPException(status_code=404, detail="考试记录不存在")
    if attempt.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权限查看此考试结果")
    if attempt.status == "in_progress":
        raise HTTPException(status_code=400, detail="考试尚未提交")

    # Get answers
    ans_stmt = select(ExamAnswer).where(ExamAnswer.attempt_id == attempt_id)
    ans_result = await db.execute(ans_stmt)
    answers = ans_result.scalars().all()

    result_items = []
    for ans in answers:
        q_stmt = select(ExamQuestion).where(ExamQuestion.id == ans.question_id)
        q_result = await db.execute(q_stmt)
        question = q_result.scalar_one_or_none()
        if not question:
            continue
        result_items.append(
            AnswerResult(
                question=QuestionBrief(**_fmt_question(question, show_answer=True)),
                user_answer=ans.user_answer,
                is_correct=ans.is_correct,
                score=ans.score,
                feedback=ans.feedback,
            ).model_dump()
        )

    # Get exam for formatting
    exam_stmt = select(Exam).where(Exam.id == attempt.exam_id).options(selectinload(Exam.user), selectinload(Exam.questions))
    exam_result = await db.execute(exam_stmt)
    exam = exam_result.scalar_one_or_none()

    duration_min = None
    if attempt.start_time and attempt.end_time:
        duration_min = int((attempt.end_time - attempt.start_time).total_seconds() / 60)

    # Statistics
    question_types: dict = {}
    for item in result_items:
        q_type = item["question"]["question_type"]
        if q_type not in question_types:
            question_types[q_type] = {"total": 0, "correct": 0, "score": 0, "total_score": 0}
        question_types[q_type]["total"] += 1
        question_types[q_type]["total_score"] += item["question"]["score"]
        if item["is_correct"]:
            question_types[q_type]["correct"] += 1
        question_types[q_type]["score"] += item["score"] or 0

    correct_count = sum(1 for i in result_items if i["is_correct"])
    score_rate = round(attempt.score / exam.total_score * 100, 1) if exam and exam.total_score > 0 else 0

    return {
        "exam": _fmt_exam(exam) if exam else {},
        "attempt": {
            "id": attempt.id,
            "start_time": attempt.start_time.strftime("%Y-%m-%d %H:%M:%S") if attempt.start_time else None,
            "end_time": attempt.end_time.strftime("%Y-%m-%d %H:%M:%S") if attempt.end_time else None,
            "duration": duration_min,
            "score": attempt.score,
            "is_passed": attempt.is_passed,
            "status": attempt.status,
        },
        "result": result_items,
        "statistics": {
            "total_questions": len(result_items),
            "correct_count": correct_count,
            "wrong_count": len(result_items) - correct_count,
            "score_rate": score_rate,
            "question_type_stats": question_types,
        },
    }


@router.get("/my-attempts", response_model=MyAttemptsResponse)
async def get_my_attempts(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取我的考试记录"""
    user_id = current_user.id

    count_stmt = select(func.count()).select_from(ExamAttempt).where(ExamAttempt.user_id == user_id)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar() or 0

    stmt = (
        select(ExamAttempt)
        .where(ExamAttempt.user_id == user_id)
        .order_by(ExamAttempt.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
        .options(selectinload(ExamAttempt.exam))
    )
    result = await db.execute(stmt)
    attempts = result.scalars().all()

    items = []
    for att in attempts:
        items.append(
            AttemptBrief(
                id=att.id,
                exam_title=att.exam.title if att.exam else "未知",
                exam_type=att.exam.exam_type if att.exam else "",
                score=att.score,
                total_score=att.exam.total_score if att.exam else 0,
                is_passed=att.is_passed,
                status=att.status,
                created_at=att.created_at.strftime("%Y-%m-%d %H:%M:%S") if att.created_at else "",
            )
        )

    return MyAttemptsResponse(list=items, total=total, page=page, per_page=per_page)


@router.post("/generate", response_model=ExamGenerateResponse)
async def generate_exam(
    body: ExamGenerateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """智能生成试卷"""
    user_id = current_user.id
    questions_data = []
    total_score = 0
    used_ids: set[int] = set()

    difficulty = body.difficulty

    # Single choice
    sc_count = body.question_count.get("single_choice", 0)
    if sc_count > 0:
        stmt = select(Exercise).where(
            Exercise.exercise_type == "multiple_choice",
            Exercise.difficulty == difficulty,
            Exercise.is_public == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        all_mc = result.scalars().all()
        single_choices = [
            e for e in all_mc
            if e.solution and len(e.solution.strip()) == 1 and e.solution.strip() in "ABCDEF"
        ]
        if len(single_choices) > sc_count:
            single_choices = random.sample(single_choices, sc_count)
        for q in single_choices:
            used_ids.add(q.id)
            options = _parse_options_from_content(q.description)
            questions_data.append({
                "type": "single_choice",
                "content": q.title,
                "options": json.dumps(options),
                "correct_answer": q.solution.strip().upper(),
                "score": 2,
                "analysis": q.description,
            })
            total_score += 2

    # Multiple choice
    mc_count = body.question_count.get("multiple_choice", 0)
    if mc_count > 0:
        stmt = select(Exercise).where(
            Exercise.exercise_type == "multiple_choice",
            Exercise.difficulty == difficulty,
            Exercise.is_public == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        all_mc = result.scalars().all()
        multi_choices = [
            e for e in all_mc
            if e.solution and ("," in e.solution or len(e.solution.strip()) > 1) and e.id not in used_ids
        ]
        if len(multi_choices) > mc_count:
            multi_choices = random.sample(multi_choices, mc_count)
        for q in multi_choices:
            used_ids.add(q.id)
            options = _parse_options_from_content(q.description)
            answer = q.solution.strip().upper()
            if "," in answer:
                answer = ",".join(a.strip() for a in answer.split(","))
            questions_data.append({
                "type": "multiple_choice",
                "content": q.title,
                "options": json.dumps(options),
                "correct_answer": answer,
                "score": 4,
                "analysis": q.description,
            })
            total_score += 4

    # True/False
    tf_count = body.question_count.get("true_false", 0)
    if tf_count > 0:
        stmt = select(Exercise).where(
            Exercise.exercise_type == "true_false",
            Exercise.difficulty == difficulty,
            Exercise.is_public == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        all_tf = [e for e in result.scalars().all() if e.id not in used_ids]
        if len(all_tf) > tf_count:
            all_tf = random.sample(all_tf, tf_count)
        for q in all_tf:
            used_ids.add(q.id)
            ans = q.solution.strip().lower() if q.solution else "false"
            if ans in ("true", "t", "yes", "y", "正确", "对", "是"):
                ans = "true"
            else:
                ans = "false"
            questions_data.append({
                "type": "true_false",
                "content": q.title,
                "correct_answer": ans,
                "score": 2,
                "analysis": q.description,
            })
            total_score += 2

    # Code questions
    code_count = body.question_count.get("code", 0)
    if code_count > 0:
        stmt = select(Exercise).where(
            Exercise.exercise_type == "code",
            Exercise.difficulty == difficulty,
            Exercise.is_public == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        all_code = [e for e in result.scalars().all() if e.id not in used_ids]
        if len(all_code) > code_count:
            all_code = random.sample(all_code, code_count)
        for q in all_code:
            used_ids.add(q.id)
            questions_data.append({
                "type": "code",
                "content": q.title + "\n\n" + (q.description or ""),
                "correct_answer": q.solution or "",
                "score": 20,
                "analysis": q.description,
                "test_cases": q.test_cases or "",
            })
            total_score += 20

    total_needed = sum(body.question_count.values())
    if len(questions_data) < total_needed * 0.5:
        raise HTTPException(
            status_code=400,
            detail=f"题库中{difficulty}难度的题目不足，请尝试其他难度或联系管理员添加更多题目",
        )

    # Create exam
    sc_n = sum(1 for q in questions_data if q["type"] == "single_choice")
    mc_n = sum(1 for q in questions_data if q["type"] == "multiple_choice")
    tf_n = sum(1 for q in questions_data if q["type"] == "true_false")
    code_n = sum(1 for q in questions_data if q["type"] == "code")

    exam = Exam(
        title=f"{difficulty}难度{body.exam_type}",
        description=f"自动生成的{difficulty}难度{body.exam_type}，包含{len(questions_data)}道题"
                    f"（单选{sc_n}道、多选{mc_n}道、判断{tf_n}道、代码{code_n}道）",
        exam_type=body.exam_type,
        difficulty=difficulty,
        duration=body.duration,
        total_score=total_score,
        pass_score=int(total_score * 0.6),
        is_published=True,
        user_id=user_id,
    )
    db.add(exam)
    await db.flush()

    for idx, q in enumerate(questions_data):
        eq = ExamQuestion(
            exam_id=exam.id,
            question_type=q["type"],
            content=q["content"],
            options=q.get("options"),
            correct_answer=q["correct_answer"],
            score=q["score"],
            analysis=q.get("analysis"),
            test_cases=q.get("test_cases", ""),
            sort_order=idx,
        )
        db.add(eq)

    await db.commit()
    await db.refresh(exam)

    # Load relationships for formatting
    stmt = select(Exam).where(Exam.id == exam.id).options(selectinload(Exam.user), selectinload(Exam.questions))
    result = await db.execute(stmt)
    exam = result.scalar_one()

    return ExamGenerateResponse(
        message="试卷生成成功",
        exam_id=exam.id,
        exam=ExamBrief(**_fmt_exam(exam)),
    )


@router.get("/{exam_id}/analysis")
async def get_exam_analysis(
    exam_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取考试分析数据"""
    user_id = current_user.id

    stmt = select(Exam).where(Exam.id == exam_id).options(selectinload(Exam.user))
    result = await db.execute(stmt)
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    if exam.user_id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="无权限查看考试分析")

    # Get all attempts
    att_stmt = select(ExamAttempt).where(ExamAttempt.exam_id == exam_id)
    att_result = await db.execute(att_stmt)
    attempts = att_result.scalars().all()

    if not attempts:
        raise HTTPException(status_code=404, detail="暂无考试记录")

    # Score distribution
    score_dist = {"0-20%": 0, "21-40%": 0, "41-60%": 0, "61-80%": 0, "81-100%": 0}
    for att in attempts:
        if att.score is None:
            continue
        pct = (att.score / exam.total_score * 100) if exam.total_score > 0 else 0
        if pct <= 20:
            score_dist["0-20%"] += 1
        elif pct <= 40:
            score_dist["21-40%"] += 1
        elif pct <= 60:
            score_dist["41-60%"] += 1
        elif pct <= 80:
            score_dist["61-80%"] += 1
        else:
            score_dist["81-100%"] += 1

    # Questions
    q_stmt = select(ExamQuestion).where(ExamQuestion.exam_id == exam_id).order_by(ExamQuestion.sort_order)
    q_result = await db.execute(q_stmt)
    questions = q_result.scalars().all()

    # All answers
    attempt_ids = [a.id for a in attempts]
    all_answers = []
    if attempt_ids:
        aa_stmt = select(ExamAnswer).where(ExamAnswer.attempt_id.in_(attempt_ids))
        aa_result = await db.execute(aa_stmt)
        all_answers = aa_result.scalars().all()

    # Question pass rate
    question_pass_rate = []
    for question in questions:
        q_answers = [a for a in all_answers if a.question_id == question.id]
        if not q_answers:
            continue
        correct_count = sum(1 for a in q_answers if a.is_correct)
        total_count = len(q_answers)
        pass_rate = (correct_count / total_count * 100) if total_count > 0 else 0
        question_pass_rate.append({
            "question_id": question.id,
            "sort_order": question.sort_order,
            "content": question.content[:100],
            "pass_rate": round(pass_rate, 1),
            "correct_count": correct_count,
            "total_count": total_count,
        })

    # Wrong question ranking
    wrong_ranking = []
    for rd in question_pass_rate:
        if rd["total_count"] > 0:
            wrong_ranking.append({
                "question_id": rd["question_id"],
                "sort_order": rd["sort_order"],
                "content": rd["content"],
                "error_rate": 100 - rd["pass_rate"],
                "correct_count": rd["correct_count"],
                "total_count": rd["total_count"],
            })
    wrong_ranking.sort(key=lambda x: x["error_rate"], reverse=True)

    # Question type stats
    qt_stats: dict = {}
    for question in questions:
        q_type = question.question_type
        if q_type not in qt_stats:
            qt_stats[q_type] = {"total": 0, "correct": 0, "total_score": 0, "score": 0}
        q_answers = [a for a in all_answers if a.question_id == question.id]
        qt_stats[q_type]["total"] += 1
        qt_stats[q_type]["total_score"] += question.score
        for a in q_answers:
            if a.is_correct:
                qt_stats[q_type]["correct"] += 1
            qt_stats[q_type]["score"] += (a.score or 0)

    for q_type, stats in qt_stats.items():
        if stats["total"] > 0:
            stats["pass_rate"] = round((stats["correct"] / stats["total"]) * 100, 1)
            stats["avg_score"] = round(stats["score"] / stats["total"], 1)
        else:
            stats["pass_rate"] = 0
            stats["avg_score"] = 0

    # Overall stats
    total_attempts = len(attempts)
    valid_scores = [a.score for a in attempts if a.score is not None]
    if valid_scores:
        avg_score = sum(valid_scores) / len(valid_scores)
        sorted_scores = sorted(valid_scores)
        n = len(sorted_scores)
        median_score = sorted_scores[n // 2] if n % 2 == 1 else (sorted_scores[n // 2 - 1] + sorted_scores[n // 2]) / 2
    else:
        avg_score = 0
        median_score = None

    pass_rate_val = (sum(1 for a in attempts if a.is_passed) / total_attempts * 100) if total_attempts > 0 else 0

    avg_time = 0
    time_entries = [
        (a.end_time - a.start_time).total_seconds() / 60
        for a in attempts if a.end_time and a.start_time
    ]
    if time_entries:
        avg_time = round(sum(time_entries) / len(time_entries), 1)

    return {
        "analysis": {
            "exam": {
                "id": exam.id,
                "title": exam.title,
                "total_attempts": total_attempts,
                "pass_rate": round(pass_rate_val, 1),
                "average_score": round(avg_score, 1),
                "total_score": exam.total_score,
            },
            "score_distribution": {
                "ranges": list(score_dist.keys()),
                "counts": list(score_dist.values()),
                "percentages": [round(c / total_attempts * 100, 1) for c in score_dist.values()],
            },
            "question_pass_rate": sorted(question_pass_rate, key=lambda x: x["sort_order"]),
            "wrong_question_ranking": wrong_ranking[:10],
            "statistics": {
                "score_summary": {
                    "min_score": min(valid_scores) if valid_scores else 0,
                    "max_score": max(valid_scores) if valid_scores else 0,
                    "avg_score": round(avg_score, 1),
                    "median_score": round(median_score, 1) if median_score is not None else None,
                    "passed_count": sum(1 for a in attempts if a.is_passed),
                    "failed_count": sum(1 for a in attempts if not a.is_passed),
                    "avg_time_minutes": avg_time,
                },
                "question_analysis": {
                    "total_questions": len(questions),
                    "average_pass_rate": round(
                        sum(r["pass_rate"] for r in question_pass_rate) / len(question_pass_rate)
                        if question_pass_rate else 0, 1
                    ),
                    "top_wrong_questions": wrong_ranking[:5],
                },
                "question_type_stats": qt_stats,
            },
        },
        "message": "考试分析获取成功",
    }
