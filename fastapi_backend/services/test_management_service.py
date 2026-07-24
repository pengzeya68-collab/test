"""Case review, requirements traceability, flow graphs, report templates."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.feature_upgrades import (
    CaseReview,
    CaseReviewAction,
    CaseReviewComment,
    ReportTemplate,
    Requirement,
    RequirementCaseLink,
    ScenarioFlowGraph,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestManagementService:
    # ---------- Flow graph ----------
    async def get_flow(self, db: AsyncSession, scenario_id: int) -> ScenarioFlowGraph | None:
        return await db.scalar(select(ScenarioFlowGraph).where(ScenarioFlowGraph.scenario_id == scenario_id))

    async def save_flow(
        self,
        db: AsyncSession,
        *,
        scenario_id: int,
        nodes: list[dict[str, Any]],
        edges: list[dict[str, Any]],
        viewport: dict[str, Any] | None = None,
    ) -> ScenarioFlowGraph:
        graph = await self.get_flow(db, scenario_id)
        if graph is None:
            graph = ScenarioFlowGraph(scenario_id=scenario_id, nodes=nodes, edges=edges, viewport=viewport, version=1)
            db.add(graph)
        else:
            graph.nodes = nodes
            graph.edges = edges
            graph.viewport = viewport
            graph.version = int(graph.version or 1) + 1
            graph.updated_at = _utcnow()
        await db.flush()
        return graph

    # ---------- Reviews ----------
    async def create_review(
        self,
        db: AsyncSession,
        *,
        project_id: int,
        case_type: str,
        case_id: int,
        user_id: int,
        case_version: int | None = None,
        required_approvals: int = 1,
    ) -> CaseReview:
        review = CaseReview(
            project_id=project_id,
            case_type=case_type,
            case_id=case_id,
            case_version=case_version,
            state="pending_review",
            submitted_by=user_id,
            submitted_at=_utcnow(),
            required_approvals=max(1, required_approvals),
            current_approvals=0,
        )
        db.add(review)
        await db.flush()
        db.add(CaseReviewAction(review_id=review.id, actor_id=user_id, action="submit", comment=None))
        await db.flush()
        return review

    async def list_reviews(
        self,
        db: AsyncSession,
        project_id: int,
        *,
        state: str | None = None,
    ) -> list[CaseReview]:
        stmt = select(CaseReview).where(CaseReview.project_id == project_id).order_by(CaseReview.id.desc())
        if state:
            stmt = stmt.where(CaseReview.state == state)
        return list((await db.scalars(stmt)).all())

    async def add_comment(
        self,
        db: AsyncSession,
        *,
        review_id: int,
        user_id: int,
        content: str,
        step_id: str | None = None,
    ) -> CaseReviewComment:
        review = await db.get(CaseReview, review_id)
        if review is None:
            raise LookupError("review not found")
        comment = CaseReviewComment(
            review_id=review_id,
            author_id=user_id,
            content=content,
            step_id=step_id,
        )
        db.add(comment)
        await db.flush()
        return comment

    async def review_action(
        self,
        db: AsyncSession,
        *,
        review_id: int,
        user_id: int,
        action: str,
        comment: str | None = None,
    ) -> CaseReview:
        review = await db.get(CaseReview, review_id)
        if review is None:
            raise LookupError("review not found")
        action = action.lower()
        if action not in {"approve", "request_changes", "reject", "cancel"}:
            raise ValueError("invalid action")
        if review.state not in {"pending_review", "changes_requested"}:
            raise ValueError("review is not actionable")
        if action == "approve":
            review.current_approvals = int(review.current_approvals or 0) + 1
            if review.current_approvals >= int(review.required_approvals or 1):
                review.state = "approved"
            else:
                review.state = "pending_review"
        elif action == "request_changes":
            review.state = "changes_requested"
        elif action == "reject":
            review.state = "rejected"
        elif action == "cancel":
            review.state = "cancelled"
        review.updated_at = _utcnow()
        db.add(CaseReviewAction(review_id=review.id, actor_id=user_id, action=action, comment=comment))
        if comment:
            db.add(CaseReviewComment(review_id=review.id, author_id=user_id, content=comment))
        await db.flush()
        return review

    async def list_comments(self, db: AsyncSession, review_id: int) -> list[CaseReviewComment]:
        return list(
            (
                await db.scalars(
                    select(CaseReviewComment)
                    .where(CaseReviewComment.review_id == review_id)
                    .order_by(CaseReviewComment.id)
                )
            ).all()
        )

    # ---------- Requirements ----------
    async def create_requirement(self, db: AsyncSession, project_id: int, payload: dict[str, Any]) -> Requirement:
        req = Requirement(
            project_id=project_id,
            external_id=payload.get("external_id"),
            external_url=payload.get("external_url"),
            title=str(payload["title"]).strip(),
            description=payload.get("description"),
            priority=payload.get("priority"),
            status=payload.get("status") or "open",
            sprint=payload.get("sprint"),
        )
        db.add(req)
        await db.flush()
        return req

    async def list_requirements(self, db: AsyncSession, project_id: int) -> list[Requirement]:
        return list(
            (
                await db.scalars(
                    select(Requirement).where(Requirement.project_id == project_id).order_by(Requirement.id.desc())
                )
            ).all()
        )

    async def link_case(
        self,
        db: AsyncSession,
        *,
        requirement_id: int,
        case_type: str,
        case_id: int,
        coverage_type: str = "functional",
    ) -> RequirementCaseLink:
        existing = await db.scalar(
            select(RequirementCaseLink).where(
                RequirementCaseLink.requirement_id == requirement_id,
                RequirementCaseLink.case_type == case_type,
                RequirementCaseLink.case_id == case_id,
            )
        )
        if existing:
            existing.coverage_type = coverage_type
            await db.flush()
            return existing
        link = RequirementCaseLink(
            requirement_id=requirement_id,
            case_type=case_type,
            case_id=case_id,
            coverage_type=coverage_type,
        )
        db.add(link)
        await db.flush()
        return link

    async def coverage_matrix(self, db: AsyncSession, project_id: int) -> dict[str, Any]:
        reqs = await self.list_requirements(db, project_id)
        links = list(
            (
                await db.scalars(
                    select(RequirementCaseLink).where(
                        RequirementCaseLink.requirement_id.in_([r.id for r in reqs] or [-1])
                    )
                )
            ).all()
        )
        by_req: dict[int, list[dict[str, Any]]] = {}
        for link in links:
            by_req.setdefault(link.requirement_id, []).append(
                {
                    "case_type": link.case_type,
                    "case_id": link.case_id,
                    "coverage_type": link.coverage_type,
                }
            )
        items = []
        covered = 0
        for req in reqs:
            cases = by_req.get(req.id) or []
            if cases:
                covered += 1
            items.append(
                {
                    "requirement": {
                        "id": req.id,
                        "title": req.title,
                        "status": req.status,
                        "priority": req.priority,
                        "external_id": req.external_id,
                    },
                    "cases": cases,
                    "covered": bool(cases),
                }
            )
        total = len(reqs) or 1
        return {
            "items": items,
            "total_requirements": len(reqs),
            "covered_requirements": covered,
            "coverage_rate": round(covered / total * 100.0, 2) if reqs else 0.0,
        }

    # ---------- Report templates ----------
    async def list_templates(self, db: AsyncSession, project_id: int) -> list[ReportTemplate]:
        return list(
            (
                await db.scalars(
                    select(ReportTemplate)
                    .where(ReportTemplate.project_id == project_id)
                    .order_by(ReportTemplate.id.desc())
                )
            ).all()
        )

    async def upsert_template(self, db: AsyncSession, project_id: int, payload: dict[str, Any]) -> ReportTemplate:
        template_id = payload.get("id")
        template = await db.get(ReportTemplate, template_id) if template_id else None
        if template is None:
            template = ReportTemplate(project_id=project_id, name=str(payload.get("name") or "Default"))
            db.add(template)
        for key in (
            "name",
            "logo_path",
            "primary_color",
            "company_name",
            "footer_text",
            "sections",
            "custom_fields",
            "is_default",
        ):
            if key in payload and payload[key] is not None:
                setattr(template, key, payload[key])
        if payload.get("is_default"):
            others = await self.list_templates(db, project_id)
            for other in others:
                if other.id != template.id:
                    other.is_default = False
        await db.flush()
        return template

    def render_report_html(self, template: ReportTemplate, context: dict[str, Any]) -> str:
        color = template.primary_color or "#409EFF"
        company = template.company_name or "TestMaster"
        title = context.get("title") or "自动化测试报告"
        summary = context.get("summary") or {}
        sections = template.sections or ["summary", "cases", "failures", "artifacts"]
        rows = "".join(
            f"<tr><td>{item.get('name')}</td><td>{item.get('status')}</td><td>{item.get('duration_ms', '-')}</td></tr>"
            for item in (context.get("cases") or [])
        )
        failures = "".join(f"<li><strong>{f.get('name')}</strong>: {f.get('error')}</li>" for f in (context.get("failures") or []))
        body_parts = []
        if "summary" in sections:
            body_parts.append(
                f"<section><h2>摘要</h2><p>通过 {summary.get('passed', 0)} / 失败 {summary.get('failed', 0)} / 总计 {summary.get('total', 0)}</p></section>"
            )
        if "cases" in sections:
            body_parts.append(
                f"<section><h2>用例结果</h2><table><thead><tr><th>用例</th><th>状态</th><th>耗时(ms)</th></tr></thead><tbody>{rows or '<tr><td colspan=3>无数据</td></tr>'}</tbody></table></section>"
            )
        if "failures" in sections:
            body_parts.append(f"<section><h2>失败详情</h2><ul>{failures or '<li>无失败</li>'}</ul></section>")
        if "artifacts" in sections:
            arts = "".join(f"<li>{a}</li>" for a in (context.get("artifacts") or []))
            body_parts.append(f"<section><h2>产物</h2><ul>{arts or '<li>无</li>'}</ul></section>")
        footer = template.footer_text or f"Generated by {company}"
        return f"""<!doctype html>
<html><head><meta charset="utf-8"/><title>{title}</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;margin:24px;color:#0f172a}}
h1{{color:{color}}} table{{border-collapse:collapse;width:100%}}
th,td{{border:1px solid #e2e8f0;padding:8px;text-align:left}} th{{background:#f8fafc}}
footer{{margin-top:32px;color:#64748b;font-size:12px}}
</style></head>
<body>
<header><h1>{title}</h1><div>{company}</div></header>
{''.join(body_parts)}
<footer>{footer}</footer>
</body></html>"""


test_management_service = TestManagementService()
