"""
测试计划路由
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi_backend.core.database import get_db
from fastapi_backend.models.models import TestPlan, Environment, ApiCase
from fastapi_backend.schemas.plans import TestPlanResponse

router = APIRouter(prefix="/api/plans", tags=["测试计划"])


@router.get("/", response_model=List[TestPlanResponse])
async def get_all_plans(
    db: AsyncSession = Depends(get_db),
    user_id: int = Query(None, description="用户ID")
):
    """获取用户所有测试计划"""
    query = select(TestPlan).order_by(TestPlan.updated_at.desc())
    if user_id:
        query = query.where(TestPlan.user_id == user_id)
    result = await db.execute(query)
    plans = result.scalars().all()
    return plans


@router.get("/{plan_id}", response_model=TestPlanResponse)
async def get_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    """获取测试计划详情"""
    result = await db.execute(select(TestPlan).filter(TestPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")
    return plan


@router.post("/", response_model=TestPlanResponse, status_code=201)
async def create_plan(
    name: str,
    description: str = None,
    environment_id: int = None,
    case_ids: List[int] = None,
    user_id: int = 1,
    db: AsyncSession = Depends(get_db)
):
    """创建测试计划"""
    import json
    plan = TestPlan(
        name=name,
        description=description,
        environment_id=environment_id,
        user_id=user_id,
        case_ids=json.dumps(case_ids) if case_ids else "[]"
    )
    db.add(plan)
    await db.commit()
    await db.refresh(plan)
    return plan


@router.put("/{plan_id}", response_model=TestPlanResponse)
async def update_plan(
    plan_id: int,
    name: str = None,
    description: str = None,
    environment_id: int = None,
    case_ids: List[int] = None,
    db: AsyncSession = Depends(get_db)
):
    """更新测试计划"""
    import json
    result = await db.execute(select(TestPlan).filter(TestPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")

    if name is not None:
        plan.name = name
    if description is not None:
        plan.description = description
    if environment_id is not None:
        plan.environment_id = environment_id
    if case_ids is not None:
        plan.case_ids = json.dumps(case_ids)

    await db.commit()
    await db.refresh(plan)
    return plan


@router.delete("/{plan_id}")
async def delete_plan(plan_id: int, db: AsyncSession = Depends(get_db)):
    """删除测试计划"""
    result = await db.execute(select(TestPlan).filter(TestPlan.id == plan_id))
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="计划不存在")

    await db.delete(plan)
    await db.commit()
    return {"success": True, "message": "删除成功"}
