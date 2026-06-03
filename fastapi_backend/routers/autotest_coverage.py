"""
AutoTest 路由 - 测试覆盖率看板

路径前缀: /api/auto-test/coverage
功能: 接口覆盖率统计、热力图数据、执行详情
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.models import User
from fastapi_backend.services.autotest_coverage_service import (
    get_coverage_summary,
    get_coverage_heatmap,
    get_api_execution_detail,
)

router = APIRouter(
    prefix="/api/auto-test/coverage",
    tags=["AutoTest-覆盖率看板"],
)


@router.get("/summary")
async def coverage_summary(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取覆盖率汇总统计"""
    return await get_coverage_summary(db, user_id=current_user.id)


@router.get("/heatmap")
async def coverage_heatmap(
    days: int = Query(30, ge=7, le=180, description="统计天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取覆盖率热力图数据"""
    return await get_coverage_heatmap(db, days, user_id=current_user.id)


@router.get("/detail")
async def api_execution_detail(
    case_ids: str = Query(..., description="用例ID列表，逗号分隔"),
    days: int = Query(30, ge=7, le=180, description="统计天数"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取接口的执行详情（支持多个用例ID）"""
    try:
        ids = [int(x.strip()) for x in case_ids.split(",") if x.strip()]
    except ValueError:
        ids = []
    return await get_api_execution_detail(db, ids, days, user_id=current_user.id)
