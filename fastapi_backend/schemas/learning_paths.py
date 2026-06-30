"""Schemas for learning paths – migrated from Flask backend/api/learning_paths.py."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


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
    language: str = "通用"
    difficulty: Optional[str] = "beginner"
    level: Optional[str] = None  # 前端兼容字段，自动映射到 difficulty
    exerciseIds: Optional[List[int]] = None  # 前端兼容字段，关联习题ID
    exercise_ids: Optional[List[int]] = None  # 兼容 snake_case
    stage: Optional[int] = 1
    estimated_hours: Optional[int] = 10
    is_public: Optional[bool] = True


class LearningPathUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    language: Optional[str] = None
    difficulty: Optional[str] = None
    level: Optional[str] = None  # 前端兼容字段，自动映射到 difficulty
    exerciseIds: Optional[List[int]] = None  # 前端兼容字段，关联习题ID
    exercise_ids: Optional[List[int]] = None  # 兼容 snake_case
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


# ── Project practice schemas (admin) ──────────────────────


class ProjectTaskCreate(BaseModel):
    title: str = ""
    description: str = ""
    task_type: str = "test_case_design"
    requirements: str = ""
    hints: str = ""
    score: int = 10


class ProjectResourceCreate(BaseModel):
    title: str = ""
    resource_type: str = "document"
    content: str = ""
    url: str = ""


class ProjectCreateRequest(BaseModel):
    title: str = "新项目"
    description: str = ""
    overview: str = ""
    difficulty: str = "medium"
    status: str = "published"
    estimated_hours: int = 8
    sort_order: int = 0
    tasks: list[ProjectTaskCreate] = []
    resources: list[ProjectResourceCreate] = []
