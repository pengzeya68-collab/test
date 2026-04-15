"""Exercises CRUD + SQL execution – migrated from Flask backend/api/exercises.py."""
from __future__ import annotations

import sqlite3
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import Exercise, User
from fastapi_backend.schemas.common import SuccessResponse

router = APIRouter(prefix="/api/v1", tags=["exercises"])


# ---------------------------------------------------------------------------
# List exercises (public)
# ---------------------------------------------------------------------------


@router.get("/exercises")
async def get_exercises(
    module: str = Query(""),
    stage: Optional[int] = Query(None),
    category: str = Query(""),
    knowledge_point: str = Query(""),
    db: AsyncSession = Depends(get_db),
):
    """获取公开习题列表"""
    stmt = select(Exercise).where(Exercise.is_public == True)  # noqa: E712

    if module:
        stmt = stmt.where(Exercise.module == module)
    if stage is not None:
        stmt = stmt.where(Exercise.stage == stage)
    if category:
        stmt = stmt.where(Exercise.category == category)
    if knowledge_point:
        stmt = stmt.where(Exercise.knowledge_point.contains(knowledge_point))

    result = await db.execute(stmt)
    exercises = result.scalars().all()

    items = []
    for ex in exercises:
        items.append({
            "id": ex.id,
            "title": ex.title,
            "description": ex.description,
            "difficulty": ex.difficulty,
            "exercise_type": ex.exercise_type,
            "language": ex.language,
            "module": ex.module,
            "category": ex.category,
            "stage": ex.stage,
            "knowledge_point": ex.knowledge_point,
            "time_estimate": ex.time_estimate,
            "is_public": ex.is_public,
            "created_by": ex.user_id,
            "created_at": ex.created_at.isoformat() if ex.created_at else None,
        })
    return items


# ---------------------------------------------------------------------------
# Get single exercise
# ---------------------------------------------------------------------------


@router.get("/exercises/{exercise_id}")
async def get_exercise(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
):
    """获取习题详情"""
    stmt = select(Exercise).where(Exercise.id == exercise_id)
    result = await db.execute(stmt)
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if not ex.is_public:
        raise HTTPException(status_code=403, detail="Access denied")

    return {
        "id": ex.id,
        "title": ex.title,
        "description": ex.description,
        "instructions": ex.instructions,
        "solution": ex.solution,
        "difficulty": ex.difficulty,
        "exercise_type": ex.exercise_type,
        "language": ex.language,
        "module": ex.module,
        "category": ex.category,
        "stage": ex.stage,
        "knowledge_point": ex.knowledge_point,
        "time_estimate": ex.time_estimate,
        "is_public": ex.is_public,
        "created_by": ex.user_id,
        "learning_path_id": ex.learning_path_id,
        "test_cases": ex.test_cases,
        "created_at": ex.created_at.isoformat() if ex.created_at else None,
        "updated_at": ex.updated_at.isoformat() if ex.updated_at else None,
    }


# ---------------------------------------------------------------------------
# Create exercise
# ---------------------------------------------------------------------------


