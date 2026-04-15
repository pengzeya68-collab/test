"""Community router – migrated from Flask backend/api/community.py."""
from __future__ import annotations

import math
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_active_user, require_admin
from fastapi_backend.models.models import Comment, Favorite, Like, Post, User

async def get_optional_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db),
) -> User | None:
    if not authorization:
        return None
    try:
        from fastapi_backend.services.auth_service import AuthService, AuthError
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not token:
            return None
        auth_service = AuthService()
        payload = auth_service.decode_token(token, expected_type="access")
        user_id = int(payload["sub"])
        user = await auth_service.get_user_by_id(db, user_id)
        if user and user.is_active:
            return user
    except Exception:
        pass
    return None

from fastapi_backend.schemas.community import (
    AdminCommentListResponse,
    AdminCommentResponse,
    AdminPostListResponse,
    CategoryInfo,
    CommentCreateRequest,
    CommentResponse,
    CommunityStatsResponse,
    FavoriteResponse,
    LikeResponse,
    PostCreateRequest,
    PostListResponse,
    PostPaginatedResponse,
    PostUpdateRequest,
)

router = APIRouter(prefix="/api/v1/community", tags=["Community"])

CATEGORIES = [
    CategoryInfo(value="experience", label="经验分享", color="#67c23a"),
    CategoryInfo(value="question", label="问题求助", color="#f56c6c"),
    CategoryInfo(value="resource", label="资源分享", color="#409eff"),
    CategoryInfo(value="job", label="求职交流", color="#e6a23c"),
    CategoryInfo(value="other", label="其他", color="#909399"),
]

_VALID_CATEGORIES = {c.value for c in CATEGORIES}


def _category_info(value: str) -> CategoryInfo:
    for c in CATEGORIES:
        if c.value == value:
            return c
    return CategoryInfo(value=value, label=value, color="#909399")


def _fmt_dt(dt: datetime | None) -> str:
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


async def _format_post(post: Post, user_id: int | None = None, db: AsyncSession | None = None) -> PostListResponse:
    cat = _category_info(post.category) if post.category else None
    tags = post.tags.split(",") if post.tags else []
    summary = post.summary or (post.content[:200] + "..." if len(post.content) > 200 else post.content)

    is_liked: bool | None = None
    is_favorited: bool | None = None
    if user_id and db:
        like_q = await db.execute(select(Like).filter_by(user_id=user_id, post_id=post.id))
        is_liked = like_q.scalar_one_or_none() is not None
        fav_q = await db.execute(select(Favorite).filter_by(user_id=user_id, post_id=post.id))
        is_favorited = fav_q.scalar_one_or_none() is not None

    return PostListResponse(
        id=post.id,
        title=post.title,
        content=post.content,
        summary=summary,
        tags=tags,
        category=cat,
        view_count=post.view_count,
        like_count=post.like_count,
        comment_count=post.comment_count,
        is_essence=post.is_essence,
        is_top=post.is_top,
        created_at=_fmt_dt(post.created_at),
        updated_at=_fmt_dt(post.updated_at),
        author={"id": post.user.id, "username": post.user.username} if post.user else {"id": 0, "username": "unknown"},
        is_liked=is_liked,
        is_favorited=is_favorited,
    )


async def _format_comment(comment: Comment, user_id: int | None = None, db: AsyncSession | None = None) -> CommentResponse:
    is_liked: bool | None = None
    if user_id and db:
        lk = await db.execute(select(Like).filter_by(user_id=user_id, comment_id=comment.id))
        is_liked = lk.scalar_one_or_none() is not None

    replies = []
    for reply in comment.replies:
        replies.append(await _format_comment(reply, user_id, db))

    return CommentResponse(
        id=comment.id,
        content=comment.content,
        like_count=comment.like_count,
        created_at=_fmt_dt(comment.created_at),
        author={"id": comment.user.id, "username": comment.user.username} if comment.user else {"id": 0, "username": "unknown"},
        replies=replies,
        is_liked=is_liked,
    )


@router.get("/categories", response_model=list[CategoryInfo])
async def get_categories():
    return CATEGORIES


@router.get("/stats", response_model=CommunityStatsResponse)
async def get_community_stats(db: AsyncSession = Depends(get_db)):
    total_posts_q = await db.execute(select(func.count(Post.id)))
    total_posts = total_posts_q.scalar() or 0
    total_users_q = await db.execute(select(func.count(User.id)))
    total_users = total_users_q.scalar() or 0
    today = datetime.utcnow().date()
    today_start = datetime.combine(today, datetime.min.time())
    today_posts_q = await db.execute(select(func.count(Post.id)).filter(Post.created_at >= today_start))
    today_posts = today_posts_q.scalar() or 0
    return CommunityStatsResponse(total_posts=total_posts, total_users=total_users, today_posts=today_posts, online_users=total_users)


