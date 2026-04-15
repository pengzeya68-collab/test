"""
面试题库统计 Schema
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class QuestionStatistics(BaseModel):
    """单个题目的统计信息"""
    question_id: int = Field(..., description="题目ID")
    title: str = Field(..., description="题目标题")
    slug: str = Field(..., description="URL标识")
    difficulty: str = Field(..., description="难度: easy/medium/hard")
    is_published: bool = Field(..., description="是否发布")

    # 提交统计
    total_submissions: int = Field(0, description="总提交次数")
    completed_submissions: int = Field(0, description="完成评估的提交次数（有分数）")

    # 分数统计
    average_score: Optional[float] = Field(None, description="平均分（仅completed_submissions > 0时有效）")
    highest_score: Optional[int] = Field(None, description="最高分")
    lowest_score: Optional[int] = Field(None, description="最低分")

    # 通过率统计（分数≥80为通过）
    pass_rate: float = Field(0.0, description="通过率（百分比）")
    passed_count: int = Field(0, description="通过次数（分数≥80）")
    failed_count: int = Field(0, description="未通过次数（分数<80）")

    # 时间统计
    recent_7_days_submissions: int = Field(0, description="最近7天提交次数")
    recent_30_days_submissions: int = Field(0, description="最近30天提交次数")
    last_submission_time: Optional[datetime] = Field(None, description="最近一次提交时间")

    # 创建时间
    created_at: datetime = Field(..., description="题目创建时间")

    model_config = ConfigDict(from_attributes=True)


class QuestionStatisticsListResponse(BaseModel):
    """题目统计列表响应"""
    items: List[QuestionStatistics] = Field(..., description="统计项列表")
    total: int = Field(..., description="总题目数")
    page: int = Field(..., description="页码")
    size: int = Field(..., description="每页数量")
    pages: int = Field(..., description="总页数")


class OverallStatistics(BaseModel):
    """整体题库统计"""
    total_questions: int = Field(0, description="总题目数")
    published_questions: int = Field(0, description="已发布题目数")
    total_submissions: int = Field(0, description="总提交次数")
    completed_submissions: int = Field(0, description="完成评估的提交次数")

    # 分数概况
    average_score: Optional[float] = Field(None, description="整体平均分")
    pass_rate: float = Field(0.0, description="整体通过率")

    # 难度分布
    easy_count: int = Field(0, description="简单题数量")
    medium_count: int = Field(0, description="中等题数量")
    hard_count: int = Field(0, description="困难题数量")

    # 活动统计
    recent_7_days_activity: int = Field(0, description="最近7天总提交次数")
    recent_30_days_activity: int = Field(0, description="最近30天总提交次数")

    # 热门题目（前5）
    top_questions: List[QuestionStatistics] = Field(default_factory=list, description="热门题目排行（按提交次数）")


class TimeSeriesDataPoint(BaseModel):
    """时间序列数据点"""
    date: str = Field(..., description="日期，格式：YYYY-MM-DD")
    count: int = Field(0, description="数量")


class SubmissionTrendResponse(BaseModel):
    """提交趋势响应"""
    daily_submissions: List[TimeSeriesDataPoint] = Field(default_factory=list, description="每日提交统计")
    weekly_submissions: List[TimeSeriesDataPoint] = Field(default_factory=list, description="每周提交统计")
    monthly_submissions: List[TimeSeriesDataPoint] = Field(default_factory=list, description="每月提交统计")


class DifficultyAnalysis(BaseModel):
    """难度分析"""
    difficulty: str = Field(..., description="难度等级")
    question_count: int = Field(0, description="题目数量")
    submission_count: int = Field(0, description="提交次数")
    average_score: Optional[float] = Field(None, description="平均分")
    pass_rate: float = Field(0.0, description="通过率")


class DifficultyAnalysisResponse(BaseModel):
    """难度分析响应"""
    analysis: List[DifficultyAnalysis] = Field(default_factory=list, description="难度分析列表")