"""UI Automation router."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Body, Depends, Header, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from fastapi_backend.core.config import settings
from fastapi_backend.core.database import get_db
from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.exceptions import BusinessException
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.models.models import User
from fastapi_backend.models.autotest import (
    ArtifactManifest,
    ArtifactUploadSession,
    AutoTestEnvironment,
    AutomationExecution,
    ExecutionEvent,
)
from fastapi_backend.schemas.ui_automation import (
    UIArtifactCreate,
    UIArtifactOut,
    UIArtifactLinkIn,
    AIAnalysisFeedbackIn,
    UICaseCreate,
    UICaseGroupCreate,
    UICaseGroupOut,
    UICaseGroupUpdate,
    UICaseOut,
    UICaseUpdate,
    UICaseVersionCreate,
    UICaseVersionOut,
    UIRunCreate,
    UIRunEventBatchIn,
    UIRunEventBatchOut,
    UIRunOut,
    DesktopAgentOut,
    DesktopAgentRegister,
    UIStepBatchSave,
    UIStepResultOut,
    UISuiteCreate,
    UISuiteUpdate,
    UISuiteOut,
    UISuiteItemCreate,
)
from fastapi_backend.services.ui_automation import (
    agent_service,
    ai_assistance,
    case_service,
    run_service,
    suite_service,
)
from fastapi_backend.services.ui_automation.runtime_environment import resolve_runtime_environment
from fastapi_backend.models.ui_automation import ArtifactAnnotation
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.routers.autotest_artifacts import (
    create_execution_upload_session,
    finalize_execution_upload_session,
    write_execution_upload_chunk,
)

router = APIRouter(prefix="/api/ui-automation", tags=["ui-automation"])


def _ensure_enabled() -> None:
    if not getattr(settings, "UI_AUTOMATION_ENABLED", False):
        raise BusinessException("UI automation feature is disabled", code="FEATURE_DISABLED", status_code=403)


async def _run_payload(db: AsyncSession, run) -> dict:
    payload = UIRunOut.model_validate(run).model_dump()
    if run.automation_execution_id:
        execution = await db.get(AutomationExecution, run.automation_execution_id)
        payload["execution_id"] = execution.public_id if execution else None
    return payload


def _agent_payload(agent) -> dict:
    """Keep datetime wire values stable across PostgreSQL and SQLite tests."""
    payload = DesktopAgentOut.model_validate(agent).model_dump()
    for key, value in payload.items():
        if isinstance(value, datetime) and value.tzinfo is None:
            payload[key] = value.replace(tzinfo=timezone.utc)
    return payload


@router.get("/runtime-config")
async def get_runtime_config(
    response: Response,
    environment_id: Optional[int] = Query(None),
    current_user: User = Depends(require_permissions("ui:execute")),
    autotest_db: AsyncSession = Depends(get_autotest_db),
):
    """Resolve execution variables for the trusted desktop main process."""
    _ensure_enabled()
    runtime = await resolve_runtime_environment(
        autotest_db,
        user_id=current_user.id,
        environment_id=environment_id,
    )
    response.headers["Cache-Control"] = "private, no-store"
    # Keep the established user-client response keys while sharing one secure resolver.
    return {
        "environment_id": runtime["id"],
        "environment_name": runtime["name"],
        "base_url": runtime["base_url"],
        "services": runtime["services"],
        "variables": runtime["variables"],
        "secret_keys": runtime["secret_keys"],
    }


@router.get("/cases")
async def list_cases(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    group_id: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    cases, total = await case_service.list_cases(
        db, current_user.id, page=page, page_size=page_size, group_id=group_id, keyword=keyword, status=status
    )
    return {
        "items": [UICaseOut.model_validate(case).model_dump() for case in cases],
        "total": total,
        "page": page,
        "size": page_size,
    }


@router.get("/cases/{case_id}")
async def get_case(
    case_id: int, current_user: User = Depends(require_permissions("ui:read")), db: AsyncSession = Depends(get_db)
):
    _ensure_enabled()
    case = await case_service.get_case(db, current_user.id, case_id)
    steps = await case_service.list_steps(db, case_id)
    payload = UICaseOut.model_validate(case).model_dump()
    payload["steps"] = [case_service.step_to_snapshot_dict(step) for step in steps]
    return payload


@router.post("/cases")
async def create_case(
    body: UICaseCreate,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    case = await case_service.create_case(db, current_user.id, body.model_dump())
    await db.commit()
    return UICaseOut.model_validate(case).model_dump()


@router.put("/cases/{case_id}")
async def update_case(
    case_id: int,
    body: UICaseUpdate,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    case = await case_service.update_case(db, current_user.id, case_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return UICaseOut.model_validate(case).model_dump()


@router.delete("/cases/{case_id}")
async def delete_case(
    case_id: int, current_user: User = Depends(require_permissions("ui:write")), db: AsyncSession = Depends(get_db)
):
    _ensure_enabled()
    await case_service.delete_case(db, current_user.id, case_id)
    await db.commit()
    return {"message": "Case deleted"}


@router.put("/cases/{case_id}/steps")
async def batch_save_steps(
    case_id: int,
    body: UIStepBatchSave,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    await case_service.get_case(db, current_user.id, case_id)
    steps = await case_service.batch_save_steps(db, case_id, [step.model_dump(by_alias=True) for step in body.steps])
    await db.commit()
    return {
        "message": f"Saved {len(steps)} steps",
        "steps": [case_service.step_to_snapshot_dict(step) for step in steps],
    }


@router.post("/cases/{case_id}/versions")
async def create_version(
    case_id: int,
    body: UICaseVersionCreate,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    version = await case_service.create_version_from_case(db, current_user.id, case_id, body.change_summary)
    await db.commit()
    return UICaseVersionOut.model_validate(version).model_dump()


@router.get("/cases/{case_id}/versions")
async def list_versions(
    case_id: int, current_user: User = Depends(require_permissions("ui:read")), db: AsyncSession = Depends(get_db)
):
    _ensure_enabled()
    versions = await case_service.list_versions(db, case_id, current_user.id)
    return {
        "items": [UICaseVersionOut.model_validate(version).model_dump() for version in versions],
        "total": len(versions),
    }


@router.get("/cases/{case_id}/versions/{version_id}")
async def get_version(
    case_id: int,
    version_id: int,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    version = await case_service.get_version(db, case_id, version_id, current_user.id)
    return UICaseVersionOut.model_validate(version).model_dump()


@router.post("/cases/{case_id}/versions/{version_id}/restore")
async def restore_version(
    case_id: int,
    version_id: int,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    case = await case_service.restore_version(db, case_id, version_id, current_user.id)
    await db.commit()
    return UICaseOut.model_validate(case).model_dump()


@router.get("/groups")
async def list_groups(current_user: User = Depends(require_permissions("ui:read")), db: AsyncSession = Depends(get_db)):
    _ensure_enabled()
    groups = await case_service.list_groups(db, current_user.id)
    return {"items": [UICaseGroupOut.model_validate(group).model_dump() for group in groups], "total": len(groups)}


@router.post("/groups")
async def create_group(
    body: UICaseGroupCreate,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    group = await case_service.create_group(db, current_user.id, body.model_dump())
    await db.commit()
    return UICaseGroupOut.model_validate(group).model_dump()


@router.put("/groups/{group_id}")
async def update_group(
    group_id: int,
    body: UICaseGroupUpdate,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    group = await case_service.update_group(db, current_user.id, group_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return UICaseGroupOut.model_validate(group).model_dump()


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int, current_user: User = Depends(require_permissions("ui:write")), db: AsyncSession = Depends(get_db)
):
    _ensure_enabled()
    await case_service.delete_group(db, current_user.id, group_id)
    await db.commit()
    return {"message": "Group deleted"}


@router.get("/suites")
async def list_ui_suites(
    current_user: User = Depends(require_permissions("ui:read")), db: AsyncSession = Depends(get_db)
):
    _ensure_enabled()
    suites = await suite_service.list_suites(db, current_user.id)
    return {"items": [UISuiteOut.model_validate(item).model_dump() for item in suites], "total": len(suites)}


@router.post("/suites")
async def create_ui_suite(
    body: UISuiteCreate,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    suite = await suite_service.create_suite(db, current_user.id, body.model_dump())
    await db.commit()
    return UISuiteOut.model_validate(suite).model_dump()


@router.get("/suites/{suite_id}")
async def get_ui_suite(
    suite_id: int, current_user: User = Depends(require_permissions("ui:read")), db: AsyncSession = Depends(get_db)
):
    _ensure_enabled()
    suite = await suite_service.get_suite(db, current_user.id, suite_id)
    return UISuiteOut.model_validate(suite).model_dump()


@router.put("/suites/{suite_id}")
async def update_ui_suite(
    suite_id: int,
    body: UISuiteUpdate,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    suite = await suite_service.update_suite(db, current_user.id, suite_id, body.model_dump(exclude_unset=True))
    await db.commit()
    return UISuiteOut.model_validate(suite).model_dump()


@router.put("/suites/{suite_id}/items")
async def replace_ui_suite_items(
    suite_id: int,
    body: list[UISuiteItemCreate],
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    suite = await suite_service.replace_items(db, current_user.id, suite_id, [item.model_dump() for item in body])
    await db.commit()
    return UISuiteOut.model_validate(suite).model_dump()


@router.get("/suites/{suite_id}/execution-plan")
async def get_ui_suite_execution_plan(
    suite_id: int, current_user: User = Depends(require_permissions("ui:read")), db: AsyncSession = Depends(get_db)
):
    _ensure_enabled()
    return await suite_service.build_execution_plan(db, current_user.id, suite_id)


@router.delete("/suites/{suite_id}")
async def delete_ui_suite(
    suite_id: int, current_user: User = Depends(require_permissions("ui:write")), db: AsyncSession = Depends(get_db)
):
    _ensure_enabled()
    await suite_service.delete_suite(db, current_user.id, suite_id)
    await db.commit()
    return {"message": "Suite deleted"}


@router.get("/runs")
async def list_runs(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=1000),
    status: Optional[str] = Query(None),
    case_id: Optional[int] = Query(None),
    suite_id: Optional[int] = Query(None),
    current_user: User = Depends(require_permissions("ui:read", "execution:read")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    runs, total = await run_service.list_runs(
        db, current_user.id, page=page, page_size=page_size, status=status, case_id=case_id, suite_id=suite_id
    )
    return {"items": [await _run_payload(db, run) for run in runs], "total": total, "page": page, "size": page_size}


@router.post("/runs")
async def create_run(
    body: UIRunCreate,
    current_user: User = Depends(require_permissions("ui:execute")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    run = await run_service.create_run(db, current_user.id, body.model_dump())
    await db.commit()
    return await _run_payload(db, run)


@router.get("/runs/{run_id}")
async def get_run(
    run_id: int,
    current_user: User = Depends(require_permissions("ui:read", "execution:read")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    run = await run_service.get_run(db, current_user.id, run_id)
    return await _run_payload(db, run)


@router.get("/runs/{run_id}/step-results")
async def get_run_step_results(
    run_id: int,
    current_user: User = Depends(require_permissions("ui:read", "execution:read")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    step_results = await run_service.list_step_results(db, current_user.id, run_id)
    return {
        "items": [UIStepResultOut.model_validate(item).model_dump() for item in step_results],
        "total": len(step_results),
    }


@router.post("/runs/{run_id}/events")
async def append_run_events(
    run_id: int,
    body: UIRunEventBatchIn,
    current_user: User = Depends(require_permissions("ui:execute")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    accepted, ignored, last_sequence, run = await run_service.append_run_events(
        db,
        current_user.id,
        run_id,
        [event.model_dump(exclude_none=True) for event in body.events],
    )
    await db.commit()
    return UIRunEventBatchOut(
        accepted=accepted, ignored=ignored, last_sequence=last_sequence, status=run.status
    ).model_dump()


@router.post("/runs/{run_id}/heartbeat")
async def heartbeat_run(
    run_id: int, current_user: User = Depends(require_permissions("ui:execute")), db: AsyncSession = Depends(get_db)
):
    _ensure_enabled()
    run = await run_service.heartbeat_run(db, current_user.id, run_id)
    await db.commit()
    return await _run_payload(db, run)


@router.post("/runs/{run_id}/cancel")
async def cancel_run(
    run_id: int,
    current_user: User = Depends(require_permissions("execution:cancel")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    run = await run_service.cancel_run(db, current_user.id, run_id)
    await db.commit()
    return await _run_payload(db, run)


@router.get("/runs/{run_id}/artifacts")
async def list_run_artifacts(
    run_id: int,
    current_user: User = Depends(require_permissions("ui:read", "execution:read")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    artifacts = await run_service.list_artifacts(db, current_user.id, run_id)
    return {"items": [UIArtifactOut.model_validate(item).model_dump() for item in artifacts], "total": len(artifacts)}


@router.get("/runs/{run_id}/artifacts/{artifact_id}/content")
async def get_run_artifact_content(
    run_id: int,
    artifact_id: int,
    current_user: User = Depends(require_permissions("artifact:download")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    artifacts = await run_service.list_artifacts(db, current_user.id, run_id)
    artifact_row = next((item for item in artifacts if item.id == artifact_id), None)
    if artifact_row is None:
        raise BusinessException("UI artifact not found", code="NOT_FOUND", status_code=404)
    if artifact_row.artifact_manifest_id:
        return RedirectResponse(
            url=f"/api/auto-test/artifacts/{artifact_row.artifact_manifest_id}/content",
            status_code=307,
        )
    artifact, content = await run_service.read_artifact_content(db, current_user.id, run_id, artifact_id)
    return Response(
        content=content,
        media_type=artifact.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{artifact.filename}"'},
    )


@router.post("/runs/{run_id}/artifacts")
async def register_run_artifact(
    run_id: int,
    body: UIArtifactCreate = Body(...),
    current_user: User = Depends(require_permissions("ui:execute")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    artifact = await run_service.register_artifact(db, current_user.id, run_id, body.model_dump())
    await db.commit()
    return UIArtifactOut.model_validate(artifact).model_dump()


@router.post("/runs/{run_id}/artifacts/link")
async def link_run_artifact(
    run_id: int,
    body: UIArtifactLinkIn,
    current_user: User = Depends(require_permissions("ui:execute")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    artifact = await run_service.link_artifact_manifest(db, current_user.id, run_id, body.artifact_manifest_id)
    await db.commit()
    return UIArtifactOut.model_validate(artifact).model_dump()


@router.get("/agents")
async def list_desktop_agents(
    current_user: User = Depends(require_permissions("ui:agent")), db: AsyncSession = Depends(get_db)
):
    _ensure_enabled()
    agents = await agent_service.list_agents(db, current_user.id)
    return {"items": [_agent_payload(agent) for agent in agents], "total": len(agents)}


@router.post("/agents")
async def register_desktop_agent(
    body: DesktopAgentRegister,
    current_user: User = Depends(require_permissions("ui:agent")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    agent, bootstrap_token = await agent_service.register_agent(db, current_user.id, body.model_dump())
    await db.commit()
    payload = _agent_payload(agent)
    payload["bootstrap_token"] = bootstrap_token
    return payload


@router.delete("/agents/{agent_id}")
@audit_log("revoke", "desktop_agent", resource_id_param="agent_id")
async def revoke_desktop_agent(
    agent_id: int,
    request: Request,
    current_user: User = Depends(require_permissions("ui:agent")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    agent = await agent_service.revoke_agent(db, current_user.id, agent_id)
    await db.commit()
    return _agent_payload(agent)


@router.post("/agents/{agent_id}/heartbeat")
async def heartbeat_desktop_agent(
    agent_id: int,
    body: dict = Body(default_factory=dict),
    agent_token: str | None = Header(default=None, alias="X-TestMaster-Agent-Token"),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    agent = await agent_service.authenticate_agent(db, agent_id, agent_token)
    cancel_run_ids = await agent_service.heartbeat_agent(db, agent, body)
    await db.commit()
    return {**_agent_payload(agent), "cancel_run_ids": cancel_run_ids}


@router.post("/agents/{agent_id}/claim")
async def claim_desktop_agent_run(
    agent_id: int,
    agent_token: str | None = Header(default=None, alias="X-TestMaster-Agent-Token"),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    agent = await agent_service.authenticate_agent(db, agent_id, agent_token)
    run, plan = await agent_service.claim_next_run(db, agent)
    await db.commit()
    if run is None:
        return {"run": None}
    return {"run": await _run_payload(db, run), "plan": plan}


@router.post("/agents/{agent_id}/runs/{run_id}/events")
async def append_agent_run_events(
    agent_id: int,
    run_id: int,
    body: UIRunEventBatchIn,
    agent_token: str | None = Header(default=None, alias="X-TestMaster-Agent-Token"),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    agent = await agent_service.authenticate_agent(db, agent_id, agent_token)
    run = await agent_service.get_agent_run(db, agent, run_id, require_active_lease=False)
    if run.status not in run_service.TERMINAL_STATUSES:
        await agent_service.get_agent_run(db, agent, run_id, require_active_lease=True, lock=True)
    accepted, ignored, last_sequence, updated = await run_service.append_run_events(
        db,
        agent.owner_id,
        run_id,
        [event.model_dump(exclude_none=True) for event in body.events],
    )
    await agent_service.heartbeat_agent(db, agent)
    await db.commit()
    return UIRunEventBatchOut(
        accepted=accepted, ignored=ignored, last_sequence=last_sequence, status=updated.status
    ).model_dump()


@router.post("/agents/{agent_id}/runs/{run_id}/artifacts/upload-sessions", status_code=201)
async def create_agent_artifact_upload(
    agent_id: int,
    run_id: int,
    body: dict = Body(default_factory=dict),
    agent_token: str | None = Header(default=None, alias="X-TestMaster-Agent-Token"),
    db: AsyncSession = Depends(get_db),
):
    """Create an upload session scoped to this Agent's active run."""
    _ensure_enabled()
    agent = await agent_service.authenticate_agent(db, agent_id, agent_token)
    run = await agent_service.get_agent_run(db, agent, run_id, require_active_lease=True, lock=True)
    execution = await run_service._ensure_authoritative_execution(db, run)
    upload_id_placeholder = "__UPLOAD_ID__"
    endpoint_template = (
        f"/api/ui-automation/agents/{agent.id}/runs/{run.id}/artifacts/upload-sessions/{upload_id_placeholder}/content"
    )
    result = await create_execution_upload_session(
        db,
        execution=execution,
        user_id=agent.owner_id,
        body=body,
    )
    result["chunk_endpoint"] = endpoint_template.replace(upload_id_placeholder, result["upload_id"])
    await run_service.heartbeat_run(db, agent.owner_id, run.id)
    await agent_service.heartbeat_agent(db, agent)
    await db.commit()
    return result


