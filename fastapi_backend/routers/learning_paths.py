"""Learning paths router – migrated from Flask backend/api/learning_paths.py."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.models import Exercise, LearningPath, User, Progress
from fastapi_backend.schemas.learning_paths import (
    AddExerciseRequest,
    LearningPathCreate,
    LearningPathDetail,
    LearningPathResponse,
    LearningPathUpdate,
)

router = APIRouter(prefix="/api/v1/learning-paths", tags=["Learning Paths"])


def _fmt_dt(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S") if dt else ""


# ── Public endpoints ──────────────────────────────────────

@router.get("/", response_model=list[LearningPathResponse])
async def get_learning_paths(
    stage: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """Get all public learning paths, optionally filtered by stage."""
    q = select(LearningPath).options(selectinload(LearningPath.exercises)).filter(
        LearningPath.is_public == True
    )
    if stage is not None:
        q = q.filter(LearningPath.stage == stage)

    result = await db.execute(q)
    paths = result.scalars().all()

    return [
        LearningPathResponse(
            id=p.id,
            title=p.title,
            description=p.description,
            language=p.language,
            difficulty=p.difficulty,
            stage=p.stage,
            estimated_hours=p.estimated_hours,
            is_public=p.is_public,
            created_by=p.user_id,
            exercise_count=len(p.exercises),
        )
        for p in paths
    ]


@router.get("/all-progress")
async def get_all_paths_progress(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's progress for all learning paths."""
    q = select(LearningPath).options(selectinload(LearningPath.exercises)).filter(
        LearningPath.is_public == True  # noqa: E712
    )
    result = await db.execute(q)
    paths = result.scalars().all()

    all_exercise_ids = []
    path_exercise_map = {}
    for p in paths:
        ids = [ex.id for ex in p.exercises]
        all_exercise_ids.extend(ids)
        path_exercise_map[p.id] = {
            "total": len(ids),
            "ids": ids,
        }

    progress_map = {}
    if all_exercise_ids:
        progress_stmt = select(Progress).where(
            Progress.user_id == current_user.id,
            Progress.exercise_id.in_(all_exercise_ids),
        )
        progress_result = await db.execute(progress_stmt)
        for p in progress_result.scalars().all():
            if p.completed:
                progress_map.setdefault(p.exercise_id, True)

    result_list = []
    for p in paths:
        info = path_exercise_map[p.id]
        completed = sum(1 for eid in info["ids"] if progress_map.get(eid, False))
        result_list.append({
            "path_id": p.id,
            "total_exercises": info["total"],
            "completed_exercises": completed,
            "progress_percent": round(completed / info["total"] * 100, 1) if info["total"] > 0 else 0,
        })

    return {"progress": result_list}


