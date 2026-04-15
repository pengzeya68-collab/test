"""
在线练习相关的数据模型
"""
from typing import Optional
from pydantic import BaseModel, Field

from fastapi_backend.schemas.interview import AIEvaluationResponse


class ExerciseSubmission(BaseModel):
    """练习代码提交"""
    exercise_id: str = Field(..., description="练习的唯一ID")
    language: str = Field(default="python", description="编程语言")
    source_code: str = Field(..., min_length=1, description="用户编写的源码")
    # 可选字段，用于提供更多上下文
    exercise_description: Optional[str] = Field(None, description="练习描述")
    test_cases: Optional[str] = Field(None, description="测试用例（JSON格式）")
    expected_output: Optional[str] = Field(None, description="预期输出")


class ExerciseEvaluationResponse(AIEvaluationResponse):
    """练习评估响应（扩展AI评估响应）"""
    pass  # 目前与AI评估响应相同，未来可能添加练习特定字段