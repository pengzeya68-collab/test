"""Controlled, auditable assistance for UI automation analysis.

The module intentionally returns recommendations rather than changing test
assets. A remote LLM is not called implicitly: the deterministic baseline is
available in every deployment and exposes the same review contract.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.ui_automation import (
    AIAnalysisFeedback,
    AIAnalysisRecord,
    UICase,
    UIStep,
    UIRun,
    UIStepResult,
)
from fastapi_backend.services.ui_automation import run_service


_INJECTION_MARKERS = re.compile(
    r"(?:ignore\s+(?:all|any|previous|above)\s+(?:instructions?|rules?)|"
    r"system\s+prompt|developer\s+message|assistant\s*:|jailbreak|do\s+not\s+follow)",
    re.IGNORECASE,
)
_SENSITIVE_TEXT = re.compile(
    r"(?:bearer\s+[a-z0-9._~+\-/=]{8,}|(?:password|passwd|secret|token|api[_-]?key)\s*[:=]\s*[^\s,;，；。]{1,200}|"
    r"\b1\d{10}\b|\b[\w.+-]+@[\w.-]+\.[a-z]{2,}\b)",
    re.IGNORECASE,
)
_LOCATOR_STRATEGIES = {"test_id", "role", "label", "placeholder", "text", "css", "xpath"}
FAILURE_CATEGORIES = {"environment", "data", "product_defect", "script", "unknown"}


def _safe_text(value: Any, limit: int, *, reject_injection: bool = True) -> str:
    text = str(value or "").replace("\x00", "").strip()
    if _INJECTION_MARKERS.search(text):
        if reject_injection:
            raise HTTPException(status_code=422, detail="输入包含疑似提示注入内容，已拒绝处理")
        return "[UNTRUSTED CONTENT OMITTED]"
    return _SENSITIVE_TEXT.sub("[REDACTED]", text)[:limit]


def _save_record(
    db: AsyncSession,
    *,
    user_id: int,
    analysis_type: str,
    target_type: str | None,
    target_id: int | None,
    traceability_id: str | None,
    input_redacted: dict[str, Any],
    output: dict[str, Any],
) -> AIAnalysisRecord:
    record = AIAnalysisRecord(
        user_id=user_id,
        analysis_type=analysis_type,
        target_type=target_type,
        target_id=target_id,
        traceability_id=traceability_id,
        input_redacted=run_service._redact_payload(input_redacted),
        output=run_service._redact_payload(output),
    )
    db.add(record)
    return record


def _failure_category(
    run: UIRun, failed_steps: list[UIStepResult]
) -> tuple[str, float, list[str], list[str], list[str]]:
    messages = " ".join(str(step.error_message or "") for step in failed_steps).lower()
    if run.status in {"infra_error", "timed_out"} or "heartbeat" in messages or "timeout" in messages:
        return (
            "environment",
            0.82,
            ["执行记录显示运行器、网络或超时异常。"],
            ["无法从当前记录确认被测系统是否同时存在功能缺陷。"],
            ["检查 Agent/桌面端心跳、网络连通性和环境可用性。", "在相同环境重试一次并对比时间线。"],
        )
    if any(
        term in messages
        for term in (
            "test data",
            "fixture",
            "seed data",
            "data not found",
            "record not found",
            "duplicate key",
            "unique constraint",
            "foreign key",
            "invalid data",
            "account not found",
            "数据不存在",
            "测试数据",
            "数据重复",
        )
    ):
        return (
            "data",
            0.74,
            ["失败信息指向测试数据缺失、冲突或不满足约束。"],
            ["当前记录无法确认数据异常来自准备脚本、环境污染还是产品写入逻辑。"],
            ["核对本次运行使用的数据集和前置清理记录。", "使用唯一且可追溯的测试数据重新执行。"],
        )
    if any(term in messages for term in ("locator", "element", "selector", "not found", "strict mode")):
        return (
            "script",
            0.76,
            ["失败步骤的错误信息包含元素定位或可操作性问题。"],
            ["当前证据无法判断页面变化来自产品改版、数据差异还是用例定位器失效。"],
            ["在相同登录态下执行定位器 dry-run。", "确认候选定位器唯一、可见且可操作后再创建新版本。"],
        )
    if any(
        term in messages
        for term in (
            "internal server error",
            "status 500",
            "status=500",
            "status 502",
            "status 503",
            "uncaught exception",
            "application crash",
            "product defect",
            "server error",
        )
    ):
        return (
            "product_defect",
            0.72,
            ["失败信息包含被测应用服务端错误、崩溃或显式产品缺陷特征。"],
            ["单次自动化记录不能排除环境依赖或测试数据触发的服务异常。"],
            ["使用相同请求和数据人工复现。", "关联服务端 trace ID、日志和需求预期后再提交缺陷。"],
        )
    if any(term in messages for term in ("assert", "expected", "mismatch", "equals")):
        return (
            "product_defect",
            0.56,
            ["稳定断言的实际结果与预期不一致，具备产品缺陷候选特征。"],
            ["断言差异本身不足以排除过期预期或测试数据问题。"],
            ["核对断言预期与需求追踪项。", "固定测试数据后复现，并附加截图/trace。"],
        )
    return (
        "unknown",
        0.35,
        ["当前执行记录没有足够的结构化失败特征。"],
        ["未能确认环境、数据、产品或脚本中的任何一项为根因。"],
        ["补充失败步骤日志、截图和复现前提。", "在人工确认前不要据此修改正式用例。"],
    )


async def analyze_failure(db: AsyncSession, user_id: int, run: UIRun) -> dict[str, Any]:
    failed_steps = list(
        (
            await db.scalars(
                select(UIStepResult)
                .where(
                    UIStepResult.run_id == run.id,
                    UIStepResult.status.in_(("failed", "error")),
                )
                .order_by(UIStepResult.id)
            )
        ).all()
    )
    category, confidence, evidence, unknowns, next_actions = _failure_category(run, failed_steps)
    output = {
        "category": category,
        "confidence": confidence,
        "evidence": [
            *evidence,
            *[
                f"步骤 {step.step_id}: {_safe_text(step.error_message, 500, reject_injection=False) or '无错误详情'}"
                for step in failed_steps[:20]
            ],
        ],
        "unknowns": unknowns,
        "next_actions": next_actions,
        "advisory_only": True,
        "engine": "guarded-heuristic-v1",
    }
    record = _save_record(
        db,
        user_id=user_id,
        analysis_type="failure_attribution",
        target_type="ui_run",
        target_id=run.id,
        traceability_id=None,
        input_redacted={
            "run_status": run.status,
            "failed_step_count": len(failed_steps),
            "error_messages": [
                _safe_text(step.error_message, 500, reject_injection=False) for step in failed_steps[:20]
            ],
        },
        output=output,
    )
    await db.commit()
    return {"analysis_id": record.id, **output}


async def suggest_locators(
    db: AsyncSession,
    user_id: int,
    case: UICase,
    *,
    step_id: str,
    probes: Any,
    current_url: Any,
    login_state_matches: Any,
) -> dict[str, Any]:
    step = await db.scalar(select(UIStep).where(UIStep.id == step_id, UIStep.case_id == case.id))
    if step is None:
        raise HTTPException(status_code=404, detail="UI 步骤不存在")
    if not isinstance(probes, list) or not probes or len(probes) > 25:
        raise HTTPException(status_code=422, detail="locator_probes 必须包含 1 到 25 个候选项")
    safe_url = _safe_text(current_url, 2000)
    if login_state_matches is not True:
        raise HTTPException(status_code=422, detail="定位器建议必须在与用例一致的登录态中验证")
    suggestions: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for probe in probes:
        if not isinstance(probe, dict):
            raise HTTPException(status_code=422, detail="定位器候选必须是对象")
        strategy = str(probe.get("strategy") or "")
        value = _safe_text(probe.get("value"), 2000)
        if strategy not in _LOCATOR_STRATEGIES or not value:
            raise HTTPException(status_code=422, detail="定位器候选的 strategy 或 value 无效")
        validation = {
            "unique_match": int(probe.get("match_count") or 0) == 1,
            "visible": probe.get("visible") is True,
            "actionable": probe.get("actionable") is True,
            "url_matches": probe.get("url_matches") is True,
            "login_state_matches": True,
            "dry_run_passed": probe.get("dry_run_passed") is True,
        }
        if all(validation.values()):
            suggestions.append(
                {
                    "locator": {
                        "strategy": strategy,
                        "value": value,
                        "options": run_service._redact_payload(probe.get("options") or {}),
                    },
                    "validation": validation,
                    "confidence": 0.9 if strategy in {"test_id", "role", "label"} else 0.72,
                    "requires_user_confirmation": True,
                }
            )
        else:
            rejected.append(
                {"strategy": strategy, "reason": ", ".join(key for key, valid in validation.items() if not valid)}
            )
    output = {
        "step_id": step_id,
        "current_url": safe_url,
        "suggestions": suggestions,
        "rejected": rejected,
        "advisory_only": True,
        "automatic_apply": False,
        "required_before_apply": ["用户确认", "创建 UI 用例新版本", "在测试分支或白名单项目中再次 dry-run"],
    }
    record = _save_record(
        db,
        user_id=user_id,
        analysis_type="locator_suggestion",
        target_type="ui_case",
        target_id=case.id,
        traceability_id=None,
        input_redacted={
            "step_id": step_id,
            "current_url": safe_url,
            "probe_count": len(probes),
            "login_state_matches": True,
        },
        output=output,
    )
    await db.commit()
    return {"analysis_id": record.id, **output}


def _make_test_points(requirement: str, traceability_id: str) -> list[dict[str, Any]]:
    fragments = [
        fragment.strip(" -•\t") for fragment in re.split(r"[\n。；;]+", requirement) if fragment.strip(" -•\t")
    ]
    if not fragments:
        raise HTTPException(status_code=422, detail="需求内容不足以生成测试点")
    points: list[dict[str, Any]] = []
    for index, fragment in enumerate(fragments[:30], start=1):
        point_id = f"{traceability_id}-TP-{index:03d}"
        points.append(
            {
                "id": point_id,
                "title": f"验证：{fragment[:120]}",
                "source_requirement": fragment[:500],
                "test_design": ["正常路径", "边界条件", "异常与权限校验"],
                "assumptions": ["需求文本未覆盖的数据准备、权限矩阵和外部依赖需要人工补充。"],
                "missing_information": ["明确的业务成功标准", "可复用测试数据", "环境与账号前置条件"],
                "requires_human_review": True,
            }
        )
    return points


async def generate_requirement_test_points(
    db: AsyncSession, user_id: int, requirement_text: Any, traceability_id: Any = None, context: Any = None
) -> dict[str, Any]:
    requirement = _safe_text(requirement_text, 12000)
    if len(requirement) < 4:
        raise HTTPException(status_code=422, detail="需求内容至少需要 4 个字符")
    trace = _safe_text(traceability_id, 100) if traceability_id else f"REQ-{uuid.uuid4().hex[:12].upper()}"
    if not re.fullmatch(r"[A-Za-z0-9_.:-]{3,100}", trace):
        raise HTTPException(status_code=422, detail="需求追踪编号只能包含字母、数字、._:-")
    safe_context = _safe_text(context, 4000) if context else ""
    points = _make_test_points(requirement, trace)
    output = {
        "traceability_id": trace,
        "test_points": points,
        "advisory_only": True,
        "engine": "guarded-heuristic-v1",
    }
    record = _save_record(
        db,
        user_id=user_id,
        analysis_type="requirement_test_points",
        target_type="requirement",
        target_id=None,
        traceability_id=trace,
        input_redacted={"requirement_text": requirement, "context": safe_context},
        output=output,
    )
    await db.commit()
    return {"analysis_id": record.id, **output}


async def generate_case_drafts(
    db: AsyncSession,
    user_id: int,
    analysis_id: str,
    point_ids: Any,
    point_overrides: Any = None,
) -> dict[str, Any]:
    if not re.fullmatch(r"[a-f0-9]{32}", str(analysis_id or "")):
        raise HTTPException(status_code=422, detail="analysis_id 无效")
    record = await db.scalar(
        select(AIAnalysisRecord).where(
            AIAnalysisRecord.id == analysis_id,
            AIAnalysisRecord.user_id == user_id,
            AIAnalysisRecord.analysis_type == "requirement_test_points",
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="需求测试点分析记录不存在")
    if not isinstance(point_ids, list) or not point_ids or len(point_ids) > 30:
        raise HTTPException(status_code=422, detail="point_ids 必须包含 1 到 30 个测试点")
    points = {
        point["id"]: dict(point) for point in (record.output or {}).get("test_points", []) if isinstance(point, dict)
    }
    if point_overrides is not None:
        if not isinstance(point_overrides, list) or len(point_overrides) > 30:
            raise HTTPException(status_code=422, detail="point_overrides 必须是最多 30 项的数组")
        for override in point_overrides:
            if not isinstance(override, dict) or str(override.get("id") or "") not in points:
                raise HTTPException(status_code=422, detail="point_overrides 包含无效测试点")
            point = points[str(override["id"])]
            if "title" in override:
                point["title"] = _safe_text(override["title"], 200)
            if "source_requirement" in override:
                point["source_requirement"] = _safe_text(override["source_requirement"], 1000)
    selected = []
    for point_id in point_ids:
        point = points.get(str(point_id))
        if point is None or point in selected:
            raise HTTPException(status_code=422, detail="point_ids 包含无效或重复测试点")
        selected.append(point)
    drafts = [
        {
            "name": point["title"][:200],
            "source_test_point_id": point["id"],
            "description": point["source_requirement"],
            "preconditions": ["由人工补充环境、账号和测试数据。"],
            "steps": [{"action": "执行与测试点对应的用户操作", "expected": "由人工确认业务成功标准"}],
            "assertions": [],
            "assumptions": point["assumptions"],
            "missing_information": point["missing_information"],
            "requires_human_review": True,
        }
        for point in selected
    ]
    output = {"traceability_id": record.traceability_id, "case_drafts": drafts, "advisory_only": True}
    draft_record = _save_record(
        db,
        user_id=user_id,
        analysis_type="requirement_case_drafts",
        target_type="ai_analysis",
        target_id=None,
        traceability_id=record.traceability_id,
        input_redacted={
            "source_analysis_id": record.id,
            "point_ids": [point["id"] for point in selected],
            "overrides": [
                {"id": point["id"], "title": point["title"], "source_requirement": point["source_requirement"]}
                for point in selected
            ],
        },
        output=output,
    )
    await db.commit()
    return {"analysis_id": draft_record.id, **output}


async def get_analysis_record(db: AsyncSession, user_id: int, analysis_id: str) -> AIAnalysisRecord:
    record = await db.scalar(
        select(AIAnalysisRecord).where(
            AIAnalysisRecord.id == analysis_id,
            AIAnalysisRecord.user_id == user_id,
        )
    )
    if record is None:
        raise HTTPException(status_code=404, detail="分析记录不存在")
    return record


async def submit_analysis_feedback(
    db: AsyncSession,
    user_id: int,
    analysis_id: str,
    *,
    accepted: bool,
    corrected_category: str | None,
    comment: Any = None,
) -> AIAnalysisFeedback:
    record = await get_analysis_record(db, user_id, analysis_id)
    predicted = (record.output or {}).get("category")
    if predicted not in FAILURE_CATEGORIES:
        predicted = None
    if corrected_category is not None and corrected_category not in FAILURE_CATEGORIES:
        raise HTTPException(status_code=422, detail="修正后的失败类别无效")
    if not accepted and corrected_category == predicted:
        raise HTTPException(status_code=422, detail="修正类别必须与原建议不同")

    safe_comment = _safe_text(comment, 2000, reject_injection=False) if comment else None
    feedback = await db.scalar(
        select(AIAnalysisFeedback)
        .where(
            AIAnalysisFeedback.analysis_id == record.id,
            AIAnalysisFeedback.user_id == user_id,
        )
        .with_for_update()
    )
    now = datetime.now(timezone.utc)
    if feedback is None:
        feedback = AIAnalysisFeedback(
            analysis_id=record.id,
            user_id=user_id,
            analysis_type=record.analysis_type,
            predicted_category=predicted,
            accepted=accepted,
            corrected_category=corrected_category,
            comment=safe_comment,
            created_at=now,
            updated_at=now,
        )
        db.add(feedback)
    else:
        feedback.analysis_type = record.analysis_type
        feedback.predicted_category = predicted
        feedback.accepted = accepted
        feedback.corrected_category = corrected_category
        feedback.comment = safe_comment
        feedback.updated_at = now
    await db.commit()
    await db.refresh(feedback)
    return feedback


async def get_feedback_metrics(
    db: AsyncSession,
    user_id: int,
    *,
    analysis_type: str | None = None,
) -> dict[str, Any]:
    query = select(AIAnalysisFeedback).where(AIAnalysisFeedback.user_id == user_id)
    if analysis_type:
        query = query.where(AIAnalysisFeedback.analysis_type == analysis_type)
    feedback_items = list((await db.scalars(query)).all())
    total = len(feedback_items)
    accepted_count = sum(1 for item in feedback_items if item.accepted)
    corrected_count = sum(
        1
        for item in feedback_items
        if item.corrected_category is not None and item.corrected_category != item.predicted_category
    )

    breakdown: dict[str, dict[str, Any]] = {}
    for item in feedback_items:
        category = item.predicted_category or "uncategorized"
        bucket = breakdown.setdefault(
            category,
            {
                "total_feedback": 0,
                "accepted_count": 0,
                "corrected_count": 0,
            },
        )
        bucket["total_feedback"] += 1
        if item.accepted:
            bucket["accepted_count"] += 1
        if item.corrected_category is not None and item.corrected_category != item.predicted_category:
            bucket["corrected_count"] += 1
    for bucket in breakdown.values():
        bucket_total = bucket["total_feedback"]
        bucket["accuracy_rate"] = round(bucket["accepted_count"] / bucket_total, 4) if bucket_total else 0.0
        bucket["correction_rate"] = round(bucket["corrected_count"] / bucket_total, 4) if bucket_total else 0.0

    return {
        "analysis_type": analysis_type,
        "total_feedback": total,
        "accepted_count": accepted_count,
        "corrected_count": corrected_count,
        "accuracy_rate": round(accepted_count / total, 4) if total else 0.0,
        "correction_rate": round(corrected_count / total, 4) if total else 0.0,
        "category_breakdown": breakdown,
    }
