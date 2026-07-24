"""Defect tracker integration service with real HTTP connectors."""

from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.feature_upgrades import DefectCaseLink, DefectRecord, DefectTrackerConfig
from fastapi_backend.models.ui_automation import UIRun, UIStepResult


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class DefectIntegrationService:
    async def list_trackers(self, db: AsyncSession, project_id: int) -> list[DefectTrackerConfig]:
        return list(
            (
                await db.scalars(
                    select(DefectTrackerConfig)
                    .where(DefectTrackerConfig.project_id == project_id, DefectTrackerConfig.is_active.is_(True))
                    .order_by(DefectTrackerConfig.id.desc())
                )
            ).all()
        )

    async def upsert_tracker(self, db: AsyncSession, project_id: int, payload: dict[str, Any]) -> DefectTrackerConfig:
        tracker_id = payload.get("id")
        tracker = await db.get(DefectTrackerConfig, tracker_id) if tracker_id else None
        if tracker is None:
            tracker = DefectTrackerConfig(
                project_id=project_id, tracker_type=payload["tracker_type"], base_url=payload["base_url"]
            )
            db.add(tracker)
        for key in (
            "tracker_type",
            "base_url",
            "credentials_encrypted",
            "project_key",
            "custom_fields_mapping",
            "default_issue_type",
            "default_priority",
            "is_active",
        ):
            if key in payload:
                setattr(tracker, key, payload[key])
        tracker.updated_at = _utcnow()
        await db.flush()
        return tracker

    async def create_from_failure(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        user_id: int,
        step_result_id: int | None = None,
        run_id: int | None = None,
        title: str | None = None,
        description: str | None = None,
        priority: str | None = None,
        severity: str | None = None,
        tracker_config_id: int | None = None,
        case_type: str = "ui",
        case_id: int | None = None,
    ) -> DefectRecord:
        step_result = await db.get(UIStepResult, step_result_id) if step_result_id else None
        run = (
            await db.get(UIRun, run_id or (step_result.run_id if step_result else None))
            if (run_id or step_result)
            else None
        )
        case_name = f"case#{run.case_id}" if run and run.case_id else "unknown-case"
        step_name = step_result.step_id if step_result else "unknown-step"
        error = (step_result.error_message if step_result else None) or (run.error_summary if run else "") or ""
        auto_title = title or f"[自动化] {case_name} - {step_name} 执行失败"
        auto_description = description or self._build_description(
            case_name=case_name,
            step_name=step_name,
            error=error,
            environment=str(run.environment_id if run else ""),
            run_url=f"/ui-automation/runs/{run.id}" if run else "",
            screenshot_url="",
            trace_url=f"/ui-automation/traces?run_id={run.id}" if run else "",
        )

        tracker = None
        if tracker_config_id:
            tracker = await db.get(DefectTrackerConfig, tracker_config_id)
        if tracker is None:
            trackers = await self.list_trackers(db, project_id)
            tracker = trackers[0] if trackers else None

        external_id = None
        external_url = None
        push_error = None
        if tracker:
            try:
                external_id, external_url = await self._push_external(
                    tracker, auto_title, auto_description, priority, severity
                )
            except Exception as exc:
                push_error = str(exc)

        record = DefectRecord(
            project_id=project_id,
            tracker_config_id=tracker.id if tracker else None,
            external_id=external_id,
            external_url=external_url,
            title=auto_title,
            description=auto_description + (f"\n\n> Tracker push failed: {push_error}" if push_error else ""),
            status="open" if not push_error else "open",
            priority=priority or (tracker.default_priority if tracker else None),
            severity=severity,
            source_type="ui_run" if run else "manual",
            source_run_id=run.id if run else None,
            source_step_result_id=step_result.id if step_result else None,
            attachments=[{"push_error": push_error}] if push_error else [],
            created_by=user_id,
            synced_at=_utcnow() if external_id and not push_error else None,
        )
        db.add(record)
        await db.flush()
        if case_id is not None or (run and run.case_id):
            db.add(
                DefectCaseLink(
                    defect_id=record.id,
                    case_type=case_type,
                    case_id=int(case_id or run.case_id),
                    linked_by=user_id,
                )
            )
            await db.flush()
        if push_error and tracker:
            # Keep local record, but make failure visible to callers.
            record.attachments = [{"push_error": push_error, "tracker_type": tracker.tracker_type}]
            await db.flush()
        return record

    async def list_defects(self, db: AsyncSession, project_id: int, status: str | None = None) -> list[DefectRecord]:
        stmt = (
            select(DefectRecord).where(DefectRecord.project_id == project_id).order_by(DefectRecord.created_at.desc())
        )
        if status:
            stmt = stmt.where(DefectRecord.status == status)
        return list((await db.scalars(stmt)).all())

    def _parse_credentials(self, tracker: DefectTrackerConfig) -> dict[str, Any]:
        raw = tracker.credentials_encrypted or ""
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except Exception:
            # allow token-only plaintext for simple setups
            return {"token": raw}

    async def _push_external(
        self,
        tracker: DefectTrackerConfig,
        title: str,
        description: str,
        priority: str | None,
        severity: str | None,
    ) -> tuple[str | None, str | None]:
        tracker_type = (tracker.tracker_type or "").lower()
        creds = self._parse_credentials(tracker)
        if tracker_type == "local":
            slug = f"TM-LOCAL-{int(_utcnow().timestamp())}"
            return slug, f"{tracker.base_url.rstrip('/')}/defects/{slug}"
        if tracker_type == "webhook":
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.post(
                    tracker.base_url,
                    json={
                        "title": title,
                        "description": description,
                        "priority": priority,
                        "severity": severity,
                        "project_key": tracker.project_key,
                    },
                    headers=self._auth_headers(creds),
                )
                resp.raise_for_status()
                data = resp.json() if resp.content else {}
                return str(data.get("id") or data.get("key") or f"WH-{int(_utcnow().timestamp())}"), data.get(
                    "url"
                ) or tracker.base_url
        if tracker_type == "jira":
            return await self._push_jira(tracker, creds, title, description, priority)
        if tracker_type == "github":
            return await self._push_github(tracker, creds, title, description)
        if tracker_type == "zentao":
            return await self._push_zentao(tracker, creds, title, description, priority, severity)
        raise ValueError(f"unsupported tracker_type: {tracker.tracker_type}")

    def _auth_headers(self, creds: dict[str, Any]) -> dict[str, str]:
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        if creds.get("token"):
            headers["Authorization"] = f"Bearer {creds['token']}"
        elif creds.get("username") and creds.get("password"):
            token = base64.b64encode(f"{creds['username']}:{creds['password']}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        elif creds.get("api_token") and creds.get("email"):
            token = base64.b64encode(f"{creds['email']}:{creds['api_token']}".encode()).decode()
            headers["Authorization"] = f"Basic {token}"
        return headers

    async def _push_jira(
        self,
        tracker: DefectTrackerConfig,
        creds: dict[str, Any],
        title: str,
        description: str,
        priority: str | None,
    ) -> tuple[str, str]:
        project_key = tracker.project_key or creds.get("project_key")
        if not project_key:
            raise ValueError("Jira project_key required")
        issue_type = tracker.default_issue_type or creds.get("issue_type") or "Bug"
        fields: dict[str, Any] = {
            "project": {"key": project_key},
            "summary": title[:255],
            "description": description,
            "issuetype": {"name": issue_type},
        }
        if priority or tracker.default_priority:
            fields["priority"] = {"name": priority or tracker.default_priority}
        url = urljoin(tracker.base_url.rstrip("/") + "/", "rest/api/2/issue")
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(url, json={"fields": fields}, headers=self._auth_headers(creds))
            if resp.status_code >= 400:
                raise RuntimeError(f"Jira create failed: {resp.status_code} {resp.text[:500]}")
            data = resp.json()
        key = data.get("key") or str(data.get("id"))
        return key, f"{tracker.base_url.rstrip('/')}/browse/{key}"

    async def _push_github(
        self,
        tracker: DefectTrackerConfig,
        creds: dict[str, Any],
        title: str,
        description: str,
    ) -> tuple[str, str]:
        # base_url like https://api.github.com/repos/owner/repo or https://github.com/owner/repo
        base = tracker.base_url.rstrip("/")
        if "api.github.com" in base:
            api = base if base.endswith("/issues") else base + "/issues"
        else:
            # convert github.com/owner/repo -> api.github.com/repos/owner/repo/issues
            parts = base.replace("https://", "").replace("http://", "").split("/")
            if len(parts) >= 3 and parts[0].endswith("github.com"):
                owner, repo = parts[1], parts[2]
                api = f"https://api.github.com/repos/{owner}/{repo}/issues"
            else:
                api = base + "/issues"
        headers = self._auth_headers(creds)
        headers["Accept"] = "application/vnd.github+json"
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(api, json={"title": title, "body": description}, headers=headers)
            if resp.status_code >= 400:
                raise RuntimeError(f"GitHub create failed: {resp.status_code} {resp.text[:500]}")
            data = resp.json()
        return str(data.get("number") or data.get("id")), data.get("html_url") or api

    async def _push_zentao(
        self,
        tracker: DefectTrackerConfig,
        creds: dict[str, Any],
        title: str,
        description: str,
        priority: str | None,
        severity: str | None,
    ) -> tuple[str, str]:
        # ZenTao open API varies by version; support token header style.
        product = tracker.project_key or creds.get("product") or "1"
        api = urljoin(tracker.base_url.rstrip("/") + "/", f"api.php/v1/products/{product}/bugs")
        payload = {
            "title": title,
            "steps": description,
            "pri": priority or tracker.default_priority or "3",
            "severity": severity or "3",
        }
        headers = self._auth_headers(creds)
        if creds.get("token") and "Token" not in headers:
            headers["Token"] = str(creds["token"])
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(api, json=payload, headers=headers)
            if resp.status_code >= 400:
                raise RuntimeError(f"ZenTao create failed: {resp.status_code} {resp.text[:500]}")
            data = resp.json() if resp.content else {}
        bug_id = str(
            (data.get("id") if isinstance(data, dict) else None)
            or data.get("data", {}).get("id")
            or f"ZT-{int(_utcnow().timestamp())}"
        )
        return bug_id, f"{tracker.base_url.rstrip('/')}/bug-view-{bug_id}.html"

    def _build_description(self, **kwargs: Any) -> str:
        return (
            "## 缺陷信息（自动生成）\n\n"
            f"**用例名称**: {kwargs.get('case_name')}\n"
            f"**失败步骤**: {kwargs.get('step_name')}\n"
            f"**错误信息**: `{kwargs.get('error')}`\n"
            f"**执行环境**: {kwargs.get('environment')}\n"
            f"**执行记录**: {kwargs.get('run_url')}\n"
            f"**截图**: {kwargs.get('screenshot_url')}\n"
            f"**Trace**: {kwargs.get('trace_url')}\n\n"
            "---\n*此缺陷由 TestMaster 自动化测试平台生成*\n"
        )


defect_integration_service = DefectIntegrationService()
