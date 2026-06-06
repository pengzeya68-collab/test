"""
收藏夹路由

路径前缀: /api/v1/favorites
"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User, Favorite

router = APIRouter(prefix="/api/v1/favorites", tags=["收藏"])


@router.get("")
async def get_favorites(
    item_type: str = Query(None, description="post/exercise/note"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    base = select(Favorite).where(Favorite.user_id == current_user.id)
    if item_type:
        base = base.where(Favorite.item_type == item_type)

    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    result = await db.execute(base.order_by(Favorite.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    favs = result.scalars().all()

    items = []
    for f in favs:
        item = {
            "id": f.id,
            "type": f.item_type,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        if f.item_type == "post" and f.post:
            item["data"] = {
                "id": f.post.id,
                "title": f.post.title,
                "summary": f.post.summary,
            }
        elif f.item_type == "exercise" and f.exercise:
            item["data"] = {"id": f.exercise.id, "title": f.exercise.title}
        elif f.item_type == "note" and f.note:
            item["data"] = {"id": f.note.id, "title": f.note.title}
        items.append(item)

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/toggle")
async def toggle_favorite(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item_type = body.get("type")
    item_id = body.get("item_id")
    if item_type not in ("post", "exercise", "note") or not item_id:
        raise HTTPException(status_code=400, detail="请提供 type(post/exercise/note) 和 item_id")

    # 查找是否已收藏
    filters = [Favorite.user_id == current_user.id, Favorite.item_type == item_type]
    if item_type == "post":
        filters.append(Favorite.post_id == item_id)
    elif item_type == "exercise":
        filters.append(Favorite.exercise_id == item_id)
    elif item_type == "note":
        filters.append(Favorite.note_id == item_id)

    existing = await db.execute(select(Favorite).where(and_(*filters)))
    fav = existing.scalar_one_or_none()

    if fav:
        await db.delete(fav)
        await db.commit()
        return {"favorited": False, "message": "已取消收藏"}
    else:
        try:
            kw = {"user_id": current_user.id, "item_type": item_type}
            if item_type == "post":
                kw["post_id"] = item_id
            elif item_type == "exercise":
                kw["exercise_id"] = item_id
            elif item_type == "note":
                kw["note_id"] = item_id
            db.add(Favorite(**kw))
            await db.commit()
            return {"favorited": True, "message": "已收藏"}
        except IntegrityError:
            await db.rollback()
            return {"favorited": True, "message": "已收藏"}


@router.get("/check")
async def check_favorite(
    item_type: str = Query(...),
    item_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filters = [Favorite.user_id == current_user.id, Favorite.item_type == item_type]
    if item_type == "post":
        filters.append(Favorite.post_id == item_id)
    elif item_type == "exercise":
        filters.append(Favorite.exercise_id == item_id)
    elif item_type == "note":
        filters.append(Favorite.note_id == item_id)
    else:
        raise HTTPException(status_code=400, detail="type 仅支持 post/exercise/note")

    existing = await db.execute(select(Favorite).where(and_(*filters)))
    fav = existing.scalar_one_or_none()
    return {"favorited": fav is not None}
