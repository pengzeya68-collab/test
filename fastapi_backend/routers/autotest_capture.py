"""Safe browser traffic capture sessions and conversion to API test assets."""

from __future__ import annotations

import asyncio
import json
import re
from collections import Counter
from fnmatch import fnmatch
from datetime import datetime, timedelta, timezone
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.deps.project_context import get_active_project_id, get_active_project_id_member
from fastapi_backend.models.autotest import (
    AutoTestCase,
    AutoTestGroup,
    AutoTestEnvironment,
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
    redact_capture_headers,
    redact_capture_source_url,
    redact_capture_value,
)
from fastapi_backend.services.har_import import HarImportError, MAX_HAR_BYTES, parse_har

router = APIRouter(prefix="/api/auto-test/import/captures", tags=["Import Center"])
_VARIABLE_NAME = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,99}$")
_HOST_NAME = re.compile(r"^[A-Za-z0-9.*-]{1,253}$")
_ASSERTION_OPERATORS = {"equals", "not_equals", "contains", "json_exists", "gte", "lte", "matches"}
# Preview runs a whole generated scenario inside one HTTP request; bound it so a
# slow target service or a long step chain cannot hang the request indefinitely.
_PREVIEW_TIMEOUT_SECONDS = 180
_REPLAY_VARIABLE_LIMIT = 100
_CAPTURE_SESSION_MAX_AGE = timedelta(hours=24)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _expire_stale_capture_sessions(db: AsyncSession, user_id: int | None = None) -> int:
    """Close abandoned recordings so a crashed desktop app cannot leave them live."""
    now = _utcnow()
    query = select(CaptureSession).where(
        CaptureSession.status.in_(("capturing", "paused")),
        CaptureSession.started_at < now - _CAPTURE_SESSION_MAX_AGE,
    )
    if user_id is not None:
        query = query.where(CaptureSession.user_id == user_id)
    stale = list((await db.scalars(query)).all())
    for capture in stale:
        capture.status = "cancelled"
        capture.ended_at = now
        capture.failure_reason = "capture session expired after 24 hours without completion"
    if stale:
        await db.commit()
    return len(stale)


async def _session_or_404(
    db: AsyncSession, session_id: str, user_id: int, project_id: int, *, for_update: bool = False
) -> CaptureSession:
    await _expire_stale_capture_sessions(db, user_id)
    query = select(CaptureSession).where(
        CaptureSession.id == session_id,
        CaptureSession.user_id == user_id,
        CaptureSession.project_id == project_id,
    )
    if for_update:
        query = query.with_for_update()
    capture = await db.scalar(query)
    if capture is None:
        raise HTTPException(status_code=404, detail="capture session not found")
    return capture


async def _replay_url_for_environment(
    db: AsyncSession, original_url: str, environment_id: int | None, user_id: int, project_id: int
) -> str:
    """Apply an owned environment base URL without losing the captured route."""
    if environment_id is None:
        return original_url
    environment = await db.scalar(
        select(AutoTestEnvironment).where(
            AutoTestEnvironment.id == environment_id,
            AutoTestEnvironment.user_id == user_id,
            AutoTestEnvironment.project_id == project_id,
        )
    )
    if environment is None:
        raise HTTPException(status_code=404, detail="replay environment not found")
    base = urlsplit(str(environment.base_url or "").strip())
    captured = urlsplit(original_url)
    if base.scheme not in {"http", "https"} or not base.netloc or not captured.path:
        raise HTTPException(status_code=422, detail="replay environment base URL is invalid")
    prefix = base.path.rstrip("/")
    route = captured.path if captured.path.startswith("/") else "/" + captured.path
    return urlunsplit((base.scheme, base.netloc, prefix + route, captured.query, ""))


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


def _exchange_detail(exchange: CapturedExchange) -> dict[str, Any]:
    """Return only the already-redacted evidence held by a capture session."""
    request = exchange.request_redacted or {}
    response = exchange.response_redacted or {}
    return {
        **candidate_from_exchange(exchange),
        "request": {
            "headers": request.get("headers") or {},
            "params": request.get("params") or {},
            "body_type": request.get("body_type") or "none",
            "content_type": request.get("content_type") or "application/json",
            "body": request.get("payload"),
        },
        "response": {
            "status": int(response.get("status") or 0),
            "headers": response.get("headers") or {},
            "body": response.get("body"),
        },
        "sequence": exchange.sequence,
        "created_at": exchange.created_at,
        "source_event_id": exchange.source_event_id,
    }


