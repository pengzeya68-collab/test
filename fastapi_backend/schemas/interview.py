from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class CodeSubmission(BaseModel):
    question_id: str = Field(..., description="面试题的唯一ID")
    language: str = Field(default="python", description="编程语言")
    source_code: str = Field(..., min_length=1, description="用户编写的源码")


class AIEvaluationResponse(BaseModel):
    is_correct: bool = Field(..., description="代码逻辑是否正确")
    score: int = Field(..., ge=0, le=100, description="代码得分")
    feedback: str = Field(..., description="AI 导师的详细评价")
    optimized_code: str | None = Field(None, description="AI 提供的优化后代码")


class UserInterviewStatistics(BaseModel):
    """用户面试统计信息"""
    # 基础统计
    total_submissions: int = Field(..., description="总提交数")
    completed_submissions: int = Field(..., description="已完成评估的提交数")

    # 分数统计
    average_score: Optional[float] = Field(None, description="平均分（仅计算有分数的提交）")
    highest_score: Optional[int] = Field(None, description="最高分")
    lowest_score: Optional[int] = Field(None, description="最低分")

    # 通过率统计
    pass_rate: float = Field(..., description="通过率（0-100）")
    passed_count: int = Field(..., description="通过的提交数（分数≥80）")
    failed_count: int = Field(..., description="未通过的提交数")

    # 时间统计
    recent_7_days_submissions: int = Field(..., description="最近7天提交量")
    today_submissions: int = Field(..., description="今日提交量")

    # 难度分布
    difficulty_distribution: Dict[str, int] = Field(
        default_factory=dict,
        description="各难度题目提交分布：{'easy': 5, 'medium': 3, 'hard': 1}"
    )

    # 最近7天每日提交量（用于图表）
    daily_submissions_last_7_days: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="最近7天每日提交量，格式：[{'date': '2024-01-01', 'count': 3}, ...]"
    )

    # 常见弱项（按标签统计）
    weak_tags: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="弱项标签统计，格式：[{'tag': '动态规划', 'count': 5, 'avg_score': 65.5}, ...]"
    )

    # 最近一次提交时间
    last_submission_time: Optional[datetime] = Field(None, description="最近一次提交时间")
