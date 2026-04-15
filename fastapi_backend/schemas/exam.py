"""Schemas for the exam system – migrated from Flask backend/api/exam.py."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ExamGenerateRequest(BaseModel):
    """智能生成试卷请求"""
    exam_type: str = "模拟考试"
    difficulty: str = "medium"
    duration: int = 60
    knowledge_points: list[str] = []
    question_count: dict[str, int] = {
        "single_choice": 10,
        "multiple_choice": 5,
        "true_false": 5,
        "code": 2,
    }


class ExamSubmitAnswer(BaseModel):
    """单题答案"""
    question_id: int
    answer: str = ""


class ExamSubmitRequest(BaseModel):
    """提交考试请求"""
    answers: list[ExamSubmitAnswer] = []


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------


class AuthorBrief(BaseModel):
    id: int
    username: str


class ExamBrief(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    exam_type: str
    difficulty: str
    duration: int
    total_score: int
    pass_score: int
    is_published: bool
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    created_at: str
    question_count: int
    author: AuthorBrief
    attempt_status: Optional[str] = None
    attempt_score: Optional[int] = None
    attempt_id: Optional[int] = None


class ExamListResponse(BaseModel):
    list: list[ExamBrief]
    total: int
    page: int
    per_page: int


class OptionItem(BaseModel):
    label: str
    text: str


class QuestionBrief(BaseModel):
    id: int
    question_type: str
    content: str
    score: int
    sort_order: int
    options: Optional[list] = None
    correct_answer: Optional[str] = None
    analysis: Optional[str] = None


class ExamDetailResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    exam_type: str
    difficulty: str
    duration: int
    total_score: int
    pass_score: int
    is_published: bool
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    created_at: str
    question_count: int
    author: AuthorBrief
    questions: list[QuestionBrief]
    attempt_status: Optional[str] = None
    attempt_score: Optional[int] = None
    attempt_id: Optional[int] = None


class ExamStartResponse(BaseModel):
    attempt_id: int
    exam: ExamBrief
    questions: list[QuestionBrief]


class ExamSubmitResponse(BaseModel):
    message: str
    score: int
    is_passed: Optional[bool] = None
    attempt_id: int


class AnswerResult(BaseModel):
    question: QuestionBrief
    user_answer: Optional[str] = None
    is_correct: Optional[bool] = None
    score: Optional[int] = None
    feedback: Optional[str] = None


class AttemptInfo(BaseModel):
    id: int
    start_time: str
    end_time: Optional[str] = None
    duration: Optional[int] = None
    score: Optional[int] = None
    is_passed: Optional[bool] = None
    status: str


class QuestionTypeStat(BaseModel):
    total: int = 0
    correct: int = 0
    score: float = 0
    total_score: float = 0


class ExamResultResponse(BaseModel):
    exam: ExamBrief
    attempt: AttemptInfo
    result: list[AnswerResult]
    statistics: dict


class AttemptBrief(BaseModel):
    id: int
    exam_title: str
    exam_type: str
    score: Optional[int] = None
    total_score: int
    is_passed: Optional[bool] = None
    status: str
    created_at: str


class MyAttemptsResponse(BaseModel):
    list: list[AttemptBrief]
    total: int
    page: int
    per_page: int


class ExamGenerateResponse(BaseModel):
    message: str
    exam_id: int
    exam: ExamBrief