def _json_diff(expected: Any, actual: Any, path: str = "$") -> list[dict[str, Any]]:
    """Small, bounded semantic diff suitable for a replay review pane."""
    if len(path) > 500:
        return []
    if isinstance(expected, str) and (expected.startswith("{{") or "[REDACTED]" in expected):
        return []
    if type(expected) is not type(actual):
        return [{"path": path, "kind": "type", "expected": type(expected).__name__, "actual": type(actual).__name__}]
    if isinstance(expected, dict):
        differences: list[dict[str, Any]] = []
        for key in sorted(set(expected) | set(actual)):
            if len(differences) >= 100:
                break
            child_path = f"{path}.{key}"
            if key not in expected:
                differences.append({"path": child_path, "kind": "added"})
            elif key not in actual:
                differences.append({"path": child_path, "kind": "removed"})
            else:
                differences.extend(_json_diff(expected[key], actual[key], child_path))
        return differences[:100]
    if isinstance(expected, list):
        differences = []
        if len(expected) != len(actual):
            differences.append({"path": path, "kind": "length", "expected": len(expected), "actual": len(actual)})
        for index, value in enumerate(expected[:50]):
            if index >= len(actual) or len(differences) >= 100:
                break
            differences.extend(_json_diff(value, actual[index], f"{path}[{index}]"))
        return differences[:100]
    if expected != actual:
        return [{"path": path, "kind": "changed", "expected": redact_capture_value(expected), "actual": redact_capture_value(actual)}]
    return []


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
    project_id: int = Depends(get_active_project_id_member),
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
        project_id=project_id,
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


@router.post("/har", status_code=status.HTTP_201_CREATED)
@audit_log("import_har", "capture_session")
async def import_har_as_capture_session(
    file: UploadFile = File(...),
    current_user: User = Depends(require_permissions("capture:create")),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id_member),
):
    """Create a reviewable capture session from a standard HAR export.

    Importing a HAR must not immediately create executable test cases.  The
    resulting evidence is redacted by the parser and follows the same manual
    review, replay and conversion path as desktop-recorded traffic.
    """
    raw = await file.read(MAX_HAR_BYTES + 1)
    if len(raw) > MAX_HAR_BYTES:
        raise HTTPException(status_code=413, detail="HAR file exceeds the 25 MB limit")
    try:
        candidates = parse_har(raw)
    except HarImportError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if not candidates:
        raise HTTPException(status_code=422, detail="HAR does not contain importable HTTP exchanges")
    capture = CaptureSession(
        user_id=current_user.id,
        project_id=project_id,
        origin="har_import",
        status="completed",
        policy_version="v1",
        source_url=redact_capture_source_url(str(file.filename or "HAR import")),
        capture_config={"domain_allowlist": [], "path_exclude": [], "source_filename": str(file.filename or "")[:200]},
        ended_at=_utcnow(),
    )
    db.add(capture)
    await db.flush()
    exchanges: list[CapturedExchange] = []
    for sequence, candidate in enumerate(candidates[:MAX_CAPTURE_EXCHANGES], start=1):
        metadata = candidate.get("source_metadata") if isinstance(candidate.get("source_metadata"), dict) else {}
        response_metadata = metadata.get("response") if isinstance(metadata.get("response"), dict) else {}
        exchanges.append(
            CapturedExchange(
                session_id=capture.id,
                sequence=sequence,
                method=candidate["method"],
                url=candidate["url"],
                request_redacted={
                    "headers": candidate.get("headers") or {},
                    "params": candidate.get("params") or {},
                    "body_type": candidate.get("body_type") or "none",
                    "content_type": candidate.get("content_type") or "application/json",
                    "payload": candidate.get("payload"),
                    "assert_rules": candidate.get("assert_rules") or [],
                },
                response_redacted={
                    "status": int(candidate.get("response_status") or 0),
                    "headers": response_metadata.get("headers") or {},
                    "body": response_metadata.get("json_sample"),
                },
                fingerprint=candidate["fingerprint"],
                resource_type=str(candidate.get("resource_type") or "fetch")[:30],
                timing_ms=max(0, min(int(candidate.get("timing_ms") or 0), 600_000)) or None,
                source_event_id=f"har-{sequence}-{candidate['fingerprint'][:24]}",
            )
        )
    db.add_all(exchanges)
    await db.commit()
    return {"id": capture.id, "status": capture.status, "imported_exchanges": len(exchanges)}


