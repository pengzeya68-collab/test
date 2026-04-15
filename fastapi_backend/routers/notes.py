"""学习笔记路由"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User, Note

router = APIRouter(prefix="/api/v1/notes", tags=["学习笔记"])


@router.get("/")
async def get_notes(
    exercise_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """获取笔记列表，可按习题ID筛选"""
    stmt = select(Note).where(Note.user_id == current_user.id)
    if exercise_id:
        stmt = stmt.where(Note.exercise_id == exercise_id)
    stmt = stmt.order_by(Note.updated_at.desc())
    result = await db.execute(stmt)
    notes = result.scalars().all()

    return {
        "notes": [
            {
                "id": n.id,
                "exercise_id": n.exercise_id,
                "title": n.title,
                "content": n.content,
                "created_at": n.created_at.strftime("%Y-%m-%d %H:%M") if n.created_at else "",
                "updated_at": n.updated_at.strftime("%Y-%m-%d %H:%M") if n.updated_at else "",
            }
            for n in notes
        ]
    }


@router.post("/")
async def create_note(
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """创建笔记"""
    title = body.get("title", "").strip()
    content = body.get("content", "").strip()
    exercise_id = body.get("exercise_id")

    if not title:
        raise HTTPException(status_code=400, detail="笔记标题不能为空")

    note = Note(
        user_id=current_user.id,
        exercise_id=exercise_id,
        title=title,
        content=content,
    )
    db.add(note)
    await db.commit()
    await db.refresh(note)

    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "exercise_id": note.exercise_id,
        "message": "笔记创建成功",
    }


@router.put("/{note_id}")
async def update_note(
    note_id: int,
    body: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """更新笔记"""
    stmt = select(Note).where(Note.id == note_id, Note.user_id == current_user.id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    if "title" in body:
        note.title = body["title"].strip()
    if "content" in body:
        note.content = body["content"].strip()

    await db.commit()

    return {"message": "笔记更新成功"}


@router.delete("/{note_id}")
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除笔记"""
    stmt = select(Note).where(Note.id == note_id, Note.user_id == current_user.id)
    result = await db.execute(stmt)
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="笔记不存在")

    await db.delete(note)
    await db.commit()

    return {"message": "笔记删除成功"}
