"""
面试代码执行服务 - 处理代码沙盒执行和AI评估
"""
import asyncio
import json
import logging
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.config import settings
from fastapi_backend.core.database import get_db
from fastapi_backend.models.models import Submission, InterviewQuestion, TestCase, Exercise
from fastapi_backend.schemas.submission import SubmissionUpdate
from fastapi_backend.services.sandbox_service import CodeSandbox
from fastapi_backend.services.ai_tutor_service import AITutorService

logger = logging.getLogger(__name__)


async def _get_question_for_submission(db: AsyncSession, submission: Submission) -> tuple:
    """根据submission获取题目，返回 (question_or_exercise, source_type)
    source_type: 'interview_question' | 'exercise' | None
    """
    qid = submission.question_id
    source = getattr(submission, 'question_source', None) or 'interview_question'

    if source == 'exercise':
        ex_result = await db.execute(select(Exercise).where(Exercise.id == qid))
        exercise = ex_result.scalar_one_or_none()
        if exercise:
            return exercise, 'exercise'

    iq_result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == qid))
    question = iq_result.scalar_one_or_none()
    if question:
        return question, 'interview_question'

    ex_result = await db.execute(select(Exercise).where(Exercise.id == qid))
    exercise = ex_result.scalar_one_or_none()
    if exercise:
        return exercise, 'exercise'

    return None, None


def _extract_question_info(q_obj, source_type: str) -> dict:
    """从InterviewQuestion或Exercise对象提取统一格式的题目信息"""
    if source_type == 'exercise' and q_obj:
        return {
            "title": q_obj.title,
            "content": q_obj.description or q_obj.instructions or "",
            "reference_answer": q_obj.solution or q_obj.expected_output or "",
            "prompt": q_obj.instructions or q_obj.description or "",
            "test_cases_json": q_obj.test_cases or "",
            "code_template": q_obj.code_template or "",
            "category": q_obj.category or "",
            "difficulty": q_obj.difficulty or "medium",
        }
    elif q_obj:
        return {
            "title": q_obj.title,
            "content": q_obj.content or q_obj.description or "",
            "reference_answer": q_obj.answer or q_obj.reference_solution or "",
            "prompt": q_obj.prompt or q_obj.content or q_obj.description or "",
            "test_cases_json": q_obj.test_cases or "",
            "code_template": q_obj.reference_solution or "",
            "category": q_obj.category or "",
            "difficulty": q_obj.difficulty or "medium",
        }
    return {
        "title": "", "content": "", "reference_answer": "", "prompt": "",
        "test_cases_json": "", "code_template": "", "category": "", "difficulty": "medium"
    }


