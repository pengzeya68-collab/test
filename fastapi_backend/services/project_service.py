"""Workspace project membership and personal-project bootstrap."""

from __future__ import annotations

import re
from typing import Iterable

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.workspace import WorkspaceProject, WorkspaceProjectMember

ROLE_RANK = {"viewer": 1, "member": 2, "admin": 3, "owner": 4}


class ProjectAccessError(PermissionError):
    pass


class ProjectNotFoundError(LookupError):
    pass


class ProjectDeletionConflictError(RuntimeError):
    """Raised when a workspace still contains members or project-scoped assets."""

    def __init__(self, blockers: dict[str, int]):
        self.blockers = blockers
        super().__init__("project is not empty")


class ProjectDeletionForbiddenError(PermissionError):
    pass


class ProjectPurgeConflictError(RuntimeError):
    """Raised when a destructive project cleanup would interrupt a live run."""

    def __init__(self, blockers: dict[str, int]):
        self.blockers = blockers
        super().__init__("project has active executions")


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


def _workspace_project_assets():
    """Return every model directly scoped to a WorkspaceProject.

    This explicit inventory intentionally excludes learning ``ProjectSpace`` models.
    A project can only be deleted after each of these user-facing assets is gone,
    preventing records from silently becoming inaccessible or cross-tenant orphans.
    """
    from fastapi_backend.models.autotest import (
        AutoTestCase,
        AutoTestEnvironment,
        AutoTestGlobalVariable,
        AutoTestGroup,
        AutoTestScenario,
        AutomationExecution,
        AutomationNotificationChannel,
        AutomationNotificationDelivery,
        CaptureSession,
        ImportJob,
        TestSuite,
    )
    from fastapi_backend.models.feature_upgrades import (
        APIContractRule,
        APIHealthMonitor,
        CaseConcurrencyTag,
        CaseReview,
        DefectRecord,
        DefectTrackerConfig,
        FlakyDetectionConfig,
        FlakyTestRecord,
        HealingConfig,
        HealingRecord,
        OpenAPISnapshot,
        ProtoFile,
        ReportTemplate,
        Requirement,
        SchemaChangeRecord,
        TraceSession,
        UIElement,
        UINetworkRule,
        UIPage,
        VisualBaseline,
        VisualComparison,
        VisualComparisonConfig,
    )
    from fastapi_backend.models.ui_automation import (
        DesktopAgent,
        UICase,
        UICaseGroup,
        UIRun,
        UISuite,
    )

    return (
        ("接口分组", AutoTestGroup, AutoTestGroup.project_id),
        ("接口用例", AutoTestCase, AutoTestCase.project_id),
        ("环境", AutoTestEnvironment, AutoTestEnvironment.project_id),
        ("全局变量", AutoTestGlobalVariable, AutoTestGlobalVariable.project_id),
        ("测试场景", AutoTestScenario, AutoTestScenario.workspace_project_id),
        ("接口套件", TestSuite, TestSuite.project_id),
        ("自动化执行", AutomationExecution, AutomationExecution.project_id),
        ("通知渠道", AutomationNotificationChannel, AutomationNotificationChannel.project_id),
        ("通知投递", AutomationNotificationDelivery, AutomationNotificationDelivery.project_id),
        ("抓包会话", CaptureSession, CaptureSession.project_id),
        ("导入任务", ImportJob, ImportJob.project_id),
        ("UI 用例", UICase, UICase.project_id),
        ("UI 分组", UICaseGroup, UICaseGroup.project_id),
        ("UI 套件", UISuite, UISuite.project_id),
        ("UI 执行", UIRun, UIRun.project_id),
        ("桌面 Agent", DesktopAgent, DesktopAgent.project_id),
        ("视觉基线", VisualBaseline, VisualBaseline.project_id),
        ("视觉对比", VisualComparison, VisualComparison.project_id),
        ("视觉配置", VisualComparisonConfig, VisualComparisonConfig.project_id),
        ("Trace 会话", TraceSession, TraceSession.project_id),
        ("协议文件", ProtoFile, ProtoFile.project_id),
        ("页面对象", UIPage, UIPage.project_id),
        ("元素对象", UIElement, UIElement.project_id),
        ("自愈记录", HealingRecord, HealingRecord.project_id),
        ("自愈配置", HealingConfig, HealingConfig.project_id),
        ("并发标签", CaseConcurrencyTag, CaseConcurrencyTag.project_id),
        ("缺陷平台", DefectTrackerConfig, DefectTrackerConfig.project_id),
        ("缺陷记录", DefectRecord, DefectRecord.project_id),
        ("Flaky 记录", FlakyTestRecord, FlakyTestRecord.project_id),
        ("Flaky 配置", FlakyDetectionConfig, FlakyDetectionConfig.project_id),
        ("网络拦截规则", UINetworkRule, UINetworkRule.project_id),
        ("OpenAPI 快照", OpenAPISnapshot, OpenAPISnapshot.project_id),
        ("Schema 变更", SchemaChangeRecord, SchemaChangeRecord.project_id),
        ("契约规则", APIContractRule, APIContractRule.project_id),
        ("API 健康监控", APIHealthMonitor, APIHealthMonitor.project_id),
        ("用例评审", CaseReview, CaseReview.project_id),
        ("需求", Requirement, Requirement.project_id),
        ("报告模板", ReportTemplate, ReportTemplate.project_id),
    )


