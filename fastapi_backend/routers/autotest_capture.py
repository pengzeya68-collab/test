"""Safe browser traffic capture sessions and conversion to API test assets."""

from __future__ import annotations

import json
import re
from fnmatch import fnmatch
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlsplit

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.models.autotest import (
    AutoTestCase,
    AutoTestGroup,
    AutoTestScenario,
    AutoTestScenarioStep,
    CapturedExchange,
    CaptureSession,
    ImportJob,
)
from fastapi_backend.models.models import User
from fastapi_backend.services.capture_import import (
    CaptureImportError,
    MAX_CAPTURE_BATCH,
    MAX_CAPTURE_EXCHANGES,
    candidate_from_exchange,
    normalize_captured_exchange,
    redact_capture_source_url,
)

router = APIRouter(prefix="/api/auto-test/import/captures", tags=["Import Center"])
_VARIABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,99}$")
_HOST_NAME = re.compile(r"^[A-Za-z0-9.*-]{1,253}$")
_ASSERTION_OPERATORS = {"equals", "not_equals", "contains", "json_exists", "gte", "lte", "matches"}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _session_or_404(db: AsyncSession, session_id: str, user_id: int) -> CaptureSession:
    capture = await db.scalar(
        select(CaptureSession).where(CaptureSession.id == session_id, CaptureSession.user_id == user_id)
    )
    if capture is None:
        raise HTTPException(status_code=404, detail="capture session not found")
    return capture


def _capture_payload(capture: CaptureSession, exchanges: list[CapturedExchange]) -> dict[str, Any]:
    return {
        "id": capture.id,
        "origin": capture.origin,
        "status": capture.status,
        "policy_version": capture.policy_version,
        "source_url": capture.source_url,
        "capture_config": capture.capture_config or {},
        "failure_reason": capture.failure_reason,
        "started_at": capture.started_at,
        "ended_at": capture.ended_at,
        "total": len(exchanges),
        "candidates": [candidate_from_exchange(exchange) for exchange in exchanges],
    }


def _normalize_capture_config(value: Any) -> dict[str, list[str]]:
    if value is None:
        return {"domain_allowlist": [], "path_exclude": []}
    if not isinstance(value, dict):
        raise HTTPException(status_code=422, detail="capture_config must be an object")
    result: dict[str, list[str]] = {}
    for name, limit in (("domain_allowlist", 50), ("path_exclude", 100)):
        raw_values = value.get(name, [])
        if not isinstance(raw_values, list) or len(raw_values) > limit:
            raise HTTPException(status_code=422, detail=f"{name} is invalid")
        values = [str(item).strip().lower() for item in raw_values if str(item).strip()]
        if any(len(item) > 253 for item in values):
            raise HTTPException(status_code=422, detail=f"{name} contains an overlong value")
        if name == "domain_allowlist" and any(not _HOST_NAME.fullmatch(item) for item in values):
            raise HTTPException(status_code=422, detail="domain_allowlist contains an invalid host pattern")
        result[name] = list(dict.fromkeys(values))
    return result


def _is_exchange_allowed(config: dict[str, Any] | None, raw_exchange: Any) -> bool:
    if not isinstance(raw_exchange, dict):
        return False
    parsed = urlsplit(str(raw_exchange.get("url") or ""))
    host = (parsed.hostname or "").lower()
    path = parsed.path or "/"
    rules = config or {}
    allowlist = rules.get("domain_allowlist") or []
    excluded = rules.get("path_exclude") or []
    if allowlist and not any(fnmatch(host, pattern) for pattern in allowlist):
        return False
    return not any(fnmatch(path, pattern) for pattern in excluded)