@router.get("")
async def list_capture_sessions(
    limit: int = 50,
    current_user: User = Depends(require_permissions("capture:export")),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id),
):
    await _expire_stale_capture_sessions(db, current_user.id)
    captures = list(
        (
            await db.scalars(
                select(CaptureSession)
                .where(CaptureSession.user_id == current_user.id, CaptureSession.project_id == project_id)
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
    project_id: int = Depends(get_active_project_id_member),
):
    # Lock the session row so concurrent appends to the same session serialize;
    # without this, two writers can read the same MAX(sequence) and collide on the
    # (session_id, sequence) unique constraint.
    capture = await _session_or_404(db, session_id, current_user.id, project_id, for_update=True)
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
    # Sequence numbering must follow MAX(sequence), not COUNT(*), so it stays
    # monotonic even if exchanges are ever deleted from a session.
    max_sequence = (
        await db.scalar(select(func.max(CapturedExchange.sequence)).where(CapturedExchange.session_id == capture.id))
        or 0
    )
    event_ids = {
        str(item.get("captureEventId") or item.get("capture_event_id") or "").strip()
        for item in values
        if isinstance(item, dict) and str(item.get("captureEventId") or item.get("capture_event_id") or "").strip()
    }
    existing_event_ids = set()
    if event_ids:
        existing_event_ids = set(
            (
                await db.scalars(
                    select(CapturedExchange.source_event_id).where(
                        CapturedExchange.session_id == capture.id,
                        CapturedExchange.source_event_id.in_(event_ids),
                    )
                )
            ).all()
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
        # Browser-to-server retry must be idempotent, but calls that happen to
        # have the same redacted payload are still independent business events.
        source_event_id = normalized.get("source_event_id")
        if source_event_id and source_event_id in existing_event_ids:
            continue
        if source_event_id:
            existing_event_ids.add(source_event_id)
        exchange = CapturedExchange(
            session_id=capture.id,
            sequence=max_sequence + len(accepted) + 1,
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
            source_event_id=source_event_id,
        )
        db.add(exchange)
        accepted.append(exchange)
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="capture exchanges were modified concurrently, please retry the batch",
        ) from exc
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
    project_id: int = Depends(get_active_project_id_member),
):
    capture = await _session_or_404(db, session_id, current_user.id, project_id)
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
    project_id: int = Depends(get_active_project_id_member),
):
    capture = await _session_or_404(db, session_id, current_user.id, project_id)
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
    project_id: int = Depends(get_active_project_id_member),
):
    capture = await _session_or_404(db, session_id, current_user.id, project_id)
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
    project_id: int = Depends(get_active_project_id_member),
):
    """Explicitly terminate an incomplete capture instead of leaving it active."""
    capture = await _session_or_404(db, session_id, current_user.id, project_id)
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
    project_id: int = Depends(get_active_project_id),
):
    capture = await _session_or_404(db, session_id, current_user.id, project_id)
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


@router.get("/{session_id}/exchanges/{exchange_id}")
async def get_capture_exchange_detail(
    session_id: str,
    exchange_id: int,
    current_user: User = Depends(require_permissions("capture:export")),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id),
):
    """Inspect one redacted exchange without loading a whole long session."""
    capture = await _session_or_404(db, session_id, current_user.id, project_id)
    exchange = await db.scalar(
        select(CapturedExchange).where(CapturedExchange.session_id == capture.id, CapturedExchange.id == exchange_id)
    )
    if exchange is None:
        raise HTTPException(status_code=404, detail="captured exchange not found")
    return _exchange_detail(exchange)


