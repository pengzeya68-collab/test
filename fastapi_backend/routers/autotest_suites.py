"""
测试套件路由（DB 持久化版）

功能：
- 套件 CRUD（DB 持久化）
- 套件内用例管理
- 套件真实执行（调用 SuiteRunner）
- 执行历史查询
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi_backend.core.autotest_database import AsyncSessionLocal
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.autotest import (
    AutoTestCase,
    AutoTestScenario,
    TestSuite,
    TestSuiteCase,
    TestSuiteExecution,
)

router = APIRouter(
    prefix="/api/auto-test/suites",
    tags=["回归套件"],
    dependencies=[Depends(get_current_user)],
)


# ========== Pydantic 模型 ==========


class SuiteCreate(BaseModel):
    name: str
    description: str = ""
    env_id: Optional[int] = None
    case_ids: List[int] = []


class SuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    env_id: Optional[int] = None


class SuiteCaseAdd(BaseModel):
    case_ids: List[int]


# ========== 套件 CRUD ==========


@router.get("")
async def list_suites(page: int = 1, size: int = 20, keyword: str = ""):
    """列出所有测试套件"""
    async with AsyncSessionLocal() as db:
        query = select(TestSuite)
        count_query = select(func.count(TestSuite.id))

        if keyword:
            query = query.where(TestSuite.name.contains(keyword))
            count_query = count_query.where(TestSuite.name.contains(keyword))

        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        result = await db.execute(
            query.order_by(TestSuite.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        suites = result.scalars().all()
        suite_ids = [s.id for s in suites]

        # 批量查询每个套件的用例数（避免 N+1）
        case_count_map = {}
        if suite_ids:
            cc_result = await db.execute(
                select(TestSuiteCase.suite_id, func.count(TestSuiteCase.id))
                .where(TestSuiteCase.suite_id.in_(suite_ids))
                .group_by(TestSuiteCase.suite_id)
            )
            case_count_map = {row[0]: row[1] for row in cc_result.all()}

        # 批量查询每个套件的最近执行状态（避免 N+1）
        last_exec_map = {}
        if suite_ids:
            max_time_subq = (
                select(
                    TestSuiteExecution.suite_id,
                    func.max(TestSuiteExecution.created_at).label("max_time"),
                )
                .where(TestSuiteExecution.suite_id.in_(suite_ids))
                .group_by(TestSuiteExecution.suite_id)
                .subquery()
            )
            le_result = await db.execute(
                select(TestSuiteExecution).join(
                    max_time_subq,
                    (TestSuiteExecution.suite_id == max_time_subq.c.suite_id)
                    & (TestSuiteExecution.created_at == max_time_subq.c.max_time),
                )
            )
            last_exec_map = {e.suite_id: e for e in le_result.scalars().all()}

        items = []
        for s in suites:
            last_exec = last_exec_map.get(s.id)
            items.append({
                "id": s.id,
                "name": s.name,
                "description": s.description,
                "env_id": s.env_id,
                "case_count": case_count_map.get(s.id, 0),
                "last_status": last_exec.status if last_exec else None,
                "last_run_at": str(last_exec.created_at) if last_exec else None,
                "created_at": str(s.created_at),
            })

        return {"list": items, "total": total, "page": page, "size": size}


@router.post("")
async def create_suite(body: SuiteCreate):
    """创建测试套件"""
    async with AsyncSessionLocal() as db:
        suite = TestSuite(
            name=body.name,
            description=body.description,
            env_id=body.env_id,
        )
        db.add(suite)
        await db.flush()

        # 添加用例关联
        for idx, case_id in enumerate(body.case_ids):
            sc = TestSuiteCase(
                suite_id=suite.id,
                case_id=case_id,
                sort_order=idx,
            )
            db.add(sc)

        await db.commit()
        await db.refresh(suite)
        return {"id": suite.id, "message": "套件创建成功"}


@router.get("/{suite_id}")
async def get_suite(suite_id: int):
    """获取套件详情（含用例列表）"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TestSuite).where(TestSuite.id == suite_id))
        suite = result.scalar_one_or_none()
        if not suite:
            raise HTTPException(404, "套件不存在")

        # 获取关联的用例
        result = await db.execute(
            select(TestSuiteCase, AutoTestCase)
            .join(AutoTestCase, TestSuiteCase.case_id == AutoTestCase.id)
            .where(TestSuiteCase.suite_id == suite_id)
            .order_by(TestSuiteCase.sort_order)
        )
        cases = []
        for sc, case in result.all():
            cases.append({
                "id": sc.id,
                "case_id": case.id,
                "case_name": case.name,
                "method": case.method,
                "url": case.url,
                "sort_order": sc.sort_order,
            })

        return {
            "id": suite.id,
            "name": suite.name,
            "description": suite.description,
            "env_id": suite.env_id,
            "cases": cases,
            "created_at": str(suite.created_at),
        }


