"""
AutoTest 统一路由 - 执行、历史、调度、邮件、导入导出

路径前缀: /api/auto-test/...
映射原 auto_test_platform main.py 中的内联端点
"""

import json
import logging
import subprocess
import uuid
import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form, BackgroundTasks, Request
from pydantic import BaseModel, model_validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.core.audit_decorator import audit_log
from fastapi_backend.core.rbac import require_permissions
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import (
    AutoTestCase,
    AutoTestEnvironment,
    AutoTestHistory,
    AutoTestScenario,
    AutoTestScenarioExecutionRecord,
    AutoTestGroup,
)
from fastapi_backend.models.models import User
from fastapi_backend.schemas.autotest import (
    AutoTestHistoryResponse,
    CaseExecutionResult,
    CaseRunRequest,
    ScheduleTaskCreate,
    ScheduleTaskResponse,
    EmailConfig,
    TestEmailRequest,
    VariablePreviewRequest,
    VariablePreviewResponse,
)
from fastapi_backend.utils.parser import replace_variables, find_variables
from fastapi_backend.core.ssrf_guard import validate_url_safety

router = APIRouter(prefix="/api/auto-test", tags=["AutoTest-执行与工具"])

# 项目根目录（routers/autotest_execution.py -> fastapi_backend/ -> TestMasterProject/）
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# 模块级后台任务集合，持有 task 引用避免被 GC 回收
_background_tasks: set = set()
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"
TASKS_DIR = AUTOTEST_DATA_DIR / "tasks"

# ========== 任务状态管理 ==========
from fastapi_backend.services.autotest_task_store import get_task, update_task


def _build_stored_task_result(stored: dict) -> Optional[dict]:
    if not stored:
        return None
    if isinstance(stored.get("result"), dict):
        return stored["result"]
    result = {
        key: value
        for key, value in stored.items()
        if key
        not in {
            "task_id",
            "status",
            "state",
            "info",
            "progress",
            "traceback",
            "created_at",
            "updated_at",
            "completed_at",
        }
    }
    return result or None


def _should_run_scenario_locally() -> bool:
    """开发环境兜底：没有可用 Celery worker 时，回退到当前 FastAPI 进程异步执行。"""
    try:
        from fastapi_backend.tasks import celery_app

        broker_url = str(celery_app.conf.broker_url or "")
        if broker_url.startswith("memory://"):
            return True

        inspect = celery_app.control.inspect(timeout=0.5)
        active_workers = inspect.ping() or {}
        return not bool(active_workers)
    except Exception:
        return True


async def _run_scenario_locally(task_id: str, scenario_id: int, env_id: Optional[int], user_id: int = None) -> None:
    logger = logging.getLogger(__name__)

    try:
        from fastapi_backend.services.autotest_scenario_runner import (
            run_scenario as execute_scenario_async,
        )

        def on_progress(current_step, total_steps, step_name):
            percent = min(int((current_step / total_steps) * 100), 100) if total_steps > 0 else 0
            progress_data = {
                "task_id": task_id,
                "scenario_id": scenario_id,
                "status": "PROGRESS",
                "info": f"执行中: {step_name}",
                "progress": {
                    "percent": percent,
                    "current": current_step,
                    "total": total_steps,
                    "current_api": step_name,
                    "current_step": current_step,
                    "total_steps": total_steps,
                    "step_name": step_name,
                },
                "updated_at": time.time(),
            }
            try:
                # 优先使用 get_running_loop（Python 3.10+ 推荐）
                loop = asyncio.get_running_loop()
                # 在同一事件循环内用 create_task，避免 run_coroutine_threadsafe 不等待的问题
                loop.create_task(update_task(task_id, progress_data))
            except RuntimeError:
                # 不在事件循环线程中，回退到线程安全方式
                try:
                    loop = asyncio.get_event_loop()
                    asyncio.run_coroutine_threadsafe(update_task(task_id, progress_data), loop)
                except RuntimeError:
                    logger.warning("无法更新任务进度: 事件循环不可用")

        result = await execute_scenario_async(scenario_id, env_id, progress_callback=on_progress, user_id=user_id)
        result["task_id"] = task_id
        result["status"] = "completed"
        result["scenario_id"] = scenario_id

        await update_task(
            task_id,
            {
                "task_id": task_id,
                "scenario_id": scenario_id,
                "status": "completed",
                "info": "任务执行成功",
                "progress": {
                    "percent": 100,
                    "current": result.get("total_steps", 0),
                    "total": result.get("total_steps", 0),
                    "current_api": "执行完成",
                    "current_step": result.get("total_steps", 0),
                    "total_steps": result.get("total_steps", 0),
                    "step_name": "执行完成",
                },
                "result": result,
                "completed_at": time.time(),
            },
        )
    except Exception as exc:
        logger.error("本地异步执行场景失败 task_id=%s: %s", task_id, exc, exc_info=True)
        await update_task(
            task_id,
            {
                "task_id": task_id,
                "scenario_id": scenario_id,
                "status": "failed",
                "info": f"任务失败: {str(exc)[:100]}",
                "error": str(exc),
                "completed_at": time.time(),
            },
        )


# ========== 接口调试发送 ==========

from fastapi_backend.utils.autotest_helpers import convert_to_dict
from fastapi_backend.services.autotest_report_service import write_allure_results


@router.post("/send")
async def send_request(
    payload: dict,
    current_user: User = Depends(get_current_active_user),
):
    from fastapi_backend.services.autotest_request_service import execute_http_request
    from fastapi_backend.schemas.autotest import AutoTestRequestConfig
    from pydantic import ValidationError

    url = payload.get("url", "")
    if not url:
        raise HTTPException(status_code=400, detail="URL 不能为空")
    method = payload.get("method", "GET").upper()
    valid_methods = {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}
    if method not in valid_methods:
        raise HTTPException(status_code=400, detail=f"不支持的 HTTP 方法: {method}")
    safe, reason = validate_url_safety(url)
    if not safe:
        raise HTTPException(status_code=400, detail=reason)
    try:
        try:
            validated_config = AutoTestRequestConfig.model_validate(payload.get("request_config") or {})
        except ValidationError as validation_error:
            raise HTTPException(status_code=422, detail=validation_error.errors())
        result = await execute_http_request(
            method=method,
            url=url,
            headers=convert_to_dict(payload.get("headers")),
            params=convert_to_dict(payload.get("params")),
            body=payload["body"] if "body" in payload else payload.get("payload"),
            body_type=payload.get("body_type", "json"),
            env_id=payload.get("env_id"),
            variables=convert_to_dict(payload.get("variables")),
            user_id=current_user.id,
            request_config=validated_config.model_dump(by_alias=True),
        )
        result.pop("_raw_headers", None)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== Celery 任务状态管理 ==========


