"""
后台管理子路由 - 社区管理
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

router = APIRouter(prefix="/api/v1/admin", tags=["Admin-社区管理"])

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


