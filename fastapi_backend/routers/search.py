"""
全局搜索路由
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from fastapi_backend.core.database import get_db
from fastapi_backend.models.models import Exercise, Post, Exam, LearningPath

router = APIRouter(prefix="/api/v1/search", tags=["搜索"])


@router.get("")
async def global_search(
    q: str = Query(..., min_length=1),
    category: Optional[str] = Query(None, description="exercises/posts/exams/paths"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    results = {"exercises": [], "posts": [], "exams": [], "paths": []}
    total = 0
    offset = (page - 1) * page_size

    if not category or category == "exercises":
        base = select(Exercise).where(or_(Exercise.title.contains(q), Exercise.description.contains(q)))
        count = await db.scalar(select(func.count()).select_from(base.subquery()))
        total += count or 0
        if category:
            stmt = base.offset(offset).limit(page_size)
        else:
            stmt = base.limit(5)
        r = await db.execute(stmt)
        results["exercises"] = [
            {
                "id": e.id,
                "title": e.title,
                "difficulty": e.difficulty,
                "knowledge_point": e.knowledge_point,
            }
            for e in r.scalars().all()
        ]

    if not category or category == "posts":
        base = select(Post).where(or_(Post.title.contains(q), Post.content.contains(q)))
        count = await db.scalar(select(func.count()).select_from(base.subquery()))
        total += count or 0
        if category:
            stmt = base.offset(offset).limit(page_size)
        else:
            stmt = base.limit(5)
        r = await db.execute(stmt)
        results["posts"] = [
            {"id": p.id, "title": p.title, "summary": p.summary, "category": p.category} for p in r.scalars().all()
        ]

    if not category or category == "exams":
        base = select(Exam).where(Exam.title.contains(q))
        count = await db.scalar(select(func.count()).select_from(base.subquery()))
        total += count or 0
        if category:
            stmt = base.offset(offset).limit(page_size)
        else:
            stmt = base.limit(5)
        r = await db.execute(stmt)
        results["exams"] = [{"id": e.id, "title": e.title, "difficulty": e.difficulty} for e in r.scalars().all()]

    if not category or category == "paths":
        base = select(LearningPath).where(or_(LearningPath.title.contains(q), LearningPath.description.contains(q)))
        count = await db.scalar(select(func.count()).select_from(base.subquery()))
        total += count or 0
        if category:
            stmt = base.offset(offset).limit(page_size)
        else:
            stmt = base.limit(5)
        r = await db.execute(stmt)
        results["paths"] = [{"id": lp.id, "title": lp.title, "difficulty": lp.difficulty} for lp in r.scalars().all()]

    return {"query": q, "total": total, "page": page, "page_size": page_size, "results": results}