def _replace_target(candidate: dict[str, Any], target: dict[str, Any], variable_name: str) -> None:
    location = str(target.get("location") or "").strip()
    exchange_id = int(target.get("exchange_id") or 0)
    if exchange_id != candidate["id"] or not location:
        return
    template = str(target.get("template") or f"{{{{{variable_name}}}}}")[:1000]
    root, _, suffix = location.partition(".")
    if root not in {"headers", "params", "payload"} or not suffix:
        raise HTTPException(status_code=422, detail="variable target location is invalid")
    target_value = candidate.get(root)
    path = suffix.split(".")
    if any(not token or len(token) > 200 for token in path):
        raise HTTPException(status_code=422, detail="variable target path is invalid")
    if root in {"headers", "params"}:
        if len(path) != 1:
            raise HTTPException(status_code=422, detail="headers and params support one target key")
        if not isinstance(target_value, dict):
            candidate[root] = target_value = {}
        target_value[path[0]] = template
        return
    if not isinstance(target_value, dict):
        raise HTTPException(status_code=422, detail="payload target requires an object payload")
    current = target_value
    for key in path[:-1]:
        next_value = current.get(key)
        if not isinstance(next_value, dict):
            current[key] = next_value = {}
        current = next_value
    current[path[-1]] = template


def _apply_variable_mappings(candidates: list[dict[str, Any]], mappings: Any) -> None:
    if mappings is None:
        return
    if not isinstance(mappings, list) or len(mappings) > 100:
        raise HTTPException(status_code=422, detail="variable_mappings is invalid")
    by_exchange_id = {candidate["id"]: candidate for candidate in candidates}
    candidate_order = {candidate["id"]: index for index, candidate in enumerate(candidates)}
    known_names: set[str] = set()
    for mapping in mappings:
        if not isinstance(mapping, dict):
            raise HTTPException(status_code=422, detail="variable mapping must be an object")
        source_exchange_id = int(mapping.get("source_exchange_id") or 0)
        variable_name = str(mapping.get("variable_name") or "").strip()
        expression = str(mapping.get("json_path") or "").strip()
        if source_exchange_id not in by_exchange_id or not _VARIABLE_NAME.fullmatch(variable_name):
            raise HTTPException(status_code=422, detail="variable source or name is invalid")
        if not expression.startswith("$") or len(expression) > 500:
            raise HTTPException(status_code=422, detail="json_path is invalid")
        if variable_name in known_names:
            raise HTTPException(status_code=422, detail="variable names must be unique")
        known_names.add(variable_name)
        source = by_exchange_id[source_exchange_id]
        source.setdefault("extractors", []).append(
            {
                "variableName": variable_name,
                "extractorType": "jsonpath",
                "expression": expression,
                "defaultValue": "",
            }
        )
        targets = mapping.get("targets") or []
        if not isinstance(targets, list) or not targets:
            raise HTTPException(status_code=422, detail="each variable mapping needs at least one confirmed target")
        for target in targets:
            if not isinstance(target, dict):
                raise HTTPException(status_code=422, detail="variable target must be an object")
            candidate = by_exchange_id.get(int(target.get("exchange_id") or 0))
            if candidate is None:
                raise HTTPException(status_code=422, detail="variable target exchange is invalid")
            if candidate_order[source_exchange_id] >= candidate_order[candidate["id"]]:
                raise HTTPException(status_code=422, detail="a variable source must occur before its target request")
            _replace_target(candidate, target, variable_name)