@router.post("/{session_id}/exchanges/{exchange_id}/replay")
@audit_log("replay", "capture_exchange", resource_id_param="exchange_id")
async def replay_capture_exchange(
    session_id: str,
    exchange_id: int,
    body: dict[str, Any] = Body(default_factory=dict),
    current_user: User = Depends(require_permissions("capture:export", "case:execute")),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id_member),
):
    """Explicitly replay one safe capture and compare it with its baseline.

    Captures often include create/update calls.  Replaying therefore always
    needs an affirmative request flag; the UI explains the target and presents
    a confirmation dialog instead of silently sending a side-effecting call.
    """
    if body.get("confirm_replay") is not True:
        raise HTTPException(status_code=422, detail="confirm_replay must be true before sending a captured request")
    capture = await _session_or_404(db, session_id, current_user.id, project_id)
    exchange = await db.scalar(
        select(CapturedExchange).where(CapturedExchange.session_id == capture.id, CapturedExchange.id == exchange_id)
    )
    if exchange is None:
        raise HTTPException(status_code=404, detail="captured exchange not found")
    if (exchange.resource_type or "").lower() not in {"xhr", "fetch"}:
        raise HTTPException(status_code=409, detail="only XHR or fetch exchanges can be replayed as API requests")

    variables = body.get("variables") or {}
    overrides = body.get("overrides") or {}
    if not isinstance(variables, dict) or len(variables) > _REPLAY_VARIABLE_LIMIT:
        raise HTTPException(status_code=422, detail="variables is invalid")
    if not isinstance(overrides, dict) or set(overrides) - {"url", "headers", "params", "payload", "body_type"}:
        raise HTTPException(status_code=422, detail="replay overrides are invalid")
    if any(len(str(key)) > 100 or len(str(value)) > 20_000 for key, value in variables.items()):
        raise HTTPException(status_code=422, detail="replay variables are too large")
    request = exchange.request_redacted or {}
    request_headers = dict(request.get("headers") or {})
    request_params = dict(request.get("params") or {})
    if overrides.get("headers") is not None:
        if not isinstance(overrides["headers"], dict):
            raise HTTPException(status_code=422, detail="override headers must be an object")
        request_headers.update({str(key): str(value) for key, value in overrides["headers"].items()})
    if overrides.get("params") is not None:
        if not isinstance(overrides["params"], dict):
            raise HTTPException(status_code=422, detail="override params must be an object")
        request_params.update({str(key): str(value) for key, value in overrides["params"].items()})
    if overrides.get("url") is not None:
        replay_url = str(overrides["url"]).strip()
    else:
        replay_url = await _replay_url_for_environment(
            db, exchange.url, body.get("environment_id"), current_user.id, project_id
        )
    if not replay_url or len(replay_url) > 4000:
        raise HTTPException(status_code=422, detail="replay URL is invalid")
    replay_body = overrides.get("payload", request.get("payload"))
    replay_body_type = str(overrides.get("body_type") or request.get("body_type") or "none").lower()
    if replay_body_type not in {"none", "json", "raw", "form", "form-data", "x-www-form-urlencoded", "binary", "graphql"}:
        raise HTTPException(status_code=422, detail="replay body_type is invalid")

    from fastapi_backend.services.autotest_request_service import execute_http_request

    replay = await execute_http_request(
        method=exchange.method,
        url=replay_url,
        headers=request_headers,
        params=request_params,
        body=replay_body,
        body_type=replay_body_type,
        env_id=body.get("environment_id"),
        variables=variables,
        user_id=current_user.id,
        request_config={"timeout_ms": min(max(int(body.get("timeout_ms") or 30_000), 100), 120_000)},
    )
    baseline = exchange.response_redacted or {}
    replay_body_safe = redact_capture_value(replay.get("response_content"), "response_body")
    baseline_body = baseline.get("body")
    return {
        "exchange_id": exchange.id,
        "replay": {
            "success": bool(replay.get("success")),
            "status": replay.get("status_code"),
            "elapsed_ms": replay.get("elapsed_ms", replay.get("execution_time", 0)),
            "headers": redact_capture_headers(replay.get("headers") or {}),
            "body": replay_body_safe,
            "error": redact_capture_value(replay.get("error"), "error") if replay.get("error") else None,
            "attempts": replay.get("attempts") or [],
        },
        "comparison": {
            "baseline_status": int(baseline.get("status") or 0),
            "status_matches": int(baseline.get("status") or 0) == int(replay.get("status_code") or 0),
            "baseline_timing_ms": exchange.timing_ms,
            "timing_delta_ms": (
                int(replay.get("elapsed_ms", replay.get("execution_time", 0)) or 0) - exchange.timing_ms
                if exchange.timing_ms is not None
                else None
            ),
            "body_differences": _json_diff(baseline_body, replay_body_safe)[:100],
        },
    }


