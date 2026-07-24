"""OpenAPI snapshot / schema diff / contract rule service."""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import AsyncSessionLocal
from fastapi_backend.models.feature_upgrades import APIContractRule, OpenAPISnapshot, SchemaChangeRecord

_logger = logging.getLogger(__name__)
_POLL_LOOP_SECONDS = 300
_poll_task: asyncio.Task | None = None


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class ContractTestingService:
    async def create_snapshot(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        spec_content: str,
        source_url: str | None = None,
        source_type: str = "upload",
        group_id: int | None = None,
    ) -> OpenAPISnapshot:
        content = spec_content.strip()
        if not content:
            raise ValueError("spec_content required")
        parsed = self.parse_openapi(content)
        snapshot = OpenAPISnapshot(
            project_id=project_id,
            group_id=group_id,
            source_url=source_url,
            source_type=source_type,
            spec_version=parsed.get("version"),
            content_hash=_content_hash(content),
            spec_content=content,
            parsed_endpoints=parsed.get("endpoints") or [],
        )
        db.add(snapshot)
        await db.flush()
        # Auto-diff against previous snapshot in same project/group
        stmt = (
            select(OpenAPISnapshot)
            .where(OpenAPISnapshot.project_id == project_id, OpenAPISnapshot.id != snapshot.id)
            .order_by(OpenAPISnapshot.id.desc())
            .limit(1)
        )
        if group_id is not None:
            stmt = stmt.where(OpenAPISnapshot.group_id == group_id)
        prev = await db.scalar(stmt)
        if prev and prev.content_hash != snapshot.content_hash:
            await self.diff_snapshots(db, project_id=project_id, old_id=prev.id, new_id=snapshot.id)
        return snapshot

    async def list_snapshots(self, db: AsyncSession, project_id: int) -> list[OpenAPISnapshot]:
        return list(
            (
                await db.scalars(
                    select(OpenAPISnapshot)
                    .where(OpenAPISnapshot.project_id == project_id)
                    .order_by(OpenAPISnapshot.id.desc())
                )
            ).all()
        )

    async def get_snapshot(self, db: AsyncSession, snapshot_id: int) -> OpenAPISnapshot:
        item = await db.get(OpenAPISnapshot, snapshot_id)
        if item is None:
            raise LookupError("snapshot not found")
        return item

    async def diff_snapshots(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        old_id: int,
        new_id: int,
    ) -> SchemaChangeRecord:
        old = await self.get_snapshot(db, old_id)
        new = await self.get_snapshot(db, new_id)
        old_eps = {(e.get("method"), e.get("path")): e for e in (old.parsed_endpoints or [])}
        new_eps = {(e.get("method"), e.get("path")): e for e in (new.parsed_endpoints or [])}
        changes: list[dict[str, Any]] = []
        breaking: list[dict[str, Any]] = []
        for key in sorted(set(old_eps) - set(new_eps)):
            item = {"type": "removed_endpoint", "method": key[0], "path": key[1]}
            changes.append(item)
            breaking.append(item)
        for key in sorted(set(new_eps) - set(old_eps)):
            changes.append({"type": "added_endpoint", "method": key[0], "path": key[1]})
        for key in sorted(set(old_eps) & set(new_eps)):
            o, n = old_eps[key], new_eps[key]
            if (o.get("request_schema") or {}) != (n.get("request_schema") or {}):
                item = {"type": "request_schema_changed", "method": key[0], "path": key[1]}
                changes.append(item)
                breaking.append(item)
            if (o.get("response_schema") or {}) != (n.get("response_schema") or {}):
                item = {"type": "response_schema_changed", "method": key[0], "path": key[1]}
                changes.append(item)
        record = SchemaChangeRecord(
            project_id=project_id,
            old_snapshot_id=old_id,
            new_snapshot_id=new_id,
            changes=changes,
            breaking_changes=breaking,
            is_breaking=bool(breaking),
        )
        db.add(record)
        await db.flush()
        return record

    async def list_changes(self, db: AsyncSession, project_id: int) -> list[SchemaChangeRecord]:
        return list(
            (
                await db.scalars(
                    select(SchemaChangeRecord)
                    .where(SchemaChangeRecord.project_id == project_id)
                    .order_by(SchemaChangeRecord.id.desc())
                )
            ).all()
        )

    async def upsert_rule(self, db: AsyncSession, project_id: int, payload: dict[str, Any]) -> APIContractRule:
        rule_id = payload.get("id")
        rule = await db.get(APIContractRule, rule_id) if rule_id else None
        if rule is None:
            rule = APIContractRule(
                project_id=project_id,
                case_id=int(payload["case_id"]),
                snapshot_id=int(payload["snapshot_id"]),
                endpoint_path=str(payload["endpoint_path"]),
                method=str(payload["method"]).upper(),
            )
            db.add(rule)
        for key in (
            "case_id",
            "snapshot_id",
            "endpoint_path",
            "method",
            "validate_request",
            "validate_response",
            "strict_mode",
            "is_active",
        ):
            if key in payload and payload[key] is not None:
                setattr(rule, key, payload[key] if key != "method" else str(payload[key]).upper())
        await db.flush()
        return rule

    async def list_rules(self, db: AsyncSession, project_id: int) -> list[APIContractRule]:
        return list(
            (
                await db.scalars(
                    select(APIContractRule)
                    .where(APIContractRule.project_id == project_id)
                    .order_by(APIContractRule.id.desc())
                )
            ).all()
        )

    async def validate_response(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        case_id: int,
        method: str,
        path: str,
        status_code: int,
        response_body: Any,
    ) -> dict[str, Any]:
        rule = await db.scalar(
            select(APIContractRule).where(
                APIContractRule.project_id == project_id,
                APIContractRule.case_id == case_id,
                APIContractRule.is_active.is_(True),
            )
        )
        if rule is None:
            return {"valid": True, "skipped": True, "reason": "no_rule"}
        snapshot = await self.get_snapshot(db, rule.snapshot_id)
        endpoint = None
        for item in snapshot.parsed_endpoints or []:
            if str(item.get("method", "")).upper() == method.upper() and self._path_match(
                str(item.get("path") or ""), path
            ):
                endpoint = item
                break
        if endpoint is None:
            return {
                "valid": not rule.strict_mode,
                "skipped": False,
                "errors": [f"endpoint not found in snapshot: {method} {path}"],
            }
        errors: list[str] = []
        if rule.validate_response:
            schema = (endpoint.get("responses") or {}).get(str(status_code)) or (endpoint.get("responses") or {}).get(
                "default"
            )
            if schema is None and rule.strict_mode:
                errors.append(f"status {status_code} not documented")
            elif schema and response_body is not None:
                # Lightweight type checks only (full JSON Schema optional).
                expected_type = schema.get("type")
                if expected_type == "object" and not isinstance(response_body, dict):
                    errors.append("response body expected object")
                if expected_type == "array" and not isinstance(response_body, list):
                    errors.append("response body expected array")
                required = schema.get("required") or []
                if isinstance(response_body, dict):
                    for key in required:
                        if key not in response_body:
                            errors.append(f"missing required field: {key}")
        return {"valid": not errors, "errors": errors, "endpoint": endpoint.get("path"), "rule_id": rule.id}

    async def attach_contract_validation(
        self,
        result: dict[str, Any],
        *,
        project_id: int | None,
        case_id: int | None,
        method: str | None = None,
        url: str | None = None,
        status_code: int | None = None,
        response_body: Any = None,
        db: AsyncSession | None = None,
        fail_closed: bool = True,
    ) -> dict[str, Any]:
        """Validate an HTTP execution result against active APIContractRule when case_id is known.

        Used by single-case run, debug-from-case, and free-form send when case_id is supplied.
        Mutates and returns ``result`` with ``contract_result``; on fail-closed sets success=False.
        """
        if not project_id or not case_id or not isinstance(result, dict):
            return result
        try:
            from urllib.parse import urlsplit

            req = result.get("request") if isinstance(result.get("request"), dict) else {}
            resolved_url = url or req.get("url") or result.get("request_url") or ""
            resolved_method = (
                method
                or req.get("method")
                or result.get("request_method")
                or result.get("method")
                or "GET"
            )
            resolved_status = status_code
            if resolved_status is None:
                resolved_status = result.get("status_code")
                if resolved_status is None and isinstance(result.get("response"), dict):
                    resolved_status = result["response"].get("status_code")
            body = response_body
            if body is None:
                body = result.get("response_content")
                if body is None:
                    body = result.get("data")
                if body is None:
                    body = result.get("body")
                if body is None and isinstance(result.get("response"), dict):
                    body = result["response"].get("body") or result["response"].get("json")
            path = urlsplit(str(resolved_url or "")).path or "/"

            async def _run(session: AsyncSession) -> dict[str, Any]:
                return await self.validate_response(
                    session,
                    project_id=int(project_id),
                    case_id=int(case_id),
                    method=str(resolved_method or "GET").upper(),
                    path=path,
                    status_code=int(resolved_status or 0),
                    response_body=body,
                )

            if db is not None:
                contract_result = await _run(db)
            else:
                async with AsyncSessionLocal() as session:
                    contract_result = await _run(session)
            result["contract_result"] = contract_result
            if (
                fail_closed
                and isinstance(contract_result, dict)
                and not contract_result.get("skipped")
                and contract_result.get("valid") is False
            ):
                errors = contract_result.get("errors") or ["contract validation failed"]
                message = "契约校验失败: " + "; ".join(str(e) for e in errors)
                result["success"] = False
                if result.get("error"):
                    result["error"] = f"{result['error']} | {message}"
                else:
                    result["error"] = message
                # Debug-style nested response envelope.
                if isinstance(result.get("response"), dict):
                    result["response"]["contract_valid"] = False
                    result["response"]["contract_errors"] = errors
        except Exception as exc:
            _logger.warning("contract attach skipped due to error: %s", exc)
            result.setdefault("contract_result", {"valid": True, "skipped": True, "reason": f"error:{exc}"})
        return result

    def parse_openapi(self, content: str) -> dict[str, Any]:
        data: Any
        try:
            data = json.loads(content)
        except Exception:
            try:
                import yaml  # type: ignore

                data = yaml.safe_load(content)
            except Exception as exc:
                raise ValueError(f"invalid OpenAPI content: {exc}") from exc
        if not isinstance(data, dict):
            raise ValueError("OpenAPI root must be object")
        version = str(data.get("openapi") or data.get("swagger") or "")
        endpoints: list[dict[str, Any]] = []
        paths = data.get("paths") or {}
        if isinstance(paths, dict):
            for path, methods in paths.items():
                if not isinstance(methods, dict):
                    continue
                for method, op in methods.items():
                    if method.lower() not in {"get", "post", "put", "patch", "delete", "head", "options"}:
                        continue
                    op = op or {}
                    responses = {}
                    for code, resp in (op.get("responses") or {}).items():
                        schema = (((resp or {}).get("content") or {}).get("application/json") or {}).get("schema") or {}
                        responses[str(code)] = schema if isinstance(schema, dict) else {"type": "object"}
                    req_schema = (
                        (((op.get("requestBody") or {}).get("content") or {}).get("application/json") or {}).get(
                            "schema"
                        )
                        or {}
                    )
                    endpoints.append(
                        {
                            "method": method.upper(),
                            "path": path,
                            "operation_id": op.get("operationId"),
                            "summary": op.get("summary"),
                            "request_schema": req_schema if isinstance(req_schema, dict) else {},
                            "responses": responses,
                            "response_schema": responses.get("200") or responses.get("201") or {},
                        }
                    )
        return {"version": version, "endpoints": endpoints}

    def _path_match(self, template: str, actual: str) -> bool:
        actual_path = actual.split("?")[0]
        if template == actual_path:
            return True
        # Escape literal segments independently; escaping the whole template
        # first hides `{id}` behind backslashes and makes path parameters never
        # match a concrete request such as `/users/123`.
        pattern = "/".join(
            r"[^/]+" if re.fullmatch(r"\{[^/{}]+\}", segment) else re.escape(segment)
            for segment in template.split("/")
        )
        try:
            return re.fullmatch(pattern, actual_path) is not None
        except re.error:
            return template.rstrip("/") == actual_path.rstrip("/")


