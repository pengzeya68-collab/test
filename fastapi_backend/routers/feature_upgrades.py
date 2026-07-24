"""Feature upgrade APIs: visual, trace, elements, healing, flaky, defects, shards, protocols."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.core.exceptions import BusinessException
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.deps.project_context import get_active_project_id_member
from fastapi_backend.models.models import User
from fastapi_backend.services.api_health_service import api_health_service
from fastapi_backend.services.codegen_service import codegen_service
from fastapi_backend.services.contract_testing_service import contract_testing_service
from fastapi_backend.services.defect_integration_service import defect_integration_service
from fastapi_backend.services.element_repository_service import element_repository_service
from fastapi_backend.services.flaky_detection_service import flaky_detection_service
from fastapi_backend.services.network_rule_service import network_rule_service
from fastapi_backend.services.protocol_executor_service import protocol_executor_service
from fastapi_backend.services.suite_sharding_service import suite_sharding_service
from fastapi_backend.services.test_management_service import test_management_service
from fastapi_backend.services.trace_viewer_service import trace_viewer_service
from fastapi_backend.services.visual_regression_service import visual_regression_service

router = APIRouter(prefix="/api/feature-upgrades", tags=["feature-upgrades"])

_IMAGE_MEDIA = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".gif": "image/gif",
}


def _serialize(obj: Any) -> Any:
    if obj is None:
        return None
    if isinstance(obj, list):
        return [_serialize(item) for item in obj]
    if hasattr(obj, "__table__"):
        data: dict[str, Any] = {}
        for column in obj.__table__.columns:
            value = getattr(obj, column.name)
            if hasattr(value, "isoformat"):
                value = value.isoformat()
            data[column.name] = value
        return data
    if hasattr(obj, "__dict__") and not isinstance(obj, dict):
        return {key: _serialize(value) for key, value in vars(obj).items() if not key.startswith("_")}
    return obj


def _safe_image_response(path_value: str | None, *, label: str) -> FileResponse:
    if not path_value:
        raise HTTPException(status_code=404, detail=f"{label} image missing")
    path = Path(path_value).resolve()
    if not path.is_file():
        raise HTTPException(status_code=404, detail=f"{label} image not found")
    # Restrict to known image extensions to avoid accidental binary dump of non-image paths.
    media = _IMAGE_MEDIA.get(path.suffix.lower())
    if media is None:
        raise HTTPException(status_code=400, detail=f"{label} is not a supported image type")
    return FileResponse(path, media_type=media, filename=path.name)


class PageCreateIn(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    url_pattern: Optional[str] = None
    parent_id: Optional[int] = None
    sort_order: int = 0


class ElementCreateIn(BaseModel):
    project_id: int
    page_id: int
    name: str
    locators: list[dict[str, Any]]
    description: Optional[str] = None
    frame_path: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    thumbnail_path: Optional[str] = None


class ElementUpdateIn(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    locators: Optional[list[dict[str, Any]]] = None
    frame_path: Optional[list[str]] = None
    tags: Optional[list[str]] = None
    thumbnail_path: Optional[str] = None
    is_deprecated: Optional[bool] = None


class BindStepElementIn(BaseModel):
    step_id: str
    element_id: int
    override_locators: Optional[list[dict[str, Any]]] = None


class HealIn(BaseModel):
    project_id: int
    original_locator: dict[str, Any] = Field(default_factory=dict)
    page_dom: str
    page_url: Optional[str] = None
    element_id: Optional[int] = None
    run_id: Optional[int] = None
    step_result_id: Optional[int] = None
    failure_reason: str = ""


class HealingReviewIn(BaseModel):
    action: str


class BaselineCreateIn(BaseModel):
    project_id: int
    ui_step_id: str
    image_path: str
    environment_id: Optional[int] = None
    browser_engine: str = "chromium"
    viewport_width: int = 1280
    viewport_height: int = 720
    device_pixel_ratio: float = 1.0
    captured_from_run_id: Optional[int] = None
    captured_from_step_result_id: Optional[int] = None


class CompareIn(BaseModel):
    project_id: int
    run_id: int
    actual_image_path: str
    ui_step_id: Optional[str] = None
    step_result_id: Optional[int] = None
    environment_id: Optional[int] = None
    browser_engine: str = "chromium"
    viewport_width: int = 1280
    viewport_height: int = 720
    threshold: Optional[float] = None


class VerdictIn(BaseModel):
    verdict: str
    comment: Optional[str] = None
    promote_baseline: bool = False


class TraceRegisterIn(BaseModel):
    project_id: int
    run_id: int
    file_path: str
    step_result_id: Optional[int] = None


class FlakyRecordIn(BaseModel):
    project_id: int
    case_type: str = "ui"
    case_id: int
    case_name: str
    status: str
    run_id: Optional[int] = None


class QuarantineIn(BaseModel):
    quarantined: bool


class TrackerUpsertIn(BaseModel):
    id: Optional[int] = None
    tracker_type: str
    base_url: str
    credentials_encrypted: Optional[str] = None
    project_key: Optional[str] = None
    custom_fields_mapping: Optional[dict[str, Any]] = None
    default_issue_type: Optional[str] = None
    default_priority: Optional[str] = None
    is_active: Optional[bool] = True


class DefectFromFailureIn(BaseModel):
    project_id: int
    step_result_id: Optional[int] = None
    run_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    severity: Optional[str] = None
    tracker_config_id: Optional[int] = None
    case_type: str = "ui"
    case_id: Optional[int] = None


class ShardCreateIn(BaseModel):
    suite_execution_id: int
    case_ids: list[int]
    suite_id: Optional[int] = None
    strategy: str = "balanced"
    online_agent_count: Optional[int] = None
    avg_durations: Optional[dict[int, float]] = None


class ShardProgressIn(BaseModel):
    completed_delta: int = 0
    passed_delta: int = 0
    failed_delta: int = 0
    completed: bool = False


class ProtocolExecuteIn(BaseModel):
    protocol: str
    config: dict[str, Any]
    variables: Optional[dict[str, Any]] = None


# ---------- Elements / Healing ----------


@router.get("/pages")
async def list_pages(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    pages = await element_repository_service.list_pages(db, project_id)
    return {"items": _serialize(pages)}


@router.post("/pages", status_code=201)
async def create_page(
    payload: PageCreateIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    page = await element_repository_service.create_page(
        db,
        project_id=payload.project_id,
        name=payload.name,
        user_id=current_user.id,
        description=payload.description,
        url_pattern=payload.url_pattern,
        parent_id=payload.parent_id,
        sort_order=payload.sort_order,
    )
    await db.commit()
    return _serialize(page)


@router.get("/elements")
async def list_elements(
    project_id: int = Query(...),
    page_id: Optional[int] = Query(None),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    items = await element_repository_service.list_elements(db, project_id=project_id, page_id=page_id)
    return {"items": _serialize(items)}


@router.post("/elements", status_code=201)
async def create_element(
    payload: ElementCreateIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        element = await element_repository_service.create_element(
            db,
            project_id=payload.project_id,
            page_id=payload.page_id,
            name=payload.name,
            locators=payload.locators,
            user_id=current_user.id,
            description=payload.description,
            frame_path=payload.frame_path,
            tags=payload.tags,
            thumbnail_path=payload.thumbnail_path,
        )
    except ValueError as exc:
        raise BusinessException(str(exc), code="INVALID_ELEMENT", status_code=400) from exc
    await db.commit()
    return _serialize(element)


@router.patch("/elements/{element_id}")
async def update_element(
    element_id: int,
    payload: ElementUpdateIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        element = await element_repository_service.update_element(
            db, element_id, payload.model_dump(exclude_unset=True)
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    return _serialize(element)


@router.post("/elements/bind-step")
async def bind_step_element(
    payload: BindStepElementIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    ref = await element_repository_service.bind_step_element(
        db,
        step_id=payload.step_id,
        element_id=payload.element_id,
        override_locators=payload.override_locators,
    )
    await db.commit()
    return _serialize(ref)


@router.post("/healing/heal")
async def heal_locator(
    payload: HealIn,
    current_user: User = Depends(require_permissions("ui:execute")),
    db: AsyncSession = Depends(get_db),
):
    result = await element_repository_service.heal(
        db,
        project_id=payload.project_id,
        original_locator=payload.original_locator,
        page_dom=payload.page_dom,
        page_url=payload.page_url,
        element_id=payload.element_id,
        run_id=payload.run_id,
        step_result_id=payload.step_result_id,
        failure_reason=payload.failure_reason,
    )
    await db.commit()
    return {
        "status": result.status,
        "confidence": result.confidence,
        "strategy_used": result.strategy_used,
        "healed_locator": result.healed_locator,
        "candidates": [{"locator": c.locator, "score": c.score, "reason": c.reason} for c in result.candidates],
    }


@router.post("/healing/{record_id}/review")
async def review_healing(
    record_id: int,
    payload: HealingReviewIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        record = await element_repository_service.review_healing(
            db, record_id, action=payload.action, user_id=current_user.id
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise BusinessException(str(exc), code="INVALID_ACTION", status_code=400) from exc
    await db.commit()
    return _serialize(record)


# ---------- Visual ----------


@router.get("/visual/baselines")
async def list_baselines(
    project_id: Optional[int] = Query(None),
    step_id: Optional[str] = Query(None),
    environment_id: Optional[int] = Query(None),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    items = await visual_regression_service.list_baselines(
        db, project_id=project_id, step_id=step_id, env_id=environment_id
    )
    return {"items": _serialize(items)}


@router.post("/visual/baselines", status_code=201)
async def create_baseline(
    payload: BaselineCreateIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        baseline = await visual_regression_service.create_baseline(
            db,
            project_id=payload.project_id,
            ui_step_id=payload.ui_step_id,
            image_path=payload.image_path,
            user_id=current_user.id,
            environment_id=payload.environment_id,
            browser_engine=payload.browser_engine,
            viewport_width=payload.viewport_width,
            viewport_height=payload.viewport_height,
            run_id=payload.captured_from_run_id,
            step_result_id=payload.captured_from_step_result_id,
        )
    except Exception as exc:
        raise BusinessException(str(exc), code="BASELINE_CREATE_FAILED", status_code=400) from exc
    await db.commit()
    return _serialize(baseline)


@router.post("/visual/compare")
async def compare_visual(
    payload: CompareIn,
    current_user: User = Depends(require_permissions("ui:execute")),
    db: AsyncSession = Depends(get_db),
):
    try:
        comparison = await visual_regression_service.compare_and_persist(
            db,
            project_id=payload.project_id,
            run_id=payload.run_id,
            actual_image_path=payload.actual_image_path,
            ui_step_id=payload.ui_step_id,
            step_result_id=payload.step_result_id,
            environment_id=payload.environment_id,
            browser_engine=payload.browser_engine,
            viewport_width=payload.viewport_width,
            viewport_height=payload.viewport_height,
            user_id=current_user.id,
        )
    except Exception as exc:
        raise BusinessException(str(exc), code="VISUAL_COMPARE_FAILED", status_code=400) from exc
    await db.commit()
    return _serialize(comparison)


@router.post("/visual/comparisons/{comparison_id}/verdict")
async def set_visual_verdict(
    comparison_id: int,
    payload: VerdictIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        comparison = await visual_regression_service.set_verdict(
            db,
            comparison_id,
            verdict=payload.verdict,
            user_id=current_user.id,
            comment=payload.comment,
            promote_baseline=payload.promote_baseline,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise BusinessException(str(exc), code="VERDICT_FAILED", status_code=400) from exc
    await db.commit()
    return _serialize(comparison)


# ---------- Trace ----------


@router.post("/traces/register", status_code=201)
async def register_trace(
    payload: TraceRegisterIn,
    current_user: User = Depends(require_permissions("ui:execute")),
    db: AsyncSession = Depends(get_db),
):
    try:
        session = await trace_viewer_service.register_trace(
            db,
            project_id=payload.project_id,
            run_id=payload.run_id,
            file_path=payload.file_path,
            step_result_id=payload.step_result_id,
        )
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    return _serialize(session)


@router.get("/traces/{trace_id}")
async def get_trace(
    trace_id: int,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    try:
        meta = await trace_viewer_service.ensure_parsed(db, trace_id)
        session = await trace_viewer_service.get_session(db, trace_id)
        await db.commit()
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    actions = []
    for action in meta.actions:
        item = dict(action)
        # Normalize fields used by the timeline UI.
        start = item.get("start_time")
        end = item.get("end_time")
        duration = item.get("duration_ms")
        if duration is None and isinstance(start, (int, float)) and isinstance(end, (int, float)):
            duration = max(0, int(end - start))
            item["duration_ms"] = duration
        item["title"] = item.get("title") or item.get("method") or item.get("api_name") or item.get("id")
        item["selector"] = item.get("selector")
        if not item["selector"]:
            params = item.get("params") or {}
            if isinstance(params, dict):
                item["selector"] = params.get("selector") or params.get("locator") or ""
        item["start_ms"] = item.get("start_ms")
        actions.append(item)

    # Build relative timeline offsets (ms from first action).
    starts = [float(a["start_time"]) for a in actions if isinstance(a.get("start_time"), (int, float))]
    origin = min(starts) if starts else 0.0
    for action in actions:
        start = action.get("start_time")
        if isinstance(start, (int, float)):
            action["start_ms"] = max(0, int(start - origin))
        else:
            action["start_ms"] = action.get("start_ms") or 0

    network = []
    for entry in meta.network:
        item = dict(entry)
        t = item.get("time")
        if isinstance(t, (int, float)) and starts:
            item["start_ms"] = max(0, int(float(t) - origin))
        else:
            item["start_ms"] = item.get("start_ms") or 0
        network.append(item)

    screenshots = []
    for idx, name in enumerate(meta.screenshots or []):
        if isinstance(name, dict):
            resource = name.get("path") or name.get("name") or name.get("resource")
        else:
            resource = str(name)
        screenshots.append(
            {
                "name": resource,
                "path": resource,
                "url": f"/api/feature-upgrades/traces/{trace_id}/resources/{quote(resource, safe='')}"
                if resource
                else None,
                "index": idx,
            }
        )

    return {
        "session": _serialize(session),
        "action_count": meta.action_count,
        "duration_ms": meta.duration_ms,
        "actions": actions,
        "network": network,
        "console": meta.console,
        "screenshots": screenshots,
        "browser_version": meta.browser_version,
        "parse_errors": meta.parse_errors,
        "timeline": {
            "origin_ms": origin,
            "duration_ms": meta.duration_ms or (max((a.get("start_ms") or 0) for a in actions) if actions else 0),
        },
    }


@router.get("/traces/{trace_id}/resources/{resource_name:path}")
async def get_trace_resource(
    trace_id: int,
    resource_name: str,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    try:
        content = await trace_viewer_service.get_resource_bytes(db, trace_id, resource_name)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise BusinessException(str(exc), code="TRACE_RESOURCE_FAILED", status_code=400) from exc

    suffix = Path(resource_name).suffix.lower()
    media = _IMAGE_MEDIA.get(suffix, "application/octet-stream")
    if suffix in {".html", ".htm"}:
        media = "text/html; charset=utf-8"
    elif suffix in {".json"}:
        media = "application/json"
    elif suffix in {".txt", ".log"}:
        media = "text/plain; charset=utf-8"
    return Response(content=content, media_type=media)


@router.get("/traces/{trace_id}/actions/{action_id}/snapshot")
async def get_trace_action_snapshot(
    trace_id: int,
    action_id: str,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    try:
        html = await trace_viewer_service.get_snapshot_html(db, trace_id, action_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not html:
        raise HTTPException(status_code=404, detail="snapshot not found")
    return {"action_id": action_id, "html": html}


@router.get("/traces/{trace_id}/actions/{action_id}/screenshot")
async def get_trace_action_screenshot(
    trace_id: int,
    action_id: str,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    try:
        content = await trace_viewer_service.get_screenshot(db, trace_id, action_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not content:
        raise HTTPException(status_code=404, detail="screenshot not found")
    return Response(content=content, media_type="image/png")


# ---------- Flaky ----------


@router.get("/flaky")
async def list_flaky(
    project_id: int = Query(...),
    classification: Optional[str] = Query(None),
    quarantined: Optional[bool] = Query(None),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    items = await flaky_detection_service.list_records(
        db, project_id=project_id, classification=classification, quarantined=quarantined
    )
    return {"items": _serialize(items)}


@router.post("/flaky/record")
async def record_flaky_result(
    payload: FlakyRecordIn,
    current_user: User = Depends(require_permissions("ui:execute")),
    db: AsyncSession = Depends(get_db),
):
    record = await flaky_detection_service.record_result(
        db,
        project_id=payload.project_id,
        case_type=payload.case_type,
        case_id=payload.case_id,
        case_name=payload.case_name,
        status=payload.status,
        run_id=payload.run_id,
    )
    await db.commit()
    return _serialize(record)


@router.post("/flaky/{record_id}/quarantine")
async def set_quarantine(
    record_id: int,
    payload: QuarantineIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        record = await flaky_detection_service.set_quarantine(
            db, record_id, quarantined=payload.quarantined, user_id=current_user.id
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    return _serialize(record)


# ---------- Defects ----------


@router.get("/defects/trackers")
async def list_trackers(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    items = await defect_integration_service.list_trackers(db, project_id)
    return {"items": _serialize(items)}


@router.post("/defects/trackers")
async def upsert_tracker(
    project_id: int = Query(...),
    payload: TrackerUpsertIn = Body(...),
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    tracker = await defect_integration_service.upsert_tracker(db, project_id, payload.model_dump(exclude_unset=True))
    await db.commit()
    return _serialize(tracker)


@router.get("/defects")
async def list_defects(
    project_id: int = Query(...),
    status: Optional[str] = Query(None),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    items = await defect_integration_service.list_defects(db, project_id, status=status)
    return {"items": _serialize(items)}


@router.post("/defects/from-failure", status_code=201)
async def create_defect_from_failure(
    payload: DefectFromFailureIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    record = await defect_integration_service.create_from_failure(
        db,
        project_id=payload.project_id,
        user_id=current_user.id,
        step_result_id=payload.step_result_id,
        run_id=payload.run_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        severity=payload.severity,
        tracker_config_id=payload.tracker_config_id,
        case_type=payload.case_type,
        case_id=payload.case_id,
    )
    await db.commit()
    return _serialize(record)


# ---------- Sharding ----------


@router.post("/shards", status_code=201)
async def create_shards(
    payload: ShardCreateIn,
    current_user: User = Depends(require_permissions("ui:execute")),
    db: AsyncSession = Depends(get_db),
    project_id: int = Depends(get_active_project_id_member),
):
    shards = await suite_sharding_service.create_shards(
        db,
        suite_execution_id=payload.suite_execution_id,
        case_ids=payload.case_ids,
        suite_id=payload.suite_id,
        strategy=payload.strategy,
        project_id=project_id,
        online_agent_count=payload.online_agent_count,
        avg_durations=payload.avg_durations,
    )
    await db.commit()
    return {"items": _serialize(shards)}


@router.get("/shards/progress/{suite_execution_id}")
async def get_shard_progress(
    suite_execution_id: int,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    return await suite_sharding_service.get_progress(db, suite_execution_id)


@router.post("/shards/{shard_id}/progress")
async def update_shard_progress(
    shard_id: int,
    payload: ShardProgressIn,
    current_user: User = Depends(require_permissions("ui:execute")),
    db: AsyncSession = Depends(get_db),
):
    try:
        shard = await suite_sharding_service.update_shard_progress(
            db,
            shard_id,
            completed_delta=payload.completed_delta,
            passed_delta=payload.passed_delta,
            failed_delta=payload.failed_delta,
            completed=payload.completed,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    return _serialize(shard)


@router.post("/shards/agent-death/{agent_id}")
async def handle_agent_death(
    agent_id: int,
    current_user: User = Depends(require_permissions("ui:execute")),
    db: AsyncSession = Depends(get_db),
):
    shards = await suite_sharding_service.handle_agent_death(db, agent_id)
    await db.commit()
    return {"reassigned": _serialize(shards)}


# ---------- Protocols ----------


class ProtoFileUpsertIn(BaseModel):
    project_id: int
    name: str
    content: str
    package_name: Optional[str] = None


def _parse_proto_services(content: str) -> list[dict[str, Any]]:
    """Lightweight .proto service/method extractor (no full protobuf compiler required)."""
    import re

    services: list[dict[str, Any]] = []
    service_blocks = re.finditer(
        r"service\s+([A-Za-z_][\w]*)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}",
        content,
        flags=re.MULTILINE,
    )
    for match in service_blocks:
        service_name = match.group(1)
        body = match.group(2) or ""
        methods = []
        for rpc in re.finditer(
            r"rpc\s+([A-Za-z_][\w]*)\s*\(\s*(stream\s+)?([A-Za-z_][\w\.]*)\s*\)\s*returns\s*\(\s*(stream\s+)?([A-Za-z_][\w\.]*)\s*\)",
            body,
        ):
            methods.append(
                {
                    "name": rpc.group(1),
                    "request_stream": bool(rpc.group(2)),
                    "request_type": rpc.group(3),
                    "response_stream": bool(rpc.group(4)),
                    "response_type": rpc.group(5),
                }
            )
        services.append({"name": service_name, "methods": methods})
    return services


@router.get("/protocols/protos")
async def list_proto_files(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi_backend.models.feature_upgrades import ProtoFile
    from sqlalchemy import select as sa_select

    items = list(
        (
            await db.scalars(
                sa_select(ProtoFile).where(ProtoFile.project_id == project_id).order_by(ProtoFile.id.desc())
            )
        ).all()
    )
    return {"items": _serialize(items)}


@router.post("/protocols/protos", status_code=201)
async def upsert_proto_file(
    payload: ProtoFileUpsertIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    import hashlib
    import os
    from datetime import datetime, timezone

    from fastapi_backend.models.feature_upgrades import ProtoFile
    from sqlalchemy import select as sa_select

    content = payload.content or ""
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    package_name = payload.package_name
    if not package_name:
        import re

        m = re.search(r"^\s*package\s+([A-Za-z_][\w\.]*)\s*;", content, flags=re.MULTILINE)
        package_name = m.group(1) if m else None
    services = _parse_proto_services(content)
    parse_error = None if services else ("no service blocks found" if "service " in content else None)

    artifact_root = Path(os.getenv("TESTMASTER_ARTIFACT_ROOT", "instance/artifacts"))
    target_dir = artifact_root / "protos" / str(payload.project_id)
    target_dir.mkdir(parents=True, exist_ok=True)
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in payload.name) or "service.proto"
    if not safe_name.endswith(".proto"):
        safe_name = f"{safe_name}.proto"
    file_path = target_dir / f"{content_hash[:12]}-{safe_name}"
    file_path.write_text(content, encoding="utf-8")

    existing = await db.scalar(
        sa_select(ProtoFile).where(ProtoFile.project_id == payload.project_id, ProtoFile.name == payload.name)
    )
    now = datetime.now(timezone.utc)
    if existing:
        existing.file_path = str(file_path)
        existing.content_hash = content_hash
        existing.package_name = package_name
        existing.services = services
        existing.parsed_at = now
        existing.parse_error = parse_error
        existing.version = int(existing.version or 1) + 1
        existing.updated_at = now
        item = existing
    else:
        item = ProtoFile(
            project_id=payload.project_id,
            name=payload.name,
            file_path=str(file_path),
            content_hash=content_hash,
            package_name=package_name,
            services=services,
            parsed_at=now,
            parse_error=parse_error,
            version=1,
            created_by=current_user.id,
        )
        db.add(item)
    await db.commit()
    await db.refresh(item)
    payload_out = _serialize(item)
    payload_out["content"] = content
    return payload_out


@router.get("/protocols/protos/{proto_id}")
async def get_proto_file(
    proto_id: int,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi_backend.models.feature_upgrades import ProtoFile

    item = await db.get(ProtoFile, proto_id)
    if item is None:
        raise HTTPException(status_code=404, detail="proto not found")
    data = _serialize(item)
    try:
        data["content"] = Path(item.file_path).read_text(encoding="utf-8")
    except Exception:
        data["content"] = ""
    return data


@router.delete("/protocols/protos/{proto_id}")
async def delete_proto_file(
    proto_id: int,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi_backend.models.feature_upgrades import ProtoFile

    item = await db.get(ProtoFile, proto_id)
    if item is None:
        raise HTTPException(status_code=404, detail="proto not found")
    path = Path(item.file_path)
    await db.delete(item)
    await db.commit()
    try:
        if path.is_file():
            path.unlink()
    except Exception:
        pass
    return {"ok": True, "id": proto_id}


@router.post("/protocols/execute")
async def execute_protocol(
    payload: ProtocolExecuteIn,
    current_user: User = Depends(require_permissions("autotest:execute")),
    db: AsyncSession = Depends(get_db),
):
    config = dict(payload.config or {})
    # Allow selecting a managed proto file by id.
    proto_file_id = config.get("proto_file_id") or config.get("grpc_proto_file_id")
    if proto_file_id and not (config.get("proto_path") or config.get("grpc_proto_path")):
        from fastapi_backend.models.feature_upgrades import ProtoFile

        proto = await db.get(ProtoFile, int(proto_file_id))
        if proto is None:
            raise HTTPException(status_code=404, detail="proto file not found")
        config["grpc_proto_path"] = proto.file_path
        config["proto_path"] = proto.file_path
    result = await protocol_executor_service.execute(payload.protocol, config, payload.variables)
    return {
        "status": result.status,
        "protocol": result.protocol,
        "duration_ms": result.duration_ms,
        "response": result.response,
        "responses": result.responses,
        "messages": result.messages,
        "events": result.events,
        "error": result.error,
        "meta": result.meta,
    }


# ---------- Healing list / visual extras ----------


@router.get("/healing")
async def list_healing_records(
    project_id: int = Query(...),
    status: Optional[str] = Query(None),
    element_id: Optional[int] = Query(None),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    items = await element_repository_service.list_healing_records(
        db, project_id=project_id, status=status, element_id=element_id
    )
    return {"items": _serialize(items)}


class MaskCreateIn(BaseModel):
    name: str
    x: float
    y: float
    width: float
    height: float
    shape: str = "rect"


class VisualConfigIn(BaseModel):
    default_threshold: Optional[float] = None
    antialiasing_tolerance: Optional[float] = None
    auto_approve_below: Optional[float] = None
    auto_reject_above: Optional[float] = None
    default_engine: Optional[str] = None
    capture_full_page: Optional[bool] = None


@router.post("/visual/baselines/{baseline_id}/masks", status_code=201)
async def add_visual_mask(
    baseline_id: int,
    payload: MaskCreateIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        mask = await visual_regression_service.add_mask(
            db,
            baseline_id=baseline_id,
            name=payload.name,
            x=payload.x,
            y=payload.y,
            width=payload.width,
            height=payload.height,
            user_id=current_user.id,
            shape=payload.shape,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    return _serialize(mask)


@router.get("/visual/baselines/{baseline_id}/masks")
async def list_visual_masks(
    baseline_id: int,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    return {"items": _serialize(await visual_regression_service.list_masks(db, baseline_id))}


@router.get("/visual/comparisons")
async def list_visual_comparisons(
    project_id: Optional[int] = Query(None),
    run_id: Optional[int] = Query(None),
    verdict: Optional[str] = Query(None),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    items = await visual_regression_service.list_comparisons(db, project_id=project_id, run_id=run_id, verdict=verdict)
    return {"items": _serialize(items)}


@router.get("/visual/comparisons/{comparison_id}")
async def get_visual_comparison(
    comparison_id: int,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await visual_regression_service.get_comparison(db, comparison_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    payload = _serialize(item)
    baseline_path = None
    if item.baseline_id:
        from fastapi_backend.models.feature_upgrades import VisualBaseline

        baseline = await db.get(VisualBaseline, item.baseline_id)
        if baseline is not None:
            baseline_path = baseline.image_path
            payload["baseline"] = _serialize(baseline)
    payload["images"] = {
        "baseline_url": f"/api/feature-upgrades/visual/comparisons/{comparison_id}/image/baseline"
        if baseline_path
        else None,
        "actual_url": f"/api/feature-upgrades/visual/comparisons/{comparison_id}/image/actual",
        "diff_url": f"/api/feature-upgrades/visual/comparisons/{comparison_id}/image/diff"
        if item.diff_image_path
        else None,
    }
    return payload


@router.get("/visual/comparisons/{comparison_id}/image/{kind}")
async def get_visual_comparison_image(
    comparison_id: int,
    kind: str,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    if kind not in {"baseline", "actual", "diff"}:
        raise HTTPException(status_code=400, detail="kind must be baseline|actual|diff")
    try:
        item = await visual_regression_service.get_comparison(db, comparison_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if kind == "actual":
        return _safe_image_response(item.actual_image_path, label="actual")
    if kind == "diff":
        return _safe_image_response(item.diff_image_path, label="diff")

    if not item.baseline_id:
        raise HTTPException(status_code=404, detail="baseline not linked")
    from fastapi_backend.models.feature_upgrades import VisualBaseline

    baseline = await db.get(VisualBaseline, item.baseline_id)
    if baseline is None:
        raise HTTPException(status_code=404, detail="baseline not found")
    return _safe_image_response(baseline.image_path, label="baseline")


@router.get("/visual/baselines/{baseline_id}/image")
async def get_visual_baseline_image(
    baseline_id: int,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi_backend.models.feature_upgrades import VisualBaseline

    baseline = await db.get(VisualBaseline, baseline_id)
    if baseline is None:
        raise HTTPException(status_code=404, detail="baseline not found")
    return _safe_image_response(baseline.image_path, label="baseline")


@router.get("/visual/config")
async def get_visual_config(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    config = await visual_regression_service.get_or_create_config(db, project_id)
    await db.commit()
    return _serialize(config)


@router.put("/visual/config")
async def update_visual_config(
    project_id: int = Query(...),
    payload: VisualConfigIn = Body(...),
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    config = await visual_regression_service.update_config(db, project_id, payload.model_dump(exclude_unset=True))
    await db.commit()
    return _serialize(config)


@router.get("/visual/stats")
async def visual_stats(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    return await visual_regression_service.stats(db, project_id)


@router.get("/traces")
async def list_traces(
    project_id: int = Query(...),
    run_id: Optional[int] = Query(None),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi_backend.models.feature_upgrades import TraceSession
    from sqlalchemy import select as sa_select

    stmt = sa_select(TraceSession).where(TraceSession.project_id == project_id).order_by(TraceSession.id.desc())
    if run_id is not None:
        stmt = stmt.where(TraceSession.run_id == run_id)
    items = list((await db.scalars(stmt.limit(100))).all())
    return {"items": _serialize(items)}


# ---------- Network rules ----------


class NetworkRuleIn(BaseModel):
    name: str
    url_pattern: str
    description: Optional[str] = None
    pattern_type: str = "glob"
    method_filter: Optional[str] = None
    resource_type: Optional[str] = None
    action: str = "fulfill"
    fulfill_status: Optional[int] = None
    fulfill_headers: Optional[dict[str, Any]] = None
    fulfill_body: Optional[str] = None
    fulfill_content_type: Optional[str] = None
    modify_headers: Optional[dict[str, Any]] = None
    delay_ms: Optional[int] = None
    abort_reason: Optional[str] = None
    is_active: bool = True


class NetworkAssignIn(BaseModel):
    rule_id: int
    target_type: str
    target_id: int
    priority: int = 0


@router.get("/network/rules")
async def list_network_rules(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    return {"items": _serialize(await network_rule_service.list_rules(db, project_id))}


@router.post("/network/rules", status_code=201)
async def create_network_rule(
    project_id: int = Query(...),
    payload: NetworkRuleIn = Body(...),
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    rule = await network_rule_service.create_rule(
        db, project_id=project_id, user_id=current_user.id, payload=payload.model_dump()
    )
    await db.commit()
    return _serialize(rule)


@router.patch("/network/rules/{rule_id}")
async def update_network_rule(
    rule_id: int,
    payload: NetworkRuleIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        rule = await network_rule_service.update_rule(db, rule_id, payload.model_dump(exclude_unset=True))
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    return _serialize(rule)


@router.delete("/network/rules/{rule_id}")
async def delete_network_rule(
    rule_id: int,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        await network_rule_service.delete_rule(db, rule_id)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    return {"ok": True}


@router.post("/network/rules/assign")
async def assign_network_rule(
    payload: NetworkAssignIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    item = await network_rule_service.assign_rule(
        db,
        rule_id=payload.rule_id,
        target_type=payload.target_type,
        target_id=payload.target_id,
        priority=payload.priority,
    )
    await db.commit()
    return _serialize(item)


@router.get("/network/rules/for-target")
async def network_rules_for_target(
    project_id: int = Query(...),
    target_type: str = Query(...),
    target_id: int = Query(...),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    rules = await network_rule_service.rules_for_target(
        db, project_id=project_id, target_type=target_type, target_id=target_id
    )
    return {"items": _serialize(rules), "agent_payload": network_rule_service.to_agent_payload(rules)}


# ---------- Contract / Health / Codegen ----------


class SnapshotIn(BaseModel):
    project_id: int
    spec_content: str
    source_url: Optional[str] = None
    source_type: str = "upload"
    group_id: Optional[int] = None


class ContractRuleIn(BaseModel):
    id: Optional[int] = None
    case_id: int
    snapshot_id: int
    endpoint_path: str
    method: str
    validate_request: bool = True
    validate_response: bool = True
    strict_mode: bool = False
    is_active: bool = True


class ContractValidateIn(BaseModel):
    project_id: int
    case_id: int
    method: str
    path: str
    status_code: int = 200
    response_body: Optional[Any] = None


class HealthMonitorIn(BaseModel):
    name: str
    case_id: int
    environment_id: int
    interval_seconds: int = 300
    timeout_ms: int = 10000
    expected_status: int = 200
    max_response_time_ms: Optional[int] = None
    is_active: bool = True


class HealthCheckIn(BaseModel):
    url: Optional[str] = None
    method: str = "GET"
    headers: Optional[dict[str, str]] = None
    body: Optional[Any] = None


class CodegenIn(BaseModel):
    snapshot_id: int
    language: str = "python"
    base_url: str = "https://api.example.com"
    class_name: str = "ApiClient"


@router.get("/contracts/snapshots")
async def list_contract_snapshots(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("autotest:read")),
    db: AsyncSession = Depends(get_db),
):
    return {"items": _serialize(await contract_testing_service.list_snapshots(db, project_id))}


@router.post("/contracts/snapshots", status_code=201)
async def create_contract_snapshot(
    payload: SnapshotIn,
    current_user: User = Depends(require_permissions("autotest:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await contract_testing_service.create_snapshot(
            db,
            project_id=payload.project_id,
            spec_content=payload.spec_content,
            source_url=payload.source_url,
            source_type=payload.source_type,
            group_id=payload.group_id,
        )
    except ValueError as exc:
        raise BusinessException(str(exc), code="INVALID_SPEC", status_code=400) from exc
    await db.commit()
    return _serialize(item)


@router.get("/contracts/changes")
async def list_schema_changes(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("autotest:read")),
    db: AsyncSession = Depends(get_db),
):
    return {"items": _serialize(await contract_testing_service.list_changes(db, project_id))}


@router.get("/contracts/rules")
async def list_contract_rules(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("autotest:read")),
    db: AsyncSession = Depends(get_db),
):
    return {"items": _serialize(await contract_testing_service.list_rules(db, project_id))}


@router.post("/contracts/rules")
async def upsert_contract_rule(
    project_id: int = Query(...),
    payload: ContractRuleIn = Body(...),
    current_user: User = Depends(require_permissions("autotest:write")),
    db: AsyncSession = Depends(get_db),
):
    rule = await contract_testing_service.upsert_rule(db, project_id, payload.model_dump(exclude_unset=True))
    await db.commit()
    return _serialize(rule)


@router.post("/contracts/validate")
async def validate_contract_response(
    payload: ContractValidateIn,
    current_user: User = Depends(require_permissions("autotest:execute")),
    db: AsyncSession = Depends(get_db),
):
    return await contract_testing_service.validate_response(
        db,
        project_id=payload.project_id,
        case_id=payload.case_id,
        method=payload.method,
        path=payload.path,
        status_code=payload.status_code,
        response_body=payload.response_body,
    )


@router.get("/health/monitors")
async def list_health_monitors(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("autotest:read")),
    db: AsyncSession = Depends(get_db),
):
    return {"items": _serialize(await api_health_service.list_monitors(db, project_id))}


@router.post("/health/monitors", status_code=201)
async def create_health_monitor(
    project_id: int = Query(...),
    payload: HealthMonitorIn = Body(...),
    current_user: User = Depends(require_permissions("autotest:write")),
    db: AsyncSession = Depends(get_db),
):
    item = await api_health_service.create_monitor(db, project_id, payload.model_dump())
    await db.commit()
    return _serialize(item)


@router.post("/health/monitors/{monitor_id}/check")
async def run_health_check(
    monitor_id: int,
    payload: Optional[HealthCheckIn] = Body(default=None),
    current_user: User = Depends(require_permissions("autotest:execute")),
    db: AsyncSession = Depends(get_db),
):
    check = payload or HealthCheckIn()
    try:
        result = await api_health_service.run_check(
            db,
            monitor_id,
            url=check.url,
            method=check.method,
            headers=check.headers,
            body=check.body,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    return _serialize(result)


@router.get("/health/monitors/{monitor_id}/results")
async def list_health_results(
    monitor_id: int,
    current_user: User = Depends(require_permissions("autotest:read")),
    db: AsyncSession = Depends(get_db),
):
    return {"items": _serialize(await api_health_service.list_results(db, monitor_id))}


@router.post("/codegen")
async def generate_client_code(
    payload: CodegenIn,
    current_user: User = Depends(require_permissions("autotest:read")),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await codegen_service.generate_from_snapshot(
            db,
            snapshot_id=payload.snapshot_id,
            language=payload.language,
            base_url=payload.base_url,
            class_name=payload.class_name,
        )
    except Exception as exc:
        raise BusinessException(str(exc), code="CODEGEN_FAILED", status_code=400) from exc


# ---------- Flow / Review / Requirements / Reports ----------


class FlowSaveIn(BaseModel):
    scenario_id: int
    nodes: list[dict[str, Any]] = Field(default_factory=list)
    edges: list[dict[str, Any]] = Field(default_factory=list)
    viewport: Optional[dict[str, Any]] = None


class ReviewCreateIn(BaseModel):
    project_id: int
    case_type: str = "ui"
    case_id: int
    case_version: Optional[int] = None
    required_approvals: int = 1


class ReviewActionIn(BaseModel):
    action: str
    comment: Optional[str] = None


class ReviewCommentIn(BaseModel):
    content: str
    step_id: Optional[str] = None


class RequirementIn(BaseModel):
    title: str
    description: Optional[str] = None
    external_id: Optional[str] = None
    external_url: Optional[str] = None
    priority: Optional[str] = None
    status: str = "open"
    sprint: Optional[str] = None


class RequirementLinkIn(BaseModel):
    requirement_id: int
    case_type: str = "ui"
    case_id: int
    coverage_type: str = "functional"


class ReportTemplateIn(BaseModel):
    id: Optional[int] = None
    name: str = "Default"
    logo_path: Optional[str] = None
    primary_color: str = "#409EFF"
    company_name: Optional[str] = None
    footer_text: Optional[str] = None
    sections: Optional[list[str]] = None
    custom_fields: Optional[dict[str, Any]] = None
    is_default: bool = False


class ReportRenderIn(BaseModel):
    template_id: int
    context: dict[str, Any] = Field(default_factory=dict)


@router.get("/flow/{scenario_id}")
async def get_flow_graph(
    scenario_id: int,
    current_user: User = Depends(require_permissions("autotest:read")),
    db: AsyncSession = Depends(get_db),
):
    graph = await test_management_service.get_flow(db, scenario_id)
    return _serialize(graph) or {"scenario_id": scenario_id, "nodes": [], "edges": [], "viewport": None}


@router.put("/flow/{scenario_id}")
async def save_flow_graph(
    scenario_id: int,
    payload: FlowSaveIn,
    current_user: User = Depends(require_permissions("autotest:write")),
    db: AsyncSession = Depends(get_db),
):
    graph = await test_management_service.save_flow(
        db,
        scenario_id=scenario_id,
        nodes=payload.nodes,
        edges=payload.edges,
        viewport=payload.viewport,
    )
    await db.commit()
    return _serialize(graph)


@router.get("/reviews")
async def list_reviews(
    project_id: int = Query(...),
    state: Optional[str] = Query(None),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    return {"items": _serialize(await test_management_service.list_reviews(db, project_id, state=state))}


@router.post("/reviews", status_code=201)
async def create_review(
    payload: ReviewCreateIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    item = await test_management_service.create_review(
        db,
        project_id=payload.project_id,
        case_type=payload.case_type,
        case_id=payload.case_id,
        user_id=current_user.id,
        case_version=payload.case_version,
        required_approvals=payload.required_approvals,
    )
    await db.commit()
    return _serialize(item)


@router.post("/reviews/{review_id}/actions")
async def review_action(
    review_id: int,
    payload: ReviewActionIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await test_management_service.review_action(
            db, review_id=review_id, user_id=current_user.id, action=payload.action, comment=payload.comment
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise BusinessException(str(exc), code="INVALID_REVIEW_ACTION", status_code=400) from exc
    await db.commit()
    return _serialize(item)


@router.post("/reviews/{review_id}/comments", status_code=201)
async def add_review_comment(
    review_id: int,
    payload: ReviewCommentIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    try:
        item = await test_management_service.add_comment(
            db, review_id=review_id, user_id=current_user.id, content=payload.content, step_id=payload.step_id
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    await db.commit()
    return _serialize(item)


@router.get("/reviews/{review_id}/comments")
async def list_review_comments(
    review_id: int,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    return {"items": _serialize(await test_management_service.list_comments(db, review_id))}


@router.get("/requirements")
async def list_requirements(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    return {"items": _serialize(await test_management_service.list_requirements(db, project_id))}


@router.post("/requirements", status_code=201)
async def create_requirement(
    project_id: int = Query(...),
    payload: RequirementIn = Body(...),
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    item = await test_management_service.create_requirement(db, project_id, payload.model_dump())
    await db.commit()
    return _serialize(item)


@router.post("/requirements/link")
async def link_requirement_case(
    payload: RequirementLinkIn,
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    item = await test_management_service.link_case(
        db,
        requirement_id=payload.requirement_id,
        case_type=payload.case_type,
        case_id=payload.case_id,
        coverage_type=payload.coverage_type,
    )
    await db.commit()
    return _serialize(item)


@router.get("/requirements/coverage")
async def requirement_coverage(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    return await test_management_service.coverage_matrix(db, project_id)


@router.get("/reports/templates")
async def list_report_templates(
    project_id: int = Query(...),
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    return {"items": _serialize(await test_management_service.list_templates(db, project_id))}


@router.post("/reports/templates")
async def upsert_report_template(
    project_id: int = Query(...),
    payload: ReportTemplateIn = Body(...),
    current_user: User = Depends(require_permissions("ui:write")),
    db: AsyncSession = Depends(get_db),
):
    item = await test_management_service.upsert_template(db, project_id, payload.model_dump(exclude_unset=True))
    await db.commit()
    return _serialize(item)


@router.post("/reports/render")
async def render_report(
    payload: ReportRenderIn,
    current_user: User = Depends(require_permissions("ui:read")),
    db: AsyncSession = Depends(get_db),
):
    from fastapi_backend.models.feature_upgrades import ReportTemplate

    template = await db.get(ReportTemplate, payload.template_id)
    if template is None:
        raise HTTPException(status_code=404, detail="template not found")
    html = test_management_service.render_report_html(template, payload.context)
    return {"html": html, "template_id": template.id}