@router.get("/tasks/{task_id}")
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """获取任务状态：非终态优先读 Celery 实时状态，终态读持久化存储"""
    # 定义终态列表

    # 1. 先查 Celery 实时状态（获取最新进度）
    celery_state = None
    celery_meta = {}
    try:
        from celery.result import AsyncResult
        from fastapi_backend.tasks import celery_app

        task_result = AsyncResult(task_id, app=celery_app)
        celery_state = task_result.state
        celery_meta = task_result.info or {}
    except Exception:
        pass

    # 2. 再查持久化存储
    stored = await get_task(task_id)

    # 2.5 校验任务归属
    if stored and stored.get("user_id") and stored["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="任务不存在")

    # 2.6 无持久化记录时无法校验归属，拒绝返回 Celery 状态
    if stored is None:
        return {"task_id": task_id, "status": "UNKNOWN", "state": "UNKNOWN", "info": "任务不存在或已过期"}

    # 3. 如果持久化存储已标记为终态（如 cancelled），优先使用持久化状态
    TERMINAL_STORED_STATUSES = {"cancelled", "completed", "failed"}
    if stored and stored.get("status") in TERMINAL_STORED_STATUSES:
        stored_status = stored["status"]
        return {
            "task_id": task_id,
            "status": stored_status,
            "state": stored_status,
            "info": stored.get("info", ""),
            "progress": stored.get("progress"),
            "result": _build_stored_task_result(stored),
            "error": stored.get("error"),
            "traceback": stored.get("traceback"),
        }

    # 4. 如果 Celery 有实时状态且任务非终态，优先使用 Celery 状态
    if celery_state and celery_state not in ("PENDING",):
        if celery_state == "PROGRESS":
            meta = celery_meta if isinstance(celery_meta, dict) else {}
            # 同时更新持久化存储
            if stored:
                stored["status"] = "PROGRESS"
                stored["info"] = f"执行中: {meta.get('step_name', '...')}"
                # 合并旧的 progress 保留 env_id 等字段
                old_progress = stored.get("progress", {}) if isinstance(stored.get("progress"), dict) else {}
                stored["progress"] = {
                    **old_progress,
                    "percent": meta.get("percent", old_progress.get("percent", 0)),
                    "current": meta.get("current", old_progress.get("current", 0)),
                    "total": meta.get("total", old_progress.get("total", 0)),
                    "current_api": meta.get("current_api", old_progress.get("current_api", "执行中...")),
                    "current_step": meta.get("current_step", old_progress.get("current_step", 0)),
                    "total_steps": meta.get("total_steps", old_progress.get("total_steps", 0)),
                    "step_name": meta.get("step_name", old_progress.get("step_name", "执行中...")),
                }
                await update_task(task_id, stored)
            return {
                "task_id": task_id,
                "status": "PROGRESS",
                "state": "PROGRESS",
                "progress": {
                    "percent": meta.get("percent", 0),
                    "current": meta.get("current", 0),
                    "total": meta.get("total", 0),
                    "current_api": meta.get("current_api", "执行中..."),
                    "current_step": meta.get("current_step", 0),
                    "total_steps": meta.get("total_steps", 0),
                    "step_name": meta.get("step_name", "执行中..."),
                },
                "info": f"执行中: {meta.get('step_name', '...')}",
            }
        elif celery_state == "STARTED":
            return {
                "task_id": task_id,
                "status": "STARTED",
                "state": "STARTED",
                "progress": {"percent": 5, "current": 0, "total": 0, "current_api": "启动中..."},
                "info": "任务启动中",
            }
        elif celery_state == "SUCCESS":
            # SUCCESS 状态：优先从持久化存储读取完整结果（包含 step_results）
            # Celery 通过 Redis 传输大结果时可能丢失 step_results
            result = None
            if stored and stored.get("result"):
                result = stored["result"]
            elif celery_meta and not isinstance(celery_meta, Exception):
                result = celery_meta
            else:
                result = {}

            # 如果持久化存储有进度信息，也使用它
            final_progress = {"percent": 100, "current": 0, "total": 0, "current_api": "执行完成"}
            if stored and stored.get("progress"):
                final_progress = stored["progress"]

            return {
                "task_id": task_id,
                "status": "completed",
                "state": "SUCCESS",
                "result": result,
                "progress": final_progress,
                "info": stored.get("info", "任务执行成功") if stored else "任务执行成功",
            }
        elif celery_state == "FAILURE":
            error_str = str(celery_meta) if isinstance(celery_meta, Exception) else str(celery_meta)
            return {
                "task_id": task_id,
                "status": "failed",
                "state": "FAILURE",
                "error": error_str,
                "info": f"任务失败: {error_str[:100]}",
            }

    # 5. 查持久化存储（终态或 Celery 无状态）
    if stored is not None:
        stored_status = stored.get("status", "UNKNOWN")
        return {
            "task_id": task_id,
            "status": stored_status,
            "state": stored_status,
            "info": stored.get("info", ""),
            "progress": stored.get("progress"),
            "result": _build_stored_task_result(stored),
            "error": stored.get("error"),
            "traceback": stored.get("traceback"),
        }

    # 6. 未知任务
    return {"task_id": task_id, "status": "UNKNOWN", "state": "UNKNOWN", "info": "任务不存在或状态已失效"}


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """取消任务，优先更新持久化存储，同时撤销 Celery 任务"""
    stored = await get_task(task_id)

    # 未知任务（不在持久化层也不在 Celery）直接返回
    if stored is None:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")

    # 校验任务归属
    if stored.get("user_id") and stored["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="任务不存在")

    current_status = stored.get("status", "")
    if current_status in ("completed", "failed", "cancelled"):
        return {"message": f"任务已处于 {current_status} 状态，无法取消", "task_id": task_id}

    try:
        from celery.result import AsyncResult
        from fastapi_backend.tasks import celery_app

        task_result = AsyncResult(task_id, app=celery_app)
        if not task_result.ready():
            task_result.revoke(terminate=True)
    except Exception:
        pass  # Celery 撤销失败不影响最终结果

    # 更新持久化状态
    stored["status"] = "cancelled"
    stored["info"] = "任务已被取消"
    stored["completed_at"] = time.time()
    await update_task(task_id, stored)

    scenario_id = stored.get("scenario_id")
    if scenario_id:
        progress = stored.get("progress") or {}
        current_steps = progress.get("current") or progress.get("current_step") or 0
        total_steps = progress.get("total") or progress.get("total_steps") or 0
        cancelled_record = AutoTestScenarioExecutionRecord(
            scenario_id=scenario_id,
            env_id=stored.get("env_id"),
            status="cancelled",
            total_steps=total_steps,
            failed_steps=0,
            success_steps=max(0, min(current_steps, total_steps)) if total_steps else 0,
            skipped_steps=max(total_steps - current_steps, 0) if total_steps else 0,
            total_time=None,
            report_url=None,
        )
        db.add(cancelled_record)
        try:
            await db.commit()
        except Exception as db_err:
            await db.rollback()
            logging.getLogger(__name__).error("取消任务时写入执行记录失败: %s", db_err)

    return {"message": "任务取消成功", "task_id": task_id}


# ========== 报告详情 ==========


@router.get("/reports/{report_id}")
async def get_report_detail(
    report_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取执行报告详情"""
    from fastapi_backend.services.autotest_report_service import get_report_detail as _get_report

    result = await _get_report(report_id, db, user_id=current_user.id)
    if result is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    # 校验报告关联的场景归属
    if result.get("scenario_id"):
        scenario_result = await db.execute(
            select(AutoTestScenario).where(
                AutoTestScenario.id == result["scenario_id"],
                AutoTestScenario.user_id == current_user.id,
            )
        )
        if not scenario_result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="报告不存在")
    return result


@router.post("/utils/preview", response_model=VariablePreviewResponse)
async def preview_variables(
    request: VariablePreviewRequest,
    current_user: User = Depends(get_current_active_user),
):
    """预览变量替换效果"""
    result = replace_variables(request.text, request.variables)
    found = find_variables(request.text)
    return VariablePreviewResponse(
        original=request.text,
        result=result,
        found_variables=found,
    )


# ========== 用例执行接口 ==========


@router.post("/cases/{case_id}/run")
@audit_log(action="execute", resource_type="case", resource_id_param="case_id")
async def run_case(
    case_id: int,
    request: Request,
    body: CaseRunRequest = None,
    current_user: User = Depends(require_permissions("case:execute")),
    db: AsyncSession = Depends(get_db),
):
    """执行用例并保存历史记录，返回完整执行结果"""
    env_id = body.env_id if body else None
    result = await db.execute(
        select(AutoTestCase).where(AutoTestCase.id == case_id, AutoTestCase.user_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    import logging

    logger = logging.getLogger(__name__)
    logger.info(f"[run_case] case_id={case_id}, DB中查出的Params: {case.params}, type={type(case.params)}")

    env = None
    if env_id:
        try:
            env_id_int = int(env_id)
            if env_id_int <= 0:
                raise HTTPException(status_code=400, detail=f"无效的环境 ID: {env_id}")
            result = await db.execute(
                select(AutoTestEnvironment).where(
                    AutoTestEnvironment.id == env_id_int, AutoTestEnvironment.user_id == current_user.id
                )
            )
            env = result.scalar_one_or_none()
            if env is None:
                raise HTTPException(status_code=400, detail=f"环境 ID {env_id} 不存在")
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"无效的环境 ID: {env_id}")
    if env is None:
        result = await db.execute(
            select(AutoTestEnvironment).where(
                AutoTestEnvironment.is_default.is_(True), AutoTestEnvironment.user_id == current_user.id
            )
        )
        env = result.scalars().first()
        if not env:
            result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.user_id == current_user.id))
            env = result.scalars().first()

    from fastapi_backend.services.autotest_execution import quick_run_case

    result_data = await quick_run_case(case, env, user_id=current_user.id)

    history = AutoTestHistory(
        case_id=case_id,
        status="success" if result_data.get("success", False) else "failed",
        execution_time=result_data.get("execution_time", 0),
        response_data=result_data.get("response"),
        error_message=result_data.get("error"),
        user_id=current_user.id,
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)

    result_data["history_id"] = history.id
    return result_data


@router.post("/cases/{case_id}/quick-run", response_model=CaseExecutionResult)
async def quick_run(
    case_id: int,
    body: CaseRunRequest = None,
    p: str = Query(None, description="已替换变量的请求参数字符串（JSON）"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """快速执行用例（结果自动保存历史记录）"""
    env_id = body.env_id if body else None
    result = await db.execute(
        select(AutoTestCase).where(AutoTestCase.id == case_id, AutoTestCase.user_id == current_user.id)
    )
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    env = None
    if env_id:
        try:
            env_id_int = int(env_id)
            if env_id_int > 0:
                result = await db.execute(
                    select(AutoTestEnvironment).where(
                        AutoTestEnvironment.id == env_id_int, AutoTestEnvironment.user_id == current_user.id
                    )
                )
                env = result.scalar_one_or_none()
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail=f"无效的环境 ID: {env_id}")

    if env is None:
        result = await db.execute(
            select(AutoTestEnvironment).where(
                AutoTestEnvironment.is_default.is_(True), AutoTestEnvironment.user_id == current_user.id
            )
        )
        env = result.scalars().first()
        if not env:
            result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.user_id == current_user.id))
            env = result.scalars().first()

    # 🔥 解析前端传来的 p（已替换变量的请求参数字符串）
    override_params = None
    if p:
        if isinstance(p, str):
            try:
                override_params = json.loads(p)
            except json.JSONDecodeError:
                override_params = None
        else:
            override_params = p

    from fastapi_backend.services.autotest_execution import quick_run_case

    result_data = await quick_run_case(case, env, override_params=override_params, user_id=current_user.id)

    history = AutoTestHistory(
        case_id=case_id,
        status="success" if result_data.get("success") else "failed",
        execution_time=result_data.get("execution_time") or result_data.get("response_time", 0),
        response_data=result_data.get("response"),
        error_message=result_data.get("error"),
        user_id=current_user.id,
    )
    db.add(history)
    await db.commit()
    await db.refresh(history)

    result_data["history_id"] = history.id
    return CaseExecutionResult(**result_data)


class BatchRunRequest(BaseModel):
    case_ids: List[int]
    env_id: Optional[int] = None
    concurrency: int = 10

    @model_validator(mode="before")
    @classmethod
    def accept_legacy_case_id_list(cls, value):
        return {"case_ids": value} if isinstance(value, list) else value

    @model_validator(mode="after")
    def validate_concurrency(self):
        if not 1 <= self.concurrency <= 20:
            raise ValueError("并发数必须在 1 到 20 之间")
        return self


async def _run_case_batch_task(task_id: str, body: BatchRunRequest, user_id: int) -> None:
    from fastapi_backend.core.autotest_database import AsyncSessionLocal
    from fastapi_backend.services.autotest_execution import quick_run_case

    results = []
    try:
        async with AsyncSessionLocal() as session:
            case_result = await session.execute(
                select(AutoTestCase).where(AutoTestCase.id.in_(body.case_ids), AutoTestCase.user_id == user_id)
            )
            case_map = {case.id: case for case in case_result.scalars().all()}
            cases = [case_map[case_id] for case_id in body.case_ids if case_id in case_map]
            env = None
            if body.env_id:
                env_result = await session.execute(
                    select(AutoTestEnvironment).where(
                        AutoTestEnvironment.id == body.env_id, AutoTestEnvironment.user_id == user_id
                    )
                )
                env = env_result.scalar_one_or_none()

            total = len(cases)
            queue = asyncio.Queue()
            for case in cases:
                queue.put_nowait(case)
            result_lock = asyncio.Lock()

            async def worker():
                while not queue.empty():
                    stored = await get_task(task_id)
                    if stored and (stored.get("cancelled") or stored.get("status") == "cancelled"):
                        return
                    try:
                        case = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        return
                    try:
                        execution = await quick_run_case(case, env, user_id=user_id)
                    except Exception as exc:
                        execution = {"success": False, "error": str(exc), "execution_time": 0}
                    async with result_lock:
                        results.append({"case_id": case.id, "case_name": case.name, **execution})
                        session.add(
                            AutoTestHistory(
                                case_id=case.id,
                                user_id=user_id,
                                status="success" if execution.get("success") else "failed",
                                execution_time=execution.get("execution_time") or 0,
                                response_data=execution.get("response"),
                                error_message=execution.get("error"),
                            )
                        )
                        await session.commit()
                        completed = len(results)
                        succeeded = sum(1 for item in results if item.get("success"))
                        await update_task(
                            task_id,
                            {
                                "status": "PROGRESS",
                                "user_id": user_id,
                                "progress": {
                                    "current": completed,
                                    "total": total,
                                    "percent": int(completed * 100 / max(total, 1)),
                                    "current_api": case.name,
                                },
                                "result": {
                                    "total": total,
                                    "completed": completed,
                                    "success": succeeded,
                                    "failed": completed - succeeded,
                                    "results": list(results),
                                },
                            },
                        )
                    queue.task_done()

            await asyncio.gather(*[worker() for _ in range(min(body.concurrency, max(total, 1)))])
            stored = await get_task(task_id)
            if stored and (stored.get("cancelled") or stored.get("status") == "cancelled"):
                return
            success = sum(1 for item in results if item.get("success"))
            result_payload = {"total": total, "success": success, "failed": total - success, "results": results}
            await update_task(
                task_id,
                {
                    "status": "completed",
                    "state": "completed",
                    "user_id": user_id,
                    "progress": {"current": total, "total": total, "percent": 100, "current_api": "执行完成"},
                    "result": result_payload,
                    "completed_at": time.time(),
                },
            )
    except Exception as exc:
        await update_task(
            task_id,
            {"status": "failed", "state": "failed", "user_id": user_id, "error": str(exc), "completed_at": time.time()},
        )


@router.post("/cases/batch-run-async", status_code=202)
async def start_batch_run(
    body: BatchRunRequest,
    current_user: User = Depends(get_current_active_user),
):
    if not body.case_ids:
        raise HTTPException(status_code=400, detail="请提供至少一个用例 ID")
    if len(body.case_ids) > 500:
        raise HTTPException(status_code=400, detail="单次后台批量运行最多支持 500 个用例")
    task_id = f"case-batch-{uuid.uuid4()}"
    await update_task(
        task_id,
        {
            "task_id": task_id,
            "task_type": "case_batch",
            "status": "PENDING",
            "state": "PENDING",
            "user_id": current_user.id,
            "progress": {"current": 0, "total": len(body.case_ids), "percent": 0, "current_api": "等待执行"},
        },
    )
    task = asyncio.create_task(_run_case_batch_task(task_id, body, current_user.id))
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    return {"task_id": task_id, "status": "PENDING"}


@router.post("/cases/batch-run")
async def batch_run(
    body: BatchRunRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """批量执行多个用例（并发执行）"""
    case_ids = body.case_ids
    env_id = body.env_id
    if not case_ids:
        raise HTTPException(status_code=400, detail="请提供至少一个用例ID")
    if len(case_ids) > 50:
        raise HTTPException(status_code=400, detail="单次批量执行最多支持 50 个用例")
    result = await db.execute(
        select(AutoTestCase).where(AutoTestCase.id.in_(case_ids), AutoTestCase.user_id == current_user.id)
    )
    cases = result.scalars().all()

    env = None
    if env_id:
        result = await db.execute(
            select(AutoTestEnvironment).where(
                AutoTestEnvironment.id == env_id, AutoTestEnvironment.user_id == current_user.id
            )
        )
        env = result.scalar_one_or_none()
    else:
        result = await db.execute(
            select(AutoTestEnvironment).where(
                AutoTestEnvironment.is_default.is_(True), AutoTestEnvironment.user_id == current_user.id
            )
        )
        env = result.scalars().first()
        if not env:
            result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.user_id == current_user.id))
            env = result.scalars().first()

    from fastapi_backend.services.autotest_execution import quick_run_case

    total = len(cases)

    # 并发执行（最多10个并发）
    import asyncio

    semaphore = asyncio.Semaphore(10)

    async def run_with_limit(case):
        async with semaphore:
            return await quick_run_case(case, env, user_id=current_user.id)

    results = await asyncio.gather(*[run_with_limit(c) for c in cases], return_exceptions=True)

    formatted_results = []
    success_count = 0
    for case, result in zip(cases, results):
        if isinstance(result, Exception):
            formatted_results.append(
                {"case_id": case.id, "case_name": case.name, "success": False, "error": str(result)}
            )
        else:
            success_count += 1 if result.get("success", False) else 0
            formatted_results.append({"case_id": case.id, "case_name": case.name, **result})

    # 批量执行也保存历史记录，与 run_case/quick_run 保持一致
    for case, result in zip(cases, results):
        if isinstance(result, Exception):
            history = AutoTestHistory(
                case_id=case.id,
                status="failed",
                execution_time=0,
                error_message=str(result),
                user_id=current_user.id,
            )
        else:
            _et = result.get("execution_time")
            execution_time = _et if _et is not None else result.get("response_time", 0)
            history = AutoTestHistory(
                case_id=case.id,
                status="success" if result.get("success", False) else "failed",
                execution_time=execution_time,
                response_data=result.get("response"),
                error_message=result.get("error"),
                user_id=current_user.id,
            )
        db.add(history)
    await db.commit()

    return {"total": total, "success": success_count, "failed": total - success_count, "results": formatted_results}


# ========== 测试历史接口 ==========


@router.get("/history")
async def get_history(
    case_id: int = None,
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取执行历史记录"""
    # 参数校验
    limit = max(1, min(limit, 100))  # 限制1-100
    offset = max(0, offset)

    query = (
        select(AutoTestHistory)
        .where(AutoTestHistory.user_id == current_user.id)
        .order_by(desc(AutoTestHistory.created_at))
    )
    if case_id:
        query = query.where(AutoTestHistory.case_id == case_id)

    # 先查总数
    from sqlalchemy import func as sa_func

    count_base = select(AutoTestHistory).where(AutoTestHistory.user_id == current_user.id)
    if case_id:
        count_base = count_base.where(AutoTestHistory.case_id == case_id)
    count_query = select(sa_func.count()).select_from(count_base.subquery())
    total = (await db.execute(count_query)).scalar_one()

    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    history = result.scalars().all()
    items = [AutoTestHistoryResponse.model_validate(h).model_dump() for h in history]
    return {"items": items, "total": total, "limit": limit, "offset": offset}


@router.delete("/history/{history_id}", status_code=204)
async def delete_history(
    history_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除历史记录"""
    result = await db.execute(
        select(AutoTestHistory).where(AutoTestHistory.id == history_id, AutoTestHistory.user_id == current_user.id)
    )
    history = result.scalar_one_or_none()
    if not history:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    await db.delete(history)
    await db.commit()
    return None


@router.get("/history/{history_id}", response_model=AutoTestHistoryResponse)
async def get_history_detail(
    history_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取历史记录详情"""
    result = await db.execute(
        select(AutoTestHistory).where(AutoTestHistory.id == history_id, AutoTestHistory.user_id == current_user.id)
    )
    history = result.scalar_one_or_none()
    if not history:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return history


# ========== 场景执行接口 ==========


@router.post("/scenarios/{scenario_id}/run")
@audit_log(action="execute", resource_type="scenario", resource_id_param="scenario_id")
async def run_scenario(
    scenario_id: int,
    request: Request,
    body: CaseRunRequest = None,
    background: bool = True,
    current_user: User = Depends(require_permissions("scenario:execute")),
):
    """执行测试场景，使用Celery异步任务"""
    env_id = body.env_id if body else None
    try:
        from fastapi_backend.core.autotest_database import AsyncSessionLocal
        from fastapi_backend.models.autotest import AutoTestScenario
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AutoTestScenario).where(
                    AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id
                )
            )
            scenario = result.scalar_one_or_none()
            if not scenario:
                raise HTTPException(status_code=404, detail="场景不存在")
            if not scenario.is_active:
                raise HTTPException(status_code=400, detail="场景已停用，禁止执行")

        from fastapi_backend.tasks import task_run_scenario
        from fastapi_backend.services.autotest_task_store import update_task as seed_task

        logger = logging.getLogger(__name__)

        task_id = None
        use_local_runner = _should_run_scenario_locally()

        if use_local_runner:
            task_id = str(uuid.uuid4())
            logger.warning(
                "未检测到可用 Celery worker，场景执行切换为本地异步模式: scenario_id=%s, env_id=%s, task_id=%s",
                scenario_id,
                env_id,
                task_id,
            )
        else:
            logger.info(f"准备发送Celery任务: scenario_id={scenario_id}, env_id={env_id}")
            task = task_run_scenario.delay(scenario_id, env_id, current_user.id)
            if task is None:
                raise ValueError("Celery任务创建失败，task为None")
            task_id = task.id
            if not task_id:
                raise ValueError("Celery任务ID为空，任务可能未成功发送")

        # 写入初始持久化记录，确保查询接口能追踪到该任务
        await seed_task(
            task_id,
            {
                "task_id": task_id,
                "scenario_id": scenario_id,
                "env_id": env_id,
                "user_id": current_user.id,
                "status": "PROGRESS",
                "info": "任务已提交，正在后台执行",
                "progress": {"percent": 0, "current": 0, "total": 0, "current_api": "等待执行..."},
                "created_at": time.time(),
            },
        )

        if use_local_runner:
            task = asyncio.create_task(_run_scenario_locally(task_id, scenario_id, env_id, user_id=current_user.id))
            _background_tasks.add(task)

            # 添加回调追踪异常，防止任务静默失败
            def _on_task_done(t: asyncio.Task):
                if t.cancelled():
                    return
                exc = t.exception()
                if exc:
                    logger.error(f"本地异步任务 {task_id} 执行异常: {exc}", exc_info=exc)

            task.add_done_callback(_background_tasks.discard)
            task.add_done_callback(_on_task_done)
            logger.info(f"本地异步任务已启动，任务ID: {task_id}")
        else:
            logger.info(f"Celery任务已发送，任务ID: {task_id}")

        # 立即返回任务ID，前端可以轮询状态
        return {
            "task_id": task_id,
            "scenario_id": scenario_id,
            "status": "PROGRESS",
            "message": "任务已提交，正在后台执行",
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger(__name__).error(f"任务提交失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")


@router.get("/scenarios/{scenario_id}/history")
async def get_scenario_execution_history(
    scenario_id: int,
    status: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = Query(20, ge=1, le=200),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """获取某个场景的执行历史记录列表"""
    result = await db.execute(
        select(AutoTestScenario).where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    # 构建查询
    query = select(AutoTestScenarioExecutionRecord).where(AutoTestScenarioExecutionRecord.scenario_id == scenario_id)

    # 状态筛选
    if status:
        normalized_status = {
            "completed": "success",
            "running": "running",
            "success": "success",
            "failed": "failed",
            "error": "error",
            "cancelled": "cancelled",
        }.get(status, status)
        query = query.where(AutoTestScenarioExecutionRecord.status == normalized_status)

    # 日期范围筛选
    if start_date:
        try:
            start_datetime = datetime.fromisoformat(start_date + "T00:00:00").replace(tzinfo=timezone.utc)
            query = query.where(AutoTestScenarioExecutionRecord.created_at >= start_datetime)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"起始日期格式无效: {start_date}")

    if end_date:
        try:
            end_datetime = datetime.fromisoformat(end_date + "T23:59:59").replace(tzinfo=timezone.utc)
            query = query.where(AutoTestScenarioExecutionRecord.created_at <= end_datetime)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"结束日期格式无效: {end_date}")

    # 先查总数（不带limit）
    from sqlalchemy import func as sa_func

    count_base = select(AutoTestScenarioExecutionRecord).where(
        AutoTestScenarioExecutionRecord.scenario_id == scenario_id
    )
    if status:
        normalized_status = {
            "completed": "success",
            "running": "running",
            "success": "success",
            "failed": "failed",
            "error": "error",
            "cancelled": "cancelled",
        }.get(status, status)
        count_base = count_base.where(AutoTestScenarioExecutionRecord.status == normalized_status)
    if start_date:
        try:
            start_datetime = datetime.fromisoformat(start_date + "T00:00:00").replace(tzinfo=timezone.utc)
            count_base = count_base.where(AutoTestScenarioExecutionRecord.created_at >= start_datetime)
        except ValueError:
            pass
    if end_date:
        try:
            end_datetime = datetime.fromisoformat(end_date + "T23:59:59").replace(tzinfo=timezone.utc)
            count_base = count_base.where(AutoTestScenarioExecutionRecord.created_at <= end_datetime)
        except ValueError:
            pass
    count_query = select(sa_func.count()).select_from(count_base.subquery())
    total = (await db.execute(count_query)).scalar_one()

    # 排序和限制
    query = query.order_by(AutoTestScenarioExecutionRecord.created_at.desc()).limit(limit)

    history_result = await db.execute(query)
    history = history_result.scalars().all()

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario.name,
        "total": total,
        "items": [
            {
                "id": rec.id,
                "env_id": rec.env_id,
                "status": rec.status,
                "total_steps": rec.total_steps,
                "success_steps": rec.success_steps,
                "failed_steps": rec.failed_steps,
                "skipped_steps": rec.skipped_steps,
                "total_time": rec.total_time,
                "report_url": rec.report_url,
                "created_at": rec.created_at,
            }
            for rec in history
        ],
    }


@router.delete("/scenarios/{scenario_id}/history/{record_id}", status_code=204)
async def delete_scenario_execution_history(
    scenario_id: int,
    record_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """删除场景执行历史记录"""
    # 验证场景存在
    result = await db.execute(
        select(AutoTestScenario).where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    # 查找并删除记录
    result = await db.execute(
        select(AutoTestScenarioExecutionRecord).where(
            AutoTestScenarioExecutionRecord.id == record_id, AutoTestScenarioExecutionRecord.scenario_id == scenario_id
        )
    )
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="执行记录不存在")

    # 删除记录
    await db.delete(record)
    await db.commit()

    # TODO: 可选删除对应的报告文件
    return None


@router.post("/scenarios/{scenario_id}/run-data-driven")
async def run_scenario_data_driven(
    scenario_id: int,
    body: CaseRunRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """数据驱动执行测试场景"""
    env_id = body.env_id
    from fastapi_backend.core.autotest_database import AsyncSessionLocal

    # 校验场景归属
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AutoTestScenario).where(
                AutoTestScenario.id == scenario_id,
                AutoTestScenario.user_id == current_user.id,
            )
        )
        scenario = result.scalar_one_or_none()
        if scenario is None:
            raise HTTPException(status_code=404, detail="场景不存在")

    # 改为后台任务执行，避免在 HTTP 请求处理器内同步运行导致超时
    task_id = str(uuid.uuid4())
    await update_task(
        task_id,
        {
            "task_id": task_id,
            "scenario_id": scenario_id,
            "user_id": current_user.id,
            "status": "running",
            "progress": 0,
            "info": "数据驱动执行已启动",
            "created_at": time.time(),
        },
    )
    background_tasks.add_task(run_scenario_data_driven_task, scenario_id, env_id, task_id, current_user.id)
    return {"task_id": task_id, "status": "running", "message": "数据驱动执行已启动"}


async def run_scenario_data_driven_task(scenario_id: int, env_id, task_id: str, user_id: int):
    """后台执行数据驱动测试场景并生成 Allure 报告"""
    from fastapi_backend.services.autotest_scenario_runner import run_scenario_data_driven as execute_data_driven

    try:
        result_data = await execute_data_driven(scenario_id, env_id, user_id=user_id)

        allure_results_dir = AUTOTEST_DATA_DIR / "allure-results" / f"scenario_{scenario_id}"
        report_dir = AUTOTEST_DATA_DIR / "reports" / f"scenario_{scenario_id}"

        import shutil as _shutil

        if allure_results_dir.exists():
            try:
                _shutil.rmtree(str(allure_results_dir))
            except Exception as e:
                logging.getLogger(__name__).warning(f"清理 allure-results 目录失败: {e}")
        allure_results_dir.mkdir(parents=True, exist_ok=True)

        history_id = str(uuid.uuid4())[:8]

        write_allure_results(allure_results_dir, scenario_id, result_data, history_id)

        try:
            import shutil

            old_report_history = report_dir / "history"
            new_results_history = allure_results_dir / "history"
            if old_report_history.exists() and old_report_history.is_dir():
                if new_results_history.exists():
                    shutil.rmtree(str(new_results_history))
                shutil.copytree(str(old_report_history), str(new_results_history))

            cmd_result = await asyncio.to_thread(
                subprocess.run,
                ["allure", "generate", str(allure_results_dir), "-o", str(report_dir), "--clean"],
                capture_output=True,
                timeout=60,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            if cmd_result.returncode == 0:
                result_data["report_url"] = f"/reports/scenario_{scenario_id}/index.html"
            else:
                result_data["report_url"] = None
        except FileNotFoundError:
            result_data["report_url"] = None
        except Exception:
            result_data["report_url"] = None

        await update_task(
            task_id,
            {
                "task_id": task_id,
                "scenario_id": scenario_id,
                "user_id": user_id,
                "status": "completed",
                "info": "数据驱动执行完成",
                "result": result_data,
                "completed_at": time.time(),
            },
        )
    except Exception as e:
        logging.getLogger(__name__).error(f"数据驱动执行失败 task_id={task_id}: {e}", exc_info=True)
        await update_task(
            task_id,
            {
                "task_id": task_id,
                "scenario_id": scenario_id,
                "user_id": user_id,
                "status": "failed",
                "info": f"执行失败: {str(e)[:100]}",
                "error": str(e),
                "completed_at": time.time(),
            },
        )


# ========== 定时任务管理接口 ==========


def _scenario_id_from_scheduler_task_id(task_id: str) -> Optional[int]:
    if task_id.startswith("auto_sched_"):
        try:
            return int(task_id[len("auto_sched_") :])
        except ValueError:
            return None
    return None


async def _get_owned_scheduler_task(task_id: str, user_id: int):
    """Return a scheduler task only after checking its scenario in the DB.

    Job metadata is a cache and may be reconstructed after restart, so it must
    never be the authority for tenant isolation.
    """
    from fastapi_backend.services.autotest_scheduler import get_scheduled_task
    from fastapi_backend.core.autotest_database import AsyncSessionLocal

    task = get_scheduled_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    scenario_id = task.get("scenario_id") or _scenario_id_from_scheduler_task_id(task_id)
    if scenario_id is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(AutoTestScenario.id).where(
                AutoTestScenario.id == int(scenario_id),
                AutoTestScenario.user_id == user_id,
            )
        )
        if result.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="任务不存在")
    task["scenario_id"] = int(scenario_id)
    task["user_id"] = user_id
    return task


@router.get("/scheduler/tasks", response_model=List[ScheduleTaskResponse])
async def list_scheduler_tasks(
    current_user: User = Depends(get_current_active_user),
):
    """获取所有定时任务"""
    from fastapi_backend.services.autotest_scheduler import get_all_scheduled_tasks

    return get_all_scheduled_tasks(user_id=current_user.id)


@router.get("/scheduler/tasks/{scenario_id}", response_model=List[ScheduleTaskResponse])
async def get_scenario_scheduler_tasks(
    scenario_id: int,
    current_user: User = Depends(get_current_active_user),
):
    """获取指定场景的定时任务"""
    from fastapi_backend.services.autotest_scheduler import get_tasks_by_scenario
    from fastapi_backend.core.autotest_database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        owned = await db.execute(
            select(AutoTestScenario.id).where(
                AutoTestScenario.id == scenario_id,
                AutoTestScenario.user_id == current_user.id,
            )
        )
        if owned.scalar_one_or_none() is None:
            raise HTTPException(status_code=404, detail="场景不存在")

    tasks = get_tasks_by_scenario(scenario_id, user_id=current_user.id)
    return tasks if tasks else []


@router.post("/scheduler/tasks", response_model=ScheduleTaskResponse)
async def create_scheduler_task(
    task: ScheduleTaskCreate,
    current_user: User = Depends(get_current_active_user),
):
    """创建定时任务"""
    from fastapi_backend.services.autotest_scheduler import add_scheduled_task
    from fastapi_backend.services.autotest_schedule_persistence import persist_schedule_to_db
    from fastapi_backend.core.autotest_database import AsyncSessionLocal as _AsyncSessionLocal

    # 校验场景归属
    async with _AsyncSessionLocal() as db:
        result = await db.execute(
            select(AutoTestScenario).where(
                AutoTestScenario.id == int(task.scenario_id),
                AutoTestScenario.user_id == current_user.id,
            )
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="场景不存在")

    try:
        result = add_scheduled_task(
            scenario_id=int(task.scenario_id),
            cron_expression=task.cron_expression,
            env_id=int(task.env_id) if task.env_id is not None else None,
            webhook_url=task.webhook_url,
            task_name=task.name,
            is_active=task.is_active,
            user_id=current_user.id,
        )
        try:
            await persist_schedule_to_db(
                int(task.scenario_id),
                task.cron_expression,
                int(task.env_id) if task.env_id is not None else None,
                task.webhook_url,
                task.name,
                True if task.is_active is None else bool(task.is_active),
                user_id=current_user.id,
            )
        except Exception:
            # Compensate the already-created APScheduler job.
            from fastapi_backend.services.autotest_scheduler import remove_scheduled_task

            remove_scheduled_task(result["task_id"])
            raise
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建定时任务失败: {str(e)}")


@router.delete("/scheduler/tasks/{task_id}")
async def delete_scheduler_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """删除定时任务"""
    from fastapi_backend.services.autotest_scheduler import remove_scheduled_task
    from fastapi_backend.services.autotest_schedule_persistence import clear_schedule_from_db

    t = await _get_owned_scheduler_task(task_id, current_user.id)

    scenario_id = t.get("scenario_id") if t else _scenario_id_from_scheduler_task_id(task_id)
    success = remove_scheduled_task(task_id)
    if success:
        try:
            if scenario_id is not None:
                await clear_schedule_from_db(int(scenario_id), user_id=current_user.id)
        except Exception:
            # Restore the job if persistence failed, keeping both stores aligned.
            from fastapi_backend.services.autotest_scheduler import add_scheduled_task

            add_scheduled_task(
                scenario_id=int(t["scenario_id"]),
                cron_expression=t["cron_expression"],
                env_id=t.get("env_id"),
                webhook_url=t.get("webhook_url"),
                task_name=t.get("name"),
                is_active=t.get("is_active", True),
                user_id=current_user.id,
            )
            raise
        return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="任务不存在或删除失败")


