"""
AI导师评估功能测试
覆盖代码评估、AI反馈生成
"""

import pytest
from unittest.mock import patch
import asyncio

from fastapi_backend.schemas.interview import CodeSubmission
from fastapi_backend.services.ai_tutor_service import AITutorService


class TestAIEvaluation:
    """AI评估功能测试"""

    def setup_method(self):
        self.tutor = AITutorService()

    @patch("fastapi_backend.services.ai_tutor_service.AITutorService._evaluate_with_real_ai")
    @pytest.mark.asyncio
    async def test_evaluate_code_with_mock(self, mock_evaluate):
        """测试代码评估功能 - 使用mock"""
        mock_evaluate.return_value = {
            "is_correct": True,
            "score": 85,
            "feedback": "代码逻辑清晰",
            "optimized_code": None,
        }

        submission = CodeSubmission(
            source_code="print('hello')",
            language="python",
            question_id="1",
        )

        result = await self.tutor.evaluate_code(submission)

        assert result is not None
        assert hasattr(result, "score")
        assert result.score == 85
        assert hasattr(result, "feedback")

    @pytest.mark.asyncio
    async def test_evaluate_code_empty_submission(self):
        """测试空提交处理"""
        submission = CodeSubmission(
            source_code=" ",
            language="python",
            question_id="1",
        )

        result = await self.tutor.evaluate_code(submission)

        assert result is not None
        assert hasattr(result, "score")

    @pytest.mark.asyncio
    async def test_evaluate_code_different_languages(self):
        """测试不同编程语言评估"""
        languages = ["python", "javascript", "java", "cpp"]

        for lang in languages:
            submission = CodeSubmission(
                source_code=f"// {lang} code",
                language=lang,
                question_id="1",
            )

            result = await self.tutor.evaluate_code(submission)
            assert result is not None
            assert hasattr(result, "score")

    @patch("fastapi_backend.services.ai_tutor_service.AITutorService._evaluate_with_real_ai")
    @pytest.mark.asyncio
    async def test_evaluate_code_timeout_handling(self, mock_evaluate):
        """测试AI服务超时处理"""
        mock_evaluate.side_effect = asyncio.TimeoutError()

        submission = CodeSubmission(
            source_code="print('hello')",
            language="python",
            question_id="1",
        )

        result = await self.tutor.evaluate_code(submission)

        assert result is not None
        assert hasattr(result, "score")

    @patch("fastapi_backend.services.ai_tutor_service.AITutorService._evaluate_with_real_ai")
    @pytest.mark.asyncio
    async def test_evaluate_code_error_handling(self, mock_evaluate):
        """测试AI服务异常处理"""
        mock_evaluate.side_effect = Exception("AI服务异常")

        submission = CodeSubmission(
            source_code="print('hello')",
            language="python",
            question_id="1",
        )

        result = await self.tutor.evaluate_code(submission)

        assert result is not None
        assert hasattr(result, "score")