async def project_deletion_blockers(db: AsyncSession, project_id: int) -> dict[str, int]:
    """Return non-empty project assets that make hard deletion unsafe."""
    blockers: dict[str, int] = {}
    for label, model, project_column in _workspace_project_assets():
        count = await db.scalar(
            select(func.count()).select_from(model).where(project_column == int(project_id))
        )
        if count:
            blockers[label] = int(count)
    return blockers


async def delete_empty_project(
    db: AsyncSession,
    *,
    user_id: int,
    project_id: int,
) -> None:
    """Delete an empty non-personal workspace owned by the current user."""
    project = await require_project_access(db, user_id, project_id, min_role="owner")
    if int(project.owner_id) != int(user_id):
        raise ProjectDeletionForbiddenError("only the project owner can delete a project")
    if project.is_personal:
        raise ProjectDeletionForbiddenError("personal projects cannot be deleted")

    member_count = await db.scalar(
        select(func.count())
        .select_from(WorkspaceProjectMember)
        .where(WorkspaceProjectMember.project_id == int(project_id))
    )
    blockers = await project_deletion_blockers(db, int(project_id))
    if int(member_count or 0) > 1:
        blockers["项目成员"] = int(member_count)
    if blockers:
        raise ProjectDeletionConflictError(blockers)

    await db.delete(project)
    await db.flush()


async def purge_project(
    db: AsyncSession,
    *,
    user_id: int,
    project_id: int,
) -> dict[str, int]:
    """Permanently remove a non-personal project and every scoped asset.

    Normal deletion deliberately rejects non-empty projects so users cannot lose
    test evidence by accident. This path is the explicit lifecycle escape hatch
    used only after a UI confirmation that names the project. It refuses to
    race a queued/running execution, then deletes project-scoped roots in
    child-first order. Database cascades remove their dependent records.
    """
    project = await require_project_access(db, user_id, project_id, min_role="owner")
    if int(project.owner_id) != int(user_id):
        raise ProjectDeletionForbiddenError("only the project owner can purge a project")
    if project.is_personal:
        raise ProjectDeletionForbiddenError("personal projects cannot be deleted")

    # Deleting a live run would leave an agent writing into a deleted project.
    # Keep this check separate from completed history, which is safe to purge.
    from fastapi_backend.models.autotest import AutomationExecution
    from fastapi_backend.models.ui_automation import UIRun

    active_statuses = ("queued", "running", "cancel_requested")
    active_automation = await db.scalar(
        select(func.count())
        .select_from(AutomationExecution)
        .where(
            AutomationExecution.project_id == int(project_id),
            AutomationExecution.status.in_(active_statuses),
        )
    )
    active_ui = await db.scalar(
        select(func.count())
        .select_from(UIRun)
        .where(UIRun.project_id == int(project_id), UIRun.status.in_(active_statuses))
    )
    active_blockers = {
        label: int(count)
        for label, count in (("运行中的自动化执行", active_automation), ("运行中的 UI 执行", active_ui))
        if int(count or 0) > 0
    }
    if active_blockers:
        raise ProjectPurgeConflictError(active_blockers)

    deleted: dict[str, int] = {}
    # The asset inventory is parent-first for diagnostics. Deleting it in
    # reverse makes dependent records disappear before their root assets.
    for label, model, project_column in reversed(_workspace_project_assets()):
        result = await db.execute(delete(model).where(project_column == int(project_id)))
        if result.rowcount and result.rowcount > 0:
            deleted[label] = int(result.rowcount)

    # Remove memberships explicitly instead of depending on the database
    # dialect's FK pragma. The project row is deleted last as the tenant root.
    await db.execute(
        delete(WorkspaceProjectMember).where(WorkspaceProjectMember.project_id == int(project_id))
    )
    await db.delete(project)
    await db.flush()
    return deleted


def is_masqueraded_user_id(project_id: int | None, known_user_ids: Iterable[int]) -> bool:
    if project_id is None:
        return False
    return int(project_id) in {int(u) for u in known_user_ids}
