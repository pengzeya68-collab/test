"""Element repository and locator healing service."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.feature_upgrades import (
    HealingConfig,
    HealingRecord,
    UIElement,
    UIPage,
    UIStepElementRef,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class HealingCandidate:
    locator: dict[str, Any]
    score: float
    reason: str


@dataclass
class HealingResult:
    healed_locator: dict[str, Any] | None
    confidence: float
    strategy_used: str | None
    candidates: list[HealingCandidate] = field(default_factory=list)
    status: str = "failed"


class ElementRepositoryService:
    async def list_pages(self, db: AsyncSession, project_id: int) -> list[UIPage]:
        return list(
            (
                await db.scalars(
                    select(UIPage).where(UIPage.project_id == project_id).order_by(UIPage.sort_order, UIPage.id)
                )
            ).all()
        )

    async def create_page(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        name: str,
        user_id: int,
        description: str | None = None,
        url_pattern: str | None = None,
        parent_id: int | None = None,
        sort_order: int = 0,
    ) -> UIPage:
        page = UIPage(
            project_id=project_id,
            name=name.strip(),
            description=description,
            url_pattern=url_pattern,
            parent_id=parent_id,
            sort_order=sort_order,
            created_by=user_id,
        )
        db.add(page)
        await db.flush()
        return page

    async def list_elements(self, db: AsyncSession, *, project_id: int, page_id: int | None = None) -> list[UIElement]:
        stmt = select(UIElement).where(UIElement.project_id == project_id, UIElement.is_deprecated.is_(False))
        if page_id is not None:
            stmt = stmt.where(UIElement.page_id == page_id)
        return list((await db.scalars(stmt.order_by(UIElement.name))).all())

    async def create_element(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        page_id: int,
        name: str,
        locators: list[dict[str, Any]],
        user_id: int,
        description: str | None = None,
        frame_path: list[str] | None = None,
        tags: list[str] | None = None,
        thumbnail_path: str | None = None,
    ) -> UIElement:
        if not locators:
            raise ValueError("locators required")
        element = UIElement(
            project_id=project_id,
            page_id=page_id,
            name=name.strip(),
            description=description,
            locators=locators,
            frame_path=frame_path or [],
            tags=tags or [],
            thumbnail_path=thumbnail_path,
            created_by=user_id,
        )
        db.add(element)
        await db.flush()
        return element

    async def update_element(self, db: AsyncSession, element_id: int, payload: dict[str, Any]) -> UIElement:
        element = await db.get(UIElement, element_id)
        if element is None:
            raise LookupError("element not found")
        for key in ("name", "description", "locators", "frame_path", "tags", "thumbnail_path", "is_deprecated"):
            if key in payload:
                setattr(element, key, payload[key])
        element.updated_at = _utcnow()
        await db.flush()
        return element

    async def bind_step_element(
        self,
        db: AsyncSession,
        *,
        step_id: str,
        element_id: int,
        override_locators: list[dict[str, Any]] | None = None,
    ) -> UIStepElementRef:
        existing = await db.scalar(
            select(UIStepElementRef).where(
                UIStepElementRef.step_id == step_id, UIStepElementRef.element_id == element_id
            )
        )
        if existing:
            existing.override_locators = override_locators
            await db.flush()
            return existing
        ref = UIStepElementRef(step_id=step_id, element_id=element_id, override_locators=override_locators)
        db.add(ref)
        element = await db.get(UIElement, element_id)
        if element:
            element.usage_count = int(element.usage_count or 0) + 1
            element.last_used_at = _utcnow()
        await db.flush()
        return ref

    async def get_or_create_healing_config(self, db: AsyncSession, project_id: int) -> HealingConfig:
        config = await db.scalar(select(HealingConfig).where(HealingConfig.project_id == project_id))
        if config:
            return config
        config = HealingConfig(project_id=project_id)
        db.add(config)
        await db.flush()
        return config

    async def heal(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        original_locator: dict[str, Any],
        page_dom: str,
        page_url: str | None = None,
        element_id: int | None = None,
        run_id: int | None = None,
        step_result_id: int | None = None,
        failure_reason: str = "",
    ) -> HealingResult:
        config = await self.get_or_create_healing_config(db, project_id)
        if not config.enabled:
            return HealingResult(healed_locator=None, confidence=0.0, strategy_used=None, status="failed")

        element = await db.get(UIElement, element_id) if element_id else None
        locator = original_locator or ((element.locators or [None])[0] if element else {}) or {}
        candidates: list[HealingCandidate] = []

        target_text = str((locator.get("options") or {}).get("name") or locator.get("value") or "").strip()
        if target_text:
            for match in self._find_by_text(page_dom, target_text)[: config.max_candidates]:
                score = self._text_similarity(match["text"], target_text) * 0.95
                candidates.append(
                    HealingCandidate(locator=match["locator"], score=score, reason=f"文本匹配: {match['text'][:80]}")
                )

        for match in self._find_by_attributes(page_dom, locator)[: config.max_candidates]:
            candidates.append(
                HealingCandidate(
                    locator=match["locator"],
                    score=float(match["similarity"]) * 0.9,
                    reason=f"属性相似: {match['matched_attr']}={match['matched_value']}",
                )
            )

        for match in self._find_by_css_hint(page_dom, locator)[: config.max_candidates]:
            candidates.append(
                HealingCandidate(
                    locator=match["locator"],
                    score=float(match["score"]) * 0.75,
                    reason=match["reason"],
                )
            )

        candidates.sort(key=lambda item: item.score, reverse=True)
        best = candidates[0] if candidates else None
        # auto_applied = high confidence for THIS RUN only.
        # Never silently mutate shared element-repository assets unless the
        # project explicitly opts in via HealingConfig.auto_mutate_assets.
        allow_mutate_assets = bool(getattr(config, "auto_mutate_assets", False))
        if best and best.score >= config.auto_apply_threshold:
            status = "auto_applied"
            if element is not None and allow_mutate_assets:
                await self._apply_heal(element, best.locator)
        elif best and best.score >= config.suggest_threshold:
            status = "suggested"
        else:
            status = "failed"

        result = HealingResult(
            healed_locator=best.locator if best else None,
            confidence=best.score if best else 0.0,
            strategy_used=best.reason if best else None,
            candidates=candidates[: config.max_candidates],
            status=status,
        )
        record = HealingRecord(
            project_id=project_id,
            element_id=element_id,
            run_id=run_id,
            step_result_id=step_result_id,
            original_locator=locator,
            failure_reason=failure_reason or "locator not found",
            page_url=(page_url or "")[:2000] or None,
            healed_locator=result.healed_locator,
            confidence=result.confidence,
            strategy_used=result.strategy_used,
            candidates=[{"locator": c.locator, "score": c.score, "reason": c.reason} for c in result.candidates],
            status=result.status,
        )
        db.add(record)
        await db.flush()
        return result

    async def list_healing_records(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        status: str | None = None,
        element_id: int | None = None,
        limit: int = 100,
    ) -> list[HealingRecord]:
        stmt = (
            select(HealingRecord)
            .where(HealingRecord.project_id == project_id)
            .order_by(HealingRecord.id.desc())
            .limit(max(1, min(limit, 500)))
        )
        if status:
            stmt = stmt.where(HealingRecord.status == status)
        if element_id is not None:
            stmt = stmt.where(HealingRecord.element_id == element_id)
        return list((await db.scalars(stmt)).all())

    async def review_healing(
        self,
        db: AsyncSession,
        record_id: int,
        *,
        action: str,
        user_id: int,
    ) -> HealingRecord:
        record = await db.get(HealingRecord, record_id)
        if record is None:
            raise LookupError("healing record not found")
        if action == "apply":
            if record.element_id and record.healed_locator:
                element = await db.get(UIElement, record.element_id)
                if element:
                    await self._apply_heal(element, record.healed_locator)
            record.status = "auto_applied"
        elif action == "reject":
            record.status = "rejected"
        else:
            raise ValueError("unsupported action")
        record.reviewed_by = user_id
        record.reviewed_at = _utcnow()
        await db.flush()
        return record

    async def _apply_heal(self, element: UIElement, healed_locator: dict[str, Any]) -> None:
        locators = list(element.locators or [])
        # put healed locator first, keep previous as fallback
        locators = [healed_locator] + [item for item in locators if item != healed_locator]
        element.locators = locators[:10]
        element.heal_count = int(element.heal_count or 0) + 1
        element.updated_at = _utcnow()

    def _find_by_text(self, dom_html: str, target_text: str) -> list[dict[str, Any]]:
        try:
            from bs4 import BeautifulSoup
        except Exception:
            return self._regex_text_fallback(dom_html, target_text)

        soup = BeautifulSoup(dom_html[:500_000], "html.parser")
        results: list[dict[str, Any]] = []
        for node in soup.find_all(string=lambda value: bool(value) and target_text.lower() in str(value).lower()):
            parent = node.parent
            if parent is None or parent.name not in {"button", "a", "span", "div", "label", "input", "li", "td", "th"}:
                continue
            results.append({"text": str(node).strip(), "locator": self._generate_locator_for_element(parent)})
        return results

    def _regex_text_fallback(self, dom_html: str, target_text: str) -> list[dict[str, Any]]:
        pattern = re.compile(re.escape(target_text), re.I)
        if not pattern.search(dom_html):
            return []
        return [
            {
                "text": target_text,
                "locator": {"strategy": "text", "value": target_text, "options": {}, "fallbacks": [], "framePath": []},
            }
        ]

    def _find_by_attributes(self, dom_html: str, locator: dict[str, Any]) -> list[dict[str, Any]]:
        try:
            from bs4 import BeautifulSoup
        except Exception:
            return []
        soup = BeautifulSoup(dom_html[:500_000], "html.parser")
        wanted = {
            "data-testid": locator.get("value") if locator.get("strategy") == "test_id" else None,
            "aria-label": (locator.get("options") or {}).get("name"),
            "placeholder": locator.get("value")
            if locator.get("strategy") == "placeholder"
            else (locator.get("options") or {}).get("name"),
            "name": locator.get("value") if locator.get("strategy") in {"label", "css"} else None,
            "id": locator.get("value") if locator.get("strategy") == "css" else None,
        }
        results: list[dict[str, Any]] = []
        for attr, value in wanted.items():
            if not value:
                continue
            for el in soup.find_all(attrs={attr: True}):
                actual = str(el.get(attr) or "")
                similarity = self._text_similarity(actual, str(value))
                if similarity < 0.5:
                    continue
                results.append(
                    {
                        "locator": self._generate_locator_for_element(el),
                        "similarity": similarity,
                        "matched_attr": attr,
                        "matched_value": actual,
                    }
                )
        return results

    def _find_by_css_hint(self, dom_html: str, locator: dict[str, Any]) -> list[dict[str, Any]]:
        if locator.get("strategy") != "css":
            return []
        value = str(locator.get("value") or "")
        token = re.split(r"[#.\s\[\]=>:~+]", value)
        token = [item for item in token if item][:3]
        if not token:
            return []
        try:
            from bs4 import BeautifulSoup
        except Exception:
            return []
        soup = BeautifulSoup(dom_html[:500_000], "html.parser")
        results = []
        for el in soup.find_all(True):
            hay = " ".join(filter(None, [el.name, el.get("id"), " ".join(el.get("class") or []), el.get("name")]))
            hits = sum(1 for item in token if item.lower() in hay.lower())
            if hits:
                results.append(
                    {
                        "locator": self._generate_locator_for_element(el),
                        "score": hits / max(1, len(token)),
                        "reason": f"结构/类名相似: {hits}/{len(token)}",
                    }
                )
        return results

    def _generate_locator_for_element(self, el: Any) -> dict[str, Any]:
        if el.get("data-testid"):
            return {
                "strategy": "test_id",
                "value": el.get("data-testid"),
                "options": {},
                "fallbacks": [],
                "framePath": [],
            }
        if el.get("aria-label"):
            return {"strategy": "label", "value": el.get("aria-label"), "options": {}, "fallbacks": [], "framePath": []}
        role = el.get("role")
        text = ""
        try:
            text = el.get_text(" ", strip=True)[:50]
        except Exception:
            text = ""
        if role or el.name in {"button", "a", "input"}:
            inferred = role or ({"button": "button", "a": "link", "input": "textbox"}.get(el.name) or el.name)
            return {
                "strategy": "role",
                "value": inferred,
                "options": {"name": text} if text else {},
                "fallbacks": [],
                "framePath": [],
            }
        if el.get("id"):
            return {"strategy": "css", "value": f"#{el.get('id')}", "options": {}, "fallbacks": [], "framePath": []}
        classes = el.get("class") or []
        if classes:
            return {
                "strategy": "css",
                "value": f"{el.name}." + ".".join(classes[:2]),
                "options": {},
                "fallbacks": [],
                "framePath": [],
            }
        if text:
            return {"strategy": "text", "value": text, "options": {}, "fallbacks": [], "framePath": []}
        return {"strategy": "css", "value": el.name or "div", "options": {}, "fallbacks": [], "framePath": []}

    def _text_similarity(self, left: str, right: str) -> float:
        a = (left or "").strip().lower()
        b = (right or "").strip().lower()
        if not a or not b:
            return 0.0
        if a == b:
            return 1.0
        if a in b or b in a:
            return 0.85
        # simple token overlap
        sa, sb = set(re.findall(r"\w+", a)), set(re.findall(r"\w+", b))
        if not sa or not sb:
            return 0.0
        return len(sa & sb) / len(sa | sb)


element_repository_service = ElementRepositoryService()
