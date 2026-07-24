"""Workspace project APIs — enterprise tenant boundary."""

from __future__ import annotations

import json
from typing import Any, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.models import User
from fastapi_backend.models.workspace import WorkspaceProjectMember
from fastapi_backend.services import project_service

router = APIRouter(prefix="/api/workspace/projects", tags=["工作区项目"])


class ProjectCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    key: Optional[str] = None


class MemberBody(BaseModel):
    user_id: int
    role: str = "member"


class ProjectPurgeBody(BaseModel):
    confirmation_name: str = Field(..., min_length=1, max_length=200)


def _project_dict(p, role: str | None = None) -> dict[str, Any]:
    return {
        "id": p.id,
        "name": p.name,
        "key": p.key,
        "description": p.description,
        "owner_id": p.owner_id,
        "is_personal": bool(p.is_personal),
        "role": role,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }


@router.get("")
async def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    x_project_id: Optional[int] = Header(default=None, alias="X-Project-Id"),
):
    projects = await project_service.list_projects_for_user(db, int(current_user.id))
    active = None
    if x_project_id is not None:
        try:
            active = await project_service.require_project_access(
                db, int(current_user.id), int(x_project_id), min_role="viewer"
            )
        except Exception:
            active = None
    if active is None and projects:
        active = projects[0]
    memberships = {
        m.project_id: m.role
        for m in (
            await db.scalars(
                select(WorkspaceProjectMember).where(
                    WorkspaceProjectMember.user_id == int(current_user.id)
                )
            )
        ).all()
    }
    await db.commit()
    return {
        "items": [_project_dict(p, memberships.get(p.id)) for p in projects],
        "active_project_id": active.id if active else None,
    }


@router.post("")
async def create_project(
    body: ProjectCreateBody,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_service.create_project(
        db,
        owner_id=int(current_user.id),
        name=body.name,
        description=body.description,
        key=body.key,
        is_personal=False,
    )
    await db.commit()
    await db.refresh(project)
    return _project_dict(project, role="owner")


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        project = await project_service.require_project_access(
            db, int(current_user.id), project_id, min_role="viewer"
        )
    except project_service.ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except project_service.ProjectAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    member = await project_service.get_member(db, project_id, int(current_user.id))
    return _project_dict(project, role=member.role if member else None)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an empty team project owned by the current user.

    Personal workspaces are permanent.  Team projects must have no extra
    members or project-scoped assets, making deletion explicit and reversible
    only through the normal asset lifecycle rather than implicit data loss.
    """
    try:
        await project_service.delete_empty_project(
            db, user_id=int(current_user.id), project_id=int(project_id)
        )
    except project_service.ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except project_service.ProjectAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except project_service.ProjectDeletionForbiddenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except project_service.ProjectDeletionConflictError as exc:
        blocker_summary = "、".join(
            f"{label} {count} 项" for label, count in exc.blockers.items()
        )
        raise HTTPException(
            status_code=409,
            detail=f"请先清理项目成员和资产后再删除：{blocker_summary}",
            headers={"X-TestMaster-Blockers": json.dumps(exc.blockers, ensure_ascii=True)},
        ) from exc
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{project_id}/purge")
async def purge_project(
    project_id: int,
    body: ProjectPurgeBody,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Explicitly and permanently delete all assets in a team project."""
    project = await db.get(project_service.WorkspaceProject, int(project_id))
    if project is None:
        raise HTTPException(status_code=404, detail=f"project {project_id} not found")
    if body.confirmation_name.strip() != project.name:
        raise HTTPException(status_code=422, detail="确认名称与项目名称不一致")
    try:
        deleted = await project_service.purge_project(
            db, user_id=int(current_user.id), project_id=int(project_id)
        )
    except project_service.ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except project_service.ProjectAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except project_service.ProjectDeletionForbiddenError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except project_service.ProjectPurgeConflictError as exc:
        blocker_summary = "、".join(f"{label} {count} 项" for label, count in exc.blockers.items())
        raise HTTPException(status_code=409, detail=f"请先停止执行后再清理项目：{blocker_summary}") from exc
    await db.commit()
    return {"ok": True, "deleted": deleted}


@router.get("/{project_id}/members")
async def list_members(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await project_service.require_project_access(
            db, int(current_user.id), project_id, min_role="viewer"
        )
    except project_service.ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except project_service.ProjectAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    members = list(
        (
            await db.scalars(
                select(WorkspaceProjectMember).where(
                    WorkspaceProjectMember.project_id == project_id
                )
            )
        ).all()
    )
    return {
        "items": [
            {"id": m.id, "project_id": m.project_id, "user_id": m.user_id, "role": m.role}
            for m in members
        ]
    }


@router.post("/{project_id}/members")
async def add_member(
    project_id: int,
    body: MemberBody,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await project_service.require_project_access(
            db, int(current_user.id), project_id, min_role="admin"
        )
        member = await project_service.add_member(
            db, project_id=project_id, user_id=body.user_id, role=body.role
        )
    except project_service.ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except project_service.ProjectAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    await db.commit()
    return {"id": member.id, "project_id": member.project_id, "user_id": member.user_id, "role": member.role}


@router.delete("/{project_id}/members/{user_id}")
async def delete_member(
    project_id: int,
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        await project_service.require_project_access(
            db, int(current_user.id), project_id, min_role="admin"
        )
        await project_service.remove_member(db, project_id=project_id, user_id=user_id)
    except project_service.ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except project_service.ProjectAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    await db.commit()
    return {"ok": True}
