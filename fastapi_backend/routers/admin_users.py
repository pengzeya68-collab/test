"""
后台管理子路由 - 用户管理
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

router = APIRouter(prefix="/api/v1/admin", tags=["Admin-用户管理"])

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