contract_testing_service = ContractTestingService()


async def poll_source_urls(session_factory=None) -> int:
    """Re-fetch OpenAPI specs from source_url and create a new snapshot when content changes."""
    factory = session_factory or AsyncSessionLocal
    created = 0
    async with factory() as db:
        snapshots = list(
            (
                await db.scalars(
                    select(OpenAPISnapshot)
                    .where(OpenAPISnapshot.source_url.is_not(None))
                    .order_by(OpenAPISnapshot.id.desc())
                )
            ).all()
        )
        # Poll latest snapshot per (project_id, source_url) only.
        seen: set[tuple[int, str]] = set()
        for snap in snapshots:
            url = (snap.source_url or "").strip()
            if not url or not url.startswith(("http://", "https://")):
                continue
            key = (int(snap.project_id), url)
            if key in seen:
                continue
            seen.add(key)
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    resp = await client.get(url)
                    resp.raise_for_status()
                    content = resp.text
                if not content.strip():
                    continue
                if _content_hash(content) == (snap.content_hash or ""):
                    continue
                await contract_testing_service.create_snapshot(
                    db,
                    project_id=int(snap.project_id),
                    spec_content=content,
                    source_url=url,
                    source_type="poll",
                    group_id=snap.group_id,
                )
                created += 1
            except Exception:
                _logger.exception("contract source_url poll failed project=%s url=%s", snap.project_id, url)
        await db.commit()
    return created


async def _poll_loop() -> None:
    while True:
        await asyncio.sleep(_POLL_LOOP_SECONDS)
        try:
            await poll_source_urls()
        except Exception:
            _logger.exception("contract poll worker loop failed")


async def start_contract_poll_worker() -> None:
    global _poll_task
    try:
        await poll_source_urls()
    except Exception:
        _logger.exception("initial contract poll failed")
    if _poll_task is None or _poll_task.done():
        _poll_task = asyncio.create_task(_poll_loop(), name="contract-source-poll-worker")


async def stop_contract_poll_worker() -> None:
    global _poll_task
    if _poll_task is not None:
        _poll_task.cancel()
        try:
            await _poll_task
        except asyncio.CancelledError:
            pass
        _poll_task = None