@router.post("/scheduler/tasks/{task_id}/run")
async def run_scheduler_task_now(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """立即执行定时任务（手动触发）"""
    await _get_owned_scheduler_task(task_id, current_user.id)

    scenario_id = task.get("scenario_id")
    user_id = None
    if scenario_id:
        from fastapi_backend.core.autotest_database import AsyncSessionLocal
        from fastapi_backend.models.autotest import AutoTestScenario
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(AutoTestScenario).where(
                    AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id
                )
            )
            scenario = result.scalar_one_or_none()
            if not scenario or not scenario.is_active:
                raise HTTPException(status_code=400, detail="场景已停用，禁止执行")
            # 从场景中获取 user_id 并传递给执行任务，避免丢失执行归属
            user_id = scenario.user_id

    try:
        from fastapi_backend.tasks import task_run_scenario

        celery_task = task_run_scenario.delay(task["scenario_id"], task.get("env_id"), user_id)
        return {"message": "任务已触发执行", "celery_task_id": celery_task.id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发执行失败: {str(e)}")


@router.post("/scheduler/tasks/{task_id}/toggle")
async def toggle_scheduler_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """切换定时任务的启用/暂停状态"""
    from fastapi_backend.services.autotest_scheduler import get_scheduled_task, toggle_task_status
    from fastapi_backend.services.autotest_schedule_persistence import persist_schedule_is_active_db

    await _get_owned_scheduler_task(task_id, current_user.id)

    try:
        result = toggle_task_status(task_id)
        t2 = get_scheduled_task(task_id)
        sid = (t2 or {}).get("scenario_id") or _scenario_id_from_scheduler_task_id(task_id)
        if sid is not None:
            try:
                await persist_schedule_is_active_db(int(sid), bool(result.get("is_active")), user_id=current_user.id)
            except Exception:
                # Toggle back if the database write failed.
                toggle_task_status(task_id)
                raise
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换状态失败: {str(e)}")


# ========== 邮件配置 API ==========


@router.get("/email/config")
async def get_email_config(
    current_user: User = Depends(get_current_active_user),
):
    """获取当前邮件配置（从持久化存储读取）"""
    from fastapi_backend.core.autotest_settings import get_settings

    settings = get_settings()
    return {
        "enabled": getattr(settings, "EMAIL_ENABLED", False),
        "smtpHost": getattr(settings, "EMAIL_SMTP_HOST", "smtp.gmail.com"),
        "smtpPort": getattr(settings, "EMAIL_SMTP_PORT", 465),
        "smtpUser": getattr(settings, "EMAIL_SMTP_USER", ""),
        "smtpPassword": "****" if getattr(settings, "EMAIL_SMTP_PASSWORD", "") else "",
        "fromEmail": getattr(settings, "EMAIL_FROM_ADDRESS", ""),
        "adminToEmail": getattr(settings, "EMAIL_ADMIN_TO", ""),
        "enableSSL": getattr(settings, "EMAIL_USE_SSL", True),
        "baseUrl": getattr(settings, "AUTO_TEST_BASE_URL", ""),
        "testToEmail": getattr(settings, "EMAIL_TEST_TO", ""),
    }


@router.post("/email/config")
async def save_email_config(
    config: EmailConfig,
    current_user: User = Depends(get_current_active_user),
):
    """保存邮件配置到持久化存储（system_config.json）"""
    from fastapi_backend.core.autotest_settings import get_settings

    settings = get_settings()
    settings.EMAIL_ENABLED = config.enabled
    settings.EMAIL_SMTP_HOST = config.smtpHost
    settings.EMAIL_SMTP_PORT = config.smtpPort
    settings.EMAIL_SMTP_USER = config.smtpUser
    if config.smtpPassword != "****":
        settings.EMAIL_SMTP_PASSWORD = config.smtpPassword
    settings.EMAIL_FROM_ADDRESS = config.fromEmail
    settings.EMAIL_ADMIN_TO = config.adminToEmail
    settings.EMAIL_USE_SSL = config.enableSSL
    settings.EMAIL_TEST_TO = config.testToEmail
    settings.AUTO_TEST_BASE_URL = config.baseUrl

    # 保存到持久化存储
    settings.save_to_persistent()

    # 重置邮件通知器单例，使新配置生效
    from fastapi_backend.services.autotest_email_notifier import get_email_notifier
    import fastapi_backend.services.autotest_email_notifier as email_notifier_module

    email_notifier_module._email_notifier_instance = None
    get_email_notifier()

    return {"message": "配置保存成功"}


@router.post("/email/test")
async def send_test_email(
    request: TestEmailRequest,
    current_user: User = Depends(get_current_active_user),
):
    """发送测试邮件验证 SMTP 配置是否正确"""
    from fastapi_backend.services.autotest_email_notifier import get_email_notifier

    notifier = get_email_notifier()
    # 使用 send_test_email 方法，不依赖 EMAIL_ENABLED 开关
    success = await notifier.send_test_email(to_email=request.to_email)
    if not success:
        raise HTTPException(status_code=500, detail="测试邮件发送失败，请检查 SMTP 配置")
    return {"message": "测试邮件发送成功"}


# ========== 导入导出 API ==========


@router.post("/import/postman")
async def import_postman(
    file: UploadFile = File(...),
    dry_run: bool = Form(False),
    target_group_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """导入 Postman Collection"""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小超过 10MB 限制")
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {str(e)}")

    root_name = data.get("info", {}).get("name", "Postman Import")
    parsed_cases = []
    imported_count = 0

    async def _import_items(items, parent_id=None):
        nonlocal imported_count, parsed_cases
        for item in items:
            if "item" in item:
                sub_name = item.get("name", "SubFolder")
                if dry_run:
                    await _import_items(item["item"], parent_id=None)
                else:
                    sub_group = AutoTestGroup(name=sub_name, parent_id=parent_id, user_id=current_user.id)
                    db.add(sub_group)
                    await db.flush()
                    await _import_items(item["item"], parent_id=sub_group.id)
            elif "request" in item:
                req = item["request"]
                method = req.get("method", "GET")
                url = ""
                if isinstance(req.get("url"), dict):
                    raw = req["url"].get("raw", "")
                    url = raw
                elif isinstance(req.get("url"), str):
                    url = req["url"]

                headers = {}
                if req.get("header"):
                    for h in req["header"]:
                        headers[h.get("key", "")] = h.get("value", "")

                payload = None
                body_type = "none"
                content_type = "application/json"
                body = req.get("body")
                body_mode = body.get("mode", "") if body else ""
                if body_mode == "raw":
                    body_type = "raw"
                    content_type = "application/json"
                    try:
                        payload = json.loads(body.get("raw", "{}"))
                    except Exception:
                        payload = {"raw": body.get("raw", "")}
                elif body_mode == "urlencoded":
                    payload = {
                        field["key"]: field.get("value", "") for field in body.get("urlencoded", []) if field.get("key")
                    }
                    body_type = "form"
                    content_type = "application/x-www-form-urlencoded"
                elif body_mode == "formdata":
                    payload = {
                        field["key"]: field.get("value", "") for field in body.get("formdata", []) if field.get("key")
                    }
                    body_type = "form-data"
                    content_type = "multipart/form-data"

                case_data = {
                    "name": item.get("name", "Unnamed"),
                    "method": method.upper(),
                    "url": url,
                    "headers": headers if headers else None,
                    "body_type": body_type,
                    "content_type": content_type,
                    "payload": payload,
                }
                if dry_run:
                    parsed_cases.append(case_data)
                else:
                    case = AutoTestCase(group_id=parent_id, user_id=current_user.id, **case_data)
                    db.add(case)
                    imported_count += 1

    if dry_run:
        await _import_items(data.get("item", []))
        return {
            "message": f"解析成功，共识别 {len(parsed_cases)} 个用例",
            "cases": parsed_cases,
            "imported_count": imported_count,
        }

    if target_group_id is not None:
        group_result = await db.execute(
            select(AutoTestGroup).where(AutoTestGroup.id == target_group_id, AutoTestGroup.user_id == current_user.id)
        )
        root_group = group_result.scalar_one_or_none()
        if not root_group:
            raise HTTPException(status_code=404, detail="目标分组不存在")
    else:
        result = await db.execute(
            select(AutoTestGroup).where(
                AutoTestGroup.name == root_name,
                AutoTestGroup.parent_id.is_(None),
                AutoTestGroup.user_id == current_user.id,
            )
        )
        root_group = result.scalar_one_or_none()
        if not root_group:
            root_group = AutoTestGroup(name=root_name, parent_id=None, user_id=current_user.id)
            db.add(root_group)
            await db.flush()

    await _import_items(data.get("item", []), root_group.id)
    await db.commit()

    return {"message": f"导入成功，共导入 {imported_count} 个用例", "imported_count": imported_count}


def _resolve_ref(ref, full_spec):
    """解析 Swagger $ref 引用，如 #/components/schemas/Pet"""
    if not ref or not ref.startswith("#/"):
        return None
    parts = ref.lstrip("#/").split("/")
    current = full_spec
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _generate_example_from_schema(schema, full_spec, depth=0):
    """从 Swagger schema 生成示例数据，递归解析 $ref"""
    if depth > 5:
        return None
    if not schema:
        return {}
    if "$ref" in schema:
        schema = _resolve_ref(schema["$ref"], full_spec) or {}
    if schema.get("type") == "object":
        result = {}
        for prop_name, prop_schema in (schema.get("properties") or {}).items():
            result[prop_name] = _generate_example_from_schema(prop_schema, full_spec, depth + 1)
        return result
    if schema.get("type") == "array":
        return [_generate_example_from_schema(schema.get("items", {}), full_spec, depth + 1)]
    if schema.get("type") == "string":
        return schema.get("example", "string")
    if schema.get("type") == "integer":
        return schema.get("example", 0)
    if schema.get("type") == "boolean":
        return schema.get("example", False)
    return schema.get("example", {})


@router.post("/import/swagger")
async def import_swagger(
    file: UploadFile = File(...),
    dry_run: bool = Form(False),
    target_group_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """导入 Swagger/OpenAPI 文档"""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小超过 10MB 限制")
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {str(e)}")

    root_name = data.get("info", {}).get("title", "Swagger Import")
    paths = data.get("paths", {})
    base_url = ""
    parsed_cases = []

    servers = data.get("servers", [])
    if servers:
        base_url = servers[0].get("url", "")

    if not dry_run:
        if target_group_id is not None:
            group_result = await db.execute(
                select(AutoTestGroup).where(
                    AutoTestGroup.id == target_group_id, AutoTestGroup.user_id == current_user.id
                )
            )
            root_group = group_result.scalar_one_or_none()
            if not root_group:
                raise HTTPException(status_code=404, detail="目标分组不存在")
        else:
            result = await db.execute(
                select(AutoTestGroup).where(
                    AutoTestGroup.name == root_name,
                    AutoTestGroup.parent_id.is_(None),
                    AutoTestGroup.user_id == current_user.id,
                )
            )
            root_group = result.scalar_one_or_none()
            if not root_group:
                root_group = AutoTestGroup(name=root_name, parent_id=None, user_id=current_user.id)
                db.add(root_group)
                await db.flush()

    imported_count = 0

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}:
                continue

            url = base_url + path
            operation_id = details.get("operationId", "")
            summary = details.get("summary", operation_id or f"{method.upper()} {path}")

            # 替换路径参数 {id} -> {{id}}
            import re

            url = re.sub(r"\{(\w+)\}", r"{{\1}}", url)

            headers = {}
            query_params = {}
            # 合并 path 级别与 operation 级别的参数
            all_params = list(methods.get("parameters", [])) + list(details.get("parameters", []))
            for param in all_params:
                # 解析参数的 $ref 引用
                if "$ref" in param:
                    param = _resolve_ref(param["$ref"], data) or {}
                param_in = param.get("in")
                param_name = param.get("name", "")
                if param_in == "header":
                    headers[param_name] = f"{{{{{param_name}}}}}"
                elif param_in == "query":
                    param_schema = param.get("schema", {}) or {}
                    if param_schema.get("type") == "string":
                        query_params[param_name] = param_schema.get("example", "string")
                    elif param_schema.get("type") == "integer":
                        query_params[param_name] = param_schema.get("example", 0)
                    else:
                        query_params[param_name] = param_schema.get("example", "")
            # 将 query 参数拼接到 URL
            if query_params:
                from urllib.parse import urlencode

                url = f"{url}?{urlencode(query_params)}"

            payload = None
            request_body = details.get("requestBody")
            if request_body:
                # 解析 requestBody 的 $ref 引用
                if "$ref" in request_body:
                    request_body = _resolve_ref(request_body["$ref"], data) or {}
                content_obj = request_body.get("content", {})
                for ct, ct_details in content_obj.items():
                    headers["Content-Type"] = ct
                    schema = ct_details.get("schema")
                    if schema:
                        # 从 schema 生成示例 payload，避免直接存储 schema dict
                        payload = _generate_example_from_schema(schema, data)
                    break

            case_data = {
                "name": summary,
                "method": method.upper(),
                "url": url,
                "headers": headers if headers else None,
                "payload": payload,
            }
            if dry_run:
                parsed_cases.append(case_data)
            else:
                case = AutoTestCase(group_id=root_group.id, user_id=current_user.id, **case_data)
                db.add(case)
            imported_count += 1

    if dry_run:
        return {
            "message": f"解析成功，共识别 {len(parsed_cases)} 个用例",
            "cases": parsed_cases,
            "imported_count": imported_count,
        }

    await db.commit()
    return {"message": f"导入成功，共导入 {imported_count} 个用例", "imported_count": imported_count}


# ========== Allure 报告辅助函数 ==========
# 已提取到 fastapi_backend.utils.autotest_helpers.write_allure_results