@router.put("/agents/{agent_id}/runs/{run_id}/artifacts/upload-sessions/{upload_id}/content", status_code=204)
async def upload_agent_artifact_chunk(
    agent_id: int,
    run_id: int,
    upload_id: str,
    request: Request,
    content_range: str | None = Header(default=None, alias="Content-Range"),
    agent_token: str | None = Header(default=None, alias="X-TestMaster-Agent-Token"),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    agent = await agent_service.authenticate_agent(db, agent_id, agent_token)
    run = await agent_service.get_agent_run(db, agent, run_id, require_active_lease=True, lock=True)
    execution = await run_service._ensure_authoritative_execution(db, run)
    await write_execution_upload_chunk(
        db,
        upload_id=upload_id,
        user_id=agent.owner_id,
        request=request,
        content_range=content_range,
        execution_id=execution.id,
    )
    await run_service.heartbeat_run(db, agent.owner_id, run.id)
    await agent_service.heartbeat_agent(db, agent)
    await db.commit()


@router.get("/agents/{agent_id}/runs/{run_id}/artifacts/upload-sessions/{upload_id}")
async def get_agent_artifact_upload_progress(
    agent_id: int,
    run_id: int,
    upload_id: str,
    agent_token: str | None = Header(default=None, alias="X-TestMaster-Agent-Token"),
    db: AsyncSession = Depends(get_db),
):
    """Expose only the owning Agent's resumable offset for a live UI run."""
    _ensure_enabled()
    agent = await agent_service.authenticate_agent(db, agent_id, agent_token)
    run = await agent_service.get_agent_run(db, agent, run_id, require_active_lease=True)
    execution = await run_service._ensure_authoritative_execution(db, run)
    session = await db.scalar(
        select(ArtifactUploadSession).where(
            ArtifactUploadSession.id == upload_id,
            ArtifactUploadSession.user_id == agent.owner_id,
            ArtifactUploadSession.execution_id == execution.id,
        )
    )
    if session is None:
        raise HTTPException(status_code=404, detail="Artifact upload session was not found")
    return {
        "upload_id": session.id,
        "status": session.status,
        "received_bytes": session.received_bytes,
        "size_bytes": session.expected_size_bytes,
        "expires_at": session.expires_at,
    }


@router.post("/agents/{agent_id}/runs/{run_id}/artifacts/upload-sessions/{upload_id}/complete")
async def complete_agent_artifact_upload(
    agent_id: int,
    run_id: int,
    upload_id: str,
    agent_token: str | None = Header(default=None, alias="X-TestMaster-Agent-Token"),
    db: AsyncSession = Depends(get_db),
):
    """Finalize, verify and link an Agent artifact to its UI run."""
    _ensure_enabled()
    agent = await agent_service.authenticate_agent(db, agent_id, agent_token)
    run = await agent_service.get_agent_run(db, agent, run_id, require_active_lease=True, lock=True)
    execution = await run_service._ensure_authoritative_execution(db, run)
    result = await finalize_execution_upload_session(
        db,
        upload_id=upload_id,
        user_id=agent.owner_id,
        execution_id=execution.id,
    )
    linked = await run_service.link_artifact_manifest(db, agent.owner_id, run.id, result["artifact_id"])
    await run_service.heartbeat_run(db, agent.owner_id, run.id)
    await agent_service.heartbeat_agent(db, agent)
    await db.commit()
    return {
        **result,
        "linked_artifact": UIArtifactOut.model_validate(linked).model_dump(),
    }


@router.post("/runs/{run_id}/ai/failure-analysis")
async def analyze_ui_failure(
    run_id: int,
    current_user: User = Depends(require_permissions("ai:analyze", "ui:read", "execution:read")),
    db: AsyncSession = Depends(get_db),
):
    """Return a redacted advisory analysis; it never changes the run or case."""
    _ensure_enabled()
    run = await run_service.get_run(db, current_user.id, run_id)
    if run.status not in {"failed", "infra_error", "timed_out", "cancelled"}:
        raise BusinessException("失败归因仅适用于已结束且未通过的运行记录", code="ANALYSIS_NOT_READY", status_code=409)
    return await ai_assistance.analyze_failure(db, current_user.id, run)


@router.post("/cases/{case_id}/ai/locator-suggestions")
async def suggest_ui_locators(
    case_id: int,
    body: dict = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("ai:analyze", "ui:read")),
    db: AsyncSession = Depends(get_db),
):
    """Accept only desktop-validated probes and return non-destructive suggestions."""
    _ensure_enabled()
    case = await case_service.get_case(db, current_user.id, case_id)
    return await ai_assistance.suggest_locators(
        db,
        current_user.id,
        case,
        step_id=body.get("step_id"),
        probes=body.get("locator_probes"),
        current_url=body.get("current_url"),
        login_state_matches=body.get("login_state_matches"),
    )


