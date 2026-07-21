"""
后台管理子路由 - 学习路径管理
从 admin_manage.py 拆分
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, or_, desc, update, Integer
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import User, Exercise, LearningPath, ExerciseSubmissionRecord
from fastapi_backend.schemas.learning_paths import (
    LearningPathCreate,
    LearningPathUpdate,
    ProjectCreateRequest,
)

router = APIRouter(prefix="/api/v1/admin", tags=["Admin-学习路径"])


@router.get("/paths")
async def list_paths(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取学习路径列表"""
    query = select(LearningPath)

    if keyword:
        query = query.where(
            or_(
                LearningPath.title.contains(keyword),
                LearningPath.description.contains(keyword),
            )
        )
    if level:
        query = query.where(LearningPath.difficulty == level)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * size
    query = query.order_by(desc(LearningPath.created_at)).offset(offset).limit(size)
    result = await db.execute(query)
    paths = result.scalars().all()

    # 真实统计：批量查询每个路径的习题数、学习人数、通过率
    path_ids = [p.id for p in paths]
    exercise_counts = {}
    learn_stats = {}  # path_id -> {learn_count, total_sub, pass_sub}
    if path_ids:
        # 习题数
        ex_count_result = await db.execute(
            select(Exercise.learning_path_id, func.count(Exercise.id))
            .where(Exercise.learning_path_id.in_(path_ids))
            .group_by(Exercise.learning_path_id)
        )
        for row in ex_count_result.all():
            exercise_counts[row[0]] = row[1]

        # 学习人数与提交通过情况（关联习题提交记录）
        sub_result = await db.execute(
            select(
                Exercise.learning_path_id,
                func.count(func.distinct(ExerciseSubmissionRecord.user_id)),
                func.count(ExerciseSubmissionRecord.id),
                func.coalesce(func.sum((ExerciseSubmissionRecord.result == "pass").cast(Integer)), 0),
            )
            .join(ExerciseSubmissionRecord, ExerciseSubmissionRecord.exercise_id == Exercise.id)
            .where(Exercise.learning_path_id.in_(path_ids))
            .group_by(Exercise.learning_path_id)
        )
        for row in sub_result.all():
            learn_stats[row[0]] = {"learn_count": row[1], "total_sub": row[2], "pass_sub": row[3]}

    path_list = []
    for p in paths:
        ex_count = exercise_counts.get(p.id, 0)
        stat = learn_stats.get(p.id, {"learn_count": 0, "total_sub": 0, "pass_sub": 0})
        total_sub = stat["total_sub"]
        pass_sub = stat["pass_sub"]
        completion_rate = round(pass_sub * 100 / total_sub, 1) if total_sub else 0
        path_list.append(
            {
                "id": p.id,
                "title": p.title,
                "description": p.description or "",
                "level": p.difficulty if hasattr(p, "difficulty") else "beginner",
                "language": p.language if hasattr(p, "language") else "通用",
                "exerciseCount": ex_count,
                "learnCount": stat["learn_count"],
                "completionRate": completion_rate,
            }
        )

    return {"list": path_list, "total": total or 0}


