"""
后台管理路由 - 用户/习题/学习路径/考试/社区/仪表盘/备份/审计/系统管理
统一 prefix: /api/v1/admin
前端通过 vite proxy 将 /admin 重写为 /api/v1/admin
"""
from typing import Optional, Any
from datetime import datetime
import os
import shutil
import json
import platform
import asyncio

from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db, AsyncSessionLocal
from fastapi_backend.core.exceptions import NotFoundException
from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import (
    User, Exercise, LearningPath, Exam, ExamQuestion,
    Post, Comment, InterviewQuestion, Submission, Progress
)
from fastapi_backend.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/admin", tags=["Admin Management"])


# ============== 仪表盘统计 ==============

@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取仪表盘统计数据"""
    # 统计卡片
    user_count = await db.scalar(select(func.count(User.id)))
    exercise_count = await db.scalar(select(func.count(Exercise.id)))
    path_count = await db.scalar(select(func.count(LearningPath.id)))
    post_count = await db.scalar(select(func.count(Post.id)))

    stats = [
        {"title": "总用户数", "value": user_count or 0},
        {"title": "习题总数", "value": exercise_count or 0},
        {"title": "学习路径", "value": path_count or 0},
        {"title": "社区帖子", "value": post_count or 0},
    ]

    # 最近注册用户
    recent_users_result = await db.execute(
        select(User).order_by(desc(User.created_at)).limit(5)
    )
    recent_users = [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "registerTime": u.created_at.isoformat() if u.created_at else "",
        }
        for u in recent_users_result.scalars().all()
    ]

    # 最近添加习题
    recent_exercises_result = await db.execute(
        select(Exercise).order_by(desc(Exercise.created_at)).limit(5)
    )
    recent_exercises = [
        {
            "id": e.id,
            "title": e.title,
            "difficulty": e.difficulty,
            "createTime": e.created_at.isoformat() if e.created_at else "",
        }
        for e in recent_exercises_result.scalars().all()
    ]

    return {
        "stats": stats,
        "recentUsers": recent_users,
        "recentExercises": recent_exercises,
    }


# ============== 用户管理 ==============

@router.get("/users")
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取用户列表"""
    query = select(User)

    if keyword:
        query = query.where(
            or_(
                User.username.contains(keyword),
                User.email.contains(keyword),
            )
        )
    if status == "active":
        query = query.where(User.is_active == True)
    elif status == "disabled":
        query = query.where(User.is_active == False)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * size
    query = query.order_by(desc(User.created_at)).offset(offset).limit(size)
    result = await db.execute(query)
    users = result.scalars().all()

    user_list = []
    for u in users:
        user_list.append({
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "phone": u.phone,
            "is_admin": u.is_admin,
            "status": "active" if u.is_active else "disabled",
            "level": u.level,
            "score": u.score,
            "studyTime": u.study_time or 0,
            "completedExercises": 0,
            "registerTime": u.created_at.isoformat() if u.created_at else "",
        })

    return {"list": user_list, "total": total or 0}


