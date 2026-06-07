"""
回归测试套件路由

创建、管理、执行测试套件（多个场景的集合）
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from datetime import datetime, timezone
import asyncio

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestScenario
from fastapi_backend.models.models import User

router = APIRouter(prefix="/api/auto-test/suites", tags=["回归套件"])

# 内存存储 - 已知限制：服务重启后数据丢失，多worker部署时数据不共享
# TODO: 迁移到数据库持久化存储
_suites: Dict[int, dict] = {}
_suite_id_seq = 1
_run_id_seq = 1
_runs: Dict[int, list] = {}
_suites_lock = asyncio.Lock()


@router.get("")
async def list_suites(current_user: User = Depends(get_current_active_user)):
    """列出当前用户的测试套件"""
    async with _suites_lock:
        suites_list = [
            {"id": k, "name": v["name"], "scenario_count": len(v["scenario_ids"]), "created_at": v["created_at"]}
            for k, v in _suites.items()
            if v.get("user_id") == current_user.id
        ]
    return {"suites": suites_list, "total": len(suites_list)}


@router.post("")
async def create_suite(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_autotest_db),
):
    """创建测试套件"""
    scenario_ids = body.get("scenario_ids", [])
    # 校验每个 scenario_id 是否存在
    if scenario_ids:
        for sid in scenario_ids:
            result = await db.execute(
                select(AutoTestScenario).where(AutoTestScenario.id == sid, AutoTestScenario.user_id == current_user.id)
            )
            if result.scalar_one_or_none() is None:
                raise HTTPException(400, f"场景 {sid} 不存在或无权访问")

    async with _suites_lock:
        global _suite_id_seq
        sid = _suite_id_seq
        _suite_id_seq += 1

        _suites[sid] = {
            "name": body.get("name", f"回归套件-{sid}"),
            "description": body.get("description", ""),
            "scenario_ids": scenario_ids,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "user_id": current_user.id,
        }
    return {"id": sid, "message": "套件创建成功"}


@router.delete("/{suite_id}")
async def delete_suite(suite_id: int, current_user: User = Depends(get_current_active_user)):
    """删除测试套件"""
    async with _suites_lock:
        if suite_id in _suites and _suites[suite_id].get("user_id") == current_user.id:
            del _suites[suite_id]
            # 清理关联的运行记录
            _runs.pop(suite_id, None)
            return {"message": "已删除"}
    raise HTTPException(404, "套件不存在")


@router.get("/{suite_id}")
async def get_suite(
    suite_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_autotest_db)
):
    """获取套件详情（含场景名称）"""
    async with _suites_lock:
        suite = _suites.get(suite_id)
        if not suite or suite.get("user_id") != current_user.id:
            raise HTTPException(404, "套件不存在")
        scenario_ids = list(suite["scenario_ids"])

    # 获取场景名称
    scenario_details = []
    for sid in scenario_ids:
        result = await db.execute(
            select(AutoTestScenario).where(AutoTestScenario.id == sid, AutoTestScenario.user_id == current_user.id)
        )
        sc = result.scalar_one_or_none()
        scenario_details.append(
            {
                "id": sid,
                "name": sc.name if sc else f"场景{sid}(已删除或无权访问)",
                "active": sc.is_active if sc else False,
            }
        )

    async with _suites_lock:
        suite = _suites.get(suite_id, suite)
    return {"suite": {**suite, "scenarios": scenario_details}}


@router.post("/{suite_id}/run")
async def run_suite(
    suite_id: int, current_user: User = Depends(get_current_active_user), db: AsyncSession = Depends(get_autotest_db)
):
    """执行回归测试套件"""
    async with _suites_lock:
        suite = _suites.get(suite_id)
        if not suite or suite.get("user_id") != current_user.id:
            raise HTTPException(404, "套件不存在")
        scenario_ids = list(suite["scenario_ids"])
        suite_name = suite["name"]

    global _run_id_seq
    async with _suites_lock:
        run_id = _run_id_seq
        _run_id_seq += 1

    # 实际执行每个场景
    results = []
    passed = 0
    failed = 0

    for sid in scenario_ids:
        result = await db.execute(
            select(AutoTestScenario).where(AutoTestScenario.id == sid, AutoTestScenario.user_id == current_user.id)
        )
        sc = result.scalar_one_or_none()
        if not sc:
            scenario_result = {
                "scenario_id": sid,
                "scenario_name": "未知",
                "status": "error",
                "message": "场景不存在",
                "duration_ms": 0,
            }
            results.append(scenario_result)
            failed += 1
            continue
        if not sc.is_active:
            scenario_result = {
                "scenario_id": sid,
                "scenario_name": sc.name,
                "status": "skipped",
                "message": "场景已停用",
                "duration_ms": 0,
            }
            results.append(scenario_result)
            failed += 1
            continue

        # 实际执行场景
        import time as _time

        t0 = _time.time()
        try:
            from fastapi_backend.services.autotest_scenario_runner import run_scenario as _run_scenario

            exec_result = await _run_scenario(sid, env_id=None, user_id=current_user.id)
            duration_ms = int((_time.time() - t0) * 1000)
            exec_failed = exec_result.get("failed_steps", 0) > 0
            scenario_result = {
                "scenario_id": sid,
                "scenario_name": sc.name,
                "status": "failed" if exec_failed else "success",
                "message": f"完成: {exec_result.get('success_steps', 0)} 成功, {exec_result.get('failed_steps', 0)} 失败",
                "duration_ms": duration_ms,
            }
            if exec_failed:
                failed += 1
            else:
                passed += 1
        except Exception as e:
            duration_ms = int((_time.time() - t0) * 1000)
            scenario_result = {
                "scenario_id": sid,
                "scenario_name": sc.name,
                "status": "error",
                "message": str(e)[:200],
                "duration_ms": duration_ms,
            }
            failed += 1
        results.append(scenario_result)

    run_record = {
        "run_id": run_id,
        "suite_id": suite_id,
        "suite_name": suite_name,
        "total": len(scenario_ids),
        "passed": passed,
        "failed": failed,
        "results": results,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    async with _suites_lock:
        _runs.setdefault(suite_id, []).append(run_record)

    return run_record


@router.get("/{suite_id}/runs")
async def get_suite_runs(suite_id: int, current_user: User = Depends(get_current_active_user)):
    """获取套件的执行历史"""
    async with _suites_lock:
        suite = _suites.get(suite_id)
        if not suite or suite.get("user_id") != current_user.id:
            raise HTTPException(404, "套件不存在")
        runs = list(_runs.get(suite_id, []))
    return {"runs": runs, "total": len(runs)}