def _apply_candidate_overrides(candidates: list[dict[str, Any]], overrides: Any) -> None:
    if overrides is None:
        return
    if not isinstance(overrides, list) or len(overrides) > len(candidates):
        raise HTTPException(status_code=422, detail="candidate_overrides is invalid")
    by_id = {candidate["id"]: candidate for candidate in candidates}
    for override in overrides:
        if not isinstance(override, dict):
            raise HTTPException(status_code=422, detail="candidate override must be an object")
        candidate = by_id.get(int(override.get("exchange_id") or 0))
        assertions = override.get("assert_rules")
        if (
            candidate is None
            or not isinstance(assertions, list)
            or len(assertions) > 50
            or any(not isinstance(item, dict) for item in assertions)
        ):
            raise HTTPException(status_code=422, detail="candidate assertion override is invalid")
        for assertion in assertions:
            field = str(assertion.get("field") or "").strip()
            operator = str(assertion.get("operator") or "equals").strip()
            expression = str(assertion.get("expression") or "").strip()
            if field not in {"status_code", "json_body", "json_schema", "response_time"}:
                raise HTTPException(status_code=422, detail="candidate assertion field is invalid")
            if operator not in _ASSERTION_OPERATORS:
                raise HTTPException(status_code=422, detail="candidate assertion operator is invalid")
            if field == "json_schema" and operator != "matches":
                raise HTTPException(status_code=422, detail="JSON Schema assertions must use matches")
            if field != "json_schema" and operator == "matches":
                raise HTTPException(status_code=422, detail="matches is only supported for JSON Schema assertions")
            if field == "json_body" and (not expression.startswith("$") or len(expression) > 500):
                raise HTTPException(status_code=422, detail="JSONPath assertion expression is invalid")
            try:
                encoded_size = len(json.dumps(assertion.get("expected"), ensure_ascii=False).encode("utf-8"))
            except (TypeError, ValueError) as exc:
                raise HTTPException(status_code=422, detail="candidate assertion expected value is invalid") from exc
            if encoded_size > 64 * 1024:
                raise HTTPException(status_code=422, detail="candidate assertion expected value is too large")
        candidate["assert_rules"] = assertions


def _case_matches_candidate(case: AutoTestCase, candidate: dict[str, Any]) -> bool:
    return (
        case.method == candidate["method"]
        and case.url == candidate["url"]
        and (case.headers or {}) == (candidate.get("headers") or {})
        and (case.params or {}) == (candidate.get("params") or {})
        and (case.payload or None) == (candidate.get("payload") or None)
        and (case.body_type or "none") == candidate.get("body_type", "none")
    )


def _apply_capture_candidate_to_case(
    case: AutoTestCase,
    candidate: dict[str, Any],
    target_group_id: int | None,
) -> None:
    """Apply only fields the redacted capture can authoritatively provide.

    Capture conversion must not erase hand-authored scripts, request policies, or
    version metadata that cannot be reconstructed from a browser network event.
    """
    if target_group_id is not None:
        case.group_id = target_group_id
    case.name = candidate["name"]
    case.headers = candidate["headers"] or None
    case.params = candidate["params"] or None
    case.body_type = candidate["body_type"]
    case.content_type = candidate["content_type"]
    case.payload = candidate["payload"]
    case.assert_rules = candidate["assert_rules"] or None
    case.extractors = candidate.get("extractors") or None
    case.description = (
        "Updated from a redacted browser capture. Confirm variable mappings and "
        "run a preview before using it in regression."
    )


