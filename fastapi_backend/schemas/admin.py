"""
后台管理接口的 Pydantic 请求模型
用于输入验证，替代裸 dict 参数
"""

from typing import Optional, List, Any
from pydantic import BaseModel, Field


# ========== 用户管理 ==========


class AdminUserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="用户名")
    email: str = Field(..., min_length=1, max_length=100, description="邮箱")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    password: str = Field("123456", min_length=6, max_length=100, description="密码")
    is_admin: bool = Field(False, description="是否管理员")
    status: str = Field("active", description="状态: active/disabled")
    level: int = Field(1, ge=1, description="等级")
    score: int = Field(0, ge=0, description="积分")


class AdminUserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    is_admin: Optional[bool] = None
    status: Optional[str] = None
    level: Optional[int] = Field(None, ge=1)
    score: Optional[int] = Field(None, ge=0)


class AdminResetPassword(BaseModel):
    new_password: str = Field("123456", min_length=6, max_length=100, description="新密码")


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class AdminUserStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_admin: Optional[bool] = None


# ========== 考试管理 ==========


class AdminExamQuestionCreate(BaseModel):
    question_type: str = Field("single_choice", description="题目类型")
    content: str = Field("", description="题目内容")
    options: Optional[List[Any]] = Field(None, description="选项列表")
    correct_answer: str = Field("", description="正确答案")
    score: int = Field(10, ge=0, description="分值")
    analysis: str = Field("", description="解析")


class AdminExamCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="考试标题")
    description: str = Field("", description="考试描述")
    exam_type: str = Field("模拟考试", description="考试类型")
    difficulty: str = Field("medium", description="难度")
    duration: int = Field(60, ge=1, description="时长(分钟)")
    total_score: int = Field(100, ge=0, description="总分")
    pass_score: int = Field(60, ge=0, description="及格分")
    is_published: bool = Field(False, description="是否发布")
    start_time: Optional[str] = Field(None, description="开始时间")
    end_time: Optional[str] = Field(None, description="结束时间")
    questions: List[AdminExamQuestionCreate] = Field(default_factory=list, description="题目列表")


class AdminExamUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    exam_type: Optional[str] = None
    difficulty: Optional[str] = None
    duration: Optional[int] = Field(None, ge=1)
    total_score: Optional[int] = Field(None, ge=0)
    pass_score: Optional[int] = Field(None, ge=0)
    is_published: Optional[bool] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    questions: Optional[List[AdminExamQuestionCreate]] = None


class AdminExamPublishToggle(BaseModel):
    is_published: Optional[bool] = Field(None, description="发布状态，不传则切换")


# ========== 习题管理 ==========


class AdminExerciseCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="习题标题")
    content: str = Field("", description="习题内容")
    answer: str = Field("", description="参考答案")
    difficulty: str = Field("easy", description="难度: easy/medium/hard")
    language: str = Field("通用", description="编程语言")
    category: str = Field("", description="分类")


class AdminExerciseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = None
    answer: Optional[str] = None
    difficulty: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None


class AdminExerciseBatchImport(BaseModel):
    items: List[AdminExerciseCreate] = Field(..., min_length=1, description="习题列表")
