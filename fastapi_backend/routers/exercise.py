"""
在线练习路由 - 支持代码执行、真实判题和AI评估
"""
from __future__ import annotations

import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User, Exercise, Submission, Progress, ExerciseSubmissionRecord
from fastapi_backend.schemas.common import SuccessResponse
from fastapi_backend.schemas.exercise import ExerciseSubmission, ExerciseEvaluationResponse
from fastapi_backend.services.ai_tutor_service import AITutorService
from fastapi_backend.services.sandbox_service import CodeSandbox

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/exercise", tags=["在线练习"])


def get_ai_tutor():
    return AITutorService()


def get_sandbox():
    return CodeSandbox()


async def _execute_and_judge(
    sandbox: CodeSandbox,
    language: str,
    source_code: str,
    test_cases: list[dict],
    setup_code: str = "",
) -> dict:
    """
    在沙箱中执行用户代码，逐个测试用例比对输出。
    返回 { total_cases, passed_count, failed_count, pass_rate, all_passed, details }
    """
    results = []
    full_code = ""

    if language == "python":
        if setup_code:
            full_code = setup_code + "\n"
        full_code += source_code

        for i, tc in enumerate(test_cases):
            case_input = tc.get("input", "")
            expected = str(tc.get("expected_output", tc.get("expected", ""))).strip()

            if case_input:
                exec_result = await sandbox.execute_code(
                    code=full_code, language="python",
                    input_data=case_input, timeout=5,
                )
            else:
                exec_result = await sandbox.execute_code(
                    code=full_code, language="python", timeout=5,
                )

            actual = exec_result.get("stdout", "").strip()
            passed = actual == expected
            results.append({
                "case_index": i + 1,
                "passed": passed,
                "expected": expected,
                "actual": actual[:500],
                "error": exec_result.get("stderr", "")[:200] if exec_result.get("stderr") else None,
            })

    elif language == "sql":
        for i, tc in enumerate(test_cases):
            setup_sql = tc.get("setup_sql", setup_code or "")
            user_sql = source_code
            expected = str(tc.get("expected_output", tc.get("expected", ""))).strip()

            combined_sql = ""
            if setup_sql:
                combined_sql = setup_sql + ";\n"
            combined_sql += user_sql

            exec_result = await sandbox.execute_code(
                code=combined_sql, language="sql", timeout=3,
            )

            actual = exec_result.get("stdout", "").strip()
            passed = actual == expected
            results.append({
                "case_index": i + 1,
                "passed": passed,
                "expected": expected,
                "actual": actual[:500],
                "error": exec_result.get("stderr", "")[:200] if exec_result.get("stderr") else None,
            })
    else:
        for i, tc in enumerate(test_cases):
            case_input = tc.get("input", "")
            expected = str(tc.get("expected_output", tc.get("expected", ""))).strip()

            exec_result = await sandbox.execute_code(
                code=source_code, language=language,
                input_data=case_input or None, timeout=5,
            )

            actual = exec_result.get("stdout", "").strip()
            passed = actual == expected
            results.append({
                "case_index": i + 1,
                "passed": passed,
                "expected": expected,
                "actual": actual[:500],
                "error": exec_result.get("stderr", "")[:200] if exec_result.get("stderr") else None,
            })

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    failed_count = total - passed_count
    pass_rate = round(passed_count / total * 100, 1) if total > 0 else 0

    return {
        "total_cases": total,
        "passed_count": passed_count,
        "failed_count": failed_count,
        "pass_rate": pass_rate,
        "all_passed": passed_count == total and total > 0,
        "details": results,
        "summary": f"通过 {passed_count}/{total} 个测试用例",
    }


