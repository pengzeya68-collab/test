"""
AI模拟面试会话 Schema
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class InterviewSessionBase(BaseModel):
    """会话基础信息"""
    user_id: int = Field(..., description="用户ID")
    question_id: Optional[int] = Field(None, description="题目ID（旧会话可能没有）")
    status: str = Field(default="started", description="状态: started/submitted/finished/abandoned")
    latest_score: Optional[int] = Field(None, ge=0, le=100, description="最新成绩 (0-100)")
    latest_submission_id: Optional[int] = Field(None, description="最新提交记录ID")


class InterviewSessionCreate(BaseModel):
    """创建会话 - 通常由系统自动创建"""
    question_id: int = Field(..., description="题目ID")
    # user_id 从当前登录用户获取，不需要前端传递


class InterviewSessionUpdate(BaseModel):
    """更新会话状态"""
    status: Optional[str] = Field(None, description="状态: started/submitted/finished/abandoned")
    latest_score: Optional[int] = Field(None, ge=0, le=100, description="最新成绩 (0-100)")
    latest_submission_id: Optional[int] = Field(None, description="最新提交记录ID")
    finished_at: Optional[datetime] = Field(None, description="结束时间")


class InterviewSessionDetail(InterviewSessionBase):
    """会话详情"""
    id: int
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InterviewSessionList(BaseModel):
    """会话列表项"""
    id: int
    user_id: int
    question_id: Optional[int] = None
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    latest_score: Optional[int] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class InterviewSessionWithQuestion(BaseModel):
    """会话详情包含题目信息"""
    id: int
    user_id: int
    question_id: Optional[int] = None
    status: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    latest_score: Optional[int] = None
    latest_submission_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    question_title: Optional[str] = None
    question_difficulty: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)