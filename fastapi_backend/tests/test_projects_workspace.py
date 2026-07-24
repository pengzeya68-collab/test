"""Phase A: workspace project isolation and personal project helpers.

Includes real-DB asset isolation for AutoTest cases and UI cases.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

from fastapi_backend.models.autotest import (
    AutoTestCase,
    AutomationExecution,
    AutomationNotificationChannel,
    AutomationNotificationDelivery,
    CaptureSession,
)
from fastapi_backend.models.ui_automation import DesktopAgent, UICase
from fastapi_backend.models.workspace import WorkspaceProject, WorkspaceProjectMember
from fastapi_backend.services import project_service
from fastapi_backend.services.project_service import ProjectAccessError
from fastapi_backend.services.ui_automation import case_service


def _memory_db():
    store: dict = {"projects": [], "members": [], "next_id": 1}
    db = AsyncMock()

    async def _scalar(stmt):
        text = str(stmt).lower()
        # membership lookup
        if "workspace_project_members" in text or "WorkspaceProjectMember" in str(stmt):
            # best-effort: return first matching if any filter impossible — tests set side effects
            return store["members"][0] if store["members"] else None
        if "is_personal" in text or "personal" in text:
            for p in store["projects"]:
                if p.is_personal:
                    return p
            return None
        if "workspace_projects" in text and "key" in text:
            for p in store["projects"]:
                if p.key and p.key in text:
                    return p
            return None
        return None

    async def _get(model, pk):
        name = getattr(model, "__name__", "")
        if name == "WorkspaceProject":
            for p in store["projects"]:
                if p.id == pk:
                    return p
        return None

    async def _flush():
        for p in store["projects"]:
            if getattr(p, "id", None) is None:
                p.id = store["next_id"]
                store["next_id"] += 1
        for m in store["members"]:
            if getattr(m, "id", None) is None:
                m.id = store["next_id"]
                store["next_id"] += 1

    def _add(obj):
        if isinstance(obj, WorkspaceProject):
            store["projects"].append(obj)
        elif isinstance(obj, WorkspaceProjectMember):
            store["members"].append(obj)

    async def _scalars(stmt):
        return type("R", (), {"all": lambda self: list(store["projects"])})()

    db.scalar = AsyncMock(side_effect=_scalar)
    db.get = AsyncMock(side_effect=_get)
    db.flush = AsyncMock(side_effect=_flush)
    db.add = MagicMock(side_effect=_add)
    db.scalars = AsyncMock(side_effect=_scalars)
    db._store = store
    return db


@pytest.mark.asyncio
async def test_ensure_personal_project_is_idempotent():
    db = _memory_db()
    p1 = await project_service.ensure_personal_project(db, 42)
    assert p1.is_personal is True
    assert p1.owner_id == 42
    assert p1.key == "personal-42"
    p2 = await project_service.ensure_personal_project(db, 42)
    assert p2 is p1
    assert len([p for p in db._store["projects"] if p.is_personal]) == 1


@pytest.mark.asyncio
async def test_two_projects_assets_do_not_leak():
    db = _memory_db()
    personal = await project_service.ensure_personal_project(db, 7)
    p1 = await project_service.create_project(db, owner_id=7, name="Alpha")
    p2 = await project_service.create_project(db, owner_id=7, name="Beta")
    assert p1.id != p2.id
    assert personal.id != p1.id

    # Owner can access
    async def _member_for_owner(stmt):
        # return owner membership for project if any
        for m in db._store["members"]:
            if m.user_id == 7:
                return m
        return None

    db.scalar = AsyncMock(side_effect=_member_for_owner)
    got = await project_service.require_project_access(db, 7, p1.id, min_role="viewer")
    assert got.id == p1.id

    # Stranger denied
    async def _no_member(stmt):
        return None

    db.scalar = AsyncMock(side_effect=_no_member)
    with pytest.raises(ProjectAccessError):
        await project_service.require_project_access(db, 99, p1.id, min_role="viewer")


@pytest.mark.asyncio
async def test_personal_project_backfill_from_user_id():
    db = _memory_db()
    pid = await project_service.project_id_for_asset_owner(db, 5)
    assert pid == db._store["projects"][0].id
    assert db._store["projects"][0].key == "personal-5"


@pytest.mark.asyncio
async def test_empty_team_project_can_be_deleted_by_its_owner(db_session):
    project = await project_service.create_project(db_session, owner_id=81, name="Disposable")
    await db_session.flush()

    await project_service.delete_empty_project(
        db_session, user_id=81, project_id=project.id
    )

    assert await db_session.get(WorkspaceProject, project.id) is None


@pytest.mark.asyncio
async def test_project_deletion_is_blocked_by_assets_and_members(db_session):
    project = await project_service.create_project(db_session, owner_id=82, name="Not Empty")
    db_session.add(
        AutoTestCase(
            name="asset blocks deletion",
            method="GET",
            url="/health",
            user_id=82,
            project_id=project.id,
        )
    )
    await project_service.add_member(db_session, project_id=project.id, user_id=83)
    await db_session.flush()

    with pytest.raises(project_service.ProjectDeletionConflictError) as exc_info:
        await project_service.delete_empty_project(
            db_session, user_id=82, project_id=project.id
        )

    assert exc_info.value.blockers["接口用例"] == 1
    assert exc_info.value.blockers["项目成员"] == 2


@pytest.mark.asyncio
async def test_personal_project_cannot_be_deleted(db_session):
    personal = await project_service.ensure_personal_project(db_session, 84)
    await db_session.flush()

    with pytest.raises(project_service.ProjectDeletionForbiddenError):
        await project_service.delete_empty_project(
            db_session, user_id=84, project_id=personal.id
        )


def test_desktop_navigation_has_at_most_seven_workspaces():
    from pathlib import Path
    import re

    nav_file = Path(__file__).resolve().parents[2] / "frontend" / "src" / "constants" / "desktop-navigation.js"
    text = nav_file.read_text(encoding="utf-8")
    labels = re.findall(r"label:\s*'([^']+)'", text)
    # only top-level group labels appear as `label:` in DESKTOP_NAVIGATION
    assert 1 <= len(labels) <= 7
    assert "概览" in labels
    assert "管理" in labels


def test_workspace_project_router_is_registered_in_application():
    """The UI has a project page, so its backend boundary must not be omitted by the registry loop."""
    from fastapi_backend.main import app

    paths = {route.path for route in app.routes}
    assert "/api/workspace/projects" in paths
    project_route_methods = {
        method
        for route in app.routes
        if route.path == "/api/workspace/projects/{project_id}"
        for method in route.methods
    }
    assert {"GET", "DELETE"}.issubset(project_route_methods)


def test_frontend_project_context_uses_single_storage_key():
    from pathlib import Path

    store = Path(__file__).resolve().parents[2] / "frontend" / "src" / "stores" / "project.js"
    text = store.read_text(encoding="utf-8")
    assert "desktop-active-project-id" in text
    assert "tm_autotest_project_id" not in text
    assert "userInfo" not in text or "user.id" not in text
    # must not fall back to user id as project id
    assert "uid > 0 ? uid" not in text

    ui_api = Path(__file__).resolve().parents[2] / "frontend" / "src" / "api" / "ui-automation.js"
    ui_text = ui_api.read_text(encoding="utf-8")
    assert "X-Project-Id" in ui_text
    assert "desktop-active-project-id" in ui_text


@pytest.mark.asyncio
async def test_real_db_two_projects_api_cases_do_not_leak(db_session):
    """Create AutoTest cases in P1/P2; list filtered by project_id must not cross."""
    import fastapi_backend.models.workspace  # noqa: F401
    import fastapi_backend.models.autotest  # noqa: F401

    user_id = 1001
    personal = await project_service.ensure_personal_project(db_session, user_id)
    p1 = await project_service.create_project(db_session, owner_id=user_id, name="P1-Alpha")
    p2 = await project_service.create_project(db_session, owner_id=user_id, name="P2-Beta")
    await db_session.flush()

    c1 = AutoTestCase(
        name="case-in-p1",
        method="GET",
        url="/p1",
        user_id=user_id,
        project_id=p1.id,
    )
    c2 = AutoTestCase(
        name="case-in-p2",
        method="POST",
        url="/p2",
        user_id=user_id,
        project_id=p2.id,
    )
    db_session.add_all([c1, c2])
    await db_session.flush()

    from sqlalchemy import select

    rows_p1 = (
        await db_session.scalars(
            select(AutoTestCase).where(
                AutoTestCase.user_id == user_id,
                AutoTestCase.project_id == p1.id,
            )
        )
    ).all()
    rows_p2 = (
        await db_session.scalars(
            select(AutoTestCase).where(
                AutoTestCase.user_id == user_id,
                AutoTestCase.project_id == p2.id,
            )
        )
    ).all()

    names_p1 = {r.name for r in rows_p1}
    names_p2 = {r.name for r in rows_p2}
    assert names_p1 == {"case-in-p1"}
    assert names_p2 == {"case-in-p2"}
    assert "case-in-p2" not in names_p1
    assert "case-in-p1" not in names_p2
    assert personal.id != p1.id != p2.id


@pytest.mark.asyncio
async def test_real_db_ui_cases_list_isolated_by_workspace_project(db_session):
    """UI case_service.list_cases must honor WorkspaceProject, not ProjectSpace."""
    import fastapi_backend.models.workspace  # noqa: F401
    import fastapi_backend.models.ui_automation  # noqa: F401

    user_id = 2002
    await project_service.ensure_personal_project(db_session, user_id)
    p1 = await project_service.create_project(db_session, owner_id=user_id, name="UI-P1")
    p2 = await project_service.create_project(db_session, owner_id=user_id, name="UI-P2")
    await db_session.flush()

    case_p1 = await case_service.create_case(
        db_session,
        user_id,
        {"name": "ui-case-p1", "base_url": "https://a.example"},
        project_id=p1.id,
    )
    case_p2 = await case_service.create_case(
        db_session,
        user_id,
        {"name": "ui-case-p2", "base_url": "https://b.example"},
        project_id=p2.id,
    )
    await db_session.flush()
    assert case_p1.project_id == p1.id
    assert case_p2.project_id == p2.id

    listed_p1, total_p1 = await case_service.list_cases(db_session, user_id, project_id=p1.id)
    listed_p2, total_p2 = await case_service.list_cases(db_session, user_id, project_id=p2.id)
    names_p1 = {c.name for c in listed_p1}
    names_p2 = {c.name for c in listed_p2}

    assert total_p1 == 1 and names_p1 == {"ui-case-p1"}
    assert total_p2 == 1 and names_p2 == {"ui-case-p2"}

    with pytest.raises(Exception):
        await case_service.get_case(db_session, user_id, case_p1.id, project_id=p2.id)

    # create_case must reject ProjectSpace-style fake ids (non-member)
    with pytest.raises(Exception):
        await case_service.create_case(
            db_session,
            user_id,
            {"name": "bad", "project_id": 999999},
            project_id=999999,
        )


@pytest.mark.asyncio
async def test_resolve_active_project_id_from_header_logic(db_session):
    import fastapi_backend.models.workspace  # noqa: F401
    from fastapi_backend.deps.project_context import resolve_active_project_id

    user_id = 3003
    personal = await project_service.ensure_personal_project(db_session, user_id)
    other = await project_service.create_project(db_session, owner_id=user_id, name="Other")
    await db_session.flush()

    assert await resolve_active_project_id(db_session, user_id, None) == personal.id
    assert await resolve_active_project_id(db_session, user_id, other.id) == other.id


@pytest.mark.asyncio
async def test_capture_agents_and_notifications_are_project_scoped(db_session):
    """Phase A assets that were formerly user-global cannot cross workspaces."""
    from sqlalchemy import select

    from fastapi_backend.services.automation_notification_outbox import queue_execution_notifications
    from fastapi_backend.services.ui_automation import agent_service

    user_id = 4004
    p1 = await project_service.create_project(db_session, owner_id=user_id, name="Operations")
    p2 = await project_service.create_project(db_session, owner_id=user_id, name="Mobile")
    agent_p1, _ = await agent_service.register_agent(
        db_session, user_id, {"name": "ops-agent"}, project_id=p1.id
    )
    agent_p2, _ = await agent_service.register_agent(
        db_session, user_id, {"name": "mobile-agent"}, project_id=p2.id
    )
    db_session.add_all([
        CaptureSession(user_id=user_id, project_id=p1.id, source_url="https://ops.example.test"),
        CaptureSession(user_id=user_id, project_id=p2.id, source_url="https://mobile.example.test"),
        AutomationNotificationChannel(
            user_id=user_id, project_id=p1.id, name="ops", channel_type="email",
            config_encrypted="encrypted", notify_on=["failed"], is_active=True,
        ),
        AutomationNotificationChannel(
            user_id=user_id, project_id=p2.id, name="mobile", channel_type="email",
            config_encrypted="encrypted", notify_on=["failed"], is_active=True,
        ),
    ])
    execution = AutomationExecution(
        execution_type="suite", target_type="suite", target_id=1, user_id=user_id,
        project_id=p1.id, status="failed", idempotency_key="project-scope-execution",
    )
    db_session.add(execution)
    await db_session.flush()

    assert [agent.id for agent in await agent_service.list_agents(db_session, user_id, project_id=p1.id)] == [agent_p1.id]
    assert [agent.id for agent in await agent_service.list_agents(db_session, user_id, project_id=p2.id)] == [agent_p2.id]
    captures = (await db_session.scalars(
        select(CaptureSession).where(CaptureSession.user_id == user_id, CaptureSession.project_id == p1.id)
    )).all()
    assert [capture.source_url for capture in captures] == ["https://ops.example.test"]

    assert await queue_execution_notifications(db_session, execution, {"status": "failed"}) == 1
    deliveries = (await db_session.scalars(select(AutomationNotificationDelivery))).all()
    assert len(deliveries) == 1
    assert deliveries[0].project_id == p1.id
