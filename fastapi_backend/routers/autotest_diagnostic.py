"""
AutoTest 诊断路由 - 数据完整性检查
从Flask的auto_test.py迁移的诊断功能

路径前缀: /api/auto-test/diagnose
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.models import (
    TestReport,
    TestReportResult,
    TestPlan,
)
from fastapi_backend.models.models import User

router = APIRouter(prefix="/api/auto-test/diagnose", tags=["AutoTest-诊断"])


@router.get("/report/{report_id}")
async def diagnose_report(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_autotest_db),
):
    """
    诊断报告数据完整性：检测同一 report_id 下是否有累积的孤儿步骤数据

    返回：{has_orphans: bool, orphan_count: int, total_count: int, latest_step_id: int}
    """
    # 获取报告（校验归属：通过 plan_id 关联 TestPlan.user_id）
    result = await db.execute(
        select(TestReport)
        .join(TestPlan, TestReport.plan_id == TestPlan.id, isouter=True)
        .where(TestReport.id == report_id, TestPlan.user_id == current_user.id)
    )
    report = result.scalar_one_or_none()

    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")

    # 获取所有步骤
    result = await db.execute(
        select(TestReportResult)
        .where(TestReportResult.report_id == report_id)
        .order_by(TestReportResult.id)
    )
    all_steps = result.scalars().all()
    total_count = len(all_steps)

    if total_count == 0:
        return {
            "has_orphans": False,
            "orphan_count": 0,
            "total_count": 0,
            "latest_step_id": None,
            "step_ids": []
        }

    latest_steps_count = report.total_count or 0

    has_orphans = total_count > latest_steps_count if latest_steps_count > 0 else False
    orphan_count = total_count - latest_steps_count if has_orphans else 0

    return {
        "has_orphans": has_orphans,
        "orphan_count": orphan_count,
        "total_count": total_count,
        "expected_count": latest_steps_count,
        "latest_step_id": all_steps[-1].id if all_steps else None,
        "step_ids": [s.id for s in all_steps]
    }


@router.get("/scenario/{scenario_id}")
async def diagnose_scenario(
    scenario_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_autotest_db),
):
    """
    诊断场景数据完整性：检查该场景下所有执行记录的数据一致性
    使用 AutoTestScenarioExecutionRecord 查询场景执行记录
    """
    from fastapi_backend.models.autotest import AutoTestScenarioExecutionRecord, AutoTestScenario

    # 先检查场景是否属于当前用户
    scenario_result = await db.execute(
        select(AutoTestScenario)
        .where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
    )
    scenario = scenario_result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    # 查询该场景的所有执行记录
    result = await db.execute(
        select(AutoTestScenarioExecutionRecord)
        .where(AutoTestScenarioExecutionRecord.scenario_id == scenario_id)
        .order_by(AutoTestScenarioExecutionRecord.id.desc())
    )
    records = result.scalars().all()

    record_diagnostics = []
    for record in records:
        record_diagnostics.append({
            "record_id": record.id,
            "status": record.status,
            "total_steps": record.total_steps,
            "success_steps": record.success_steps,
            "failed_steps": record.failed_steps,
            "skipped_steps": record.skipped_steps,
            "total_time": record.total_time,
            "report_url": record.report_url,
            "created_at": record.created_at.isoformat() if record.created_at else None,
        })

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario.name,
        "total_records": len(records),
        "records": record_diagnostics
    }


@router.get("/data-consistency")
async def check_data_consistency(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    检查自动化测试数据一致性
    返回各种数据完整性统计
    """
    # 检查报告和步骤的一致性（仅当前用户的数据）
    result = await db.execute(
        select(
            func.count(func.distinct(TestReport.id)).label("total_reports"),
            func.count(TestReportResult.id).label("total_steps"),
            func.count(func.distinct(TestReportResult.report_id)).label("reports_with_steps")
        )
        .join(TestPlan, TestReport.plan_id == TestPlan.id, isouter=True)
        .where(TestPlan.user_id == current_user.id)
    )
    stats = result.first()

    # 检查没有步骤的报告（仅当前用户）
    result = await db.execute(
        select(TestReport.id, TestReport.plan_name)
        .join(TestPlan, TestReport.plan_id == TestPlan.id, isouter=True)
        .outerjoin(TestReportResult, TestReport.id == TestReportResult.report_id)
        .where(TestPlan.user_id == current_user.id)
        .group_by(TestReport.id)
        .having(func.count(TestReportResult.id) == 0)
    )
    reports_without_steps = result.all()

    return {
        "data_consistency": {
            "total_reports": stats.total_reports,
            "total_steps": stats.total_steps,
            "reports_with_steps": stats.reports_with_steps,
            "reports_without_steps": len(reports_without_steps),
        },
        "issues": {
            "reports_without_steps": [
                {"id": r.id, "title": r.plan_name} for r in reports_without_steps
            ]
        }
    }