@router.get("/{path_id}", response_model=LearningPathDetail)
async def get_learning_path(
    path_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a single learning path with its exercises."""
    q = (
        select(LearningPath)
        .options(selectinload(LearningPath.exercises))
        .filter(LearningPath.id == path_id)
    )
    result = await db.execute(q)
    path = result.scalar_one_or_none()

    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    if not path.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    return LearningPathDetail(
        id=path.id,
        title=path.title,
        description=path.description,
        language=path.language,
        difficulty=path.difficulty,
        stage=path.stage,
        estimated_hours=path.estimated_hours,
        is_public=path.is_public,
        created_by=path.user_id,
        exercise_count=len(path.exercises),
        created_at=_fmt_dt(path.created_at),
        updated_at=_fmt_dt(path.updated_at),
        exercises=[
            {
                "id": ex.id,
                "title": ex.title,
                "description": ex.description,
                "difficulty": ex.difficulty,
                "exercise_type": ex.exercise_type,
                "category": ex.category,
                "knowledge_point": ex.knowledge_point,
                "time_estimate": ex.time_estimate,
                "language": ex.language,
            }
            for ex in path.exercises
        ],
    )


# ── Authenticated endpoints ───────────────────────────────

@router.post("/", response_model=LearningPathDetail, status_code=201)
async def create_learning_path(
    payload: LearningPathCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new learning path."""
    new_path = LearningPath(
        title=payload.title,
        description=payload.description or "",
        language=payload.language,
        difficulty=payload.difficulty or "beginner",
        stage=payload.stage or 1,
        estimated_hours=payload.estimated_hours or 10,
        is_public=payload.is_public if payload.is_public is not None else True,
        user_id=current_user.id,
    )
    db.add(new_path)
    await db.commit()
    await db.refresh(new_path)

    return LearningPathDetail(
        id=new_path.id,
        title=new_path.title,
        description=new_path.description,
        language=new_path.language,
        difficulty=new_path.difficulty,
        stage=new_path.stage,
        estimated_hours=new_path.estimated_hours,
        is_public=new_path.is_public,
        created_by=new_path.user_id,
        exercise_count=0,
        created_at=_fmt_dt(new_path.created_at),
        updated_at=_fmt_dt(new_path.updated_at),
        exercises=[],
    )


@router.put("/{path_id}")
async def update_learning_path(
    path_id: int,
    payload: LearningPathUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a learning path (owner only)."""
    result = await db.execute(
        select(LearningPath).filter(LearningPath.id == path_id)
    )
    path = result.scalar_one_or_none()

    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    if path.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    if payload.title is not None:
        path.title = payload.title
    if payload.description is not None:
        path.description = payload.description
    if payload.language is not None:
        path.language = payload.language
    if payload.difficulty is not None:
        path.difficulty = payload.difficulty
    if payload.stage is not None:
        path.stage = payload.stage
    if payload.estimated_hours is not None:
        path.estimated_hours = payload.estimated_hours
    if payload.is_public is not None:
        path.is_public = payload.is_public

    await db.commit()
    return {"message": "Learning path updated successfully"}


@router.delete("/{path_id}")
async def delete_learning_path(
    path_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a learning path (owner only)."""
    result = await db.execute(
        select(LearningPath).filter(LearningPath.id == path_id)
    )
    path = result.scalar_one_or_none()

    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    if path.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(path)
    await db.commit()
    return {"message": "Learning path deleted successfully"}


# ── Exercises in a learning path ──────────────────────────

@router.get("/{path_id}/exercises", response_model=list[dict])
async def get_path_exercises(
    path_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all exercises in a learning path."""
    q = (
        select(LearningPath)
        .options(selectinload(LearningPath.exercises))
        .filter(LearningPath.id == path_id)
    )
    result = await db.execute(q)
    path = result.scalar_one_or_none()

    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    if not path.is_public and path.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    return [
        {
            "id": ex.id,
            "title": ex.title,
            "description": ex.description,
            "difficulty": ex.difficulty,
            "exercise_type": ex.exercise_type,
            "language": ex.language,
            "category": ex.category,
            "time_estimate": ex.time_estimate,
        }
        for ex in path.exercises
    ]


@router.post("/{path_id}/exercises")
async def add_exercise_to_path(
    path_id: int,
    payload: AddExerciseRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Add an exercise to a learning path (owner only)."""
    result = await db.execute(
        select(LearningPath).filter(LearningPath.id == path_id)
    )
    path = result.scalar_one_or_none()

    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")
    if path.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    ex_result = await db.execute(
        select(Exercise).filter(Exercise.id == payload.exercise_id)
    )
    exercise = ex_result.scalar_one_or_none()

    if not exercise:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if exercise.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to exercise")

    exercise.learning_path_id = path_id
    await db.commit()
    return {"message": "Exercise added to learning path successfully"}


@router.get("/{path_id}/progress")
async def get_learning_path_progress(
    path_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get current user's progress for a specific learning path."""
    q = (
        select(LearningPath)
        .options(selectinload(LearningPath.exercises))
        .filter(LearningPath.id == path_id)
    )
    result = await db.execute(q)
    path = result.scalar_one_or_none()

    if not path:
        raise HTTPException(status_code=404, detail="Learning path not found")

    exercise_ids = [ex.id for ex in path.exercises]
    total = len(exercise_ids)

    if total == 0:
        return {
            "path_id": path_id,
            "total_exercises": 0,
            "completed_exercises": 0,
            "progress_percent": 0,
            "exercises": [],
        }

    progress_stmt = select(Progress).where(
        Progress.user_id == current_user.id,
        Progress.exercise_id.in_(exercise_ids),
    )
    progress_result = await db.execute(progress_stmt)
    progresses = progress_result.scalars().all()

    progress_map = {}
    for p in progresses:
        progress_map[p.exercise_id] = {
            "completed": p.completed or False,
            "score": p.score,
            "attempts": p.attempts or 0,
        }

    completed_count = sum(1 for ex_id in exercise_ids if progress_map.get(ex_id, {}).get("completed", False))

    exercises = []
    for ex in path.exercises:
        p = progress_map.get(ex.id, {})
        exercises.append({
            "id": ex.id,
            "title": ex.title,
            "completed": p.get("completed", False),
            "score": p.get("score"),
            "attempts": p.get("attempts", 0),
        })

    return {
        "path_id": path_id,
        "total_exercises": total,
        "completed_exercises": completed_count,
        "progress_percent": round(completed_count / total * 100, 1) if total > 0 else 0,
        "exercises": exercises,
    }