@router.post("/evaluate", response_model=SuccessResponse[ExerciseEvaluationResponse])
async def evaluate_exercise_code(
    submission: ExerciseSubmission,
    tutor: AITutorService = Depends(get_ai_tutor),
    sandbox: CodeSandbox = Depends(get_sandbox),
):
    """
    接收用户编写的练习代码，在沙箱中真实执行判题，再由 AI 给出评分与建议。
    """
    from fastapi_backend.schemas.interview import CodeSubmission

    code_submission = CodeSubmission(
        question_id=submission.exercise_id,
        language=submission.language,
        source_code=submission.source_code,
    )

    question_prompt = submission.exercise_description
    judge_result = None

    if submission.test_cases:
        try:
            test_cases = json.loads(submission.test_cases) if isinstance(submission.test_cases, str) else submission.test_cases
            if isinstance(test_cases, list) and len(test_cases) > 0:
                judge_result = await _execute_and_judge(
                    sandbox=sandbox,
                    language=submission.language,
                    source_code=submission.source_code,
                    test_cases=test_cases,
                )
        except (json.JSONDecodeError, TypeError):
            pass

    elif submission.expected_output:
        expected = submission.expected_output.strip()
        exec_result = await sandbox.execute_code(
            code=submission.source_code,
            language=submission.language,
            timeout=5,
        )
        actual = exec_result.get("stdout", "").strip()
        passed = actual == expected
        judge_result = {
            "total_cases": 1,
            "passed_count": 1 if passed else 0,
            "failed_count": 0 if passed else 1,
            "pass_rate": 100.0 if passed else 0.0,
            "all_passed": passed,
            "details": [{
                "case_index": 1,
                "passed": passed,
                "expected": expected[:500],
                "actual": actual[:500],
                "error": exec_result.get("stderr", "")[:200] if exec_result.get("stderr") else None,
            }],
            "summary": "通过 1/1 个测试用例" if passed else "未通过测试用例",
        }

    result = await tutor.evaluate_code(
        submission=code_submission,
        question_prompt=question_prompt,
        judge_result=judge_result,
    )

    return SuccessResponse(data=result, message="练习代码评估完成")