@router.get("/posts", response_model=PostPaginatedResponse)
async def get_posts(page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=100), category: Optional[str] = Query(None), tag: Optional[str] = Query(None), search: Optional[str] = Query(None), sort: str = Query("latest"), current_user: Optional[User] = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    user_id = None
    if current_user:
        user_id = current_user.id
    q = select(Post).options(selectinload(Post.user)).filter(Post.is_approved == True)
    if category:
        q = q.filter(Post.category == category)
    if tag:
        q = q.filter(Post.tags.like(f"%{tag}%"))
    if search:
        q = q.filter(or_(Post.title.like(f"%{search}%"), Post.content.like(f"%{search}%")))
    if sort == "essence":
        q = q.filter(Post.is_essence == True)
    if sort == "hot":
        q = q.order_by((Post.like_count + Post.comment_count + Post.view_count / 10).desc(), Post.created_at.desc())
    else:
        q = q.order_by(Post.is_top.desc(), Post.created_at.desc())
    count_q = select(func.count()).select_from(q.subquery())
    total_result = await db.execute(count_q)
    total = total_result.scalar() or 0
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    posts = result.scalars().all()
    return PostPaginatedResponse(list=[await _format_post(p, user_id, db) for p in posts], total=total, page=page, per_page=per_page, total_pages=math.ceil(total / per_page) if total else 0)


@router.get("/posts/{post_id}", response_model=PostListResponse)
async def get_post_detail(post_id: int, current_user: Optional[User] = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    user_id = current_user.id if current_user else None
    q = select(Post).options(selectinload(Post.user)).filter(Post.id == post_id)
    result = await db.execute(q)
    post = result.scalar_one_or_none()
    if not post:
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="帖子不存在")
    if not post.is_approved:
        if not user_id:
            from fastapi import HTTPException; raise HTTPException(status_code=404, detail="不存在或未通过审核")
        user_q = await db.execute(select(User).filter_by(id=user_id))
        user = user_q.scalar_one_or_none()
        is_admin = user and user.is_admin
        is_author = user_id == post.user_id
        if not is_admin and not is_author:
            from fastapi import HTTPException; raise HTTPException(status_code=404, detail="不存在或未通过审核")
    post.view_count += 1
    await db.commit()
    return await _format_post(post, user_id, db)


