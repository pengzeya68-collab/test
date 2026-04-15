"""Schemas for learning paths – migrated from Flask backend/api/learning_paths.py."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── Exercise schemas ──────────────────────────────────────

class ExerciseBrief(BaseModel):
    """Brief exercise info included in learning path responses."""
    id: int
    title: str
    description: Optional[str] = None
    difficulty: Optional[str] = None
    exercise_type: Optional[str] = None
    category: Optional[str] = None
    knowledge_point: Optional[str] = None
    time_estimate: Optional[int] = None
    language: Optional[str] = None

    model_config = {"from_attributes": True}


# ── Learning path schemas ─────────────────────────────────

class LearningPathCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    language: str
    difficulty: Optional[str] = "beginner"
    stage: Optional[int] = 1
    estimated_hours: Optional[int] = 10
    is_public: Optional[bool] = True


class LearningPathUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    difficulty: Optional[str] = None
    stage: Optional[int] = None
    estimated_hours: Optional[int] = None
    is_public: Optional[bool] = None


class LearningPathResponse(BaseModel):
    """Response for list endpoint – no exercises."""
    id: int
    title: str
    description: Optional[str] = None
    language: str
    difficulty: Optional[str] = None
    stage: Optional[int] = None
    estimated_hours: Optional[int] = None
    is_public: Optional[bool] = None
    created_by: Optional[int] = None
    exercise_count: int = 0

    model_config = {"from_attributes": True}


class LearningPathDetail(LearningPathResponse):
    """Detail endpoint – includes exercises and timestamps."""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    exercises: list[ExerciseBrief] = []

    model_config = {"from_attributes": True}


class AddExerciseRequest(BaseModel):
    exercise_id: int
