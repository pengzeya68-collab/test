"""UI network intercept rule library."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.feature_upgrades import UINetworkRule, UINetworkRuleAssignment


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NetworkRuleService:
    async def list_rules(self, db: AsyncSession, project_id: int, *, active_only: bool = False) -> list[UINetworkRule]:
        stmt = select(UINetworkRule).where(UINetworkRule.project_id == project_id).order_by(UINetworkRule.id.desc())
        if active_only:
            stmt = stmt.where(UINetworkRule.is_active.is_(True))
        return list((await db.scalars(stmt)).all())

    async def create_rule(self, db: AsyncSession, *, project_id: int, user_id: int, payload: dict[str, Any]) -> UINetworkRule:
        rule = UINetworkRule(
            project_id=project_id,
            name=str(payload["name"]).strip(),
            description=payload.get("description"),
            url_pattern=str(payload["url_pattern"]),
            pattern_type=payload.get("pattern_type") or "glob",
            method_filter=payload.get("method_filter"),
            resource_type=payload.get("resource_type"),
            action=payload.get("action") or "fulfill",
            fulfill_status=payload.get("fulfill_status"),
            fulfill_headers=payload.get("fulfill_headers"),
            fulfill_body=payload.get("fulfill_body"),
            fulfill_content_type=payload.get("fulfill_content_type"),
            modify_headers=payload.get("modify_headers"),
            modify_body_jsonpath=payload.get("modify_body_jsonpath"),
            delay_ms=payload.get("delay_ms"),
            abort_reason=payload.get("abort_reason"),
            source=payload.get("source") or "manual",
            mock_rule_id=payload.get("mock_rule_id"),
            is_active=bool(payload.get("is_active", True)),
            created_by=user_id,
        )
        db.add(rule)
        await db.flush()
        return rule

    async def update_rule(self, db: AsyncSession, rule_id: int, payload: dict[str, Any]) -> UINetworkRule:
        rule = await db.get(UINetworkRule, rule_id)
        if rule is None:
            raise LookupError("network rule not found")
        for key in (
            "name",
            "description",
            "url_pattern",
            "pattern_type",
            "method_filter",
            "resource_type",
            "action",
            "fulfill_status",
            "fulfill_headers",
            "fulfill_body",
            "fulfill_content_type",
            "modify_headers",
            "modify_body_jsonpath",
            "delay_ms",
            "abort_reason",
            "source",
            "mock_rule_id",
            "is_active",
        ):
            if key in payload:
                setattr(rule, key, payload[key])
        await db.flush()
        return rule

    async def delete_rule(self, db: AsyncSession, rule_id: int) -> None:
        rule = await db.get(UINetworkRule, rule_id)
        if rule is None:
            raise LookupError("network rule not found")
        await db.delete(rule)
        await db.flush()

    async def assign_rule(
        self,
        db: AsyncSession,
        *,
        rule_id: int,
        target_type: str,
        target_id: int,
        priority: int = 0,
    ) -> UINetworkRuleAssignment:
        existing = await db.scalar(
            select(UINetworkRuleAssignment).where(
                UINetworkRuleAssignment.rule_id == rule_id,
                UINetworkRuleAssignment.target_type == target_type,
                UINetworkRuleAssignment.target_id == target_id,
            )
        )
        if existing:
            existing.priority = priority
            await db.flush()
            return existing
        item = UINetworkRuleAssignment(
            rule_id=rule_id,
            target_type=target_type,
            target_id=target_id,
            priority=priority,
        )
        db.add(item)
        await db.flush()
        return item

    async def rules_for_target(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        target_type: str,
        target_id: int,
    ) -> list[UINetworkRule]:
        assignments = list(
            (
                await db.scalars(
                    select(UINetworkRuleAssignment)
                    .where(
                        UINetworkRuleAssignment.target_type == target_type,
                        UINetworkRuleAssignment.target_id == target_id,
                    )
                    .order_by(UINetworkRuleAssignment.priority.desc(), UINetworkRuleAssignment.id)
                )
            ).all()
        )
        if not assignments:
            return []
        rule_ids = [a.rule_id for a in assignments]
        rules = list(
            (
                await db.scalars(
                    select(UINetworkRule).where(
                        UINetworkRule.id.in_(rule_ids),
                        UINetworkRule.project_id == project_id,
                        UINetworkRule.is_active.is_(True),
                    )
                )
            ).all()
        )
        by_id = {r.id: r for r in rules}
        return [by_id[rid] for rid in rule_ids if rid in by_id]

    def to_agent_payload(self, rules: list[UINetworkRule]) -> list[dict[str, Any]]:
        payload = []
        for rule in rules:
            payload.append(
                {
                    "id": rule.id,
                    "name": rule.name,
                    "urlPattern": rule.url_pattern,
                    "patternType": rule.pattern_type,
                    "method": rule.method_filter,
                    "resourceType": rule.resource_type,
                    "action": rule.action,
                    "status": rule.fulfill_status,
                    "headers": rule.fulfill_headers or rule.modify_headers,
                    "body": rule.fulfill_body,
                    "contentType": rule.fulfill_content_type,
                    "delayMs": rule.delay_ms,
                    "abortReason": rule.abort_reason,
                }
            )
        return payload


network_rule_service = NetworkRuleService()