@router.post("/exercises")
async def create_exercise(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建习题"""
    required = ["title", "description", "language", "category"]
    if not body or any(not body.get(f) for f in required):
        raise HTTPException(status_code=400, detail="标题、描述、语言、分类为必填字段，不能为空")

    ex = Exercise(
        title=body["title"],
        description=body["description"],
        instructions=body.get("instructions", ""),
        solution=body.get("solution", ""),
        difficulty=body.get("difficulty", "easy"),
        language=body["language"],
        module=body.get("module", "normal"),
        category=body.get("category"),
        time_estimate=body.get("time_estimate"),
        is_public=body.get("is_public", True),
        user_id=current_user.id,
        learning_path_id=body.get("learning_path_id"),
    )
    db.add(ex)
    await db.commit()
    await db.refresh(ex)

    return {
        "message": "Exercise created successfully",
        "exercise": {
            "id": ex.id,
            "title": ex.title,
            "language": ex.language,
            "difficulty": ex.difficulty,
        },
    }


# ---------------------------------------------------------------------------
# Update exercise
# ---------------------------------------------------------------------------


@router.put("/exercises/{exercise_id}")
async def update_exercise(
    exercise_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新习题"""
    stmt = select(Exercise).where(Exercise.id == exercise_id)
    result = await db.execute(stmt)
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if ex.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    updatable = [
        "title", "description", "instructions", "solution", "difficulty",
        "language", "module", "time_estimate", "is_public", "learning_path_id",
    ]
    for field in updatable:
        if field in body:
            setattr(ex, field, body[field])
    if "category" in body:
        if not body["category"]:
            raise HTTPException(status_code=400, detail="分类不能为空")
        ex.category = body["category"]

    await db.commit()
    return {"message": "Exercise updated successfully"}


# ---------------------------------------------------------------------------
# Delete exercise
# ---------------------------------------------------------------------------


@router.delete("/exercises/{exercise_id}")
async def delete_exercise(
    exercise_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除习题"""
    stmt = select(Exercise).where(Exercise.id == exercise_id)
    result = await db.execute(stmt)
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")
    if ex.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    await db.delete(ex)
    await db.commit()
    return {"message": "Exercise deleted successfully"}


# ---------------------------------------------------------------------------
# Submit solution (simple check)
# ---------------------------------------------------------------------------


@router.post("/exercises/submit")
async def submit_solution(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """提交习题答案"""
    if not body or "exercise_id" not in body or "solution" not in body:
        raise HTTPException(status_code=400, detail="Exercise ID and solution are required")

    stmt = select(Exercise).where(Exercise.id == body["exercise_id"])
    result = await db.execute(stmt)
    ex = result.scalar_one_or_none()
    if not ex:
        raise HTTPException(status_code=404, detail="Exercise not found")

    is_correct = body["solution"].strip() == (ex.solution or "").strip()
    return {
        "correct": is_correct,
        "message": "Solution submitted successfully",
        "expected_solution": ex.solution if is_correct else None,
    }


# ---------------------------------------------------------------------------
# User's exercises
# ---------------------------------------------------------------------------


@router.get("/exercises/user")
async def get_user_exercises(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取当前用户的习题"""
    stmt = select(Exercise).where(Exercise.user_id == current_user.id)
    result = await db.execute(stmt)
    exercises = result.scalars().all()

    return [
        {
            "id": ex.id,
            "title": ex.title,
            "difficulty": ex.difficulty,
            "language": ex.language,
            "module": ex.module,
            "category": ex.category,
            "is_public": ex.is_public,
        }
        for ex in exercises
    ]


# ---------------------------------------------------------------------------
# Public exercises (auth required)
# ---------------------------------------------------------------------------


@router.get("/exercises/public")
async def get_public_exercises(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取公开习题"""
    stmt = select(Exercise).where(Exercise.is_public == True)  # noqa: E712
    result = await db.execute(stmt)
    exercises = result.scalars().all()

    return [
        {
            "id": ex.id,
            "title": ex.title,
            "difficulty": ex.difficulty,
            "language": ex.language,
            "module": ex.module,
            "category": ex.category,
            "created_by": ex.user_id,
        }
        for ex in exercises
    ]


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


@router.get("/exercises/categories")
async def get_categories(
    language: str = Query(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取习题分类"""
    stmt = select(Exercise).where(
        or_(Exercise.user_id == current_user.id, Exercise.is_public == True)  # noqa: E712
    )
    if language:
        stmt = stmt.where(Exercise.language == language)

    result = await db.execute(stmt)
    exercises = result.scalars().all()

    categories: dict = {}
    for ex in exercises:
        cat = ex.category or "Uncategorized"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append({
            "id": ex.id,
            "title": ex.title,
            "difficulty": ex.difficulty,
            "time_estimate": ex.time_estimate,
        })
    return categories


# ---------------------------------------------------------------------------
# Execute SQL (in-memory SQLite)
# ---------------------------------------------------------------------------


@router.post("/exercises/execute-sql")
async def execute_sql(
    body: dict,
    current_user: User = Depends(get_current_user),
):
    """在内存 SQLite 中执行 SQL"""
    if not body or "setup_sql" not in body or "user_sql" not in body:
        raise HTTPException(status_code=400, detail="缺少必要参数：setup_sql 和 user_sql 都是必填项")

    user_sql = body["user_sql"].strip()
    setup_sql = body["setup_sql"]

    if not user_sql:
        raise HTTPException(status_code=400, detail="请输入SQL语句")

    # Block dangerous SQL
    dangerous = ["drop", "delete", "truncate", "alter", "create", "insert", "update", "pragma"]
    lower_sql = user_sql.lower()
    for kw in dangerous:
        if kw in lower_sql:
            raise HTTPException(status_code=400, detail=f"禁止执行包含 {kw} 关键字的SQL语句")

    start_time = time.time()
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    try:
        if setup_sql.strip():
            cursor.executescript(setup_sql)
            conn.commit()

        cursor.execute(user_sql)

        if user_sql.lower().startswith(("select", "show", "describe", "explain")):
            columns = [d[0] for d in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            conn.commit()
            conn.close()
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "columns": columns,
                "rows": [list(row) for row in rows],
                "row_count": len(rows),
                "elapsed_ms": elapsed_ms,
            }
        else:
            conn.commit()
            row_count = cursor.rowcount
            conn.close()
            elapsed_ms = int((time.time() - start_time) * 1000)
            return {
                "success": True,
                "message": f"执行成功，影响 {row_count} 行",
                "row_count": row_count,
                "elapsed_ms": elapsed_ms,
            }
    except sqlite3.Error as e:
        conn.close()
        elapsed_ms = int((time.time() - start_time) * 1000)
        return {"success": False, "error": str(e), "elapsed_ms": elapsed_ms}
