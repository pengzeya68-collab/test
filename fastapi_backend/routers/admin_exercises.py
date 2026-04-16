"""
后台管理子路由 - 习题管理
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
from fastapi import UploadFile, File
router = APIRouter(prefix="/api/v1/admin", tags=["Admin-习题管理"])

@router.get("/exercises")
async def list_exercises(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取习题列表"""
    query = select(Exercise)

    if keyword:
        query = query.where(
            or_(Exercise.title.contains(keyword), Exercise.description.contains(keyword))
        )
    if difficulty:
        query = query.where(Exercise.difficulty == difficulty)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * size
    query = query.order_by(desc(Exercise.created_at)).offset(offset).limit(size)
    result = await db.execute(query)
    exercises = result.scalars().all()

    exercise_list = []
    for e in exercises:
        exercise_list.append({
            "id": e.id,
            "title": e.title,
            "category": e.category if hasattr(e, "category") else "",
            "difficulty": e.difficulty,
            "content": e.description if hasattr(e, "description") else "",
            "answer": e.solution if hasattr(e, "solution") else "",
            "passRate": 0,
            "createTime": e.created_at.isoformat() if e.created_at else "",
        })

    return {"list": exercise_list, "total": total or 0}


@router.post("/exercises")
async def create_exercise(
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建习题"""
    new_exercise = Exercise(
        title=data.get("title", ""),
        description=data.get("content", ""),
        solution=data.get("answer", ""),
        difficulty=data.get("difficulty", "easy"),
        language=data.get("language", "通用"),
        category=data.get("category", ""),
    )
    db.add(new_exercise)
    await db.commit()
    await db.refresh(new_exercise)
    return {"message": "创建成功", "id": new_exercise.id}


@router.put("/exercises/{exercise_id}")
async def update_exercise(
    exercise_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新习题"""
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="习题不存在")

    if "title" in data:
        exercise.title = data["title"]
    if "content" in data:
        exercise.description = data["content"]
    if "answer" in data:
        exercise.solution = data["answer"]
    if "difficulty" in data:
        exercise.difficulty = data["difficulty"]
    if "category" in data:
        exercise.category = data["category"]

    await db.commit()
    return {"message": "更新成功"}


@router.delete("/exercises/{exercise_id}")
async def delete_exercise(
    exercise_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除习题"""
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="习题不存在")

    await db.delete(exercise)
    await db.commit()
    return {"message": "删除成功"}


@router.post("/exercises/import")
async def import_exercises(
    file: UploadFile = File(...),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """批量导入习题"""
    import json

    content = await file.read()
    success_count = 0
    fail_count = 0
    fail_reasons = []

    try:
        if file.filename.endswith(".json"):
            items = json.loads(content.decode("utf-8"))
            if isinstance(items, dict):
                items = [items]
        else:
            return {"success_count": 0, "fail_count": 1, "fail_reasons": ["仅支持JSON格式"]}

        for item in items:
            try:
                new_exercise = Exercise(
                    title=item.get("title", ""),
                    description=item.get("description", item.get("instructions", "")),
                    solution=item.get("solution", item.get("answer", "")),
                    difficulty=item.get("difficulty", "easy"),
                    language=item.get("language", "通用"),
                    category=item.get("category", ""),
                )
                db.add(new_exercise)
                success_count += 1
            except Exception as e:
                fail_count += 1
                fail_reasons.append(f"行{success_count + fail_count}: {str(e)}")

        await db.commit()
    except Exception as e:
        fail_count += 1
        fail_reasons.append(f"文件解析失败: {str(e)}")

    return {
        "success_count": success_count,
        "fail_count": fail_count,
        "fail_reasons": fail_reasons,
        "msg": f"导入完成，成功{success_count}条，失败{fail_count}条",
    }


@router.get("/exercises/{exercise_id}")
async def get_exercise(
    exercise_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取习题详情"""
    result = await db.execute(select(Exercise).where(Exercise.id == exercise_id))
    exercise = result.scalar_one_or_none()
    if not exercise:
        raise HTTPException(status_code=404, detail="习题不存在")

    return {
        "id": exercise.id,
        "title": exercise.title,
        "description": exercise.description,
        "solution": exercise.solution,
        "difficulty": exercise.difficulty,
        "category": exercise.category,
        "language": exercise.language,
        "exercise_type": exercise.exercise_type,
        "knowledge_point": exercise.knowledge_point,
        "is_public": exercise.is_public,
        "createTime": exercise.created_at.isoformat() if exercise.created_at else "",
    }


@router.post("/exercises/batch-import")
async def batch_import_exercises(
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """批量导入习题（JSON格式）"""
    exercises_data = data.get("exercises", [])
    if not exercises_data:
        raise HTTPException(status_code=400, detail="没有可导入的习题数据")

    created = []
    for item in exercises_data:
        exercise = Exercise(
            title=item.get("title"),
            description=item.get("content") or item.get("description"),
            solution=item.get("answer") or item.get("solution"),
            difficulty=item.get("difficulty", "easy"),
            category=item.get("category"),
            language=item.get("language", "通用"),
            exercise_type=item.get("exercise_type", "text"),
            is_public=item.get("is_public", True),
            admin_id=current_user.id,
            user_id=current_user.id,
        )
        db.add(exercise)
        created.append(exercise)

    await db.commit()
    for e in created:
        await db.refresh(e)

    return {"message": f"成功导入 {len(created)} 道习题", "count": len(created)}