@router.post("/users")
async def create_user(
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建用户"""
    existing = await db.execute(
        select(User).where(
            or_(User.username == data.get("username"), User.email == data.get("email"))
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在")

    password = data.get("password", "123456")
    new_user = User(
        username=data.get("username", ""),
        email=data.get("email", ""),
        phone=data.get("phone"),
        password_hash=AuthService.hash_password(password),
        is_admin=data.get("is_admin", False),
        is_active=data.get("status", "active") == "active",
        level=data.get("level", 1),
        score=data.get("score", 0),
    )
    db.add(new_user)
    try:
        await db.flush()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在（并发冲突）")
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="用户创建失败，事务已回滚")
    await db.refresh(new_user)
    return {"message": "创建成功", "id": new_user.id}


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if "username" in data:
        user.username = data["username"]
    if "email" in data:
        user.email = data["email"]
    if "phone" in data:
        user.phone = data["phone"]
    if "level" in data:
        user.level = data["level"]
    if "score" in data:
        user.score = data["score"]
    if "is_admin" in data:
        user.is_admin = data["is_admin"]
    if "status" in data:
        user.is_active = data["status"] == "active"
    if "password" in data and data["password"]:
        user.password_hash = AuthService.hash_password(data["password"])

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="用户更新失败，事务已回滚")
    return {"message": "更新成功"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除用户"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    from fastapi_backend.models.models import (
        Post, Comment, Submission, InterviewSession, ExamAttempt, UserProgress
    )
    for model in [Comment, Submission, InterviewSession, ExamAttempt, UserProgress]:
        try:
            related = await db.execute(select(model).where(model.user_id == user_id))
            for obj in related.scalars().all():
                await db.delete(obj)
        except Exception:
            pass

    related_posts = await db.execute(select(Post).where(Post.author_id == user_id))
    for post in related_posts.scalars().all():
        await db.delete(post)

    await db.delete(user)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="删除失败，事务已回滚")
    return {"message": "删除成功"}


@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """切换用户启用/禁用状态"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_active = not user.is_active
    await db.commit()
    action = "启用" if user.is_active else "禁用"
    return {"message": f"用户已{action}"}


@router.post("/users/{user_id}/toggle-admin")
async def toggle_user_admin(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """切换用户管理员权限"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能修改自己的管理员权限")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_admin = not user.is_admin
    await db.commit()
    action = "设置为管理员" if user.is_admin else "取消管理员权限"
    return {"message": f"用户已{action}"}


@router.put("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """重置用户密码"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    new_password = data.get("new_password", "123456")
    user.password_hash = AuthService.hash_password(new_password)
    await db.commit()
    return {"message": "密码重置成功"}


# ============== 习题管理 ==============

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


# ============== 学习路径管理 ==============

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


# ============== 考试管理 ==============

@router.get("/exams")
async def list_exams(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    exam_type: Optional[str] = Query(None),
    is_published: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    try:
        query = select(Exam)

        if keyword:
            query = query.where(Exam.title.contains(keyword))
        if exam_type:
            query = query.where(Exam.exam_type == exam_type) if hasattr(Exam, "exam_type") else query
        if is_published is not None and is_published != "":
            is_pub = is_published == "true"
            query = query.where(Exam.is_published == is_pub) if hasattr(Exam, "is_published") else query

        total = await db.scalar(select(func.count()).select_from(query.subquery()))
        offset = (page - 1) * size
        query = query.order_by(desc(Exam.created_at)).offset(offset).limit(size)
        result = await db.execute(query)
        exams = result.scalars().all()

        exam_list = []
        for e in exams:
            try:
                exam_list.append({
                    "id": e.id,
                    "title": e.title,
                    "exam_type": getattr(e, "exam_type", ""),
                    "difficulty": getattr(e, "difficulty", "medium"),
                    "duration": getattr(e, "duration", 60),
                    "total_score": getattr(e, "total_score", 100),
                    "pass_score": getattr(e, "pass_score", 60),
                    "is_published": getattr(e, "is_published", False),
                    "question_count": len(getattr(e, 'questions', []) or []),
                    "attempt_count": 0,
                    "pass_rate": 0,
                    "created_at": e.created_at.isoformat() if e.created_at else "",
                })
            except Exception:
                exam_list.append({
                    "id": getattr(e, 'id', 0),
                    "title": getattr(e, 'title', '(数据异常)'),
                    "exam_type": "",
                    "created_at": "",
                })

        return {"list": exam_list, "total": total or 0}
    except Exception as exc:
        import logging
        logging.getLogger(__name__).error(f"获取考试列表失败: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="获取考试列表失败")


@router.get("/exams/{exam_id}")
async def get_exam(
    exam_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取考试详情"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    # 获取题目
    q_result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam_id)
    )
    questions = q_result.scalars().all()

    return {
        "id": exam.id,
        "title": exam.title,
        "exam_type": getattr(exam, "exam_type", ""),
        "difficulty": getattr(exam, "difficulty", "medium"),
        "duration": getattr(exam, "duration", 60),
        "total_score": getattr(exam, "total_score", 100),
        "pass_score": getattr(exam, "pass_score", 60),
        "description": getattr(exam, "description", ""),
        "is_published": getattr(exam, "is_published", False),
        "start_time": getattr(exam, "start_time", None),
        "end_time": getattr(exam, "end_time", None),
        "questions": [
            {
                "id": q.id,
                "question_type": getattr(q, "question_type", "single_choice"),
                "content": getattr(q, "content", ""),
                "options": getattr(q, "options", []),
                "correct_answer": getattr(q, "correct_answer", ""),
                "score": getattr(q, "score", 10),
                "analysis": getattr(q, "analysis", ""),
            }
            for q in questions
        ],
    }


@router.post("/exams")
async def create_exam(
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """创建考试"""
    questions = data.pop("questions", [])
    new_exam = Exam(
        title=data.get("title", ""),
        description=data.get("description", ""),
        exam_type=data.get("exam_type", "模拟考试"),
        difficulty=data.get("difficulty", "medium"),
        duration=data.get("duration", 60),
        total_score=data.get("total_score", 100),
        pass_score=data.get("pass_score", 60),
        is_published=data.get("is_published", False),
        start_time=data.get("start_time"),
        end_time=data.get("end_time"),
        user_id=current_user.id,
    )

    db.add(new_exam)
    await db.flush()

    # 添加题目
    for q_data in questions:
        new_q = ExamQuestion(
            exam_id=new_exam.id,
            question_type=q_data.get("question_type", "single_choice"),
            content=q_data.get("content", ""),
            correct_answer=q_data.get("correct_answer", ""),
            score=q_data.get("score", 10),
            analysis=q_data.get("analysis", ""),
            options=str(q_data.get("options", [])) if q_data.get("options") else None,
        )
        db.add(new_q)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="考试创建失败，事务已回滚")
    return {"message": "考试创建成功", "id": new_exam.id}


@router.put("/exams/{exam_id}")
async def update_exam(
    exam_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新考试"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    for field in ["title", "description", "difficulty", "exam_type", "duration", "total_score", "pass_score", "start_time", "end_time"]:
        if field in data and hasattr(exam, field):
            setattr(exam, field, data[field])
    if "is_published" in data and hasattr(exam, "is_published"):
        exam.is_published = data["is_published"]

    # 更新题目（简单策略：先删后加）
    questions = data.get("questions", None)
    if questions is not None:
        old_q_result = await db.execute(
            select(ExamQuestion).where(ExamQuestion.exam_id == exam_id)
        )
        for old_q in old_q_result.scalars().all():
            await db.delete(old_q)

        for q_data in questions:
            new_q = ExamQuestion(
                exam_id=exam_id,
                question_type=q_data.get("question_type", "single_choice"),
                content=q_data.get("content", ""),
                correct_answer=q_data.get("correct_answer", ""),
                score=q_data.get("score", 10),
                analysis=q_data.get("analysis", ""),
                options=str(q_data.get("options", [])) if q_data.get("options") else None,
            )
            db.add(new_q)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="考试更新失败，事务已回滚")
    return {"message": "考试更新成功"}


@router.delete("/exams/{exam_id}")
async def delete_exam(
    exam_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除考试"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    # 删除关联题目
    q_result = await db.execute(
        select(ExamQuestion).where(ExamQuestion.exam_id == exam_id)
    )
    for q in q_result.scalars().all():
        await db.delete(q)

    await db.delete(exam)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=500, detail="考试删除失败，事务已回滚")
    return {"message": "删除成功"}


@router.put("/exams/{exam_id}/publish")
async def toggle_exam_publish(
    exam_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """切换考试发布状态"""
    result = await db.execute(select(Exam).where(Exam.id == exam_id))
    exam = result.scalar_one_or_none()
    if not exam:
        raise HTTPException(status_code=404, detail="考试不存在")

    if hasattr(exam, "is_published"):
        exam.is_published = data.get("is_published", not exam.is_published)
        await db.commit()
    return {"message": "操作成功"}


# ============== 社区管理 ==============

@router.get("/community/posts")
async def list_posts(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    keyword: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    is_essence: Optional[str] = Query(None),
    is_top: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取帖子列表"""
    query = select(Post)

    if keyword:
        query = query.where(
            or_(Post.title.contains(keyword), Post.content.contains(keyword))
        )
    if category:
        if hasattr(Post, "category"):
            query = query.where(Post.category == category)
    if is_essence is not None and is_essence != "":
        if hasattr(Post, "is_essence"):
            query = query.where(Post.is_essence == (is_essence == "true"))
    if is_top is not None and is_top != "":
        if hasattr(Post, "is_top"):
            query = query.where(Post.is_top == (is_top == "true"))

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * size
    query = query.order_by(desc(Post.created_at)).offset(offset).limit(size)
    result = await db.execute(query)
    posts = result.scalars().all()

    post_list = []
    for p in posts:
        post_list.append({
            "id": p.id,
            "title": p.title,
            "author": getattr(p, "author_name", "") or f"用户{p.user_id}",
            "category": getattr(p, "category", ""),
            "view_count": getattr(p, "view_count", 0),
            "like_count": getattr(p, "like_count", 0),
            "comment_count": getattr(p, "comment_count", 0),
            "is_essence": getattr(p, "is_essence", False),
            "is_top": getattr(p, "is_top", False),
            "created_at": p.created_at.isoformat() if p.created_at else "",
        })

    return {"list": post_list, "total": total or 0}


@router.post("/community/posts/{post_id}/toggle-essence")
async def toggle_post_essence(
    post_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """切换帖子精华状态"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    if hasattr(post, "is_essence"):
        post.is_essence = not post.is_essence
        await db.commit()
        action = "设为精华" if post.is_essence else "取消精华"
        return {"message": f"帖子已{action}"}
    return {"message": "操作成功"}


@router.post("/community/posts/{post_id}/toggle-top")
async def toggle_post_top(
    post_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """切换帖子置顶状态"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    if hasattr(post, "is_top"):
        post.is_top = not post.is_top
        await db.commit()
        action = "置顶" if post.is_top else "取消置顶"
        return {"message": f"帖子已{action}"}
    return {"message": "操作成功"}


@router.delete("/community/posts/{post_id}")
async def delete_post(
    post_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除帖子"""
    result = await db.execute(select(Post).where(Post.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="帖子不存在")

    # 删除关联评论
    c_result = await db.execute(select(Comment).where(Comment.post_id == post_id))
    for c in c_result.scalars().all():
        await db.delete(c)

    await db.delete(post)
    await db.commit()
    return {"message": "帖子已删除"}


@router.get("/community/comments")
async def list_comments(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    post_id: Optional[int] = Query(None),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取评论列表"""
    query = select(Comment)

    if post_id:
        query = query.where(Comment.post_id == post_id)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * size
    query = query.order_by(desc(Comment.created_at)).offset(offset).limit(size)
    result = await db.execute(query)
    comments = result.scalars().all()

    comment_list = []
    for c in comments:
        # 获取帖子标题
        post_result = await db.execute(select(Post.title).where(Post.id == c.post_id))
        post_title = post_result.scalar_one_or_none() or ""

        comment_list.append({
            "id": c.id,
            "content": c.content,
            "author": getattr(c, "author_name", "") or f"用户{c.user_id}",
            "post_id": c.post_id,
            "post_title": post_title,
            "like_count": getattr(c, "like_count", 0),
            "created_at": c.created_at.isoformat() if c.created_at else "",
        })

    return {"list": comment_list, "total": total or 0}


@router.delete("/community/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """删除评论"""
    result = await db.execute(select(Comment).where(Comment.id == comment_id))
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=404, detail="评论不存在")

    await db.delete(comment)
    await db.commit()
    return {"message": "评论已删除"}


# ============== 管理员登录/信息 ==============

BACKUP_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backups")


@router.post("/login")
async def admin_login(data: dict):
    """管理员登录"""
    username = data.get("username", "")
    password = data.get("password", "")

    auth_service = AuthService()

    async with AsyncSessionLocal() as session:
        user = await auth_service.authenticate_user(session, username, password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )

    if not user.is_admin and not user.is_super_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无管理员权限"
        )

    token_pair = auth_service.create_token_pair(user)
    return {
        "token": token_pair.access_token,
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_admin": user.is_admin,
            "is_super_admin": user.is_super_admin,
            "avatar": user.avatar,
            "role": user.role
        }
    }


@router.get("/info")
async def get_admin_info(current_user: User = Depends(require_admin)):
    """获取当前管理员信息"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "is_admin": current_user.is_admin,
        "is_super_admin": current_user.is_super_admin,
        "avatar": current_user.avatar,
        "role": current_user.role
    }


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    data: dict,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """更新用户状态（兼容api/admin.js中的PATCH调用）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    if "is_active" in data:
        user.is_active = data["is_active"]
    if "is_admin" in data:
        user.is_admin = data["is_admin"]

    await db.commit()
    return {"message": "状态更新成功"}


# ============== 学习路径兼容路径 ==============

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


# ============== 习题兼容路由 ==============

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


# ============== 备份管理 ==============

@router.get("/backups")
async def list_backups(
    current_user: User = Depends(require_admin),
):
    """获取备份列表"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backups = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.endswith(".db") or f.endswith(".zip"):
            filepath = os.path.join(BACKUP_DIR, f)
            stat = os.stat(filepath)
            backups.append({
                "name": f,
                "size": stat.st_size,
                "createTime": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            })
    return {"list": backups, "total": len(backups)}


@router.post("/backups")
async def create_backup(
    current_user: User = Depends(require_admin),
):
    """创建数据库备份"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.db"

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "instance", "testmaster.db")
    db_path = os.path.abspath(db_path)
    if os.path.exists(db_path):
        await asyncio.to_thread(shutil.copy2, db_path, os.path.join(BACKUP_DIR, backup_name))
        return {"message": "备份创建成功", "name": backup_name}
    else:
        return {"message": "数据库文件不存在，跳过备份", "name": None}


@router.delete("/backups/old")
async def delete_old_backups(
    current_user: User = Depends(require_admin),
):
    """清理旧备份（保留最近5个）"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    files = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db") or f.endswith(".zip")]
    )

    if len(files) <= 5:
        return {"message": "没有需要清理的旧备份"}

    deleted = 0
    for f in files[:-5]:
        os.remove(os.path.join(BACKUP_DIR, f))
        deleted += 1

    return {"message": f"已清理 {deleted} 个旧备份"}


def _safe_backup_path(name: str) -> str:
    filepath = os.path.join(BACKUP_DIR, name)
    filepath = os.path.abspath(filepath)
    if not filepath.startswith(os.path.abspath(BACKUP_DIR)):
        raise HTTPException(status_code=400, detail="非法文件路径")
    return filepath


@router.get("/backups/download/{name}")
async def download_backup(
    name: str,
    current_user: User = Depends(require_admin),
):
    filepath = _safe_backup_path(name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    return FileResponse(filepath, filename=name)


@router.post("/backups/{name}/restore")
async def restore_backup(
    name: str,
    current_user: User = Depends(require_admin),
):
    backup_path = _safe_backup_path(name)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "instance", "testmaster.db")
    db_path = os.path.abspath(db_path)
    await asyncio.to_thread(shutil.copy2, backup_path, db_path)
    return {"message": "备份恢复成功"}


@router.delete("/backups/{name}")
async def delete_backup(
    name: str,
    current_user: User = Depends(require_admin),
):
    filepath = _safe_backup_path(name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="备份文件不存在")

    os.remove(filepath)
    return {"message": "备份删除成功"}


# ============== 审计日志 ==============

@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取审计日志（基于用户操作记录）"""
    total = await db.scalar(select(func.count(Submission.id))) or 0
    offset = (page - 1) * size

    query = select(Submission).order_by(desc(Submission.created_at)).offset(offset).limit(size)
    result = await db.execute(query)
    submissions = result.scalars().all()

    logs = []
    for s in submissions:
        user_result = await db.execute(select(User).where(User.id == s.user_id))
        user = user_result.scalar_one_or_none()
        q_result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == s.question_id))
        question = q_result.scalar_one_or_none()
        logs.append({
            "id": s.id,
            "user": user.username if user else "unknown",
            "action": "代码提交",
            "detail": f"提交了面试题 \"{question.title if question else '未知'}\" 的代码",
            "status": s.execution_status,
            "createTime": s.created_at.isoformat() if s.created_at else None,
        })

    return {"list": logs, "total": total, "page": page, "size": size}


# ============== 系统指标 ==============

@router.get("/system/metrics")
async def get_system_metrics(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取系统指标"""
    # 数据库统计
    total_users = await db.scalar(select(func.count(User.id))) or 0
    total_submissions = await db.scalar(select(func.count(Submission.id))) or 0
    total_exercises = await db.scalar(select(func.count(Exercise.id))) or 0
    total_paths = await db.scalar(select(func.count(LearningPath.id))) or 0
    total_questions = await db.scalar(select(func.count(InterviewQuestion.id))) or 0
    total_exams = await db.scalar(select(func.count(Exam.id))) or 0

    # 数据库文件大小
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "instance", "testmaster.db")
    db_path = os.path.abspath(db_path)
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    # 备份目录大小
    backup_size = 0
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            fp = os.path.join(BACKUP_DIR, f)
            if os.path.isfile(fp):
                backup_size += os.path.getsize(fp)

    return {
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
        },
        "database": {
            "size_bytes": db_size,
            "size_mb": round(db_size / 1024 / 1024, 2),
            "total_users": total_users,
            "total_submissions": total_submissions,
            "total_exercises": total_exercises,
            "total_learning_paths": total_paths,
            "total_interview_questions": total_questions,
            "total_exams": total_exams,
        },
        "backups": {
            "size_bytes": backup_size,
            "size_mb": round(backup_size / 1024 / 1024, 2),
            "count": len(os.listdir(BACKUP_DIR)) if os.path.exists(BACKUP_DIR) else 0,
        }
    }
