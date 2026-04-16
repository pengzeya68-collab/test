import asyncio
import json
import logging
import os
from typing import Optional, Dict, Any

from fastapi_backend.schemas.interview import CodeSubmission, AIEvaluationResponse

logger = logging.getLogger(__name__)


class AITutorService:
    def __init__(self, db=None):
        self.db = db
        self._config = None
        self.api_key = None
        self.base_url = None
        self.model = None
        self.timeout = 30
        self.max_tokens = 2000
        self.temperature = 0.7
        self.provider = "openai"
        self.group_id = None

    async def _load_config(self):
        if self._config:
            return self._config
        if self.db is None:
            return None
        from sqlalchemy import select
        from fastapi_backend.models.models import AIConfig
        result = await self.db.execute(select(AIConfig).where(AIConfig.is_active == True))
        self._config = result.scalar_one_or_none()
        return self._config

    async def evaluate_code(
        self,
        submission: CodeSubmission,
        question_prompt: Optional[str] = None,
        judge_result: Optional[Dict[str, Any]] = None
    ) -> AIEvaluationResponse:
        logger.info(f"收到代码提交: 题目 {submission.question_id}, 语言 {submission.language}")

        config = await self._load_config()

        if not config:
            from fastapi_backend.core.config import settings
            if not settings.AI_API_KEY or settings.AI_API_KEY == "your_model_api_key_here":
                logger.warning("AI API密钥未配置，返回模拟评估结果")
                return await self._get_mock_evaluation()
            self.api_key = settings.AI_API_KEY
            self.base_url = settings.AI_BASE_URL
            self.model = settings.AI_MODEL
            self.timeout = settings.AI_TIMEOUT_SECONDS
            self.max_tokens = settings.AI_MAX_TOKENS
            self.temperature = settings.AI_TEMPERATURE
            self.provider = settings.AI_PROVIDER.lower()
        else:
            self.api_key = config.api_key
            self.base_url = config.base_url
            self.model = config.model
            self.timeout = config.timeout_seconds
            self.max_tokens = config.max_tokens
            self.temperature = config.temperature
            self.provider = config.provider.lower()
            self.group_id = getattr(config, 'group_id', None)

        try:
            return await self._evaluate_with_real_ai(
                submission=submission,
                question_prompt=question_prompt,
                judge_result=judge_result
            )
        except Exception as exc:
            logger.error(f"AI评估失败，使用fallback: {exc}")
            return await self._get_fallback_evaluation(judge_result)

    async def _evaluate_with_real_ai(
        self,
        submission: CodeSubmission,
        question_prompt: Optional[str] = None,
        judge_result: Optional[Dict[str, Any]] = None
    ) -> AIEvaluationResponse:
        logger.info(f"开始真实AI评估，使用provider: {self.provider}, model: {self.model}")

        prompt = self._build_evaluation_prompt(
            submission=submission,
            question_prompt=question_prompt,
            judge_result=judge_result
        )

        if self.provider in ("openai", "minimax", "custom"):
            return await self._call_openai_api(prompt)
        elif self.provider == "anthropic":
            return await self._call_anthropic_api(prompt)
        elif self.provider == "azure":
            return await self._call_azure_openai_api(prompt)
        else:
            logger.warning(f"未知的AI provider: {self.provider}，使用fallback")
            return await self._get_fallback_evaluation(judge_result)

    def _build_evaluation_prompt(
        self,
        submission: CodeSubmission,
        question_prompt: Optional[str] = None,
        judge_result: Optional[Dict[str, Any]] = None
    ) -> str:
        prompt_parts = [
            "你是一个专业的编程面试官。请评估以下代码提交：",
            "",
            f"题目ID: {submission.question_id}",
            f"编程语言: {submission.language}",
            "",
            "=== 用户代码 ===",
            submission.source_code,
            ""
        ]

        if question_prompt:
            prompt_parts.extend([
                "=== 题目提示 ===",
                question_prompt,
                ""
            ])

        if judge_result:
            passed = judge_result.get('passed_count', 0)
            total = judge_result.get('total_cases', 0)
            pass_rate = judge_result.get('pass_rate', 0.0)

            prompt_parts.extend([
                "=== 判题结果 ===",
                f"通过测试用例: {passed}/{total}",
                f"通过率: {pass_rate:.1f}%",
                ""
            ])

        prompt_parts.extend([
            "=== 评估要求 ===",
            "请以JSON格式返回评估结果，包含以下字段：",
            "1. is_correct: boolean - 代码逻辑是否正确",
            "2. score: integer (0-100) - 代码质量评分",
            "3. feedback: string - 详细的改进建议",
            "4. optimized_code: string or null - 优化后的代码示例（可选）",
            "",
            "评估时请考虑：",
            "- 代码正确性（是否解决了问题）",
            "- 代码可读性",
            "- 时间复杂度",
            "- 空间复杂度",
            "- 边界情况处理",
            "- 代码风格",
            "",
            "请直接返回JSON，不要有其他文字："
        ])

        return "\n".join(prompt_parts)

    async def _call_openai_api(self, prompt: str) -> AIEvaluationResponse:
        try:
            import openai
            import httpx
        except ImportError:
            logger.error("openai库未安装，无法调用API")
            raise RuntimeError("openai库未安装")

        http_client = httpx.AsyncClient(
            timeout=self.timeout,
            trust_env=False,
        )

        try:
            client_kwargs = {
                "api_key": self.api_key,
                "http_client": http_client,
            }
            base_url = self.base_url
            if base_url:
                if not base_url.endswith("/v1"):
                    base_url = base_url.rstrip("/") + "/v1"
                client_kwargs["base_url"] = base_url

            client = openai.AsyncOpenAI(**client_kwargs)

            extra_body = None
            if getattr(self, 'provider', '') == 'minimax' and getattr(self, 'group_id', None):
                extra_body = {"group_id": self.group_id}

            try:
                response = await client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "你是一个专业的编程面试官，请评估代码质量。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"},
                    extra_body=extra_body,
                )

                content = response.choices[0].message.content
                if not content:
                    raise ValueError("API返回空内容")

                result_data = json.loads(content)
                return AIEvaluationResponse(**result_data)

            finally:
                await client.close()

        except json.JSONDecodeError as e:
            logger.error(f"解析AI响应JSON失败: {e}, 内容: {content[:200]}")
            raise ValueError(f"无效的JSON响应: {e}")
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {e}")
            raise
        finally:
            try:
                await http_client.aclose()
            except Exception:
                pass

    async def _call_anthropic_api(self, prompt: str) -> AIEvaluationResponse:
        logger.warning("Anthropic API暂未实现，使用fallback")
        raise NotImplementedError("Anthropic API暂未实现")

    async def _call_azure_openai_api(self, prompt: str) -> AIEvaluationResponse:
        logger.warning("Azure OpenAI API暂未实现，使用fallback")
        raise NotImplementedError("Azure OpenAI API暂未实现")

    async def _get_mock_evaluation(self) -> AIEvaluationResponse:
        logger.info("正在模拟 AI 大模型评估过程...")
        await asyncio.sleep(2)

        mock_result = {
            "is_correct": True,
            "score": 85,
            "feedback": "逻辑基本正确，但时间复杂度可以优化为 O(n)。",
            "optimized_code": "def optimized_func():\n    pass # 这里是优化的代码"
        }

        return AIEvaluationResponse(**mock_result)

    async def _get_fallback_evaluation(
        self,
        judge_result: Optional[Dict[str, Any]] = None
    ) -> AIEvaluationResponse:
        if judge_result:
            passed = judge_result.get('passed_count', 0)
            total = judge_result.get('total_cases', 1)
            pass_rate = judge_result.get('pass_rate', 0.0)

            score = int(pass_rate)
            is_correct = score >= 80

            feedback = f"代码通过了 {passed}/{total} 个测试用例，通过率 {pass_rate:.1f}%。"
            if is_correct:
                feedback += " 代码基本正确，但仍有改进空间。"
            else:
                feedback += " 代码需要进一步优化以通过更多测试用例。"
        else:
            score = 50
            is_correct = False
            feedback = "AI评估暂时不可用，请检查配置后重试。"

        return AIEvaluationResponse(
            is_correct=is_correct,
            score=score,
            feedback=feedback,
            optimized_code=None
        )
