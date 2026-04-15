"""
AI模拟面试题目 Schema
"""
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field


class InterviewQuestionBase(BaseModel):
    """题目基础信息"""
    title: str = Field(..., min_length=1, max_length=500, description="题目标题")
    slug: Optional[str] = Field(None, min_length=1, max_length=200, description="URL友好标识，需唯一")
    difficulty: str = Field(default="medium", description="难度: easy/medium/hard")
    tags: Optional[str] = Field(None, description="标签列表 JSON 格式，如 [\"数组\", \"动态规划\"]")
    description: Optional[str] = Field(None, description="题目描述，支持Markdown")
    prompt: Optional[str] = Field(None, description="AI提示词，用于引导AI评估")
    input_spec: Optional[str] = Field(None, description="输入规范说明")
    output_spec: Optional[str] = Field(None, description="输出规范说明")
    examples: Optional[str] = Field(None, description="示例输入输出 JSON 格式")
    reference_solution: Optional[str] = Field(None, description="参考答案，支持多语言代码")
    test_cases: Optional[str] = Field(None, description="测试用例 JSON 格式（旧字段，逐步迁移到TestCase表）")
    is_published: bool = Field(default=True, description="是否发布")


class InterviewQuestionCreate(InterviewQuestionBase):
    """创建题目"""
    pass


class InterviewQuestionUpdate(BaseModel):
    """更新题目 - 所有字段可选"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="题目标题")
    slug: Optional[str] = Field(None, min_length=1, max_length=200, description="URL友好标识，需唯一")
    difficulty: Optional[str] = Field(None, description="难度: easy/medium/hard")
    tags: Optional[str] = Field(None, description="标签列表 JSON 格式")
    description: Optional[str] = Field(None, min_length=1, description="题目描述")
    prompt: Optional[str] = Field(None, min_length=1, description="AI提示词")
    input_spec: Optional[str] = Field(None, description="输入规范说明")
    output_spec: Optional[str] = Field(None, description="输出规范说明")
    examples: Optional[str] = Field(None, description="示例输入输出 JSON 格式")
    reference_solution: Optional[str] = Field(None, description="参考答案")
    test_cases: Optional[str] = Field(None, description="测试用例 JSON 格式")
    is_published: Optional[bool] = Field(None, description="是否发布")


class InterviewQuestionDetail(InterviewQuestionBase):
    """题目详情"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewQuestionList(BaseModel):
    """题目列表项"""
    id: int
    title: str
    slug: Optional[str] = None
    difficulty: str
    tags: Optional[str] = None
    is_published: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InterviewQuestionListResponse(BaseModel):
    """题目列表响应"""
    items: list[InterviewQuestionList]
    total: int
    page: int
    size: int
    pages: int