"""
在线练习路由 - 支持代码执行、真实判题和AI评估
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import (
    User,
    Exercise,
    Progress,
    ExerciseSubmissionRecord,
)
from fastapi_backend.schemas.common import SuccessResponse
from fastapi_backend.schemas.exercise import (
    ExerciseSubmission,
    ExerciseEvaluationResponse,
)
from fastapi_backend.deps.ai_points import require_ai_points
from fastapi_backend.services.ai_tutor_service import AITutorService
from fastapi_backend.services.sandbox_service import CodeSandbox

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/exercise", tags=["在线练习"])


def get_ai_tutor():
    return AITutorService()


def get_sandbox():
    return CodeSandbox()


# 语言别名映射：统一各种变体到标准语言名
_LANGUAGE_ALIASES = {
    "python3": "python",
    "python2": "python",
    "py": "python",
    "bash": "shell",
    "sh": "shell",
    "zsh": "shell",
    "sqlite": "sql",
    "mysql": "sql",
    "postgresql": "sql",
    "pgsql": "sql",
    "中文": "python",  # 中文理论题中的代码题默认按python处理
}


def _normalize_language(language: str, exercise_type: str = "") -> str:
    """标准化语言名称：小写 + 别名映射 + exercise_type推断"""
    lang = (language or "").lower().strip()
    # 别名映射
    if lang in _LANGUAGE_ALIASES:
        return _LANGUAGE_ALIASES[lang]
    # 已知语言直接返回
    if lang in ("python", "sql", "shell", "javascript"):
        return lang
    # 根据 exercise_type 推断
    if exercise_type == "sql":
        return "sql"
    if exercise_type == "code":
        return "python"
    # 默认 python
    return "python"


async def _smart_judge_python_function(
    sandbox: CodeSandbox,
    user_code: str,
    reference_code: str,
) -> dict:
    """
    智能判题：对 Python 函数题，从参考答案提取函数签名，
    用通用测试输入同时调用用户函数和参考函数，比较返回值。
    """
    import re

    # 从参考答案中提取函数名和参数
    func_match = re.search(r"def\s+(\w+)\s*\(([^)]*)\)", reference_code)
    if not func_match:
        # 无法提取函数名，回退到执行比较
        ref_result = await sandbox.execute_code(code=reference_code, language="python", timeout=5)
        user_result = await sandbox.execute_code(code=user_code, language="python", timeout=5)
        ref_out = ref_result.get("stdout", "").strip()
        user_out = user_result.get("stdout", "").strip()
        passed = ref_out == user_out and ref_out != ""
        return {
            "total_cases": 1,
            "passed_count": 1 if passed else 0,
            "failed_count": 0 if passed else 1,
            "pass_rate": 100.0 if passed else 0.0,
            "all_passed": passed,
            "details": [
                {
                    "case_index": 1,
                    "passed": passed,
                    "expected": ref_out[:500] or "(无输出)",
                    "actual": user_out[:500] or "(无输出)",
                }
            ],
            "summary": "输出匹配" if passed else "输出不匹配",
        }

    func_name = func_match.group(1)
    params_str = func_match.group(2).strip()

    # 根据参数名生成通用测试输入
    test_inputs = _generate_test_inputs(func_name, params_str)

    if not test_inputs:
        # 无法生成测试输入，回退
        ref_result = await sandbox.execute_code(code=reference_code, language="python", timeout=5)
        user_result = await sandbox.execute_code(code=user_code, language="python", timeout=5)
        ref_out = ref_result.get("stdout", "").strip()
        user_out = user_result.get("stdout", "").strip()
        passed = ref_out == user_out and ref_out != ""
        return {
            "total_cases": 1,
            "passed_count": 1 if passed else 0,
            "failed_count": 0 if passed else 1,
            "pass_rate": 100.0 if passed else 0.0,
            "all_passed": passed,
            "details": [
                {
                    "case_index": 1,
                    "passed": passed,
                    "expected": ref_out[:500] or "(无输出)",
                    "actual": user_out[:500] or "(无输出)",
                }
            ],
            "summary": "输出匹配" if passed else "输出不匹配",
        }

    # 用参考答案生成 expected，用用户代码生成 actual
    results = []
    for i, args in enumerate(test_inputs):
        args_str = ", ".join(repr(a) for a in args)
        call_line = f"print({func_name}({args_str}))"

        # 执行参考答案
        ref_code = f"{reference_code}\n{call_line}"
        ref_result = await sandbox.execute_code(code=ref_code, language="python", timeout=5)
        expected = ref_result.get("stdout", "").strip()

        # 执行用户代码
        user_exec_code = f"{user_code}\n{call_line}"
        user_result = await sandbox.execute_code(code=user_exec_code, language="python", timeout=5)
        actual = user_result.get("stdout", "").strip()

        passed = actual == expected
        results.append(
            {
                "case_index": i + 1,
                "passed": passed,
                "expected": expected[:500] or "(无输出)",
                "actual": actual[:500] or "(无输出)",
                "error": user_result.get("stderr", "")[:200] if user_result.get("stderr") else None,
            }
        )

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    return {
        "total_cases": total,
        "passed_count": passed_count,
        "failed_count": total - passed_count,
        "pass_rate": round(passed_count / total * 100, 1) if total > 0 else 0.0,
        "all_passed": passed_count == total and total > 0,
        "details": results,
        "summary": f"通过 {passed_count}/{total} 个测试用例",
    }


def _generate_test_inputs(func_name: str, params_str: str) -> list[list]:
    """
    根据函数名和参数名生成通用测试输入。
    返回 list of args lists，如 [[1, 10], [0, 5], [-1, 1]]
    """
    params = [p.strip().split("=")[0].strip() for p in params_str.split(",") if p.strip()]
    if not params:
        return []

    # 根据函数名和参数名推断测试输入
    fn = func_name.lower()
    n_params = len(params)

    # 密码强度检查类
    if "password" in fn or "passwd" in fn:
        return [
            ["Abc123!"],  # 长度7 → weak
            ["Abcd123!"],  # 全满足 → strong
            ["Abcd1234"],  # 缺特殊字符 → medium
            ["abcd1234"],  # 缺大写+特殊 → weak
            ["ABCDEFGH"],  # 只有大写 → weak
            ["Abcdefg!"],  # 缺数字 → medium
        ]

    # 边界值类
    if "boundary" in fn or "bound" in fn:
        if n_params == 2:
            return [[1, 10], [0, 100], [-5, 5], [1, 1]]
        return [[1, 10]]

    # 排序类
    if "sort" in fn:
        return [
            [[3, 1, 2]],
            [[5, 5, 5]],
            [[]],
            [[1]],
            [[9, 3, 7, 1, 5]],
        ]

    # 查找类
    if "find" in fn or "search" in fn or "index" in fn:
        if n_params == 2:
            return [[1, [1, 2, 3]], [5, [1, 2, 3]], [3, [3]]]
        return [[1, 2, 3]]

    # 判断/检查类
    if "check" in fn or "is_" in fn or "valid" in fn or "verify" in fn:
        if n_params == 1:
            return [["test"], [""], ["123"], ["ABC"]]
        if n_params == 2:
            return [[1, 10], [0, 0], [10, 1]]
        return [[1]]

    # 计算/生成类
    if "calc" in fn or "compute" in fn or "generat" in fn or "fib" in fn or "factorial" in fn:
        if n_params == 1:
            return [[1], [5], [10], [0]]
        if n_params == 2:
            return [[1, 10], [0, 5], [3, 3]]
        return [[1]]

    # 反转类
    if "revers" in fn:
        return [["hello"], [""], ["a"], ["12345"]]

    # 通用：根据参数数量生成基础测试
    if n_params == 1:
        return [[1], [0], [-1], [10], [100]]
    if n_params == 2:
        return [[1, 10], [0, 5], [5, 1], [0, 0], [-1, 1]]
    if n_params == 3:
        return [[1, 2, 3], [0, 0, 0], [-1, 0, 1]]

    return []


async def _execute_and_judge(
    sandbox: CodeSandbox,
    language: str,
    source_code: str,
    test_cases: list[dict],
    setup_code: str = "",
    function_name: str = "",
) -> dict:
    """
    在沙箱中执行用户代码，逐个测试用例比对结果。
    支持两种测试用例格式：
    1. 函数调用型: {"function": "check_password_strength", "args": ["Abc123!"], "expected": "weak"}
       → 自动生成调用代码，比较返回值
    2. 输入输出型: {"input": "...", "expected_output": "..."}
       → 通过 stdin 提供输入，比较 stdout
    返回 { total_cases, passed_count, failed_count, pass_rate, all_passed, details }
    """
    results = []

    if language == "python":
        for i, tc in enumerate(test_cases):
            # 函数调用型测试用例
            func_call = tc.get("function", "")
            func_args = tc.get("args", [])
            expected = str(tc.get("expected", tc.get("expected_output", ""))).strip()

            if func_call:
                # 生成调用代码：先执行用户代码定义函数，再调用并 print 结果
                args_str = ", ".join(repr(a) for a in func_args)
                call_code = f"{source_code}\nprint({func_call}({args_str}))"
                exec_result = await sandbox.execute_code(
                    code=call_code,
                    language="python",
                    timeout=5,
                )
            else:
                # 输入输出型测试用例
                case_input = tc.get("input", "")
                full_code = (setup_code + "\n" if setup_code else "") + source_code
                exec_result = await sandbox.execute_code(
                    code=full_code,
                    language="python",
                    input_data=case_input or None,
                    timeout=5,
                )

            actual = exec_result.get("stdout", "").strip()
            passed = actual == expected
            results.append(
                {
                    "case_index": i + 1,
                    "passed": passed,
                    "expected": expected,
                    "actual": actual[:500] if actual else "(无输出)",
                    "error": exec_result.get("stderr", "")[:200] if exec_result.get("stderr") else None,
                }
            )

    elif language == "sql":
        for i, tc in enumerate(test_cases):
            tc_setup = tc.get("setup_sql", setup_code or "")
            user_sql = source_code
            expected = str(tc.get("expected_output", tc.get("expected", ""))).strip()

            exec_result = await sandbox.execute_code(
                code=user_sql,
                language="sql",
                timeout=3,
                setup_sql=tc_setup,
            )

            actual = exec_result.get("stdout", "").strip()
            passed = actual == expected
            results.append(
                {
                    "case_index": i + 1,
                    "passed": passed,
                    "expected": expected,
                    "actual": actual[:500] if actual else "(无输出)",
                    "error": exec_result.get("stderr", "")[:200] if exec_result.get("stderr") else None,
                }
            )
    else:
        # shell 等其他语言
        for i, tc in enumerate(test_cases):
            func_call = tc.get("function", "")
            func_args = tc.get("args", [])
            expected = str(tc.get("expected_output", tc.get("expected", ""))).strip()

            if func_call and language == "python":
                args_str = ", ".join(repr(a) for a in func_args)
                call_code = f"{source_code}\nprint({func_call}({args_str}))"
            else:
                call_code = source_code

            case_input = tc.get("input", "")
            exec_result = await sandbox.execute_code(
                code=call_code,
                language=language,
                input_data=case_input or None,
                timeout=5,
            )

            actual = exec_result.get("stdout", "").strip()
            passed = actual == expected
            results.append(
                {
                    "case_index": i + 1,
                    "passed": passed,
                    "expected": expected,
                    "actual": actual[:500] if actual else "(无输出)",
                    "error": exec_result.get("stderr", "")[:200] if exec_result.get("stderr") else None,
                }
            )

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
    current_user: User = Depends(get_current_user),
    tutor: AITutorService = Depends(get_ai_tutor),
    sandbox: CodeSandbox = Depends(get_sandbox),
    db: AsyncSession = Depends(get_db),
    _ai=Depends(require_ai_points("exercise_code_eval")),
):
    """
    接收用户编写的练习代码，在沙箱中真实执行判题，再由 AI 给出评分与建议。
    """
    from fastapi_backend.schemas.interview import CodeSubmission

    # 标准化语言
    normalized_language = _normalize_language(submission.language)

    code_submission = CodeSubmission(
        question_id=submission.exercise_id,
        language=normalized_language,
        source_code=submission.source_code,
    )

    question_prompt = submission.exercise_description
    judge_result = None

    if submission.test_cases:
        try:
            test_cases = (
                json.loads(submission.test_cases) if isinstance(submission.test_cases, str) else submission.test_cases
            )
            if isinstance(test_cases, list) and len(test_cases) > 0:
                judge_result = await _execute_and_judge(
                    sandbox=sandbox,
                    language=normalized_language,
                    source_code=submission.source_code,
                    test_cases=test_cases,
                )
        except (json.JSONDecodeError, TypeError):
            pass

    elif submission.expected_output:
        expected = submission.expected_output.strip()
        exec_result = await sandbox.execute_code(
            code=submission.source_code,
            language=normalized_language,
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
            "details": [
                {
                    "case_index": 1,
                    "passed": passed,
                    "expected": expected[:500],
                    "actual": actual[:500],
                    "error": exec_result.get("stderr", "")[:200] if exec_result.get("stderr") else None,
                }
            ],
            "summary": "通过 1/1 个测试用例" if passed else "未通过测试用例",
        }

    try:
        result = await tutor.evaluate_code(
            submission=code_submission,
            question_prompt=question_prompt,
            judge_result=judge_result,
        )
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=502, detail="AI 服务调用失败，积分已退还")

    await _ai()
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

    # 确保 exercise_id 是整数（前端可能传字符串）
    try:
        exercise_id = int(body["exercise_id"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="exercise_id 必须是有效整数")

    stmt = select(Exercise).where(Exercise.id == exercise_id)
    result = await db.execute(stmt)
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="习题不存在")
    if not ex.is_public:
        raise HTTPException(status_code=403, detail="该习题未公开，无法提交")

    solution = body["solution"]

    # 语言标准化：统一小写 + 别名映射
    raw_language = body.get("language", ex.language or "python")
    language = _normalize_language(raw_language, ex.exercise_type)

    # 智能推断 exercise_type
    exercise_type = body.get("exercise_type", ex.exercise_type or "text")
    # 如果 language 是 sql 但 exercise_type 不是 sql，修正
    if language == "sql" and exercise_type != "sql":
        exercise_type = "sql"
    # 如果 exercise_type 是 sql 但 language 不是 sql，修正
    if exercise_type == "sql" and language != "sql":
        language = "sql"

    judge_result = None
    is_correct = False

    if language == "sql":
        setup_sql = ex.setup_sql or ""

        exec_result = await sandbox.execute_code(
            code=solution,
            language="sql",
            timeout=3,
            setup_sql=setup_sql,
        )
        actual = exec_result.get("stdout", "").strip()

        if exec_result.get("exit_code", 1) != 0:
            is_correct = False
            judge_result = {
                "total_cases": 1,
                "passed_count": 0,
                "failed_count": 1,
                "pass_rate": 0.0,
                "all_passed": False,
                "details": [
                    {
                        "case_index": 1,
                        "passed": False,
                        "expected": "SQL执行成功",
                        "actual": actual[:500] or exec_result.get("stderr", "")[:500],
                    }
                ],
                "summary": "SQL执行失败",
            }
        elif ex.solution and ex.solution.strip():
            ref_result = await sandbox.execute_code(
                code=ex.solution,
                language="sql",
                timeout=3,
                setup_sql=setup_sql,
            )
            expected = ref_result.get("stdout", "").strip()
            is_correct = actual == expected and actual != ""

            judge_result = {
                "total_cases": 1,
                "passed_count": 1 if is_correct else 0,
                "failed_count": 0 if is_correct else 1,
                "pass_rate": 100.0 if is_correct else 0.0,
                "all_passed": is_correct,
                "details": [
                    {
                        "case_index": 1,
                        "passed": is_correct,
                        "expected": expected[:500] if expected else "(无输出)",
                        "actual": actual[:500] if actual else "(无输出)",
                    }
                ],
                "summary": "SQL 执行结果匹配" if is_correct else "SQL 执行结果不匹配",
            }
        else:
            is_correct = actual != ""
            judge_result = {
                "total_cases": 1,
                "passed_count": 1 if is_correct else 0,
                "failed_count": 0 if is_correct else 1,
                "pass_rate": 100.0 if is_correct else 0.0,
                "all_passed": is_correct,
                "details": [
                    {
                        "case_index": 1,
                        "passed": is_correct,
                        "expected": "SQL执行成功并返回结果",
                        "actual": actual[:500] if actual else "(无输出)",
                    }
                ],
                "summary": "SQL 执行成功" if is_correct else "SQL 未返回结果",
            }

    elif language == "javascript":
        is_correct = False
        judge_result = {
            "total_cases": 0,
            "passed_count": 0,
            "failed_count": 0,
            "pass_rate": 0.0,
            "all_passed": False,
            "details": [],
            "summary": "JavaScript 暂不支持在线判题，请参考答案在本地环境练习",
        }

    elif exercise_type == "code" or language in ("python", "shell"):
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
            # 有参考答案但没有 test_cases：智能判题
            # 对于 Python 函数题，用参考答案生成测试用例
            if language == "python" and "def " in ex.solution:
                judge_result = await _smart_judge_python_function(
                    sandbox=sandbox,
                    user_code=solution,
                    reference_code=ex.solution,
                )
                is_correct = judge_result["all_passed"]
            else:
                # 非 Python 或非函数题：执行比较 stdout
                exec_result = await sandbox.execute_code(
                    code=solution,
                    language=language,
                    timeout=5,
                )
                actual = exec_result.get("stdout", "").strip()

                if exec_result.get("exit_code", -1) != 0 or exec_result.get("stderr", ""):
                    is_correct = False
                    judge_result = {
                        "total_cases": 1,
                        "passed_count": 0,
                        "failed_count": 1,
                        "pass_rate": 0.0,
                        "all_passed": False,
                        "details": [
                            {
                                "case_index": 1,
                                "passed": False,
                                "expected": "代码运行无错误",
                                "actual": exec_result.get("stderr", "")[:500],
                            }
                        ],
                        "summary": "代码运行出错",
                    }
                else:
                    ref_result = await sandbox.execute_code(
                        code=ex.solution,
                        language=language,
                        timeout=5,
                    )
                    expected = ref_result.get("stdout", "").strip()
                    is_correct = actual == expected and actual != ""

                    judge_result = {
                        "total_cases": 1,
                        "passed_count": 1 if is_correct else 0,
                        "failed_count": 0 if is_correct else 1,
                        "pass_rate": 100.0 if is_correct else 0.0,
                        "all_passed": is_correct,
                        "details": [
                            {
                                "case_index": 1,
                                "passed": is_correct,
                                "expected": expected[:500] if expected else "(无输出)",
                                "actual": actual[:500] if actual else "(无输出)",
                            }
                        ],
                        "summary": "输出正确" if is_correct else "输出不匹配",
                    }
        else:
            # 无 test_cases 也无参考答案：仅检查代码能否运行
            exec_result = await sandbox.execute_code(
                code=solution,
                language=language,
                timeout=5,
            )
            no_error = exec_result.get("exit_code", -1) == 0 and not exec_result.get("stderr", "")
            is_correct = no_error
            judge_result = {
                "total_cases": 1,
                "passed_count": 1 if no_error else 0,
                "failed_count": 0 if no_error else 1,
                "pass_rate": 100.0 if no_error else 0.0,
                "all_passed": no_error,
                "details": [
                    {
                        "case_index": 1,
                        "passed": no_error,
                        "expected": "代码运行无错误",
                        "actual": exec_result.get("stdout", "")[:500]
                        if no_error
                        else exec_result.get("stderr", "")[:500],
                    }
                ],
                "summary": "代码运行成功（无测试用例，仅检查运行无错）" if no_error else "代码运行出错",
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

    before_scores = {}
    if is_correct:
        try:
            from fastapi_backend.routers.skills import (
                _calculate_skill_score,
                SKILL_CATEGORY_MAP,
                SKILL_DIMENSIONS,
            )

            for skill_key in SKILL_CATEGORY_MAP:
                before_scores[skill_key] = await _calculate_skill_score(current_user.id, skill_key, db)
        except Exception as e:
            logger.warning(f"计算提交前技能分数失败: {e}")

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
            progress.attempts = (progress.attempts or 0) + 1
            if is_correct:
                progress.completed = True
                progress.score = 100
                progress.completed_at = datetime.now(timezone.utc)
        else:
            progress = Progress(
                user_id=current_user.id,
                exercise_id=ex.id,
                completed=is_correct,
                score=100 if is_correct else 0,
                completed_at=datetime.now(timezone.utc) if is_correct else None,
                attempts=1,
            )
            db.add(progress)

        await db.commit()
    except Exception as e:
        logger.error(f"保存提交记录失败: {e}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail="提交记录保存失败，请重试")

    skill_change = None
    if is_correct and before_scores:
        try:
            after_scores = {}
            for skill_key in SKILL_CATEGORY_MAP:
                after_scores[skill_key] = await _calculate_skill_score(current_user.id, skill_key, db)

            changes = []
            for skill_key in SKILL_CATEGORY_MAP:
                diff = after_scores[skill_key] - before_scores[skill_key]
                if diff > 0:
                    changes.append(
                        {
                            "key": skill_key,
                            "name": SKILL_DIMENSIONS[skill_key]["name"],
                            "before": before_scores[skill_key],
                            "after": after_scores[skill_key],
                            "change": diff,
                        }
                    )

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
    page: int = 1,
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户所有习题的完成进度（支持分页）"""
    from sqlalchemy import func

    # total 与 items 使用相同的 WHERE 条件，确保分页计数一致
    base_filter = Progress.user_id == current_user.id

    # 获取总数
    count_stmt = select(func.count()).select_from(Progress).where(base_filter)
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # 分页查询
    stmt = select(Progress).where(base_filter)
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    progresses = result.scalars().all()

    progress_map = {}
    for p in progresses:
        progress_map[p.exercise_id] = {
            "completed": p.completed or False,
            "score": p.score,
            "attempts": p.attempts or 0,
        }

    return {
        "progress": progress_map,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


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
        activities.append(
            {
                "id": s.id,
                "type": "exercise_submit",
                "exercise_id": s.exercise_id,
                "exercise_title": exercise_map.get(s.exercise_id, f"习题#{s.exercise_id}"),
                "result": s.result,
                "score": s.score,
                "created_at": s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "",
            }
        )

    return {"activities": activities}


@router.get("/wrong-answers")
async def get_wrong_answers(
    page: int = 1,
    page_size: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的错题本（使用 SQL 子查询优化，支持分页）"""
    from sqlalchemy import func, distinct

    # 使用子查询找出所有有失败记录的习题ID
    wrong_exercises_stmt = (
        select(ExerciseSubmissionRecord.exercise_id)
        .where(
            ExerciseSubmissionRecord.user_id == current_user.id,
            ExerciseSubmissionRecord.result == "fail",
        )
        .group_by(ExerciseSubmissionRecord.exercise_id)
    )
    wrong_result = await db.execute(wrong_exercises_stmt)
    wrong_exercise_ids = [row[0] for row in wrong_result.all()]

    if not wrong_exercise_ids:
        return {
            "wrong_answers": [],
            "mastered": [],
            "wrong_count": 0,
            "mastered_count": 0,
        }

    # 使用子查询找出已经有成功记录的习题ID
    correct_exercises_stmt = select(distinct(ExerciseSubmissionRecord.exercise_id)).where(
        ExerciseSubmissionRecord.user_id == current_user.id,
        ExerciseSubmissionRecord.result == "pass",
        ExerciseSubmissionRecord.exercise_id.in_(wrong_exercise_ids),
    )
    correct_result = await db.execute(correct_exercises_stmt)
    mastered_ids = {row[0] for row in correct_result.all()}

    still_wrong_ids = [eid for eid in wrong_exercise_ids if eid not in mastered_ids]

    # 获取习题信息
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

    # 单次聚合查询获取所有错题的失败次数和最新失败时间
    wrong_stats_map = {}
    if still_wrong_ids:
        stats_stmt = (
            select(
                ExerciseSubmissionRecord.exercise_id,
                func.count().label("wrong_count"),
                func.max(ExerciseSubmissionRecord.created_at).label("last_wrong_at"),
            )
            .where(
                ExerciseSubmissionRecord.user_id == current_user.id,
                ExerciseSubmissionRecord.exercise_id.in_(still_wrong_ids),
                ExerciseSubmissionRecord.result == "fail",
            )
            .group_by(ExerciseSubmissionRecord.exercise_id)
        )
        stats_result = await db.execute(stats_stmt)
        for row in stats_result.all():
            wrong_stats_map[row.exercise_id] = row

    wrong_list = []
    for eid in still_wrong_ids:
        info = exercise_map.get(eid, {})
        row = wrong_stats_map.get(eid)
        wrong_list.append(
            {
                **info,
                "status": "wrong",
                "wrong_count": row.wrong_count if row else 0,
                "last_wrong_at": row.last_wrong_at.strftime("%Y-%m-%d %H:%M") if row and row.last_wrong_at else "",
            }
        )

    # 分页
    total_wrong = len(wrong_list)
    start = (page - 1) * page_size
    end = start + page_size
    paginated_wrong = wrong_list[start:end]

    mastered_list = [{**exercise_map.get(eid, {}), "status": "mastered"} for eid in mastered_ids]

    return {
        "wrong_answers": paginated_wrong,
        "mastered": mastered_list,
        "wrong_count": total_wrong,
        "mastered_count": len(mastered_ids),
        "page": page,
        "page_size": page_size,
    }


@router.get("/daily-tasks")
async def get_daily_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取今日任务和完成情况（使用数据库聚合优化）"""
    from datetime import datetime
    from zoneinfo import ZoneInfo
    from sqlalchemy import func, Integer

    CN_TZ = ZoneInfo("Asia/Shanghai")
    now_local = datetime.now(CN_TZ)
    today_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0)

    # 使用数据库聚合查询今日提交统计
    today_stats_stmt = select(
        func.count().label("total"),
        func.sum(func.cast(ExerciseSubmissionRecord.result == "pass", Integer)).label("correct"),
    ).where(
        ExerciseSubmissionRecord.user_id == current_user.id,
        ExerciseSubmissionRecord.created_at >= today_start,
    )
    today_result = await db.execute(today_stats_stmt)
    today_stats = today_result.one()
    today_total = today_stats.total or 0
    today_correct = today_stats.correct or 0

    # 使用 COUNT 查询总完成数
    total_completed_stmt = (
        select(func.count())
        .select_from(Progress)
        .where(
            Progress.user_id == current_user.id,
            Progress.completed,
        )
    )
    total_result = await db.execute(total_completed_stmt)
    total_completed = total_result.scalar()

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
    """获取与指定习题相关的推荐习题（同类型+同语言+相关知识点）"""
    ex_stmt = select(Exercise).where(Exercise.id == exercise_id)
    ex_result = await db.execute(ex_stmt)
    exercise = ex_result.scalar_one_or_none()

    if not exercise:
        return {"related": []}

    base_conditions = [
        Exercise.id != exercise_id,
        Exercise.is_public,
    ]
    if exercise.exercise_type:
        base_conditions.append(Exercise.exercise_type == exercise.exercise_type)
    if exercise.language:
        base_conditions.append(Exercise.language == exercise.language)

    soft_conditions = []
    if exercise.knowledge_point:
        soft_conditions.append(Exercise.knowledge_point == exercise.knowledge_point)
    if exercise.category:
        soft_conditions.append(Exercise.category == exercise.category)

    if soft_conditions:
        related_stmt = (
            select(Exercise)
            .where(
                *base_conditions,
                or_(*soft_conditions),
            )
            .order_by(Exercise.stage.nulls_first(), Exercise.difficulty)
            .limit(6)
        )
    else:
        related_stmt = (
            select(Exercise)
            .where(*base_conditions)
            .order_by(Exercise.stage.nulls_first(), Exercise.difficulty)
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
        related_list.append(
            {
                "id": r.id,
                "title": r.title,
                "difficulty": r.difficulty,
                "category": r.category,
                "knowledge_point": r.knowledge_point,
                "stage": r.stage,
                "completed": r.id in completed_ids,
            }
        )

    return {"related": related_list}
