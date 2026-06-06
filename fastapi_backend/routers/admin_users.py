"""
后台管理子路由 - 用户管理
从 admin_manage.py 拆分
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db, AsyncSessionLocal
from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import (
    User,
    Exercise,
    LearningPath,
    Post,
    Comment,
    Submission,
    Like,
    Favorite,
    AuditLog,
)
from fastapi_backend.schemas.admin import (
    AdminUserCreate,
    AdminUserUpdate,
    AdminResetPassword,
    AdminLoginRequest,
    AdminUserStatusUpdate,
)
from fastapi_backend.services.auth_service import AuthService

router = APIRouter(prefix="/api/v1/admin", tags=["Admin-用户管理"])


@router.get("/dashboard/stats")
async def get_dashboard_stats(current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
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
    recent_users_result = await db.execute(select(User).order_by(desc(User.created_at)).limit(5))
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
    recent_exercises_result = await db.execute(select(Exercise).order_by(desc(Exercise.created_at)).limit(5))
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
    db: AsyncSession = Depends(get_db),
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
        query = query.where(User.is_active)
    elif status == "disabled":
        query = query.where(~User.is_active)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    offset = (page - 1) * size
    query = query.order_by(desc(User.created_at)).offset(offset).limit(size)
    result = await db.execute(query)
    users = result.scalars().all()

    user_list = []
    for u in users:
        user_list.append(
            {
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
            }
        )

    return {"list": user_list, "total": total or 0}


@router.post("/users")
async def create_user(
    data: AdminUserCreate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建用户"""
    existing = await db.execute(
        select(User).where(or_(User.username == data.username, User.email == data.email))
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在")

    new_user = User(
        username=data.username,
        email=data.email,
        phone=data.phone,
        password_hash=AuthService.hash_password(data.password),
        is_admin=data.is_admin,
        is_active=data.status == "active",
        level=data.level,
        score=data.score,
    )
    db.add(new_user)
    try:
        await db.flush()
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error(f"创建用户时数据库冲突: {e}")
        raise HTTPException(status_code=409, detail="用户名或邮箱已存在（并发冲突）")
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error(f"创建用户失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="用户创建失败，事务已回滚")
    await db.refresh(new_user)
    return {"message": "创建成功", "id": new_user.id}


@router.put("/users/{user_id}")
async def update_user(
    user_id: int,
    data: AdminUserUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新用户信息"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = data.model_dump(exclude_unset=True)
    if "username" in update_data:
        user.username = update_data["username"]
    if "email" in update_data:
        user.email = update_data["email"]
    if "phone" in update_data:
        user.phone = update_data["phone"]
    if "level" in update_data:
        user.level = update_data["level"]
    if "score" in update_data:
        user.score = update_data["score"]
    if "is_admin" in update_data:
        user.is_admin = update_data["is_admin"]
    if "status" in update_data:
        user.is_active = update_data["status"] == "active"
    if "password" in update_data and update_data["password"]:
        user.password_hash = AuthService.hash_password(update_data["password"])

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error(f"更新用户失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="用户更新失败，事务已回滚")
    return {"message": "更新成功"}


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """删除用户"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能删除自己的账号")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    from fastapi_backend.models.models import (
        Post,
        InterviewSession,
        ExamAttempt,
        UserProgress,
        UserAchievement,
        Note,
        DailyCheckin,
    )
    from sqlalchemy import delete as sql_delete

    # 批量删除关联数据
    for model in [Comment, Submission, InterviewSession, ExamAttempt, UserProgress, Like, Favorite, UserAchievement, Note, DailyCheckin]:
        try:
            await db.execute(sql_delete(model).where(model.user_id == user_id))
        except Exception as e:
            logging.getLogger(__name__).warning(f"删除用户时清理 {model.__name__} 关联数据失败: {e}")

    # 删除用户帖子关联的 Like 和 Favorite，再删帖子
    user_post_ids = (await db.execute(select(Post.id).where(Post.user_id == user_id))).scalars().all()
    if user_post_ids:
        await db.execute(sql_delete(Like).where(Like.post_id.in_(user_post_ids)))
        await db.execute(sql_delete(Favorite).where(Favorite.post_id.in_(user_post_ids)))
    await db.execute(sql_delete(Post).where(Post.user_id == user_id))

    await db.delete(user)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error(f"删除用户失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="删除失败，事务已回滚")
    # 写入审计日志
    try:
        log = AuditLog(user_id=current_user.id, admin_id=current_user.id, action="删除用户", action_type="user_management", detail=f"删除用户: {user.username} (ID: {user_id})")
        db.add(log)
        await db.commit()
    except Exception:
        pass
    return {"message": "删除成功"}


@router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """切换用户启用/禁用状态"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能禁用自己的账号")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_active = not user.is_active
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error(f"切换用户状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="操作失败")
    action = "启用" if user.is_active else "禁用"
    # 写入审计日志
    try:
        log = AuditLog(user_id=current_user.id, admin_id=current_user.id, action=f"{action}用户", action_type="user_management", detail=f"{action}用户: {user.username} (ID: {user_id})")
        db.add(log)
        await db.commit()
    except Exception:
        pass
    return {"message": f"用户已{action}"}


@router.post("/users/{user_id}/toggle-admin")
async def toggle_user_admin(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """切换用户管理员权限"""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="不能修改自己的管理员权限")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.is_admin = not user.is_admin
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error(f"切换管理员权限失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="操作失败")
    action = "设置为管理员" if user.is_admin else "取消管理员权限"
    # 写入审计日志
    try:
        log = AuditLog(user_id=current_user.id, admin_id=current_user.id, action=f"{action}", action_type="user_management", detail=f"{action}: {user.username} (ID: {user_id})")
        db.add(log)
        await db.commit()
    except Exception:
        pass
    return {"message": f"用户已{action}"}


@router.put("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    data: AdminResetPassword,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """重置用户密码"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    user.password_hash = AuthService.hash_password(data.new_password)
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error(f"重置密码失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="密码重置失败")
    # 写入审计日志
    try:
        log = AuditLog(user_id=current_user.id, admin_id=current_user.id, action="重置用户密码", action_type="user_management", detail=f"重置用户密码: {user.username} (ID: {user_id})")
        db.add(log)
        await db.commit()
    except Exception:
        pass
    return {"message": "密码重置成功"}


@router.post("/login")
async def admin_login(data: AdminLoginRequest):
    """管理员登录"""
    username = data.username
    password = data.password

    auth_service = AuthService()

    async with AsyncSessionLocal() as session:
        user = await auth_service.authenticate_user(session, username, password)
        if user:
            # 在 session 关闭前提取 role 信息，避免 DetachedInstanceError
            user_role = user.role
            user_id = user.id
            user_username = user.username
            user_email = user.email
            user_is_admin = user.is_admin
            user_is_super_admin = user.is_super_admin
            user_avatar = user.avatar

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")

    if not user_is_admin and not user_is_super_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无管理员权限")

    # 重新构造 user 对象供 create_token_pair 使用（仅需 id/username/is_admin）
    token_pair = auth_service.create_token_pair(user)
    return {
        "token": token_pair.access_token,
        "user": {
            "id": user_id,
            "username": user_username,
            "email": user_email,
            "is_admin": user_is_admin,
            "is_super_admin": user_is_super_admin,
            "avatar": user_avatar,
            "role": user_role,
        },
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
        "role": current_user.role,
    }


@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    data: AdminUserStatusUpdate,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """更新用户状态（兼容api/admin.js中的PATCH调用）"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")

    update_data = data.model_dump(exclude_unset=True)
    if "is_active" in update_data:
        user.is_active = update_data["is_active"]
    if "is_admin" in update_data:
        user.is_admin = update_data["is_admin"]

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logging.getLogger(__name__).error(f"更新用户状态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="状态更新失败")
    return {"message": "状态更新成功"}
