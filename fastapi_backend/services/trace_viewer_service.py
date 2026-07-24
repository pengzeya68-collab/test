"""Playwright trace.zip parsing and indexing service."""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.feature_upgrades import TraceSession


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class TraceMetadata:
    action_count: int = 0
    duration_ms: int | None = None
    actions: list[dict[str, Any]] = field(default_factory=list)
    screenshots: list[str] = field(default_factory=list)
    network: list[dict[str, Any]] = field(default_factory=list)
    console: list[dict[str, Any]] = field(default_factory=list)
    browser_version: str | None = None
    parse_errors: list[str] = field(default_factory=list)


class TraceViewerService:
    async def register_trace(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        run_id: int,
        file_path: str,
        step_result_id: int | None = None,
    ) -> TraceSession:
        path = Path(file_path)
        if not path.is_file():
            raise FileNotFoundError(file_path)
        content = path.read_bytes()
        file_hash = hashlib.sha256(content).hexdigest()
        existing = await db.scalar(
            select(TraceSession).where(TraceSession.run_id == run_id, TraceSession.file_hash == file_hash)
        )
        if existing:
            return existing
        session = TraceSession(
            project_id=project_id,
            run_id=run_id,
            step_result_id=step_result_id,
            file_path=str(path),
            file_size_bytes=len(content),
            file_hash=file_hash,
        )
        db.add(session)
        await db.flush()
        return session

    async def get_session(self, db: AsyncSession, trace_id: int) -> TraceSession:
        session = await db.get(TraceSession, trace_id)
        if session is None:
            raise LookupError("trace session not found")
        return session

    async def ensure_parsed(self, db: AsyncSession, trace_id: int) -> TraceMetadata:
        session = await self.get_session(db, trace_id)
        if session.parsed and session.parse_cache:
            cache = session.parse_cache
            return TraceMetadata(
                action_count=session.action_count or 0,
                duration_ms=session.duration_ms,
                actions=list(cache.get("actions") or []),
                screenshots=list(cache.get("screenshots") or []),
                network=list(cache.get("network") or []),
                console=list(cache.get("console") or []),
                browser_version=session.browser_version,
                parse_errors=list(cache.get("parse_errors") or []),
            )

        metadata = self.parse_trace_file(session.file_path)
        session.parsed = True
        session.action_count = metadata.action_count
        session.duration_ms = metadata.duration_ms
        session.browser_version = metadata.browser_version
        session.parse_cache = {
            "actions": metadata.actions[:2000],
            "screenshots": metadata.screenshots[:500],
            "network": metadata.network[:2000],
            "console": metadata.console[:1000],
            "parse_errors": metadata.parse_errors[:50],
        }
        await db.flush()
        return metadata

    def parse_trace_file(self, file_path: str) -> TraceMetadata:
        metadata = TraceMetadata()
        path = Path(file_path)
        if not path.is_file():
            metadata.parse_errors.append("trace file missing")
            return metadata

        try:
            with zipfile.ZipFile(path, "r") as zf:
                names = zf.namelist()
                metadata.screenshots = [
                    n for n in names if n.startswith("resources/") and n.lower().endswith((".png", ".jpeg", ".jpg"))
                ]
                trace_files = [n for n in names if n.endswith(".trace") or n.endswith(".network")]
                actions_by_id: dict[str, dict[str, Any]] = {}
                for tf in trace_files:
                    try:
                        with zf.open(tf) as handle:
                            for raw in handle:
                                try:
                                    event = json.loads(raw.decode("utf-8", errors="replace"))
                                except Exception:
                                    continue
                                self._ingest_event(event, actions_by_id, metadata)
                    except Exception as exc:
                        metadata.parse_errors.append(f"{tf}: {exc}")
                metadata.actions = sorted(
                    actions_by_id.values(),
                    key=lambda item: float(item.get("start_time") or 0),
                )
                metadata.action_count = len(metadata.actions)
                metadata.duration_ms = self._calc_duration(metadata.actions)
        except zipfile.BadZipFile:
            metadata.parse_errors.append("invalid zip")
        except Exception as exc:
            metadata.parse_errors.append(str(exc))
        return metadata

    def _ingest_event(
        self, event: dict[str, Any], actions_by_id: dict[str, dict[str, Any]], metadata: TraceMetadata
    ) -> None:
        event_type = event.get("type")
        if event_type == "before-call":
            call_id = str(event.get("callId") or event.get("id") or len(actions_by_id))
            actions_by_id[call_id] = {
                "id": call_id,
                "method": event.get("method") or event.get("apiName") or "unknown",
                "api_name": event.get("apiName"),
                "params": self._redact_params(event.get("params") or {}),
                "start_time": event.get("startTime") or event.get("time"),
                "snapshot": event.get("snapshot"),
                "screenshot": event.get("screenshot"),
            }
        elif event_type == "after-call":
            call_id = str(event.get("callId") or event.get("id") or "")
            action = actions_by_id.get(call_id)
            if action:
                end_time = event.get("endTime") or event.get("time")
                action["end_time"] = end_time
                start = action.get("start_time")
                if isinstance(start, (int, float)) and isinstance(end_time, (int, float)):
                    action["duration_ms"] = max(0, int(end_time - start))
                if event.get("error"):
                    action["error"] = event.get("error")
        elif event_type in {"resource-snapshot", "frame-snapshot"}:
            pass
        elif event_type == "console":
            metadata.console.append(
                {
                    "level": event.get("level") or event.get("type") or "log",
                    "text": str(event.get("text") or event.get("message") or "")[:2000],
                    "time": event.get("time") or event.get("timestamp"),
                }
            )
        elif event_type in {"request", "response", "event"} and (
            "url" in event or "requestUrl" in event or event.get("class") == "Network"
        ):
            metadata.network.append(
                {
                    "method": event.get("method") or event.get("requestMethod"),
                    "url": event.get("url") or event.get("requestUrl"),
                    "status": event.get("status") or event.get("statusCode"),
                    "duration_ms": event.get("duration") or event.get("duration_ms"),
                    "resource_type": event.get("resourceType") or event.get("type"),
                    "time": event.get("time") or event.get("timestamp") or event.get("startTime"),
                }
            )
        if not metadata.browser_version:
            browser = (
                event.get("browserName") or event.get("browser") or (event.get("contextOptions") or {}).get("userAgent")
            )
            if browser:
                metadata.browser_version = str(browser)[:50]

    def _calc_duration(self, actions: list[dict[str, Any]]) -> int | None:
        starts = [float(a["start_time"]) for a in actions if isinstance(a.get("start_time"), (int, float))]
        ends = [
            float(a.get("end_time") or a.get("start_time"))
            for a in actions
            if isinstance(a.get("end_time"), (int, float)) or isinstance(a.get("start_time"), (int, float))
        ]
        if not starts or not ends:
            return None
        return max(0, int(max(ends) - min(starts)))

    def _redact_params(self, params: Any) -> Any:
        if isinstance(params, dict):
            redacted = {}
            for key, value in params.items():
                if any(
                    token in str(key).lower() for token in ("password", "token", "secret", "authorization", "cookie")
                ):
                    redacted[key] = "[REDACTED]"
                else:
                    redacted[key] = self._redact_params(value)
            return redacted
        if isinstance(params, list):
            return [self._redact_params(item) for item in params[:50]]
        if isinstance(params, str) and len(params) > 500:
            return params[:500] + "…"
        return params

    async def get_resource_bytes(self, db: AsyncSession, trace_id: int, resource_name: str) -> bytes:
        session = await self.get_session(db, trace_id)
        with zipfile.ZipFile(session.file_path, "r") as zf:
            if resource_name not in zf.namelist():
                raise LookupError("resource not found")
            return zf.read(resource_name)

    async def get_snapshot_html(self, db: AsyncSession, trace_id: int, action_id: str) -> str:
        metadata = await self.ensure_parsed(db, trace_id)
        action = next((item for item in metadata.actions if str(item.get("id")) == str(action_id)), None)
        if not action:
            return ""
        snapshot = action.get("snapshot")
        if isinstance(snapshot, str) and snapshot:
            try:
                return (await self.get_resource_bytes(db, trace_id, snapshot)).decode("utf-8", errors="replace")
            except Exception:
                return ""
        # fallback: first html resource
        session = await self.get_session(db, trace_id)
        with zipfile.ZipFile(session.file_path, "r") as zf:
            for name in zf.namelist():
                if name.endswith(".html"):
                    return zf.read(name).decode("utf-8", errors="replace")
        return ""

    async def get_screenshot(self, db: AsyncSession, trace_id: int, action_id: str) -> bytes:
        metadata = await self.ensure_parsed(db, trace_id)
        action = next((item for item in metadata.actions if str(item.get("id")) == str(action_id)), None)
        resource = None
        if action and isinstance(action.get("screenshot"), str):
            resource = action["screenshot"]
        elif metadata.screenshots:
            # map by action order if no explicit link
            try:
                index = next(i for i, item in enumerate(metadata.actions) if str(item.get("id")) == str(action_id))
                resource = metadata.screenshots[min(index, len(metadata.screenshots) - 1)]
            except StopIteration:
                resource = metadata.screenshots[0]
        if not resource:
            return b""
        return await self.get_resource_bytes(db, trace_id, resource)


trace_viewer_service = TraceViewerService()
