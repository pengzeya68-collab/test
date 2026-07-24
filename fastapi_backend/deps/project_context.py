"""Resolve active WorkspaceProject from X-Project-Id for automation APIs."""

from __future__ import annotations

from typing import Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.models import User
from fastapi_backend.models.workspace import WorkspaceProject
from fastapi_backend.services import project_service


async def resolve_active_project_id(
    db: AsyncSession,
    user_id: int,
    x_project_id: int | None = None,
    *,
    min_role: str = "viewer",
) -> int:
    """Validate header project (if any) or fall back to personal project."""
    try:
        if x_project_id is not None:
            project = await project_service.require_project_access(
                db, int(user_id), int(x_project_id), min_role=min_role
            )
            return int(project.id)
        return await project_service.resolve_project_id_for_user(db, int(user_id), None)
    except project_service.ProjectNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc) or "项目不存在") from exc
    except project_service.ProjectAccessError as exc:
        raise HTTPException(status_code=403, detail=str(exc) or "无权访问该项目") from exc


async def get_active_project_id(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    x_project_id: Optional[int] = Header(default=None, alias="X-Project-Id"),
) -> int:
    """FastAPI dependency: active workspace project id for the request."""
    return await resolve_active_project_id(db, int(current_user.id), x_project_id)


async def get_active_project_id_member(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    x_project_id: Optional[int] = Header(default=None, alias="X-Project-Id"),
) -> int:
    """Same as get_active_project_id but requires member role for writes."""
    return await resolve_active_project_id(
        db, int(current_user.id), x_project_id, min_role="member"
    )


def project_scope_clause(column, project_id: int):
    """Strict filter: assets stamped with this workspace project."""
    return column == int(project_id)


def project_scope_with_legacy_null(
    column,
    project_id: int,
    *,
    user_id_column,
    user_id: int,
    is_personal_active: bool,
):
    """Project match for all members; legacy NULL rows only on personal project for owner.

    Team projects: ``column == project_id`` only (shared among members).
    Personal projects: also include historical rows with NULL project_id owned by user.
    """
    if is_personal_active and user_id_column is not None:
        return or_(
            column == int(project_id),
            and_(column.is_(None), user_id_column == int(user_id)),
        )
    return column == int(project_id)


async def is_personal_project(db: AsyncSession, project_id: int) -> bool:
    project = await db.get(WorkspaceProject, int(project_id))
    return bool(project and project.is_personal)


def asset_visible_in_project(
    *,
    asset_project_id: int | None,
    asset_user_id: int | None,
    active_project_id: int,
    viewer_user_id: int,
    is_personal_active: bool,
) -> bool:
    """In-memory visibility check matching project_scope_with_legacy_null."""
    if asset_project_id is not None:
        return int(asset_project_id) == int(active_project_id)
    return bool(is_personal_active and asset_user_id is not None and int(asset_user_id) == int(viewer_user_id))