@router.post("/posts", response_model=PostListResponse, status_code=201)
async def create_post(payload: PostCreateRequest, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    if payload.category not in _VALID_CATEGORIES:
        from fastapi import HTTPException; raise HTTPException(status_code=400, detail="分类不正确")
    tags_str = ",".join([t.strip() for t in payload.tags if t.strip()]) if payload.tags else ""
    post = Post(title=payload.title.strip(), content=payload.content.strip(), summary=payload.summary.strip() if payload.summary else "", tags=tags_str, category=payload.category, user_id=current_user.id)
    db.add(post)
    await db.commit()
    await db.refresh(post)
    q = select(Post).options(selectinload(Post.user)).filter(Post.id == post.id)
    result = await db.execute(q)
    post = result.scalar_one()
    return await _format_post(post, current_user.id, db)


@router.put("/posts/{post_id}", response_model=PostListResponse)
async def update_post(post_id: int, payload: PostUpdateRequest, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    q = select(Post).options(selectinload(Post.user)).filter(Post.id == post_id)
    result = await db.execute(q)
    post = result.scalar_one_or_none()
    if not post:
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="帖子不存在")
    if post.user_id != current_user.id:
        from fastapi import HTTPException; raise HTTPException(status_code=403, detail="无权限修改此帖子")
    if payload.title is not None: post.title = payload.title.strip()
    if payload.content is not None: post.content = payload.content.strip()
    if payload.summary is not None: post.summary = payload.summary.strip()
    if payload.category is not None:
        if payload.category in _VALID_CATEGORIES: post.category = payload.category
    if payload.tags is not None: post.tags = ",".join([t.strip() for t in payload.tags if t.strip()])
    post.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(post)
    q = select(Post).options(selectinload(Post.user)).filter(Post.id == post.id)
    result = await db.execute(q)
    post = result.scalar_one()
    return await _format_post(post, current_user.id, db)


@router.delete("/posts/{post_id}")
async def delete_post(post_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    q = select(Post).filter(Post.id == post_id)
    result = await db.execute(q)
    post = result.scalar_one_or_none()
    if not post:
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="帖子不存在")
    if post.user_id != current_user.id:
        from fastapi import HTTPException; raise HTTPException(status_code=403, detail="无权限删除此帖子")
    await db.delete(post)
    await db.commit()
    return {"message": "帖子删除成功"}


@router.post("/posts/{post_id}/like", response_model=LikeResponse)
async def like_post(post_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    q = select(Post).filter(Post.id == post_id)
    result = await db.execute(q)
    post = result.scalar_one_or_none()
    if not post:
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="帖子不存在")
    like_q = await db.execute(select(Like).filter_by(user_id=current_user.id, post_id=post_id))
    like = like_q.scalar_one_or_none()
    if like:
        await db.delete(like); post.like_count = max(0, post.like_count - 1); action = "unliked"
    else:
        like = Like(user_id=current_user.id, post_id=post_id); db.add(like); post.like_count += 1; action = "liked"
    await db.commit()
    return LikeResponse(message="点赞成功" if action == "liked" else "取消点赞成功", action=action, like_count=post.like_count)


@router.post("/posts/{post_id}/favorite", response_model=FavoriteResponse)
async def favorite_post(post_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    q = select(Post).filter(Post.id == post_id)
    result = await db.execute(q)
    post = result.scalar_one_or_none()
    if not post:
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="帖子不存在")
    fav_q = await db.execute(select(Favorite).filter_by(user_id=current_user.id, post_id=post_id))
    fav = fav_q.scalar_one_or_none()
    if fav:
        await db.delete(fav); action = "unfavorited"
    else:
        fav = Favorite(user_id=current_user.id, post_id=post_id); db.add(fav); action = "favorited"
    await db.commit()
    return FavoriteResponse(message="收藏成功" if action == "favorited" else "取消收藏成功", action=action)


@router.get("/posts/{post_id}/comments", response_model=list[CommentResponse])
async def get_comments(post_id: int, current_user: Optional[User] = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    user_id = current_user.id if current_user else None
    post_q = await db.execute(select(Post).filter_by(id=post_id))
    if not post_q.scalar_one_or_none():
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="帖子不存在")
    q = select(Comment).options(selectinload(Comment.user), selectinload(Comment.replies)).filter(Comment.post_id == post_id, Comment.parent_id == None).order_by(Comment.created_at.desc())
    result = await db.execute(q)
    comments = result.scalars().all()
    return [await _format_comment(c, user_id, db) for c in comments]


@router.post("/posts/{post_id}/comments", response_model=CommentResponse, status_code=201)
async def create_comment(post_id: int, payload: CommentCreateRequest, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    post_q = await db.execute(select(Post).filter_by(id=post_id))
    post = post_q.scalar_one_or_none()
    if not post:
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="帖子不存在")
    if payload.parent_id:
        parent_q = await db.execute(select(Comment).filter_by(id=payload.parent_id, post_id=post_id))
        if not parent_q.scalar_one_or_none():
            from fastapi import HTTPException; raise HTTPException(status_code=404, detail="父评论不存在")
    comment = Comment(content=payload.content.strip(), user_id=current_user.id, post_id=post_id, parent_id=payload.parent_id)
    db.add(comment); post.comment_count += 1; await db.commit(); await db.refresh(comment)
    q = select(Comment).options(selectinload(Comment.user)).filter(Comment.id == comment.id)
    result = await db.execute(q)
    comment = result.scalar_one()
    return await _format_comment(comment, current_user.id, db)


@router.post("/comments/{comment_id}/like", response_model=LikeResponse)
async def like_comment(comment_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    q = select(Comment).filter(Comment.id == comment_id)
    result = await db.execute(q)
    comment = result.scalar_one_or_none()
    if not comment:
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="评论不存在")
    like_q = await db.execute(select(Like).filter_by(user_id=current_user.id, comment_id=comment_id))
    like = like_q.scalar_one_or_none()
    if like:
        await db.delete(like); comment.like_count = max(0, comment.like_count - 1); action = "unliked"
    else:
        like = Like(user_id=current_user.id, comment_id=comment_id); db.add(like); comment.like_count += 1; action = "liked"
    await db.commit()
    return LikeResponse(message="点赞成功" if action == "liked" else "取消点赞成功", action=action, like_count=comment.like_count)


@router.get("/user/{user_id}/posts", response_model=PostPaginatedResponse)
async def get_user_posts(user_id: int, page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=100), current_user: Optional[User] = Depends(get_optional_user), db: AsyncSession = Depends(get_db)):
    me = current_user.id if current_user else None
    user_q = await db.execute(select(User).filter_by(id=user_id))
    if not user_q.scalar_one_or_none():
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="用户不存在")
    q = select(Post).options(selectinload(Post.user)).filter_by(user_id=user_id).order_by(Post.created_at.desc())
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    posts = result.scalars().all()
    return PostPaginatedResponse(list=[await _format_post(p, me, db) for p in posts], total=total, page=page, per_page=per_page)


