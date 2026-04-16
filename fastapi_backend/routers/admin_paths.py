"""
后台管理子路由 - 学习路径管理
从 admin_manage.py 拆分
"""
from typing import Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db, AsyncSessionLocal
from fastapi_backend.core.exceptions import NotFoundException
from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import User, Exercise, LearningPath, Exam, ExamQuestion, Post, Comment, InterviewQuestion, Submission, Progress
from fastapi_backend.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/admin", tags=["Admin-学习路径"])

@router.get("/paths")
async def list_paths(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取学习路径列表"""
    query = select(LearningPath)

    if keyword:
        query = query.where(
            or_(LearningPath.title.contains(keyword), LearningPath.description.contains(keyword))
        )
    if level:
        query = query.where(LearningPath.difficulty == level)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * size
    query = query.order_by(desc(LearningPath.created_at)).offset(offset).limit(size)
    result = await db.execute(query)
    paths = result.scalars().all()

    path_list = []
    for p in paths:
        path_list.append({
            "id": p.id,
            "title": p.title,
            "description": p.description or "",
            "level": p.difficulty if hasattr(p, "difficulty") else "beginner",
            "exerciseCount": 0,
            "learnCount": 0,
            "completionRate": 0,
        })

    return {"list": path_list, "total": total or 0}


@router.get("/paths/{path_id}")
async def get_path(
    path_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取学习路径详情"""
    result = await db.execute(select(LearningPath).where(LearningPath.id == path_id))
    path = result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    return {
        "id": path.id,
        "title": path.title,
        "description": path.description or "",
        "level": path.difficulty if hasattr(path, "difficulty") else "beginner",
        "exerciseIds": [],
    }


@router.get("/paths/exercises")
async def get_path_exercises(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取可选习题列表（用于穿梭框）"""
    result = await db.execute(select(Exercise))
    exercises = result.scalars().all()

    return [
        {"key": e.id, "label": e.title}
        for e in exercises
    ]


@router.post("/paths")
async def create_path(
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建学习路径"""
    new_path = LearningPath(
        title=data.get("title", ""),
        description=data.get("description", ""),
        difficulty=data.get("level", data.get("difficulty", "beginner")),
        language=data.get("language", "通用"),
    )
    db.add(new_path)
    await db.commit()
    await db.refresh(new_path)
    return {"message": "创建成功", "id": new_path.id}


@router.put("/paths/{path_id}")
async def update_path(
    path_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新学习路径"""
    result = await db.execute(select(LearningPath).where(LearningPath.id == path_id))
    path = result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    if "title" in data:
        path.title = data["title"]
    if "description" in data:
        path.description = data["description"]
    if "level" in data or "difficulty" in data:
        path.difficulty = data.get("level", data.get("difficulty", path.difficulty))

    await db.commit()
    return {"message": "更新成功"}


@router.delete("/paths/{path_id}")
async def delete_path(
    path_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除学习路径"""
    result = await db.execute(select(LearningPath).where(LearningPath.id == path_id))
    path = result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    await db.delete(path)
    await db.commit()
    return {"message": "删除成功"}


@router.get("/learning-paths")
async def list_learning_paths_v2(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取学习路径列表（兼容 /admin/learning-paths 路径）"""
    return await list_paths(page, size, keyword, level, current_user, db)


@router.get("/learning-paths/{path_id}")
async def get_learning_path_v2(
    path_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取学习路径详情（兼容路径）"""
    return await get_path(path_id, current_user, db)


@router.post("/learning-paths")
async def create_learning_path_v2(
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建学习路径（兼容路径）"""
    return await create_path(data, current_user, db)


@router.put("/learning-paths/{path_id}")
async def update_learning_path_v2(
    path_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新学习路径（兼容路径）"""
    return await update_path(path_id, data, current_user, db)


@router.delete("/learning-paths/{path_id}")
async def delete_learning_path_v2(
    path_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除学习路径（兼容路径）"""
    return await delete_path(path_id, current_user, db)


