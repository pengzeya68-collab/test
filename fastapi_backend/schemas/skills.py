"""Schemas for skills – migrated from Flask backend/api/skills.py."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class SkillItem(BaseModel):
    key: str
    name: str
    description: str
    score: int
    level: str
    suggestion: str
    weight: float


class IndustryAverageItem(BaseModel):
    name: str
    score: int


class RadarIndicator(BaseModel):
    name: str
    max: int = 100


class RadarData(BaseModel):
    indicators: list[RadarIndicator]
    user_data: list[int]
    industry_data: list[int]


class SkillRadarResponse(BaseModel):
    overall_score: float
    overall_level: str
    skills: list[SkillItem]
    industry_average: list[IndustryAverageItem]
    radar_data: RadarData


class RecommendedExercise(BaseModel):
    id: int
    title: str
    difficulty: Optional[str] = None
    time_estimate: Optional[int] = None


class SkillDetailResponse(BaseModel):
    key: str
    name: str
    description: str
    score: int
    level: str
    suggestion: str
    recommended_exercises: list[RecommendedExercise]


class SkillProgressItem(BaseModel):
    skill: str
    current: int
    target: int
    monthly_growth: int
    months_needed: Optional[float] = None


class SkillProgressResponse(BaseModel):
    progress: list[SkillProgressItem]
    last_updated: str
