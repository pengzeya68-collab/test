"""Schemas for onboarding assessment."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class AssessmentQuestion(BaseModel):
    id: int
    dimension: str
    dimension_name: str
    question: str
    options: list[str]
    difficulty: int = 1


class AssessmentAnswer(BaseModel):
    question_id: int
    selected_index: int


class AssessmentSubmitRequest(BaseModel):
    answers: list[AssessmentAnswer]


class DimensionScore(BaseModel):
    key: str
    name: str
    score: int
    level: str


class AssessmentSubmitResponse(BaseModel):
    overall_score: float
    overall_level: str
    dimension_scores: list[DimensionScore]
    recommended_paths: list[RecommendedPath]
    has_completed_assessment: bool = True


class RecommendedPath(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    priority: int = 1
    reason: str = ""


class AssessmentStatusResponse(BaseModel):
    has_completed_assessment: bool
    overall_score: Optional[float] = None
    overall_level: Optional[str] = None