@router.get("/user/favorites", response_model=PostPaginatedResponse)
async def get_user_favorites(page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=100), current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_db)):
    fav_q = select(Favorite).filter_by(user_id=current_user.id).order_by(Favorite.created_at.desc())
    fav_result = await db.execute(fav_q)
    favorites = fav_result.scalars().all()
    post_ids = [f.post_id for f in favorites]
    if not post_ids:
        return PostPaginatedResponse(list=[], total=0, page=page, per_page=per_page)
    q = select(Post).options(selectinload(Post.user)).filter(Post.id.in_(post_ids))
    result = await db.execute(q)
    all_posts = result.scalars().all()
    posts_sorted = sorted(all_posts, key=lambda p: post_ids.index(p.id))
    total = len(posts_sorted); start = (page - 1) * per_page; end = start + per_page; paginated = posts_sorted[start:end]
    return PostPaginatedResponse(list=[await _format_post(p, current_user.id, db) for p in paginated], total=total, page=page, per_page=per_page)


@router.get("/admin/posts", response_model=AdminPostListResponse)
async def admin_get_posts(page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=100), is_essence: Optional[bool] = Query(None), is_top: Optional[bool] = Query(None), _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    q = select(Post).options(selectinload(Post.user)).order_by(Post.created_at.desc())
    if is_essence is not None: q = q.filter(Post.is_essence == is_essence)
    if is_top is not None: q = q.filter(Post.is_top == is_top)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    posts = result.scalars().all()
    return AdminPostListResponse(list=[await _format_post(p, None, db) for p in posts], total=total, page=page, per_page=per_page)


@router.post("/admin/posts/{post_id}/toggle-essence")
async def admin_toggle_essence(post_id: int, _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    q = select(Post).filter(Post.id == post_id)
    result = await db.execute(q)
    post = result.scalar_one_or_none()
    if not post:
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="帖子不存在")
    post.is_essence = not post.is_essence; await db.commit(); return {"message": "操作成功"}


@router.post("/admin/posts/{post_id}/toggle-top")
async def admin_toggle_top(post_id: int, _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    q = select(Post).filter(Post.id == post_id)
    result = await db.execute(q)
    post = result.scalar_one_or_none()
    if not post:
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="帖子不存在")
    post.is_top = not post.is_top; await db.commit(); return {"message": "操作成功"}


@router.delete("/admin/posts/{post_id}")
async def admin_delete_post(post_id: int, _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    q = select(Post).filter(Post.id == post_id)
    result = await db.execute(q)
    post = result.scalar_one_or_none()
    if not post:
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="帖子不存在")
    await db.delete(post); await db.commit(); return {"message": "帖子已删除"}


@router.get("/admin/comments", response_model=AdminCommentListResponse)
async def admin_get_comments(page: int = Query(1, ge=1), per_page: int = Query(10, ge=1, le=100), post_id: Optional[int] = Query(None), _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    q = select(Comment).options(selectinload(Comment.user)).order_by(Comment.created_at.desc())
    if post_id: q = q.filter(Comment.post_id == post_id)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(q)
    comments = result.scalars().all()
    items = []
    for c in comments:
        items.append(AdminCommentResponse(id=c.id, content=c.content, like_count=c.like_count, created_at=_fmt_dt(c.created_at), author={"id": c.user.id, "username": c.user.username} if c.user else {"id": 0, "username": "unknown"}, post_id=c.post_id))
    return AdminCommentListResponse(list=items, total=total, page=page, per_page=per_page)


@router.delete("/admin/comments/{comment_id}")
async def admin_delete_comment(comment_id: int, _admin: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    q = select(Comment).filter(Comment.id == comment_id)
    result = await db.execute(q)
    comment = result.scalar_one_or_none()
    if not comment:
        from fastapi import HTTPException; raise HTTPException(status_code=404, detail="评论不存在")
    await db.delete(comment); await db.commit(); return {"message": "评论已删除"}
