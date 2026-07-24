"""Enterprise workspace projects (not learning ProjectSpace / MockProject)."""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import relationship

from fastapi_backend.core.database import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class WorkspaceProject(Base):
    """Tenant boundary for autotest / UI / feature assets."""

    __tablename__ = "workspace_projects"
    __table_args__ = (
        UniqueConstraint("key", name="uq_workspace_projects_key"),
        Index("idx_workspace_projects_owner_id", "owner_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    key = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, nullable=False, index=True)
    is_personal = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    members = relationship(
        "WorkspaceProjectMember",
        back_populates="project",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class WorkspaceProjectMember(Base):
    __tablename__ = "workspace_project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_workspace_project_member"),
        Index("idx_workspace_project_members_user", "user_id"),
        Index("idx_workspace_project_members_project", "project_id"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer, ForeignKey("workspace_projects.id", ondelete="CASCADE"), nullable=False
    )
    user_id = Column(Integer, nullable=False, index=True)
    role = Column(String(20), nullable=False, default="member")  # owner|admin|member|viewer
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    project = relationship("WorkspaceProject", back_populates="members")
