"""
回归测试套件路由

创建、管理、执行测试套件（多个场景的集合）
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from datetime import datetime, timezone
from pathlib import Path
import asyncio
import copy
import json
import os

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestScenario
from fastapi_backend.models.models import User

router = APIRouter(prefix="/api/auto-test/suites", tags=["回归套件"])

# 持久化存储：通过 JSON 文件保存套件数据，避免服务重启后丢失
# 注意：套件当前使用JSON文件+内存字典存储，DB模型TestSuite/TestSuiteCase/TestSuiteExecution未使用
# TODO: 未来版本应迁移到DB存储以支持多Worker共享
_SUITES_FILE = Path(__file__).parent.parent / "autotest_data" / "suites.json"
_SUITES_FILE.parent.mkdir(parents=True, exist_ok=True)
_RUNS_FILE = _SUITES_FILE.parent / "runs" / "runs.json"


def _load_suites() -> dict:
    if _SUITES_FILE.exists():
        try:
            return {int(k): v for k, v in json.loads(_SUITES_FILE.read_text(encoding="utf-8")).items()}
        except Exception:
            return {}
    return {}


def _save_suites(suites: dict) -> None:
    try:
        _SUITES_FILE.write_text(
            json.dumps({str(k): v for k, v in suites.items()}, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except Exception:
        pass


def _save_runs_to_file() -> None:
    """持久化执行记录到文件"""
    try:
        _RUNS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _RUNS_FILE.write_text(
            json.dumps({str(k): v for k, v in _runs.items()}, ensure_ascii=False, default=str),
            encoding="utf-8",
        )
    except Exception:
        pass


def _load_runs_from_file() -> None:
    """从文件加载执行记录"""
    if _RUNS_FILE.exists():
        try:
            loaded = json.loads(_RUNS_FILE.read_text(encoding="utf-8"))
            # JSON的key是str，需要转回int
            for k, v in loaded.items():
                _runs[int(k)] = v
        except Exception:
            pass


_suites: Dict[int, dict] = _load_suites()
_suite_id_seq = max(_suites.keys(), default=0) + 1
_runs: Dict[int, list] = {}
_load_runs_from_file()
# 根据已加载的执行记录初始化 _run_id_seq，避免重启后ID冲突
_max_run_id = 0
for _records in _runs.values():
    for _rec in _records:
        _max_run_id = max(_max_run_id, _rec.get("run_id", 0) if isinstance(_rec, dict) else 0)
_run_id_seq = _max_run_id + 1
_suites_lock = asyncio.Lock()


@router.get("")
async def list_suites(current_user: User = Depends(require_permissions("suite:read"))):
    """列出当前用户的测试套件"""
    async with _suites_lock:
        suites_list = [
            {"id": k, "name": v["name"], "scenario_count": len(v["scenario_ids"]), "created_at": v["created_at"]}
            for k, v in _suites.items()
            if v.get("user_id") == current_user.id
        ]
    return {"suites": suites_list, "total": len(suites_list)}


@router.post("")
@audit_log(action="create", resource_type="suite")
async def create_suite(
    body: Dict[str, Any],
    request: Request,
    current_user: User = Depends(require_permissions("suite:create")),
    db: AsyncSession = Depends(get_autotest_db),
):
    """创建测试套件"""
    scenario_ids = body.get("scenario_ids", [])
    # 去重 scenario_ids（保持顺序）
    scenario_ids = list(dict.fromkeys(scenario_ids))
    # 校验每个 scenario_id 是否存在
    # 注意：场景校验的 DB 查询在 _suites_lock 之外执行，避免持锁等待 DB IO
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
        _save_suites(_suites)
    return {"id": sid, "message": "套件创建成功"}


@router.delete("/{suite_id}")
@audit_log(action="delete", resource_type="suite", resource_id_param="suite_id")
async def delete_suite(
    suite_id: int,
    request: Request,
    current_user: User = Depends(get_current_active_user),
):
    """删除测试套件"""
    async with _suites_lock:
        if suite_id in _suites and _suites[suite_id].get("user_id") == current_user.id:
            del _suites[suite_id]
            _save_suites(_suites)
            # 清理关联的运行记录
            _runs.pop(suite_id, None)
            _save_runs_to_file()
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
        # 在锁内深拷贝快照，避免释放锁后被并发修改导致竞态条件
        suite = copy.deepcopy(suite)

    scenario_ids = list(suite.get("scenario_ids", []))

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

    return {"suite": {**suite, "scenario_ids": list(suite.get("scenario_ids", [])), "scenarios": scenario_details}}


@router.post("/{suite_id}/run")
@audit_log(action="execute", resource_type="suite", resource_id_param="suite_id")
async def run_suite(
    suite_id: int,
    request: Request,
    body: Dict[str, Any] = None,
    current_user: User = Depends(require_permissions("suite:execute")),
    db: AsyncSession = Depends(get_autotest_db),
):
    """执行回归测试套件"""
    async with _suites_lock:
        suite = _suites.get(suite_id)
        if not suite or suite.get("user_id") != current_user.id:
            raise HTTPException(404, "套件不存在")
        scenario_ids = list(suite["scenario_ids"])
        suite_name = suite["name"]
        suite_env_id = suite.get("env_id")

    # 从请求参数获取 env_id，未传则回退到套件配置
    env_id = body.get("env_id") if body else None
    if env_id is None:
        env_id = suite_env_id

    global _run_id_seq
    async with _suites_lock:
        run_id = _run_id_seq
        _run_id_seq += 1

    # 实际执行每个场景
    results = []
    passed = 0
    failed = 0
    skipped = 0

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
            skipped += 1
            continue

        # 实际执行场景
        import time as _time

        t0 = _time.time()
        try:
            from fastapi_backend.services.autotest_scenario_runner import run_scenario as _run_scenario

            exec_result = await _run_scenario(sid, env_id=env_id, user_id=current_user.id)
            duration_ms = int((_time.time() - t0) * 1000)
            exec_failed = not exec_result.get("success", False)
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
        "skipped": skipped,
        "results": results,
        "started_at": datetime.now(timezone.utc).isoformat(),
    }
    async with _suites_lock:
        _runs.setdefault(suite_id, []).append(run_record)
        _save_runs_to_file()

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