@router.get("/paths/{path_id}")
async def get_path(
    path_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取学习路径详情"""
    result = await db.execute(select(LearningPath).where(LearningPath.id == path_id))
    path = result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    # 查询真实关联的习题ID列表
    exercise_ids_result = await db.execute(select(Exercise.id).where(Exercise.learning_path_id == path_id))
    exercise_ids = [row[0] for row in exercise_ids_result.all()]

    return {
        "id": path.id,
        "title": path.title,
        "description": path.description or "",
        "level": path.difficulty if hasattr(path, "difficulty") else "beginner",
        "language": path.language if hasattr(path, "language") else "通用",
        "exerciseIds": exercise_ids,
    }


@router.get("/paths/exercises")
async def get_path_exercises(current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """获取可选习题列表（用于穿梭框）"""
    result = await db.execute(select(Exercise))
    exercises = result.scalars().all()

    return [{"key": e.id, "label": e.title} for e in exercises]


@router.post("/paths")
async def create_path(
    data: LearningPathCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建学习路径"""
    path_data_dict = data.model_dump(exclude_unset=True)

    # 前端兼容：level 字段映射到 difficulty
    difficulty = path_data_dict.get("difficulty") or path_data_dict.get("level") or "beginner"

    new_path = LearningPath(
        title=data.title,
        description=data.description,
        difficulty=difficulty,
        language=data.language,
    )
    db.add(new_path)
    await db.flush()  # 获取 new_path.id

    # 处理关联习题
    exercise_ids = path_data_dict.get("exerciseIds") or path_data_dict.get("exercise_ids")
    if exercise_ids is not None:
        # 先清除旧关联（保险起见）
        await db.execute(update(Exercise).where(Exercise.learning_path_id == new_path.id).values(learning_path_id=None))
        # 再设置新关联
        if exercise_ids:
            await db.execute(update(Exercise).where(Exercise.id.in_(exercise_ids)).values(learning_path_id=new_path.id))

    await db.commit()
    await db.refresh(new_path)
    return {"message": "创建成功", "id": new_path.id}


@router.put("/paths/{path_id}")
async def update_path(
    path_id: int,
    data: LearningPathUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新学习路径"""
    result = await db.execute(select(LearningPath).where(LearningPath.id == path_id))
    path = result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=404, detail="路径不存在")

    path_data_dict = data.model_dump(exclude_unset=True)

    # 前端兼容：level 字段映射到 difficulty
    if "level" in path_data_dict:
        if not path_data_dict.get("difficulty"):
            path.difficulty = path_data_dict.get("level")
        path_data_dict.pop("level", None)

    # 应用其余字段
    for key, value in path_data_dict.items():
        if key in ("exerciseIds", "exercise_ids"):
            continue
        if hasattr(path, key):
            setattr(path, key, value)

    # 处理关联习题
    exercise_ids = path_data_dict.get("exerciseIds") or path_data_dict.get("exercise_ids")
    if exercise_ids is not None:
        # 先清除旧关联
        await db.execute(update(Exercise).where(Exercise.learning_path_id == path_id).values(learning_path_id=None))
        # 再设置新关联
        if exercise_ids:
            await db.execute(update(Exercise).where(Exercise.id.in_(exercise_ids)).values(learning_path_id=path_id))

    await db.commit()
    return {"message": "更新成功"}


@router.delete("/paths/{path_id}")
async def delete_path(
    path_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
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
    db: AsyncSession = Depends(get_db),
):
    """获取学习路径列表（兼容 /admin/learning-paths 路径）"""
    return await list_paths(page, size, keyword, level, current_user, db)


@router.get("/learning-paths/{path_id}")
async def get_learning_path_v2(
    path_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取学习路径详情（兼容路径）"""
    return await get_path(path_id, current_user, db)


@router.post("/learning-paths")
async def create_learning_path_v2(
    data: LearningPathCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建学习路径（兼容路径）"""
    return await create_path(data, current_user, db)


@router.put("/learning-paths/{path_id}")
async def update_learning_path_v2(
    path_id: int,
    data: LearningPathUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新学习路径（兼容路径）"""
    return await update_path(path_id, data, current_user, db)


@router.delete("/learning-paths/{path_id}")
async def delete_learning_path_v2(
    path_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除学习路径（兼容路径）"""
    return await delete_path(path_id, current_user, db)


@router.post("/learning-paths/{path_id}/projects")
async def create_project_for_path(
    path_id: int,
    body: ProjectCreateRequest,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """为学习路径创建项目实战"""
    from fastapi_backend.models.models import ProjectSpace, ProjectTask, ProjectResource

    q = select(LearningPath).filter(LearningPath.id == path_id)
    result = await db.execute(q)
    path = result.scalar_one_or_none()
    if not path:
        raise HTTPException(status_code=404, detail="学习路径不存在")

    project = ProjectSpace(
        learning_path_id=path_id,
        title=body.title,
        description=body.description,
        overview=body.overview,
        difficulty=body.difficulty,
        status=body.status,
        estimated_hours=body.estimated_hours,
        sort_order=body.sort_order,
    )
    db.add(project)
    await db.flush()

    for idx, task_data in enumerate(body.tasks):
        task = ProjectTask(
            project_id=project.id,
            title=task_data.title,
            description=task_data.description,
            task_type=task_data.task_type,
            requirements=task_data.requirements,
            hints=task_data.hints,
            score=task_data.score,
            sort_order=idx,
        )
        db.add(task)

    for idx, res_data in enumerate(body.resources):
        resource = ProjectResource(
            project_id=project.id,
            title=res_data.title,
            resource_type=res_data.resource_type,
            content=res_data.content,
            url=res_data.url,
            sort_order=idx,
        )
        db.add(resource)

    await db.commit()
    await db.refresh(project)

    return {"message": "项目创建成功", "project_id": project.id, "title": project.title}