@router.get("/{session_id}/analysis")
async def analyze_capture_session(
    session_id: str,
    current_user: User = Depends(require_permissions("capture:export")),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id),
):
    """Return explainable, redaction-safe traffic quality signals.

    This deliberately provides suggestions instead of mutating cases.  A
    recording is evidence, not a ready-to-run regression asset: the tester
    reviews candidates, variable mappings and assertions before conversion.
    """
    capture = await _session_or_404(db, session_id, current_user.id, project_id)
    exchanges = list((await db.scalars(
        select(CapturedExchange).where(CapturedExchange.session_id == capture.id).order_by(CapturedExchange.sequence)
    )).all())
    status_codes = Counter()
    methods = Counter()
    hosts = Counter()
    fingerprints = Counter()
    slow = []
    failed = []
    redacted_fields = 0
    timings = sorted(item.timing_ms for item in exchanges if item.timing_ms is not None)
    p95 = timings[max(0, int(len(timings) * 0.95) - 1)] if timings else None
    for item in exchanges:
        response = item.response_redacted or {}
        status_code = int(response.get("status") or 0)
        status_codes[f"{status_code // 100}xx" if status_code else "unknown"] += 1
        methods[item.method] += 1
        hosts[urlsplit(item.url).hostname or "unknown"] += 1
        fingerprints[item.fingerprint] += 1
        if item.timing_ms is not None and p95 is not None and item.timing_ms >= p95 and len(timings) >= 3:
            slow.append({"id": item.id, "sequence": item.sequence, "url": item.url, "timing_ms": item.timing_ms})
        if status_code >= 400 or item.failure_reason:
            failed.append({"id": item.id, "sequence": item.sequence, "url": item.url, "status": status_code, "reason": item.failure_reason})
        serialized = json.dumps({"request": item.request_redacted, "response": response}, ensure_ascii=False)
        redacted_fields += serialized.count("******")
    suggestions = []
    if failed:
        suggestions.append({"type": "failure", "title": "先处理异常请求", "detail": f"发现 {len(failed)} 条 HTTP 异常或网络失败记录；不要直接把它们作为成功断言导入。"})
    if len(fingerprints) < len(exchanges):
        suggestions.append({"type": "deduplicate", "title": "合并重复调用", "detail": f"检测到 {len(exchanges) - len(fingerprints)} 条重复流量；转换时保留有业务意义的一次调用即可。"})
    if p95 is not None:
        suggestions.append({"type": "performance", "title": "设置性能断言", "detail": f"本次流量 P95 为 {p95} ms；可为关键接口添加小于等于该阈值或团队 SLA 的响应时间断言。"})
    if redacted_fields:
        suggestions.append({"type": "security", "title": "敏感数据已脱敏", "detail": f"检测到 {redacted_fields} 处令牌、Cookie 或敏感字段已遮蔽；请通过环境变量或登录态配置恢复执行所需凭据。"})
    if capture.origin == "har_import":
        suggestions.append({"type": "mobile", "title": "移动端流量导入", "detail": "HAR 可以来自移动设备代理工具；TLS 证书固定的应用无法通过常规代理解密，应使用应用提供的测试开关或导入可用 HAR。"})
    return {
        "session_id": capture.id,
        "total": len(exchanges),
        "methods": dict(methods),
        "status_classes": dict(status_codes),
        "top_hosts": [{"host": host, "count": count} for host, count in hosts.most_common(10)],
        "p95_timing_ms": p95,
        "slow_exchanges": slow[:20],
        "failed_exchanges": failed[:50],
        "duplicate_count": len(exchanges) - len(fingerprints),
        "redacted_field_count": redacted_fields,
        "suggestions": suggestions,
    }


