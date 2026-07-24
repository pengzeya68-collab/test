"""Workspace project membership and personal-project bootstrap."""

from __future__ import annotations

import re
from typing import Iterable

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.workspace import WorkspaceProject, WorkspaceProjectMember

ROLE_RANK = {"viewer": 1, "member": 2, "admin": 3, "owner": 4}


class ProjectAccessError(PermissionError):
    pass


class ProjectNotFoundError(LookupError):
    pass


def _slugify(name: str, owner_id: int) -> str:
    base = re.sub(r"[^a-zA-Z0-9_-]+", "-", (name or "project").strip().lower()).strip("-") or "project"
    return f"{base}-{owner_id}"[:90]


async def ensure_personal_project(db: AsyncSession, user_id: int) -> WorkspaceProject:
    """Idempotent: one personal project per user."""
    existing = await db.scalar(
        select(WorkspaceProject).where(
            WorkspaceProject.owner_id == int(user_id),
            WorkspaceProject.is_personal.is_(True),
        )
    )
    if existing is not None:
        return existing
    project = WorkspaceProject(
        name="个人项目",
        key=f"personal-{int(user_id)}",
        description="兼容迁移自动创建的个人工作区",
        owner_id=int(user_id),
        is_personal=True,
    )
    db.add(project)
    await db.flush()
    db.add(
        WorkspaceProjectMember(
            project_id=project.id,
            user_id=int(user_id),
            role="owner",
        )
    )
    await db.flush()
    return project


async def create_project(
    db: AsyncSession,
    *,
    owner_id: int,
    name: str,
    description: str | None = None,
    key: str | None = None,
    is_personal: bool = False,
) -> WorkspaceProject:
    slug = (key or _slugify(name, owner_id)).strip()[:100]
    base_slug = slug
    for attempt in range(8):
        clash = await db.scalar(select(WorkspaceProject).where(WorkspaceProject.key == slug))
        if clash is None:
            break
        suffix = f"-{owner_id}" if attempt == 0 else f"-{owner_id}-{attempt + 1}"
        slug = f"{base_slug[: max(1, 100 - len(suffix))]}{suffix}"
    else:
        slug = f"project-{owner_id}-{int(__import__('time').time())}"[:100]
    project = WorkspaceProject(
        name=(name or "未命名项目").strip()[:200],
        key=slug,
        description=description,
        owner_id=int(owner_id),
        is_personal=bool(is_personal),
    )
    db.add(project)
    await db.flush()
    db.add(
        WorkspaceProjectMember(
            project_id=project.id,
            user_id=int(owner_id),
            role="owner",
        )
    )
    await db.flush()
    return project


async def list_projects_for_user(db: AsyncSession, user_id: int) -> list[WorkspaceProject]:
    await ensure_personal_project(db, user_id)
    rows = (
        await db.scalars(
            select(WorkspaceProject)
            .join(WorkspaceProjectMember, WorkspaceProjectMember.project_id == WorkspaceProject.id)
            .where(WorkspaceProjectMember.user_id == int(user_id))
            .order_by(WorkspaceProject.is_personal.desc(), WorkspaceProject.id.asc())
        )
    ).all()
    return list(rows)


async def get_member(
    db: AsyncSession, project_id: int, user_id: int
) -> WorkspaceProjectMember | None:
    return await db.scalar(
        select(WorkspaceProjectMember).where(
            WorkspaceProjectMember.project_id == int(project_id),
            WorkspaceProjectMember.user_id == int(user_id),
        )
    )


async def require_project_access(
    db: AsyncSession,
    user_id: int,
    project_id: int,
    min_role: str = "viewer",
) -> WorkspaceProject:
    project = await db.get(WorkspaceProject, int(project_id))
    if project is None:
        raise ProjectNotFoundError(f"project {project_id} not found")
    member = await get_member(db, project_id, user_id)
    if member is None and project.owner_id == int(user_id):
        # Repair missing owner membership
        member = WorkspaceProjectMember(
            project_id=project.id, user_id=int(user_id), role="owner"
        )
        db.add(member)
        await db.flush()
    if member is None:
        raise ProjectAccessError("not a project member")
    need = ROLE_RANK.get(min_role, 1)
    have = ROLE_RANK.get(str(member.role or "viewer"), 0)
    if have < need:
        raise ProjectAccessError(f"requires role {min_role}")
    return project


async def add_member(
    db: AsyncSession,
    *,
    project_id: int,
    user_id: int,
    role: str = "member",
) -> WorkspaceProjectMember:
    # Never allow elevating arbitrary users to owner via member API
    role_norm = role if role in ROLE_RANK else "member"
    if role_norm == "owner":
        role_norm = "admin"
    existing = await get_member(db, project_id, user_id)
    if existing is not None:
        if existing.role == "owner":
            return existing
        existing.role = role_norm
        await db.flush()
        return existing
    member = WorkspaceProjectMember(
        project_id=int(project_id), user_id=int(user_id), role=role_norm
    )
    db.add(member)
    await db.flush()
    return member


async def remove_member(db: AsyncSession, *, project_id: int, user_id: int) -> None:
    member = await get_member(db, project_id, user_id)
    if member is None:
        return
    if member.role == "owner":
        raise ProjectAccessError("cannot remove project owner")
    await db.delete(member)
    await db.flush()


async def resolve_project_id_for_user(
    db: AsyncSession,
    user_id: int,
    project_id: int | None = None,
) -> int:
    """Return validated project_id, or personal project when omitted (compat)."""
    if project_id is not None:
        project = await require_project_access(db, user_id, int(project_id), min_role="viewer")
        return int(project.id)
    personal = await ensure_personal_project(db, user_id)
    return int(personal.id)


async def project_id_for_asset_owner(db: AsyncSession, owner_user_id: int | None) -> int:
    """Map historical user-scoped assets onto personal workspace project."""
    uid = int(owner_user_id or 0)
    if uid <= 0:
        uid = 1
    personal = await ensure_personal_project(db, uid)
    return int(personal.id)


def is_masqueraded_user_id(project_id: int | None, known_user_ids: Iterable[int]) -> bool:
    if project_id is None:
        return False
    return int(project_id) in {int(u) for u in known_user_ids}