@router.post("/requirements/test-points")
async def generate_requirement_test_points(
    body: dict = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("ai:analyze")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    return await ai_assistance.generate_requirement_test_points(
        db,
        current_user.id,
        body.get("requirement_text"),
        body.get("traceability_id"),
        body.get("context"),
    )


@router.post("/requirements/case-drafts")
async def generate_requirement_case_drafts(
    body: dict = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("ai:analyze")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    return await ai_assistance.generate_case_drafts(
        db,
        current_user.id,
        body.get("analysis_id"),
        body.get("point_ids"),
        body.get("point_overrides"),
    )


@router.get("/ai-analysis/metrics")
async def get_ai_feedback_metrics(
    analysis_type: str | None = Query(None, min_length=1, max_length=40),
    current_user: User = Depends(require_permissions("ai:feedback")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    return await ai_assistance.get_feedback_metrics(
        db,
        current_user.id,
        analysis_type=analysis_type,
    )


@router.post("/ai-analysis/{analysis_id}/feedback")
@audit_log("feedback", "ai_analysis")
async def submit_ai_analysis_feedback(
    analysis_id: str,
    body: AIAnalysisFeedbackIn,
    request: Request,
    current_user: User = Depends(require_permissions("ai:feedback")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    feedback = await ai_assistance.submit_analysis_feedback(
        db,
        current_user.id,
        analysis_id,
        accepted=body.accepted,
        corrected_category=body.corrected_category,
        comment=body.comment,
    )
    return {
        "id": feedback.id,
        "analysis_id": feedback.analysis_id,
        "analysis_type": feedback.analysis_type,
        "predicted_category": feedback.predicted_category,
        "accepted": feedback.accepted,
        "corrected_category": feedback.corrected_category,
        "comment": feedback.comment,
        "created_at": feedback.created_at,
        "updated_at": feedback.updated_at,
    }


@router.get("/ai-analysis/{analysis_id}")
async def get_ai_analysis(
    analysis_id: str,
    current_user: User = Depends(require_permissions("ai:analyze")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    record = await ai_assistance.get_analysis_record(db, current_user.id, analysis_id)
    return {
        "id": record.id,
        "analysis_type": record.analysis_type,
        "target_type": record.target_type,
        "target_id": record.target_id,
        "traceability_id": record.traceability_id,
        "engine": record.engine,
        "status": record.status,
        "output": record.output,
        "created_at": record.created_at,
    }


@router.get("/runs/{run_id}/defect-report")
@audit_log("read", "ui_defect_report", resource_id_param="run_id")
async def get_ui_defect_report(
    run_id: int,
    current_user: User = Depends(require_permissions("ui:read", "execution:read")),
    db: AsyncSession = Depends(get_db),
):
    """Generate a reproducible, redacted failure report from immutable execution records."""
    _ensure_enabled()
    run = await run_service.get_run(db, current_user.id, run_id)
    if run.status not in {"failed", "infra_error", "timed_out", "cancelled"}:
        raise BusinessException(
            "Defect report is available after a non-passing run finishes", code="REPORT_NOT_READY", status_code=409
        )
    execution = await db.get(AutomationExecution, run.automation_execution_id) if run.automation_execution_id else None
    steps = await run_service.list_step_results(db, current_user.id, run_id)
    artifacts = await run_service.list_artifacts(db, current_user.id, run_id)
    events = []
    if execution:
        events = list(
            (
                await db.scalars(
                    select(ExecutionEvent)
                    .where(ExecutionEvent.execution_id == execution.id)
                    .order_by(ExecutionEvent.sequence)
                )
            ).all()
        )
    environment_summary = None
    if run.environment_id is not None:
        environment = await db.get(AutoTestEnvironment, run.environment_id)
        if environment and environment.user_id == current_user.id:
            environment_summary = {
                "id": environment.id,
                "name": getattr(environment, "env_name", None) or getattr(environment, "name", None),
            }
    return {
        "run_id": run.id,
        "execution_id": execution.public_id if execution else None,
        "status": run.status,
        "execution_version": {"case_version_id": run.case_version_id, "suite_id": run.suite_id, "attempt": run.attempt},
        "environment": environment_summary,
        "reproduction": {
            "browser": run.browser or "chromium",
            "browser_version": run.browser_version,
            "desktop_version": run.desktop_version,
            "requires_login_state": bool(run.artifact_manifest and run.artifact_manifest.get("requires_login_state")),
        },
        "failed_steps": [
            UIStepResultOut.model_validate(step).model_dump() for step in steps if step.status in {"failed", "error"}
        ],
        "timeline": [
            {
                "sequence": event.sequence,
                "level": event.level,
                "type": event.event_type,
                "payload": event.payload_redacted or {},
                "created_at": event.created_at,
            }
            for event in events
        ],
        "artifacts": [
            {
                "id": artifact.id,
                "kind": artifact.type,
                "filename": artifact.filename,
                "artifact_manifest_id": artifact.artifact_manifest_id,
                "content_url": f"/api/auto-test/artifacts/{artifact.artifact_manifest_id}/content"
                if artifact.artifact_manifest_id
                else f"/api/ui-automation/runs/{run.id}/artifacts/{artifact.id}/content",
            }
            for artifact in artifacts
        ],
    }


async def _owned_shared_artifact(db: AsyncSession, user_id: int, artifact_manifest_id: int) -> ArtifactManifest:
    artifact = await db.scalar(
        select(ArtifactManifest)
        .join(AutomationExecution, ArtifactManifest.execution_id == AutomationExecution.id)
        .where(ArtifactManifest.id == artifact_manifest_id, AutomationExecution.user_id == user_id)
    )
    if artifact is None:
        raise HTTPException(status_code=404, detail="Artifact was not found")
    return artifact


@router.get("/artifacts/{artifact_manifest_id}/annotations")
@audit_log("read", "artifact_annotation", resource_id_param="artifact_manifest_id")
async def get_artifact_annotations(
    artifact_manifest_id: int,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    await _owned_shared_artifact(db, current_user.id, artifact_manifest_id)
    layer = await db.scalar(
        select(ArtifactAnnotation).where(
            ArtifactAnnotation.artifact_manifest_id == artifact_manifest_id,
            ArtifactAnnotation.user_id == current_user.id,
        )
    )
    return {"artifact_manifest_id": artifact_manifest_id, "annotations": layer.annotations if layer else []}


@router.put("/artifacts/{artifact_manifest_id}/annotations")
@audit_log("update", "artifact_annotation", resource_id_param="artifact_manifest_id")
async def save_artifact_annotations(
    artifact_manifest_id: int,
    body: dict = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    _ensure_enabled()
    await _owned_shared_artifact(db, current_user.id, artifact_manifest_id)
    annotations = body.get("annotations")
    if not isinstance(annotations, list) or len(annotations) > 500:
        raise HTTPException(status_code=422, detail="annotations must be a list containing at most 500 entries")
    if any(not isinstance(item, dict) for item in annotations):
        raise HTTPException(status_code=422, detail="each annotation must be an object")
    layer = await db.scalar(
        select(ArtifactAnnotation).where(
            ArtifactAnnotation.artifact_manifest_id == artifact_manifest_id,
            ArtifactAnnotation.user_id == current_user.id,
        )
    )
    if layer is None:
        layer = ArtifactAnnotation(
            artifact_manifest_id=artifact_manifest_id, user_id=current_user.id, annotations=annotations
        )
        db.add(layer)
    else:
        layer.annotations = annotations
    await db.commit()
    return {"artifact_manifest_id": artifact_manifest_id, "annotations": annotations}


@router.get("/health")
async def health():
    return {
        "status": "ok",
        "enabled": getattr(settings, "UI_AUTOMATION_ENABLED", False),
        "module": "ui-automation",
        "phase": "phase-1",
    }