@router.get("/{session_id}/export")
@audit_log("export", "capture_session", resource_id_param="session_id")
async def export_capture_har(
    session_id: str,
    current_user: User = Depends(require_permissions("capture:export")),
    db: AsyncSession = Depends(get_autotest_db),
    project_id: int = Depends(get_active_project_id),
):
    """Export only the already-redacted capture representation as HAR-compatible JSON."""
    capture = await _session_or_404(db, session_id, current_user.id, project_id)
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
        request_payload = request.get("payload")
        request_entry: dict[str, Any] = {
            "method": exchange.method,
            "url": exchange.url,
            "httpVersion": "HTTP/1.1",
            "headers": [{"name": key, "value": value} for key, value in (request.get("headers") or {}).items()],
            "queryString": [{"name": key, "value": value} for key, value in (request.get("params") or {}).items()],
            "cookies": [],
            "headersSize": -1,
            "bodySize": -1,
        }
        if request_payload is not None:
            request_entry["postData"] = {
                "mimeType": request.get("content_type") or "application/octet-stream",
                "text": request_payload if isinstance(request_payload, str) else json.dumps(request_payload, ensure_ascii=False),
            }
        response_body = response.get("body")
        response_entry: dict[str, Any] = {
            "status": int(response.get("status") or 0),
            "statusText": "",
            "httpVersion": "HTTP/1.1",
            "headers": [{"name": key, "value": value} for key, value in (response.get("headers") or {}).items()],
            "cookies": [],
            "content": {"size": -1, "mimeType": (response.get("headers") or {}).get("content-type", "")},
            "redirectURL": "",
            "headersSize": -1,
            "bodySize": -1,
        }
        if response_body is not None:
            response_entry["content"]["text"] = (
                response_body if isinstance(response_body, str) else json.dumps(response_body, ensure_ascii=False)
            )
        entries.append(
            {
                "startedDateTime": exchange.created_at.isoformat() if exchange.created_at else None,
                "time": exchange.timing_ms or 0,
                "request": request_entry,
                "response": response_entry,
                "cache": {},
                "timings": {"blocked": -1, "dns": -1, "connect": -1, "send": 0, "wait": exchange.timing_ms or 0, "receive": 0, "ssl": -1},
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
    project_id: int = Depends(get_active_project_id_member),
):
    capture = await _session_or_404(db, session_id, current_user.id, project_id)
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
    if any((exchange.resource_type or "").lower() not in {"xhr", "fetch"} for exchange in exchanges):
        raise HTTPException(
            status_code=422,
            detail="only XHR and fetch exchanges can be converted to API cases; inspect page traffic in the workbench",
        )
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
            select(AutoTestGroup).where(
                AutoTestGroup.id == target_group_id,
                AutoTestGroup.user_id == current_user.id,
                AutoTestGroup.project_id == project_id,
            )
        )
        if group is None:
            raise HTTPException(status_code=404, detail="target group not found")

    job = ImportJob(
        user_id=current_user.id,
        project_id=project_id,
        source_type="browser_capture",
        status="running",
    )
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
            project_id=project_id,
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
            workspace_project_id=project_id,
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
    project_id: int = Depends(get_active_project_id_member),
):
    """Run a generated capture flow once; only a passing preview activates it for regression."""
    capture = await _session_or_404(db, session_id, current_user.id, project_id)
    scenario_id = int(body.get("scenario_id") or 0)
    scenario = await db.scalar(
        select(AutoTestScenario).where(
            AutoTestScenario.id == scenario_id,
            AutoTestScenario.user_id == current_user.id,
            AutoTestScenario.workspace_project_id == project_id,
        )
    )
    if scenario is None:
        raise HTTPException(status_code=404, detail="generated scenario not found")
    jobs = list(
        (
            await db.scalars(
                select(ImportJob).where(
                    ImportJob.user_id == current_user.id,
                    ImportJob.project_id == project_id,
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

    try:
        result = await asyncio.wait_for(
            run_scenario(scenario.id, env_id=body.get("env_id"), user_id=current_user.id),
            timeout=_PREVIEW_TIMEOUT_SECONDS,
        )
    except asyncio.TimeoutError as exc:
        scenario.is_active = False
        job.summary = {
            **(job.summary or {}),
            "preview_status": "timed_out",
            "preview_result": {"success": False, "timeout_seconds": _PREVIEW_TIMEOUT_SECONDS},
        }
        await db.commit()
        raise HTTPException(
            status_code=504,
            detail=(
                f"场景预览超过 {_PREVIEW_TIMEOUT_SECONDS} 秒未结束，已按未通过处理并保持场景未启用。"
                "请减少预览步骤数量或确认被测服务响应正常后重试。"
            ),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        scenario.is_active = False
        job.summary = {
            **(job.summary or {}),
            "preview_status": "error",
            "preview_result": {"success": False, "error": str(exc)[:500]},
        }
        await db.commit()
        raise HTTPException(
            status_code=502,
            detail=f"场景预览执行异常，已按未通过处理：{str(exc)[:300]}",
        ) from exc
    success = bool(result.get("success"))
    scenario.is_active = success
    job.summary = {
        **(job.summary or {}),
        "preview_status": "passed" if success else "failed",
        "preview_result": {"success": success, "failed_steps": result.get("failed_steps", 0)},
    }
    await db.commit()
    return {"scenario_id": scenario.id, "status": job.summary["preview_status"], "result": result}
