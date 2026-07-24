"""Advisory failure attribution for API/suite automation executions.

Mirrors the guarded-heuristic contract used by UI run analysis
(``services.ui_automation.ai_assistance``): the engine is deterministic and
available in every deployment, inputs are redacted before persistence, every
call is audited through ``AIAnalysisRecord``, and the output is strictly
advisory — it never mutates executions, suites, scenarios or cases.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.models.autotest import (
    AutomationExecution,
    AutomationExecutionItem,
)
from fastapi_backend.services.ui_automation.ai_assistance import (
    _safe_text,
    _save_record,
)

_FAILED_ITEM_STATUSES = ("failed", "error", "timed_out", "infra_error")
_TERMINAL_FAILURE_STATUSES = {"failed", "infra_error", "timed_out", "cancelled"}


def _execution_failure_category(
    execution: AutomationExecution, failed_items: list[AutomationExecutionItem]
) -> tuple[str, float, list[str], list[str], list[str]]:
    messages = " ".join(
        [str(execution.error_message or "")]
        + [str(item.error_message or "") for item in failed_items]
    ).lower()
    error_code = str(execution.error_code or "").lower()
    if (
        execution.status in {"infra_error", "timed_out"}
        or error_code.startswith(("heartbeat", "runner", "lease"))
        or any(term in messages for term in ("heartbeat", "lease expired", "runner", "agent offline"))
    ):
        return (
            "environment",
            0.82,
            ["执行记录显示运行器、心跳、租约或整体超时异常。"],
            ["无法从当前记录确认被测系统是否同时存在功能缺陷。"],
            ["检查执行器/Agent 心跳、网络连通性和环境可用性。", "在相同环境重试一次并对比事件流时间线。"],
        )
    if any(
        term in messages
        for term in (
            "connection refused",
            "connect timeout",
            "connecttimeout",
            "name or service not known",
            "network is unreachable",
            "no route to host",
            "ssl",
            "certificate",
            "proxy",
            "dns",
        )
    ):
        return (
            "environment",
            0.66,
            ["失败信息指向网络连通性、TLS 证书或代理配置问题。"],
            ["单次网络异常不能排除被测服务自身不可用。"],
            ["确认目标环境地址、证书与代理配置。", "在相同网络环境重试并对比结果。"],
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
            "unauthorized",
            "forbidden",
            "token expired",
            "status 401",
            "status 403",
            "数据不存在",
            "测试数据",
            "数据重复",
        )
    ):
        return (
            "data",
            0.74,
            ["失败信息指向测试数据缺失、冲突、约束不满足或前置凭据失效。"],
            ["当前记录无法确认数据异常来自准备脚本、环境污染还是产品写入逻辑。"],
            ["核对本次执行使用的数据集、账号凭据和前置清理记录。", "使用唯一且可追溯的测试数据重新执行。"],
        )
    if any(
        term in messages
        for term in (
            "internal server error",
            "status 500",
            "status=500",
            "status 502",
            "status 503",
            "bad gateway",
            "service unavailable",
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
    if any(
        term in messages
        for term in (
            "jsonpath",
            "extractor",
            "unresolved variable",
            "variable not found",
            "invalid assertion",
            "assert rule",
            "malformed",
            "parse error",
        )
    ):
        return (
            "script",
            0.76,
            ["失败步骤的错误信息指向用例定义问题（变量提取、断言规则或请求配置）。"],
            ["当前证据无法判断配置问题来自用例编写错误还是被测接口契约变化。"],
            ["核对失败用例的变量映射、提取器和断言规则。", "确认接口实际响应结构后修正用例并重新执行。"],
        )
    if any(term in messages for term in ("assert", "expected", "mismatch", "equals", "not equal")):
        return (
            "product_defect",
            0.56,
            ["稳定断言的实际结果与预期不一致，具备产品缺陷候选特征。"],
            ["断言差异本身不足以排除过期预期或测试数据问题。"],
            ["核对断言预期与需求追踪项。", "固定测试数据后复现，并附加响应快照。"],
        )
    return (
        "unknown",
        0.35,
        ["当前执行记录没有足够的结构化失败特征。"],
        ["未能确认环境、数据、产品或脚本中的任何一项为根因。"],
        ["补充失败步骤日志、响应内容和复现前提。", "在人工确认前不要据此修改正式用例。"],
    )


async def analyze_execution_failure(
    db: AsyncSession, user_id: int, execution: AutomationExecution
) -> dict[str, Any]:
    """Produce a redacted, audited, advisory attribution for a failed execution."""
    failed_items = list(
        (
            await db.scalars(
                select(AutomationExecutionItem)
                .where(
                    AutomationExecutionItem.execution_id == execution.id,
                    AutomationExecutionItem.status.in_(_FAILED_ITEM_STATUSES),
                )
                .order_by(AutomationExecutionItem.sequence)
            )
        ).all()
    )
    category, confidence, evidence, unknowns, next_actions = _execution_failure_category(execution, failed_items)
    if execution.error_message:
        evidence = [
            *evidence,
            f"执行级错误：{_safe_text(execution.error_message, 500, reject_injection=False) or '无错误详情'}",
        ]
    evidence = [
        *evidence,
        *[
            f"用例 {item.target_name or item.target_id}（序号 {item.sequence}）: "
            f"{_safe_text(item.error_message, 500, reject_injection=False) or '无错误详情'}"
            for item in failed_items[:20]
        ],
    ]
    output = {
        "category": category,
        "confidence": confidence,
        "evidence": evidence,
        "unknowns": unknowns,
        "next_actions": next_actions,
        "advisory_only": True,
        "engine": "guarded-heuristic-v1",
    }
    record = _save_record(
        db,
        user_id=user_id,
        analysis_type="failure_attribution",
        target_type="automation_execution",
        target_id=execution.id,
        traceability_id=None,
        input_redacted={
            "execution_public_id": execution.public_id,
            "execution_status": execution.status,
            "error_code": execution.error_code,
            "error_message": (
                _safe_text(execution.error_message, 500, reject_injection=False) if execution.error_message else None
            ),
            "failed_item_count": len(failed_items),
            "failed_items": [
                {
                    "sequence": item.sequence,
                    "target_name": item.target_name,
                    "error_message": _safe_text(item.error_message, 500, reject_injection=False),
                }
                for item in failed_items[:20]
            ],
        },
        output=output,
    )
    await db.commit()
    return {"analysis_id": record.id, **output}