class InterviewExecutionService:
    def __init__(self):
        self.sandbox = CodeSandbox()
        self.ai_tutor = AITutorService()

    async def execute_and_evaluate_submission_by_id(
        self,
        submission_id: int
    ) -> None:
        """
        通过提交ID执行并评估代码提交
        在后台任务中使用，内部创建数据库会话
        """
        async for db in get_db():
            try:
                result = await db.execute(
                    select(Submission).where(Submission.id == submission_id)
                )
                submission = result.scalar_one_or_none()

                if not submission:
                    logger.error(f"提交 #{submission_id} 不存在")
                    return

                await self.execute_and_evaluate_submission(db, submission)

            except Exception as exc:
                logger.error(f"处理提交 #{submission_id} 时发生异常: {exc}")

    async def execute_and_evaluate_submission(
        self,
        db: AsyncSession,
        submission: Submission
    ) -> Submission:
        logger.info(f"开始执行提交 #{submission.id} (会话 #{submission.session_id})")

        if submission.language == "text":
            logger.info(f"提交 #{submission.id} 为文本回答，跳过沙盒执行，直接AI评估")
            update_data = SubmissionUpdate(
                execution_status="skipped",
                execution_result=json.dumps({"type": "text_answer", "skipped": True}, ensure_ascii=False),
                ai_evaluation_status="running"
            )
            await self._update_submission(db, submission, update_data)
            await self._evaluate_text_answer(db, submission)
        else:
            execution_result = await self._execute_code(db, submission)
            await self._update_execution_result(db, submission, execution_result)
            if execution_result["exit_code"] == 0:
                await self._evaluate_with_ai(db, submission, execution_result)
            else:
                update_data = SubmissionUpdate(
                    ai_evaluation_status="failed",
                    feedback=f"代码执行失败，无法进行AI评估。错误: {execution_result.get('stderr', '未知错误')}"
                )
                await self._update_submission(db, submission, update_data)

        logger.info(f"提交 #{submission.id} 处理完成")
        return submission

    async def _execute_code(self, db: AsyncSession, submission: Submission) -> dict:
        """在沙盒中执行代码并进行判题"""
        logger.info(f"在沙盒中执行提交 #{submission.id} 的代码")

        try:
            timeout = settings.SANDBOX_DEFAULT_TIMEOUT_SECONDS

            q_obj, source_type = await _get_question_for_submission(db, submission)
            q_info = _extract_question_info(q_obj, source_type)

            if not q_obj:
                logger.error(f"提交 #{submission.id} 关联的题目 #{submission.question_id} 不存在")
                return {
                    "exit_code": -1,
                    "stdout": "",
                    "stderr": f"关联的题目 #{submission.question_id} 不存在",
                    "execution_time_ms": 0,
                    "execution_status": "failed",
                    "judge_result": None
                }

            test_cases = []

            if source_type == 'exercise':
                try:
                    tc_json = json.loads(q_info["test_cases_json"]) if q_info["test_cases_json"] else []
                    if isinstance(tc_json, list):
                        test_cases = tc_json
                except (json.JSONDecodeError, TypeError):
                    pass
            else:
                test_case_query = select(TestCase).where(TestCase.question_id == q_obj.id)
                test_case_result = await db.execute(test_case_query)
                test_case_objects = test_case_result.scalars().all()

                if test_case_objects:
                    for tc in test_case_objects:
                        test_cases.append({
                            "input": tc.input,
                            "output": tc.expected_output,
                            "is_example": tc.is_example,
                            "is_hidden": tc.is_hidden,
                            "description": tc.description
                        })
                    logger.info(f"从TestCase表读取到 {len(test_cases)} 个测试用例")
                else:
                    try:
                        test_cases = json.loads(q_obj.test_cases) if hasattr(q_obj, 'test_cases') and q_obj.test_cases else []
                        if not isinstance(test_cases, list):
                            test_cases = []
                        logger.info(f"从JSON字段读取到 {len(test_cases)} 个测试用例")
                    except (json.JSONDecodeError, AttributeError) as e:
                        logger.error(f"题目 #{q_obj.id} 的测试用例JSON解析失败: {e}")
                        test_cases = []

            # 如果没有测试用例，只执行代码不判题
            if not test_cases:
                logger.info(f"题目 #{q_obj.id} 没有测试用例，只执行代码")
                result = await self.sandbox.execute_python_code(
                    code=submission.source_code,
                    timeout=timeout
                )
            else:
                # 进行判题
                judge_result = await self._judge_code_with_test_cases(submission.source_code, test_cases, timeout)

                # 构建执行结果
                result = {
                    "exit_code": 0 if judge_result["all_passed"] else -1,
                    "stdout": judge_result.get("summary", ""),
                    "stderr": "",
                    "execution_time_ms": judge_result.get("total_execution_time_ms", 0),
                    "execution_status": "success" if judge_result["all_passed"] else "failed",
                    "judge_result": judge_result
                }
                return result

            # 记录执行状态
            execution_status = "success" if result["exit_code"] == 0 else "failed"
            if result["exit_code"] == -1 and "timed out" in result.get("stderr", ""):
                execution_status = "timeout"

            result["execution_status"] = execution_status
            result["judge_result"] = None  # 没有判题结果
            return result

        except Exception as exc:
            logger.error(f"执行提交 #{submission.id} 时发生异常: {exc}")
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"执行过程中发生异常: {exc}",
                "execution_time_ms": 0,
                "execution_status": "failed",
                "judge_result": None
            }

    async def _judge_code_with_test_cases(self, source_code: str, test_cases: list, timeout: int) -> dict:
        """
        使用测试用例判题

        Args:
            source_code: 源代码
            test_cases: 测试用例列表，每个元素应包含 'input' 和 'output' 字段
            timeout: 每个测试用例的超时时间

        Returns:
            判题结果字典
        """
        logger.info(f"开始判题，共有 {len(test_cases)} 个测试用例")

        case_results = []
        passed_count = 0
        total_execution_time_ms = 0

        for i, test_case in enumerate(test_cases):
            case_num = i + 1
            logger.info(f"执行测试用例 #{case_num}")

            # 获取输入和预期输出
            input_data = test_case.get("input", "")
            expected_output = test_case.get("output", "")

            # 执行代码
            try:
                sandbox_result = await self.sandbox.execute_python_code_with_input(
                    code=source_code,
                    input_data=input_data,
                    timeout=timeout
                )

                execution_time_ms = sandbox_result.get("execution_time_ms", 0)
                total_execution_time_ms += execution_time_ms

                # 判断是否通过
                actual_output = sandbox_result.get("stdout", "").strip()
                # 去除尾部换行符，比较输出
                passed = actual_output == expected_output.strip()

                if passed:
                    passed_count += 1

                case_result = {
                    "case_number": case_num,
                    "input": input_data,
                    "expected_output": expected_output,
                    "actual_output": actual_output,
                    "passed": passed,
                    "exit_code": sandbox_result.get("exit_code", -1),
                    "stderr": sandbox_result.get("stderr", ""),
                    "execution_time_ms": execution_time_ms
                }

                case_results.append(case_result)

                logger.info(f"测试用例 #{case_num} {'通过' if passed else '失败'}")

            except Exception as e:
                logger.error(f"执行测试用例 #{case_num} 时发生异常: {e}")
                case_result = {
                    "case_number": case_num,
                    "input": input_data,
                    "expected_output": expected_output,
                    "actual_output": "",
                    "passed": False,
                    "exit_code": -1,
                    "stderr": f"执行异常: {e}",
                    "execution_time_ms": 0
                }
                case_results.append(case_result)

        # 计算总体结果
        total_cases = len(test_cases)
        all_passed = passed_count == total_cases
        pass_rate = (passed_count / total_cases * 100) if total_cases > 0 else 0

        summary = f"通过 {passed_count}/{total_cases} 个测试用例，通过率 {pass_rate:.1f}%"
        if all_passed:
            summary += " [PASS]"
        else:
            summary += " [FAIL]"

        judge_result = {
            "case_results": case_results,
            "passed_count": passed_count,
            "failed_count": total_cases - passed_count,
            "total_cases": total_cases,
            "all_passed": all_passed,
            "pass_rate": pass_rate,
            "summary": summary,
            "total_execution_time_ms": total_execution_time_ms
        }

        logger.info(f"判题完成: {summary}")
        return judge_result

    async def _update_execution_result(
        self,
        db: AsyncSession,
        submission: Submission,
        execution_result: dict
    ) -> None:
        """更新提交记录的执行结果"""
        # 构建执行结果JSON，包含判题结果
        execution_result_data = {
            "stdout": execution_result.get("stdout", ""),
            "stderr": execution_result.get("stderr", ""),
            "exit_code": execution_result.get("exit_code", -1),
            "execution_time_ms": execution_result.get("execution_time_ms", 0)
        }

        # 如果有判题结果，也保存
        judge_result = execution_result.get("judge_result")
        if judge_result:
            execution_result_data["judge_result"] = judge_result

        execution_result_json = json.dumps(execution_result_data, ensure_ascii=False)

        # 更新提交记录
        update_data = SubmissionUpdate(
            execution_status=execution_result.get("execution_status", "failed"),
            execution_result=execution_result_json,
            ai_evaluation_status="running" if execution_result.get("exit_code") == 0 else "failed"
        )

        await self._update_submission(db, submission, update_data)
        logger.info(f"提交 #{submission.id} 执行结果已更新: {execution_result.get('execution_status')}")

    async def _evaluate_text_answer(
        self,
        db: AsyncSession,
        submission: Submission
    ) -> None:
        logger.info(f"开始AI评估文本回答 #{submission.id}")

        try:
            from fastapi_backend.models.models import AIConfig

            q_obj, source_type = await _get_question_for_submission(db, submission)
            q_info = _extract_question_info(q_obj, source_type)

            question_title = q_info["title"]
            question_content = q_info["content"]
            reference_answer = q_info["reference_answer"]

            ai_config_result = await db.execute(select(AIConfig).where(AIConfig.is_active == True))
            ai_config = ai_config_result.scalar_one_or_none()

            if not ai_config:
                update_data = SubmissionUpdate(
                    ai_evaluation_status="failed",
                    score=50,
                    feedback="AI服务未配置，无法评估文本回答。请在管理后台配置AI大模型。"
                )
                await self._update_submission(db, submission, update_data)
                return

            import httpx
            from openai import AsyncOpenAI

            http_client = httpx.AsyncClient(timeout=ai_config.timeout_seconds, trust_env=False)

            try:
                client_kwargs = {"api_key": ai_config.api_key, "http_client": http_client}
                base_url = ai_config.base_url
                if base_url:
                    if not base_url.endswith("/v1"):
                        base_url = base_url.rstrip("/") + "/v1"
                    client_kwargs["base_url"] = base_url

                client = AsyncOpenAI(**client_kwargs)
                extra_body = None
                if ai_config.provider == "minimax" and ai_config.group_id:
                    extra_body = {"group_id": ai_config.group_id}

                prompt = f"""你是一位资深的软件测试面试官。请评估候选人对以下面试题的回答。

题目：{question_title}
题目描述：{question_content}
参考答案：{reference_answer}
候选人回答：{submission.source_code}

请从以下维度评估：
1. 回答的准确性和完整性
2. 是否理解了核心概念
3. 是否有实际项目经验的体现
4. 表达是否清晰有条理

请以JSON格式返回评估结果：
{{"score": 分数(0-100的整数), "feedback": "详细点评", "strengths": ["优点1", "优点2"], "weaknesses": ["不足1"], "suggestion": "改进建议"}}"""

                response = await client.chat.completions.create(
                    model=ai_config.model,
                    messages=[
                        {"role": "system", "content": "你是一位资深软件测试面试官，请客观公正地评估候选人的回答。请以JSON格式回复。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000,
                    extra_body=extra_body,
                )
                await client.close()

                content = response.choices[0].message.content if response.choices else ""

                import json as _json
                try:
                    result = _json.loads(content)
                    score = result.get("score", 60)
                    feedback_parts = [result.get("feedback", "")]
                    if result.get("strengths"):
                        feedback_parts.append("优点: " + ", ".join(result["strengths"]))
                    if result.get("weaknesses"):
                        feedback_parts.append("不足: " + ", ".join(result["weaknesses"]))
                    if result.get("suggestion"):
                        feedback_parts.append("建议: " + result["suggestion"])
                    feedback = "\n".join(feedback_parts)
                except _json.JSONDecodeError:
                    score = 60
                    feedback = content if content else "AI评估完成"

                update_data = SubmissionUpdate(
                    ai_evaluation_status="completed",
                    score=score,
                    feedback=feedback
                )
                await self._update_submission(db, submission, update_data)
                logger.info(f"文本回答 #{submission.id} AI评估完成，得分: {score}")

            finally:
                try:
                    await http_client.aclose()
                except Exception:
                    pass

        except Exception as exc:
            logger.error(f"AI评估文本回答 #{submission.id} 时发生异常: {exc}")
            update_data = SubmissionUpdate(
                ai_evaluation_status="failed",
                score=50,
                feedback=f"AI评估过程中发生异常，请稍后重试。"
            )
            await self._update_submission(db, submission, update_data)

    async def _evaluate_with_ai(
        self,
        db: AsyncSession,
        submission: Submission,
        execution_result: dict
    ) -> None:
        """使用AI评估代码"""
        logger.info(f"开始AI评估提交 #{submission.id}")

        try:
            q_obj, source_type = await _get_question_for_submission(db, submission)
            q_info = _extract_question_info(q_obj, source_type)

            question_prompt = q_info["prompt"] if q_obj else None

            judge_result = execution_result.get("judge_result")

            from fastapi_backend.schemas.interview import CodeSubmission
            code_submission = CodeSubmission(
                question_id=str(submission.question_id),
                language=submission.language,
                source_code=submission.source_code
            )

            ai_tutor = AITutorService(db=db)
            ai_result = await ai_tutor.evaluate_code(
                submission=code_submission,
                question_prompt=question_prompt,
                judge_result=judge_result
            )

            # 5. 更新评估结果
            update_data = SubmissionUpdate(
                ai_evaluation_status="completed",
                score=ai_result.score,
                feedback=ai_result.feedback
            )

            await self._update_submission(db, submission, update_data)
            logger.info(f"提交 #{submission.id} AI评估完成，得分: {ai_result.score}")

        except Exception as exc:
            logger.error(f"AI评估提交 #{submission.id} 时发生异常: {exc}")
            # 使用fallback评估结果
            fallback_score = 50
            fallback_feedback = f"AI评估过程中发生异常: {exc}。请检查AI配置或稍后重试。"

            # 尝试基于判题结果给出更好的fallback
            judge_result = execution_result.get("judge_result")
            if judge_result:
                passed = judge_result.get('passed_count', 0)
                total = judge_result.get('total_cases', 1)
                fallback_score = int(judge_result.get('pass_rate', 50))
                fallback_feedback = f"AI评估失败。代码通过了 {passed}/{total} 个测试用例。"

            update_data = SubmissionUpdate(
                ai_evaluation_status="failed",
                score=fallback_score,
                feedback=fallback_feedback
            )
            await self._update_submission(db, submission, update_data)

    async def _update_submission(
        self,
        db: AsyncSession,
        submission: Submission,
        update_data: SubmissionUpdate
    ) -> None:
        """更新提交记录"""
        for field, value in update_data.model_dump(exclude_unset=True).items():
            if value is not None:
                setattr(submission, field, value)

        await db.commit()
        await db.refresh(submission)


# 全局服务实例
interview_execution_service = InterviewExecutionService()