@router.post("", status_code=status.HTTP_201_CREATED)
@audit_log("create", "capture_session")
async def create_capture_session(
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("capture:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    origin = str(body.get("origin") or "desktop_browser").strip().lower()
    if origin not in {"desktop_browser", "har_import"}:
        raise HTTPException(status_code=422, detail="capture origin is invalid")
    raw_source_url = str(body.get("source_url") or "").strip()
    if len(raw_source_url) > 4000:
        raise HTTPException(status_code=422, detail="source_url is too long")
    source_url = redact_capture_source_url(raw_source_url)
    capture = CaptureSession(
        user_id=current_user.id,
        origin=origin,
        source_url=source_url,
        capture_config=_normalize_capture_config(body.get("capture_config")),
        policy_version="v1",
    )
    db.add(capture)
    await db.commit()
    await db.refresh(capture)
    return {
        "id": capture.id,
        "status": capture.status,
        "policy_version": capture.policy_version,
        "capture_config": capture.capture_config,
    }


@router.get("")
async def list_capture_sessions(
    limit: int = 50,
    current_user: User = Depends(require_permissions("capture:export")),
    db: AsyncSession = Depends(get_autotest_db),
):
    captures = list(
        (
            await db.scalars(
                select(CaptureSession)
                .where(CaptureSession.user_id == current_user.id)
                .order_by(CaptureSession.created_at.desc())
                .limit(min(max(limit, 1), 100))
            )
        ).all()
    )
    return {
        "captures": [
            {
                "id": capture.id,
                "origin": capture.origin,
                "status": capture.status,
                "source_url": capture.source_url,
                "capture_config": capture.capture_config or {},
                "failure_reason": capture.failure_reason,
                "started_at": capture.started_at,
                "ended_at": capture.ended_at,
            }
            for capture in captures
        ]
    }


@router.post("/{session_id}/exchanges")
async def append_capture_exchanges(
    session_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("capture:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    capture = await _session_or_404(db, session_id, current_user.id)
    if capture.status == "paused":
        raise HTTPException(status_code=409, detail="capture session is paused")
    if capture.status != "capturing":
        raise HTTPException(status_code=409, detail="capture session is not accepting exchanges")
    values = body.get("exchanges")
    if not isinstance(values, list) or not values or len(values) > MAX_CAPTURE_BATCH:
        raise HTTPException(status_code=422, detail=f"exchanges must contain 1 to {MAX_CAPTURE_BATCH} records")
    try:
        if len(json.dumps(values, ensure_ascii=True, default=str).encode("utf-8")) > MAX_CAPTURE_BATCH * 1024 * 1024:
            raise HTTPException(status_code=413, detail="capture batch is too large")
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="capture batch is invalid") from exc

    count = (
        await db.scalar(
            select(func.count()).select_from(CapturedExchange).where(CapturedExchange.session_id == capture.id)
        )
        or 0
    )
    if count >= MAX_CAPTURE_EXCHANGES:
        raise HTTPException(status_code=409, detail="capture session reached its exchange limit")
    existing_fingerprints = set(
        (await db.scalars(select(CapturedExchange.fingerprint).where(CapturedExchange.session_id == capture.id))).all()
    )
    accepted: list[CapturedExchange] = []
    errors: list[dict[str, Any]] = []
    for index, raw_exchange in enumerate(values):
        if count + len(accepted) >= MAX_CAPTURE_EXCHANGES:
            errors.append({"index": index, "error": "capture session reached its exchange limit"})
            continue
        try:
            if not _is_exchange_allowed(capture.capture_config, raw_exchange):
                errors.append({"index": index, "error": "exchange excluded by capture policy"})
                continue
            normalized = normalize_captured_exchange(raw_exchange)
        except CaptureImportError as exc:
            errors.append({"index": index, "error": str(exc)})
            continue
        if normalized["fingerprint"] in existing_fingerprints:
            continue
        existing_fingerprints.add(normalized["fingerprint"])
        exchange = CapturedExchange(
            session_id=capture.id,
            sequence=count + len(accepted) + 1,
            method=normalized["method"],
            url=normalized["url"],
            request_redacted={
                "headers": normalized["headers"],
                "params": normalized["params"],
                "body_type": normalized["body_type"],
                "content_type": normalized["content_type"],
                "payload": normalized["payload"],
                "assert_rules": normalized["assert_rules"],
            },
            response_redacted=normalized["response"],
            fingerprint=normalized["fingerprint"],
            page_url=normalized["page_url"],
            resource_type=normalized["resource_type"],
            timing_ms=normalized["timing_ms"],
            failure_reason=normalized.get("failure_reason"),
        )
        db.add(exchange)
        accepted.append(exchange)
    await db.commit()
    for exchange in accepted:
        await db.refresh(exchange)
    return {
        "accepted": len(accepted),
        "skipped_duplicates": len(values) - len(accepted) - len(errors),
        "errors": errors,
        "exchange_ids": [exchange.id for exchange in accepted],
    }


@router.post("/{session_id}/complete")
@audit_log("complete", "capture_session", resource_id_param="session_id")
async def complete_capture_session(
    session_id: str,
    current_user: User = Depends(require_permissions("capture:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    capture = await _session_or_404(db, session_id, current_user.id)
    if capture.status == "completed":
        return {"id": capture.id, "status": capture.status}
    if capture.status != "capturing":
        raise HTTPException(status_code=409, detail="capture session cannot be completed")
    capture.status = "completed"
    capture.ended_at = _utcnow()
    await db.commit()
    return {"id": capture.id, "status": capture.status}


@router.post("/{session_id}/pause")
@audit_log("pause", "capture_session", resource_id_param="session_id")
async def pause_capture_session(
    session_id: str,
    current_user: User = Depends(require_permissions("capture:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    capture = await _session_or_404(db, session_id, current_user.id)
    if capture.status == "completed":
        raise HTTPException(status_code=409, detail="completed capture session cannot be paused")
    capture.status = "paused"
    await db.commit()
    return {"id": capture.id, "status": capture.status}


@router.post("/{session_id}/resume")
@audit_log("resume", "capture_session", resource_id_param="session_id")
async def resume_capture_session(
    session_id: str,
    current_user: User = Depends(require_permissions("capture:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    capture = await _session_or_404(db, session_id, current_user.id)
    if capture.status != "paused":
        raise HTTPException(status_code=409, detail="capture session is not paused")
    capture.status = "capturing"
    await db.commit()
    return {"id": capture.id, "status": capture.status}


@router.post("/{session_id}/cancel")
@audit_log("cancel", "capture_session", resource_id_param="session_id")
async def cancel_capture_session(
    session_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("capture:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    """Explicitly terminate an incomplete capture instead of leaving it active."""
    capture = await _session_or_404(db, session_id, current_user.id)
    if capture.status == "completed":
        raise HTTPException(status_code=409, detail="completed capture session cannot be cancelled")
    if capture.status == "cancelled":
        return {"id": capture.id, "status": capture.status}
    reason = str(body.get("reason") or "cancelled by user").strip()[:500]
    capture.status = "cancelled"
    capture.failure_reason = reason or "cancelled by user"
    capture.ended_at = _utcnow()
    await db.commit()
    return {"id": capture.id, "status": capture.status}


@router.get("/{session_id}")
async def get_capture_session(
    session_id: str,
    current_user: User = Depends(require_permissions("capture:export")),
    db: AsyncSession = Depends(get_autotest_db),
):
    capture = await _session_or_404(db, session_id, current_user.id)
    exchanges = list(
        (
            await db.scalars(
                select(CapturedExchange)
                .where(CapturedExchange.session_id == capture.id)
                .order_by(CapturedExchange.sequence)
            )
        ).all()
    )
    return _capture_payload(capture, exchanges)


@router.get("/{session_id}/export")
@audit_log("export", "capture_session", resource_id_param="session_id")
async def export_capture_har(
    session_id: str,
    current_user: User = Depends(require_permissions("capture:export")),
    db: AsyncSession = Depends(get_autotest_db),
):
    """Export only the already-redacted capture representation as HAR-compatible JSON."""
    capture = await _session_or_404(db, session_id, current_user.id)
    exchanges = list(
        (
            await db.scalars(
                select(CapturedExchange)
                .where(CapturedExchange.session_id == capture.id)
                .order_by(CapturedExchange.sequence)
            )
        ).all()
    )
    entries = []
    for exchange in exchanges:
        request = exchange.request_redacted or {}
        response = exchange.response_redacted or {}
        entries.append(
            {
                "startedDateTime": exchange.created_at.isoformat() if exchange.created_at else None,
                "time": exchange.timing_ms or 0,
                "request": {
                    "method": exchange.method,
                    "url": exchange.url,
                    "headers": [{"name": key, "value": value} for key, value in (request.get("headers") or {}).items()],
                    "postData": {
                        "mimeType": request.get("content_type"),
                        "text": json.dumps(request.get("payload"), ensure_ascii=False),
                    }
                    if request.get("payload") is not None
                    else None,
                },
                "response": {
                    "status": int(response.get("status") or 0),
                    "headers": [
                        {"name": key, "value": value} for key, value in (response.get("headers") or {}).items()
                    ],
                    "content": {
                        "text": json.dumps(response.get("body"), ensure_ascii=False),
                        "mimeType": "application/json",
                    }
                    if response.get("body") is not None
                    else {},
                },
                "_resourceType": exchange.resource_type,
                "_failureReason": exchange.failure_reason,
            }
        )
    return JSONResponse(
        content={"log": {"version": "1.2", "creator": {"name": "TestMaster", "version": "1"}, "entries": entries}},
        headers={
            "Content-Disposition": f'attachment; filename="capture-{capture.id}.har"',
            "Cache-Control": "private, no-store",
        },
    )


@router.post("/{session_id}/convert")
@audit_log("convert", "capture_session", resource_id_param="session_id")
async def convert_capture_to_assets(
    session_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("capture:export", "case:create", "scenario:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    capture = await _session_or_404(db, session_id, current_user.id)
    if capture.status != "completed":
        raise HTTPException(status_code=409, detail="complete the capture session before converting it")
    exchange_ids = body.get("exchange_ids")
    if not isinstance(exchange_ids, list) or not exchange_ids or len(exchange_ids) > MAX_CAPTURE_EXCHANGES:
        raise HTTPException(status_code=422, detail="exchange_ids is invalid")
    try:
        selected_ids = [int(value) for value in exchange_ids]
    except (TypeError, ValueError) as exc:
        raise HTTPException(status_code=422, detail="exchange_ids is invalid") from exc
    if len(selected_ids) != len(set(selected_ids)):
        raise HTTPException(status_code=422, detail="exchange_ids must be unique")
    exchanges = list(
        (
            await db.scalars(
                select(CapturedExchange)
                .where(CapturedExchange.session_id == capture.id, CapturedExchange.id.in_(selected_ids))
                .order_by(CapturedExchange.sequence)
            )
        ).all()
    )
    if len(exchanges) != len(selected_ids):
        raise HTTPException(status_code=404, detail="one or more captured exchanges were not found")
    candidates = [candidate_from_exchange(exchange) for exchange in exchanges]
    _apply_variable_mappings(candidates, body.get("variable_mappings"))
    _apply_candidate_overrides(candidates, body.get("candidate_overrides"))
    if bool(body.get("create_scenario")) and body.get("confirm_dependency_review") is not True:
        raise HTTPException(status_code=422, detail="confirm_dependency_review must be true before creating a scenario")
    conflict_strategy = str(body.get("conflict_strategy") or "skip").lower()
    if conflict_strategy not in {"skip", "copy", "update"}:
        raise HTTPException(status_code=422, detail="conflict_strategy must be skip, copy, or update")
    if conflict_strategy == "update" and body.get("confirm_update") is not True:
        raise HTTPException(status_code=422, detail="confirm_update must be true when updating existing cases")
    target_group_id = body.get("target_group_id")
    if target_group_id is not None:
        group = await db.scalar(
            select(AutoTestGroup).where(AutoTestGroup.id == target_group_id, AutoTestGroup.user_id == current_user.id)
        )
        if group is None:
            raise HTTPException(status_code=404, detail="target group not found")

    job = ImportJob(user_id=current_user.id, source_type="browser_capture", status="running")
    db.add(job)
    await db.flush()
    selected_cases: list[AutoTestCase] = []
    imported = skipped = copied = updated = 0
    for candidate in candidates:
        existing_cases = list(
            (
                await db.scalars(
                    select(AutoTestCase).where(
                        AutoTestCase.user_id == current_user.id,
                        AutoTestCase.method == candidate["method"],
                        AutoTestCase.url == candidate["url"],
                    )
                )
            ).all()
        )
        duplicate = next((case for case in existing_cases if _case_matches_candidate(case, candidate)), None)
        if duplicate is not None and conflict_strategy == "skip":
            skipped += 1
            continue
        if duplicate is not None and conflict_strategy == "update":
            _apply_capture_candidate_to_case(duplicate, candidate, target_group_id)
            selected_cases.append(duplicate)
            updated += 1
            continue
        name = candidate["name"]
        if duplicate is not None:
            name = f"{name} (capture copy)"[:200]
            copied += 1
        case = AutoTestCase(
            group_id=target_group_id,
            user_id=current_user.id,
            name=name,
            method=candidate["method"],
            url=candidate["url"],
            headers=candidate["headers"] or None,
            params=candidate["params"] or None,
            body_type=candidate["body_type"],
            content_type=candidate["content_type"],
            payload=candidate["payload"],
            assert_rules=candidate["assert_rules"] or None,
            extractors=candidate.get("extractors") or None,
            description="Created from a redacted browser capture. Confirm variable mappings and run a preview before using it in regression.",
        )
        db.add(case)
        selected_cases.append(case)
        imported += 1
    await db.flush()

    scenario = None
    if bool(body.get("create_scenario")) and selected_cases:
        scenario_name = str(body.get("scenario_name") or f"Captured flow {capture.id[:8]}").strip()[:200]
        if not scenario_name:
            raise HTTPException(status_code=422, detail="scenario_name is invalid")
        scenario = AutoTestScenario(
            name=scenario_name,
            description="Generated from selected browser capture exchanges. It requires a successful preview run before regression use.",
            user_id=current_user.id,
            is_active=False,
        )
        db.add(scenario)
        await db.flush()
        db.add_all(
            [
                AutoTestScenarioStep(
                    scenario_id=scenario.id,
                    api_case_id=case.id,
                    step_order=(index + 1) * 10,
                    is_active=True,
                    step_type="api_request",
                )
                for index, case in enumerate(selected_cases)
            ]
        )

    for exchange in exchanges:
        exchange.selected = True
    job.status = "completed"
    job.completed_at = _utcnow()
    job.summary = {
        "capture_session_id": capture.id,
        "selected_count": len(exchanges),
        "imported_count": imported,
        "copied_count": copied,
        "updated_count": updated,
        "skipped_count": skipped,
        "scenario_id": scenario.id if scenario else None,
        "requires_preview": bool(scenario),
    }
    await db.commit()
    return {"import_job_id": job.id, **job.summary, "case_ids": [case.id for case in selected_cases]}


@router.post("/{session_id}/preview")
@audit_log("preview_execute", "capture_session", resource_id_param="session_id")
async def preview_capture_scenario(
    session_id: str,
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("capture:export", "scenario:execute", "scenario:update")),
    db: AsyncSession = Depends(get_autotest_db),
):
    """Run a generated capture flow once; only a passing preview activates it for regression."""
    capture = await _session_or_404(db, session_id, current_user.id)
    scenario_id = int(body.get("scenario_id") or 0)
    scenario = await db.scalar(
        select(AutoTestScenario).where(
            AutoTestScenario.id == scenario_id,
            AutoTestScenario.user_id == current_user.id,
        )
    )
    if scenario is None:
        raise HTTPException(status_code=404, detail="generated scenario not found")
    jobs = list(
        (
            await db.scalars(
                select(ImportJob).where(
                    ImportJob.user_id == current_user.id,
                    ImportJob.source_type == "browser_capture",
                    ImportJob.status == "completed",
                )
            )
        ).all()
    )
    job = next(
        (
            item
            for item in jobs
            if (item.summary or {}).get("capture_session_id") == capture.id
            and (item.summary or {}).get("scenario_id") == scenario.id
        ),
        None,
    )
    if job is None:
        raise HTTPException(status_code=409, detail="scenario is not a pending preview generated from this capture")
    from fastapi_backend.services.autotest_scenario_runner import run_scenario

    result = await run_scenario(scenario.id, env_id=body.get("env_id"), user_id=current_user.id)
    success = bool(result.get("success"))
    scenario.is_active = success
    job.summary = {
        **(job.summary or {}),
        "preview_status": "passed" if success else "failed",
        "preview_result": {"success": success, "failed_steps": result.get("failed_steps", 0)},
    }
    await db.commit()
    return {"scenario_id": scenario.id, "status": job.summary["preview_status"], "result": result}
