"""
代码提交记录 Schema
"""
import json
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, ConfigDict, Field, computed_field


class SubmissionBase(BaseModel):
    """提交基础信息"""
    session_id: int = Field(..., description="会话ID")
    user_id: int = Field(..., description="用户ID")
    question_id: int = Field(..., description="题目ID")
    language: str = Field(default="python", description="编程语言")
    source_code: str = Field(..., min_length=1, description="源代码")
    execution_status: str = Field(default="pending", description="执行状态: pending/running/success/failed")
    ai_evaluation_status: str = Field(default="pending", description="AI评估状态: pending/running/completed/failed")
    score: Optional[int] = Field(None, ge=0, le=100, description="AI评分 (0-100)")
    feedback: Optional[str] = Field(None, description="AI反馈")
    execution_result: Optional[str] = Field(None, description="执行结果 JSON 格式")


class SubmissionCreate(BaseModel):
    """创建提交记录 - 前端提交的数据"""
    session_id: int = Field(..., description="会话ID")
    language: str = Field(default="python", description="编程语言")
    source_code: str = Field(..., min_length=1, description="源代码")
    # user_id 和 question_id 从会话中获取，不需要前端传递


class SubmissionUpdate(BaseModel):
    """更新提交记录 - 用于更新执行和评估状态"""
    execution_status: Optional[str] = Field(None, description="执行状态: pending/running/success/failed")
    ai_evaluation_status: Optional[str] = Field(None, description="AI评估状态: pending/running/completed/failed")
    score: Optional[int] = Field(None, ge=0, le=100, description="AI评分 (0-100)")
    feedback: Optional[str] = Field(None, description="AI反馈")
    execution_result: Optional[str] = Field(None, description="执行结果 JSON 格式")


class SubmissionDetail(SubmissionBase):
    """提交记录详情"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def parsed_execution_result(self) -> Optional[dict[str, Any]]:
        """解析后的执行结果"""
        if not self.execution_result:
            return None
        try:
            return json.loads(self.execution_result)
        except json.JSONDecodeError:
            return None


class SubmissionList(BaseModel):
    """提交记录列表项"""
    id: int
    session_id: int
    user_id: int
    question_id: int
    language: str
    execution_status: str
    ai_evaluation_status: str
    score: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SubmissionWithSessionInfo(BaseModel):
    """提交记录包含会话信息"""
    id: int
    session_id: int
    user_id: int
    question_id: int
    language: str
    source_code: str
    execution_status: str
    ai_evaluation_status: str
    score: Optional[int] = None
    feedback: Optional[str] = None
    execution_result: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    session_status: str
    question_title: str
    question_difficulty: str

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def parsed_execution_result(self) -> Optional[dict[str, Any]]:
        """解析后的执行结果"""
        if not self.execution_result:
            return None
        try:
            return json.loads(self.execution_result)
        except json.JSONDecodeError:
            return None


class SubmissionResultDetail(SubmissionWithSessionInfo):
    """提交结果详情 - 用于完整评估报告"""
    # 题目详细信息
    question_description: Optional[str] = None
    question_prompt: Optional[str] = None
    question_test_cases: Optional[str] = None

    # 解析后的测试用例结果
    @computed_field
    @property
    def test_case_results(self) -> Optional[list[dict[str, Any]]]:
        """测试用例结果列表"""
        parsed = self.parsed_execution_result
        if not parsed:
            return None
        judge_result = parsed.get("judge_result")
        if not judge_result:
            return None
        return judge_result.get("case_results")

    @computed_field
    @property
    def judge_summary(self) -> Optional[dict[str, Any]]:
        """判题结果摘要"""
        parsed = self.parsed_execution_result
        if not parsed:
            return None
        judge_result = parsed.get("judge_result")
        if not judge_result:
            return None
        # 返回摘要信息
        return {
            "passed_count": judge_result.get("passed_count"),
            "failed_count": judge_result.get("failed_count"),
            "total_cases": judge_result.get("total_cases"),
            "pass_rate": judge_result.get("pass_rate"),
            "all_passed": judge_result.get("all_passed"),
            "summary": judge_result.get("summary"),
            "total_execution_time_ms": judge_result.get("total_execution_time_ms")
        }

    # AI评估结果（已包含在基类中）
    @computed_field
    @property
    def ai_evaluation(self) -> dict[str, Any]:
        """AI评估结果"""
        return {
            "score": self.score,
            "feedback": self.feedback,
            "is_correct": self.score is not None and self.score >= 80 if self.score else False
        }


class SubmissionHistoryItem(BaseModel):
    """提交历史列表项"""
    id: int
    session_id: int
    question_id: int
    question_title: str
    question_difficulty: str
    language: str
    execution_status: str
    ai_evaluation_status: str
    score: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def is_passed(self) -> bool:
        """是否通过（基于判题结果或AI评分）"""
        # 如果AI评分存在，使用80分作为通过标准
        if self.score is not None:
            return self.score >= 80

        # 如果执行状态为success且AI评估完成，视为通过
        if self.execution_status == "success" and self.ai_evaluation_status == "completed":
            return True

        return False

    @computed_field
    @property
    def status_summary(self) -> str:
        """状态摘要"""
        if self.execution_status == "pending":
            return "待执行"
        elif self.execution_status == "running":
            return "执行中"
        elif self.execution_status == "success":
            if self.ai_evaluation_status == "pending":
                return "执行成功，待评估"
            elif self.ai_evaluation_status == "running":
                return "执行成功，评估中"
            elif self.ai_evaluation_status == "completed":
                return f"评估完成 ({self.score}分)"
            elif self.ai_evaluation_status == "failed":
                return "执行成功，评估失败"
        elif self.execution_status == "failed":
            return "执行失败"
        elif self.execution_status == "timeout":
            return "执行超时"

        return "未知状态"