@router.put("/{suite_id}")
async def update_suite(suite_id: int, body: SuiteUpdate):
    """更新套件基本信息"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TestSuite).where(TestSuite.id == suite_id))
        suite = result.scalar_one_or_none()
        if not suite:
            raise HTTPException(404, "套件不存在")

        if body.name is not None:
            suite.name = body.name
        if body.description is not None:
            suite.description = body.description
        if body.env_id is not None:
            suite.env_id = body.env_id

        await db.commit()
        return {"message": "更新成功"}


@router.delete("/{suite_id}")
async def delete_suite(suite_id: int):
    """删除测试套件"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TestSuite).where(TestSuite.id == suite_id))
        suite = result.scalar_one_or_none()
        if not suite:
            raise HTTPException(404, "套件不存在")
        await db.delete(suite)
        await db.commit()
        return {"message": "删除成功"}


# ========== 套件用例管理 ==========


@router.post("/{suite_id}/cases")
async def add_cases_to_suite(suite_id: int, body: SuiteCaseAdd):
    """向套件中添加用例"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TestSuite).where(TestSuite.id == suite_id))
        if not result.scalar_one_or_none():
            raise HTTPException(404, "套件不存在")

        # 获取当前最大排序号
        max_order_result = await db.execute(
            select(func.max(TestSuiteCase.sort_order)).where(TestSuiteCase.suite_id == suite_id)
        )
        max_order = max_order_result.scalar() or 0

        added = 0
        for case_id in body.case_ids:
            # 检查是否已存在
            existing = await db.execute(
                select(TestSuiteCase).where(
                    TestSuiteCase.suite_id == suite_id,
                    TestSuiteCase.case_id == case_id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            max_order += 1
            sc = TestSuiteCase(
                suite_id=suite_id,
                case_id=case_id,
                sort_order=max_order,
            )
            db.add(sc)
            added += 1

        await db.commit()
        return {"message": f"成功添加 {added} 个用例", "added": added}


@router.delete("/{suite_id}/cases/{case_link_id}")
async def remove_case_from_suite(suite_id: int, case_link_id: int):
    """从套件中移除用例"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(TestSuiteCase).where(
                TestSuiteCase.id == case_link_id,
                TestSuiteCase.suite_id == suite_id,
            )
        )
        sc = result.scalar_one_or_none()
        if not sc:
            raise HTTPException(404, "用例关联不存在")
        await db.delete(sc)
        await db.commit()
        return {"message": "已移除"}


# ========== 套件执行 ==========


@router.post("/{suite_id}/run")
async def run_suite(suite_id: int, env_id: Optional[int] = None):
    """执行测试套件（真实执行）"""
    from fastapi_backend.services.autotest_suite_runner import SuiteRunner

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(TestSuite).where(TestSuite.id == suite_id))
        suite = result.scalar_one_or_none()
        if not suite:
            raise HTTPException(404, "套件不存在")

    runner = SuiteRunner(suite_id, env_id=env_id)
    try:
        exec_result = await runner.execute()
        return exec_result
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"执行失败: {str(e)}")


@router.get("/{suite_id}/executions")
async def list_executions(suite_id: int, page: int = 1, size: int = 20):
    """获取套件的执行历史"""
    async with AsyncSessionLocal() as db:
        total_result = await db.execute(
            select(func.count(TestSuiteExecution.id)).where(TestSuiteExecution.suite_id == suite_id)
        )
        total = total_result.scalar() or 0

        result = await db.execute(
            select(TestSuiteExecution)
            .where(TestSuiteExecution.suite_id == suite_id)
            .order_by(TestSuiteExecution.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        executions = result.scalars().all()

        items = [
            {
                "id": e.id,
                "suite_id": e.suite_id,
                "env_id": e.env_id,
                "status": e.status,
                "total_cases": e.total_cases,
                "passed_cases": e.passed_cases,
                "failed_cases": e.failed_cases,
                "duration_ms": e.duration_ms,
                "started_at": str(e.started_at) if e.started_at else None,
                "finished_at": str(e.finished_at) if e.finished_at else None,
                "created_at": str(e.created_at),
            }
            for e in executions
        ]

        return {"list": items, "total": total, "page": page, "size": size}