@router.post("/submit")
async def submit_exercise(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    sandbox: CodeSandbox = Depends(get_sandbox),
):
    """
    提交习题答案，真实判题并保存提交记录。
    支持：文本题（字符串比对）、代码题（沙箱执行+输出比对）、SQL题（内存SQLite执行+结果比对）
    """
    if not body or "exercise_id" not in body or "solution" not in body:
        raise HTTPException(status_code=400, detail="exercise_id 和 solution 为必填项")

    stmt = select(Exercise).where(Exercise.id == body["exercise_id"])
    result = await db.execute(stmt)
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="习题不存在")

    solution = body["solution"]
    exercise_type = body.get("exercise_type", ex.exercise_type or "text")
    language = body.get("language", ex.language or "python")
    judge_result = None
    is_correct = False

    if exercise_type == "code" or language in ("python", "shell"):
        test_cases_raw = ex.test_cases if ex.test_cases else "[]"
        try:
            test_cases = json.loads(test_cases_raw) if isinstance(test_cases_raw, str) else test_cases_raw
        except (json.JSONDecodeError, TypeError):
            test_cases = []

        if isinstance(test_cases, list) and len(test_cases) > 0:
            judge_result = await _execute_and_judge(
                sandbox=sandbox,
                language=language,
                source_code=solution,
                test_cases=test_cases,
            )
            is_correct = judge_result["all_passed"]
        elif ex.solution:
            exec_result = await sandbox.execute_code(
                code=solution, language=language, timeout=5,
            )
            actual = exec_result.get("stdout", "").strip()
            expected = ex.solution.strip()
            is_correct = actual == expected
            judge_result = {
                "total_cases": 1,
                "passed_count": 1 if is_correct else 0,
                "failed_count": 0 if is_correct else 1,
                "pass_rate": 100.0 if is_correct else 0.0,
                "all_passed": is_correct,
                "details": [{
                    "case_index": 1,
                    "passed": is_correct,
                    "expected": expected[:500],
                    "actual": actual[:500],
                }],
                "summary": "通过" if is_correct else "未通过",
            }
        else:
            exec_result = await sandbox.execute_code(
                code=solution, language=language, timeout=5,
            )
            no_errors = exec_result.get("exit_code", -1) == 0 and not exec_result.get("stderr")
            is_correct = no_errors
            judge_result = {
                "total_cases": 1,
                "passed_count": 1 if no_errors else 0,
                "failed_count": 0 if no_errors else 1,
                "pass_rate": 100.0 if no_errors else 0.0,
                "all_passed": no_errors,
                "details": [],
                "summary": "代码执行成功，无报错" if no_errors else f"代码执行出错: {exec_result.get('stderr', '')[:200]}",
            }

    elif language == "sql":
        setup_sql = ex.test_cases or ""
        expected_output = ex.solution or ""

        combined_sql = ""
        if setup_sql:
            combined_sql = setup_sql + ";\n"
        combined_sql += solution

        exec_result = await sandbox.execute_code(
            code=combined_sql, language="sql", timeout=3,
        )
        actual = exec_result.get("stdout", "").strip()
        expected = expected_output.strip()

        if expected:
            is_correct = actual == expected
        else:
            is_correct = exec_result.get("exit_code", -1) == 0

        judge_result = {
            "total_cases": 1,
            "passed_count": 1 if is_correct else 0,
            "failed_count": 0 if is_correct else 1,
            "pass_rate": 100.0 if is_correct else 0.0,
            "all_passed": is_correct,
            "details": [{
                "case_index": 1,
                "passed": is_correct,
                "expected": expected[:500] if expected else "(无预期输出)",
                "actual": actual[:500],
            }],
            "summary": "SQL 执行结果匹配" if is_correct else "SQL 执行结果不匹配",
        }

    else:
        is_correct = solution.strip() == (ex.solution or "").strip()
        judge_result = {
            "total_cases": 1,
            "passed_count": 1 if is_correct else 0,
            "failed_count": 0 if is_correct else 1,
            "pass_rate": 100.0 if is_correct else 0.0,
            "all_passed": is_correct,
            "details": [],
            "summary": "答案正确" if is_correct else "答案不正确",
        }

    try:
        submission_record = ExerciseSubmissionRecord(
            user_id=current_user.id,
            exercise_id=ex.id,
            code=solution,
            result="pass" if is_correct else "fail",
            score=100 if is_correct else 0,
        )
        db.add(submission_record)

        progress_stmt = select(Progress).where(
            Progress.user_id == current_user.id,
            Progress.exercise_id == ex.id,
        )
        progress_result = await db.execute(progress_stmt)
        progress = progress_result.scalar_one_or_none()

        if progress:
            progress.completed = is_correct
            progress.score = 100 if is_correct else 0
            if is_correct:
                progress.completed_at = datetime.utcnow()
        else:
            progress = Progress(
                user_id=current_user.id,
                exercise_id=ex.id,
                completed=is_correct,
                score=100 if is_correct else 0,
                completed_at=datetime.utcnow() if is_correct else None,
            )
            db.add(progress)

        await db.commit()
    except Exception as e:
        logger.warning(f"保存提交记录失败: {e}")
        await db.rollback()

    skill_change = None
    if is_correct:
        try:
            from fastapi_backend.routers.skills import _calculate_skill_score, SKILL_CATEGORY_MAP, SKILL_DIMENSIONS
            before_scores = {}
            for skill_key in SKILL_CATEGORY_MAP:
                before_scores[skill_key] = await _calculate_skill_score(current_user.id, skill_key, db)

            after_scores = {}
            for skill_key in SKILL_CATEGORY_MAP:
                after_scores[skill_key] = await _calculate_skill_score(current_user.id, skill_key, db)

            changes = []
            for skill_key in SKILL_CATEGORY_MAP:
                diff = after_scores[skill_key] - before_scores[skill_key]
                if diff > 0:
                    changes.append({
                        "key": skill_key,
                        "name": SKILL_DIMENSIONS[skill_key]["name"],
                        "before": before_scores[skill_key],
                        "after": after_scores[skill_key],
                        "change": diff,
                    })

            if changes:
                skill_change = changes
        except Exception as e:
            logger.warning(f"计算技能分数变化失败: {e}")

    return {
        "correct": is_correct,
        "judge_result": judge_result,
        "message": "答案正确！" if is_correct else "答案不正确，请再试试",
        "expected_solution": ex.solution if is_correct else None,
        "skill_change": skill_change,
    }


