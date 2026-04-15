"""
面试题测试用例 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class TestCaseBase(BaseModel):
    """测试用例基础信息"""
    input: str = Field(..., min_length=0, description="输入数据")
    expected_output: str = Field(..., min_length=0, description="预期输出")
    is_example: bool = Field(default=False, description="是否为示例用例（用户可见）")
    is_hidden: bool = Field(default=False, description="是否为隐藏用例（用户不可见，用于判题）")
    description: Optional[str] = Field(None, description="用例描述")


class TestCaseCreate(TestCaseBase):
    """创建测试用例"""
    question_id: int = Field(..., ge=1, description="关联题目ID")


class TestCaseUpdate(BaseModel):
    """更新测试用例 - 所有字段可选"""
    input: Optional[str] = Field(None, min_length=0, description="输入数据")
    expected_output: Optional[str] = Field(None, min_length=0, description="预期输出")
    is_example: Optional[bool] = Field(None, description="是否为示例用例")
    is_hidden: Optional[bool] = Field(None, description="是否为隐藏用例")
    description: Optional[str] = Field(None, description="用例描述")


class TestCaseDetail(TestCaseBase):
    """测试用例详情"""
    id: int
    question_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestCaseList(BaseModel):
    """测试用例列表项"""
    id: int
    question_id: int
    input: str
    expected_output: str
    is_example: bool
    is_hidden: bool
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TestCaseListResponse(BaseModel):
    """测试用例列表响应"""
    items: list[TestCaseList]
    total: int
    page: int
    size: int
    pages: int


class TestCaseBatchCreate(BaseModel):
    """批量创建测试用例"""
    test_cases: list[TestCaseBase] = Field(..., min_items=1, description="测试用例列表")


class TestCaseBatchUpdate(BaseModel):
    """批量更新测试用例"""
    test_cases: list[TestCaseUpdate] = Field(..., min_items=1, description="测试用例列表")