@router.get("/progress")
async def get_exercise_progress(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户所有习题的完成进度"""
    stmt = select(Progress).where(Progress.user_id == current_user.id)
    result = await db.execute(stmt)
    progresses = result.scalars().all()

    progress_map = {}
    for p in progresses:
        progress_map[p.exercise_id] = {
            "completed": p.completed or False,
            "score": p.score,
            "attempts": p.attempts or 0,
        }

    return {"progress": progress_map}


@router.get("/recent-activity")
async def get_recent_activity(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户最近的学习活动"""
    sub_stmt = (
        select(ExerciseSubmissionRecord)
        .where(ExerciseSubmissionRecord.user_id == current_user.id)
        .order_by(ExerciseSubmissionRecord.created_at.desc())
        .limit(10)
    )
    sub_result = await db.execute(sub_stmt)
    submissions = sub_result.scalars().all()

    exercise_ids = list({s.exercise_id for s in submissions})
    exercise_map = {}
    if exercise_ids:
        ex_stmt = select(Exercise).where(Exercise.id.in_(exercise_ids))
        ex_result = await db.execute(ex_stmt)
        for ex in ex_result.scalars().all():
            exercise_map[ex.id] = ex.title

    activities = []
    for s in submissions:
        activities.append({
            "id": s.id,
            "type": "exercise_submit",
            "exercise_id": s.exercise_id,
            "exercise_title": exercise_map.get(s.exercise_id, f"习题#{s.exercise_id}"),
            "result": s.result,
            "score": s.score,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "",
        })

    return {"activities": activities}


@router.get("/wrong-answers")
async def get_wrong_answers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的错题本"""
    wrong_stmt = (
        select(ExerciseSubmissionRecord)
        .where(
            ExerciseSubmissionRecord.user_id == current_user.id,
            ExerciseSubmissionRecord.result == "fail",
        )
        .order_by(ExerciseSubmissionRecord.created_at.desc())
    )
    wrong_result = await db.execute(wrong_stmt)
    wrong_submissions = wrong_result.scalars().all()

    wrong_exercise_ids = list({s.exercise_id for s in wrong_submissions})

    later_correct_stmt = (
        select(ExerciseSubmissionRecord)
        .where(
            ExerciseSubmissionRecord.user_id == current_user.id,
            ExerciseSubmissionRecord.result == "pass",
        )
    )
    later_correct_result = await db.execute(later_correct_stmt)
    later_correct_ids = {s.exercise_id for s in later_correct_result.scalars().all()}

    still_wrong_ids = [eid for eid in wrong_exercise_ids if eid not in later_correct_ids]
    mastered_ids = [eid for eid in wrong_exercise_ids if eid in later_correct_ids]

    all_ids = wrong_exercise_ids
    exercise_map = {}
    if all_ids:
        ex_stmt = select(Exercise).where(Exercise.id.in_(all_ids))
        ex_result = await db.execute(ex_stmt)
        for ex in ex_result.scalars().all():
            exercise_map[ex.id] = {
                "id": ex.id,
                "title": ex.title,
                "difficulty": ex.difficulty,
                "category": ex.category,
                "knowledge_point": ex.knowledge_point,
                "stage": ex.stage,
            }

    wrong_list = []
    for eid in still_wrong_ids:
        info = exercise_map.get(eid, {})
        subs = [s for s in wrong_submissions if s.exercise_id == eid]
        latest = subs[0] if subs else None
        wrong_list.append({
            **info,
            "status": "wrong",
            "wrong_count": len(subs),
            "last_wrong_at": latest.created_at.strftime("%Y-%m-%d %H:%M") if latest and latest.created_at else "",
        })

    mastered_list = []
    for eid in mastered_ids:
        info = exercise_map.get(eid, {})
        mastered_list.append({
            **info,
            "status": "mastered",
        })

    return {
        "wrong_answers": wrong_list,
        "mastered": mastered_list,
        "wrong_count": len(still_wrong_ids),
        "mastered_count": len(mastered_ids),
    }


@router.get("/daily-tasks")
async def get_daily_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取今日任务和完成情况"""
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    today_submissions_stmt = select(ExerciseSubmissionRecord).where(
        ExerciseSubmissionRecord.user_id == current_user.id,
        ExerciseSubmissionRecord.created_at >= today_start,
    )
    today_result = await db.execute(today_submissions_stmt)
    today_submissions = today_result.scalars().all()

    today_correct = sum(1 for s in today_submissions if s.result == "pass")
    today_total = len(today_submissions)

    progress_stmt = select(Progress).where(
        Progress.user_id == current_user.id,
        Progress.completed == True,  # noqa: E712
    )
    progress_result = await db.execute(progress_stmt)
    total_completed = len(progress_result.scalars().all())

    checkin_today = False
    try:
        from fastapi_backend.models.models import DailyCheckin
        checkin_stmt = select(DailyCheckin).where(
            DailyCheckin.user_id == current_user.id,
            DailyCheckin.checkin_date >= today_start,
        )
        checkin_result = await db.execute(checkin_stmt)
        checkin_today = checkin_result.scalar_one_or_none() is not None
    except Exception:
        pass

    tasks = [
        {
            "id": "checkin",
            "title": "每日签到",
            "description": "签到获取经验，连续签到奖励更多",
            "icon": "📅",
            "completed": checkin_today,
            "target": 1,
            "progress": 1 if checkin_today else 0,
            "reward": "5~20经验",
        },
        {
            "id": "exercise_3",
            "title": "完成3道习题",
            "description": "每天坚持练习，稳步提升技能",
            "icon": "✏️",
            "completed": today_correct >= 3,
            "target": 3,
            "progress": min(today_correct, 3),
            "reward": "技能分数提升",
        },
        {
            "id": "exercise_5",
            "title": "完成5道习题",
            "description": "挑战更多习题，加速成长",
            "icon": "🔥",
            "completed": today_correct >= 5,
            "target": 5,
            "progress": min(today_correct, 5),
            "reward": "成就进度推进",
        },
        {
            "id": "review_wrong",
            "title": "复习1道错题",
            "description": "回顾错题，避免重复犯错",
            "icon": "📖",
            "completed": False,
            "target": 1,
            "progress": 0,
            "reward": "知识巩固",
        },
    ]

    completed_count = sum(1 for t in tasks if t["completed"])

    return {
        "tasks": tasks,
        "completed_count": completed_count,
        "total_count": len(tasks),
        "today_correct": today_correct,
        "today_total": today_total,
        "total_completed": total_completed,
    }


@router.get("/{exercise_id}/related")
async def get_related_exercises(
    exercise_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取与指定习题相关的推荐习题"""
    ex_stmt = select(Exercise).where(Exercise.id == exercise_id)
    ex_result = await db.execute(ex_stmt)
    exercise = ex_result.scalar_one_or_none()

    if not exercise:
        return {"related": []}

    conditions = []
    if exercise.category:
        conditions.append(Exercise.category == exercise.category)
    if exercise.knowledge_point:
        conditions.append(Exercise.knowledge_point == exercise.knowledge_point)
    if exercise.stage:
        conditions.append(Exercise.stage == exercise.stage)

    if conditions:
        related_stmt = (
            select(Exercise)
            .where(
                Exercise.id != exercise_id,
                Exercise.is_public == True,  # noqa: E712
                or_(*conditions),
            )
            .order_by(Exercise.stage, Exercise.difficulty)
            .limit(6)
        )
    else:
        related_stmt = (
            select(Exercise)
            .where(
                Exercise.id != exercise_id,
                Exercise.is_public == True,  # noqa: E712
            )
            .order_by(Exercise.stage, Exercise.difficulty)
            .limit(6)
        )
    related_result = await db.execute(related_stmt)
    related = related_result.scalars().all()

    progress_stmt = select(Progress).where(
        Progress.user_id == current_user.id,
    )
    progress_result = await db.execute(progress_stmt)
    completed_ids = {p.exercise_id for p in progress_result.scalars().all() if p.completed}

    related_list = []
    for r in related:
        related_list.append({
            "id": r.id,
            "title": r.title,
            "difficulty": r.difficulty,
            "category": r.category,
            "knowledge_point": r.knowledge_point,
            "stage": r.stage,
            "completed": r.id in completed_ids,
        })

    return {"related": related_list}
