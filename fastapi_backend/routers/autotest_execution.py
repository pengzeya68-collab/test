"""
AutoTest 统一路由 - 执行、历史、调度、邮件、导入导出

路径前缀: /api/auto-test/...
映射原 auto_test_platform main.py 中的内联端点
"""
import json
import subprocess
import time
import uuid
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.models import User
from fastapi_backend.models.autotest import (
    AutoTestCase,
    AutoTestEnvironment,
    AutoTestHistory,
    AutoTestScenario,
    AutoTestScenarioExecutionRecord,
    AutoTestGroup,
    AutoTestGlobalVariable,
)
from fastapi_backend.utils.encryption import decrypt
from fastapi_backend.schemas.autotest import (
    AutoTestHistoryResponse,
    CaseExecutionResult,
    CaseRunRequest,
    AutoTestEnvironmentResponse,
    ScheduleTaskCreate,
    ScheduleTaskResponse,
    EmailConfig,
    TestEmailRequest,
    VariablePreviewRequest,
    VariablePreviewResponse,
)
from fastapi_backend.utils.parser import replace_variables, find_variables

router = APIRouter(prefix="/api/auto-test", tags=["AutoTest-执行与工具"], dependencies=[Depends(get_current_user)])

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"
TASKS_DIR = AUTOTEST_DATA_DIR / "tasks"

# 任务状态存储（替代 Celery）
_task_store: dict = {}  # 内存缓存
_task_store_lock = asyncio.Lock()

# ========== 任务状态管理 ==========
from fastapi_backend.services.autotest_task_store import (
    get_task, update_task, delete_task, get_all_tasks
)

# ========== 接口调试发送 ==========

from fastapi_backend.utils.autotest_helpers import convert_to_dict
from fastapi_backend.services.autotest_report_service import write_allure_results

@router.post("/send")
async def send_request(payload: dict):
    from fastapi_backend.services.autotest_request_service import execute_http_request
    url = payload.get("url", "")
    if not url:
        raise HTTPException(status_code=400, detail="URL 不能为空")
    try:
        return await execute_http_request(
            method=payload.get("method", "GET").upper(),
            url=url,
            headers=convert_to_dict(payload.get("headers")),
            params=convert_to_dict(payload.get("params")),
            body=payload.get("body") or payload.get("payload"),
            body_type=payload.get("body_type", "json"),
            env_id=payload.get("env_id"),
            variables=convert_to_dict(payload.get("variables")),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ========== Celery 任务状态管理 ==========

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """获取Celery任务状态"""
    try:
        from celery.result import AsyncResult
        from fastapi_backend.tasks import celery_app

        task_result = AsyncResult(task_id, app=celery_app)

        if task_result.state == 'PENDING':
            return {
                "task_id": task_id,
                "status": "PENDING",
                "state": "PENDING",
                "info": "任务等待中"
            }
        elif task_result.state == 'PROGRESS':
            meta = task_result.info or {}
            return {
                "task_id": task_id,
                "status": "PROGRESS",
                "state": "PROGRESS",
                "progress": {
                    "percent": meta.get('percent', 0),
                    "current": meta.get('current', 0),
                    "total": meta.get('total', 0),
                    "current_api": meta.get('current_api', '执行中...'),
                    "current_step": meta.get('current_step', 0),
                    "total_steps": meta.get('total_steps', 0),
                    "step_name": meta.get('step_name', '执行中...')
                },
                "info": "任务执行中"
            }
        elif task_result.state == 'STARTED':
            return {
                "task_id": task_id,
                "status": "STARTED",
                "state": "STARTED",
                "progress": {"percent": 5, "current": 0, "total": 0, "current_api": '启动中...'},
                "info": "任务执行中"
            }
        elif task_result.state == 'RETRY':
            return {
                "task_id": task_id,
                "status": "RETRY",
                "state": "RETRY",
                "info": "任务重试中",
                "traceback": task_result.traceback
            }
        elif task_result.state == 'SUCCESS':
            return {
                "task_id": task_id,
                "status": "SUCCESS",
                "state": "SUCCESS",
                "result": task_result.result,
                "progress": {"percent": 100, "current": 0, "total": 0, "current_api": '执行完成'},
                "info": "任务执行成功"
            }
        elif task_result.state == 'FAILURE':
            return {
                "task_id": task_id,
                "status": "FAILURE",
                "state": "FAILURE",
                "error": str(task_result.result),
                "traceback": task_result.traceback
            }
        else:
            return {
                "task_id": task_id,
                "status": "UNKNOWN",
                "state": task_result.state
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取任务状态失败: {str(e)}")


@router.post("/tasks/{task_id}/cancel")
async def cancel_task(task_id: str):
    """取消正在执行的Celery任务"""
    try:
        from celery.result import AsyncResult
        from fastapi_backend.tasks import celery_app

        task_result = AsyncResult(task_id, app=celery_app)

        if not task_result.ready():
            task_result.revoke(terminate=True)
            return {"message": "任务取消请求已提交", "task_id": task_id}
        else:
            return {"message": "任务已完成或已取消", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"取消任务失败: {str(e)}")


# ========== 报告详情 ==========

@router.get("/reports/{report_id}")
async def get_report_detail(report_id: int, db: AsyncSession = Depends(get_db)):
    """获取执行报告详情"""
    from fastapi_backend.services.autotest_report_service import get_report_detail as _get_report
    result = await _get_report(report_id, db)
    if result is None:
        raise HTTPException(status_code=404, detail="报告不存在")
    return result


@router.post("/utils/preview", response_model=VariablePreviewResponse)
async def preview_variables(request: VariablePreviewRequest):
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
async def run_case(case_id: int, body: CaseRunRequest = None, db: AsyncSession = Depends(get_db)):
    """执行用例并保存历史记录，返回完整执行结果"""
    env_id = body.env_id if body else None
    result = await db.execute(select(AutoTestCase).where(AutoTestCase.id == case_id))
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
            result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.id == env_id_int))
            env = result.scalar_one_or_none()
        except (ValueError, TypeError):
            pass
    if env is None:
        result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.is_default == True))
        env = result.scalar_one_or_none()
        if not env:
            result = await db.execute(select(AutoTestEnvironment))
            env = result.scalars().first()

    from fastapi_backend.services.autotest_execution import quick_run_case
    result_data = await quick_run_case(case, env)

    history = AutoTestHistory(
        case_id=case_id,
        status="success" if result_data["success"] else "failed",
        execution_time=result_data.get("execution_time", 0),
        response_data=result_data.get("response"),
        error_message=result_data.get("error"),
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
    db: AsyncSession = Depends(get_db)
):
    """快速执行用例（不保存历史记录）"""
    env_id = body.env_id if body else None
    result = await db.execute(select(AutoTestCase).where(AutoTestCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")

    env = None
    if env_id:
        try:
            env_id_int = int(env_id)
            if env_id_int > 0:
                result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.id == env_id_int))
                env = result.scalar_one_or_none()
        except (ValueError, TypeError):
            pass

    if env is None:
        result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.is_default == True))
        env = result.scalars().first()
        if not env:
            result = await db.execute(select(AutoTestEnvironment))
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
    result_data = await quick_run_case(case, env, override_params=override_params)
    return CaseExecutionResult(**result_data)


@router.post("/cases/batch-run")
async def batch_run(case_ids: List[int], env_id: int = None, db: AsyncSession = Depends(get_db)):
    """批量执行多个用例"""
    result = await db.execute(select(AutoTestCase).where(AutoTestCase.id.in_(case_ids)))
    cases = result.scalars().all()

    env = None
    if env_id:
        result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.id == env_id))
        env = result.scalar_one_or_none()
    else:
        result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.is_default == True))
        env = result.scalar_one_or_none()
        if not env:
            result = await db.execute(select(AutoTestEnvironment))
            env = result.scalars().first()

    from fastapi_backend.services.autotest_execution import quick_run_case
    results = []
    total = len(cases)
    success_count = 0

    for case in cases:
        exec_result = await quick_run_case(case, env)
        success_count += 1 if exec_result["success"] else 0
        results.append({"case_id": case.id, "case_name": case.name, **exec_result})

    return {"total": total, "success": success_count, "failed": total - success_count, "results": results}


# ========== 测试历史接口 ==========

@router.get("/history", response_model=list[AutoTestHistoryResponse])
async def get_history(
    case_id: int = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """获取执行历史记录"""
    query = select(AutoTestHistory).order_by(desc(AutoTestHistory.created_at))
    if case_id:
        query = query.where(AutoTestHistory.case_id == case_id)
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    history = result.scalars().all()
    return history


@router.delete("/history/{history_id}", status_code=204)
async def delete_history(history_id: int, db: AsyncSession = Depends(get_db)):
    """删除历史记录"""
    result = await db.execute(select(AutoTestHistory).where(AutoTestHistory.id == history_id))
    history = result.scalar_one_or_none()
    if not history:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    await db.delete(history)
    await db.commit()
    return None


@router.get("/history/{history_id}", response_model=AutoTestHistoryResponse)
async def get_history_detail(history_id: int, db: AsyncSession = Depends(get_db)):
    """获取历史记录详情"""
    result = await db.execute(select(AutoTestHistory).where(AutoTestHistory.id == history_id))
    history = result.scalar_one_or_none()
    if not history:
        raise HTTPException(status_code=404, detail="历史记录不存在")
    return history


# ========== 场景执行接口 ==========

@router.post("/scenarios/{scenario_id}/run")
async def run_scenario(scenario_id: int, body: CaseRunRequest = None, background: bool = True):
    """执行测试场景，使用Celery异步任务"""
    env_id = body.env_id if body else None
    try:
        from fastapi_backend.core.autotest_database import AsyncSessionLocal
        from fastapi_backend.models.autotest import AutoTestScenario
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
            scenario = result.scalar_one_or_none()
            if not scenario:
                raise HTTPException(status_code=404, detail="场景不存在")
            if not scenario.is_active:
                raise HTTPException(status_code=400, detail="场景已停用，禁止执行")

        from fastapi_backend.tasks import task_run_scenario
        import logging
        logger = logging.getLogger(__name__)

        # 创建Celery任务
        logger.info(f"准备发送Celery任务: scenario_id={scenario_id}, env_id={env_id}")
        task = task_run_scenario.delay(scenario_id, env_id)
        if task is None:
            raise ValueError("Celery任务创建失败，task为None")
        task_id = task.id
        if not task_id:
            raise ValueError("Celery任务ID为空，任务可能未成功发送")

        logger.info(f"Celery任务已发送，任务ID: {task_id}")

        # 立即返回任务ID，前端可以轮询状态
        return {
            "task_id": task_id,
            "scenario_id": scenario_id,
            "status": "PROGRESS",
            "message": "任务已提交，正在后台执行"
        }
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"任务提交失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"任务提交失败: {str(e)}")


@router.get("/scenarios/{scenario_id}/history")
async def get_scenario_execution_history(
    scenario_id: int,
    status: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """获取某个场景的执行历史记录列表"""
    result = await db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    # 构建查询
    query = select(AutoTestScenarioExecutionRecord).where(
        AutoTestScenarioExecutionRecord.scenario_id == scenario_id
    )

    # 状态筛选
    if status and status in ['completed', 'failed', 'running']:
        query = query.where(AutoTestScenarioExecutionRecord.status == status)

    # 日期范围筛选
    if start_date:
        try:
            start_datetime = datetime.fromisoformat(start_date + "T00:00:00")
            query = query.where(AutoTestScenarioExecutionRecord.created_at >= start_datetime)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"起始日期格式无效: {start_date}")

    if end_date:
        try:
            end_datetime = datetime.fromisoformat(end_date + "T23:59:59")
            query = query.where(AutoTestScenarioExecutionRecord.created_at <= end_datetime)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"结束日期格式无效: {end_date}")

    # 排序和限制
    query = query.order_by(AutoTestScenarioExecutionRecord.created_at.desc()).limit(limit)

    history_result = await db.execute(query)
    history = history_result.scalars().all()

    return {
        "scenario_id": scenario_id,
        "scenario_name": scenario.name,
        "total": len(history),
        "items": [
            {
                "id": rec.id,
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
    db: AsyncSession = Depends(get_db)
):
    """删除场景执行历史记录"""
    # 验证场景存在
    result = await db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")

    # 查找并删除记录
    result = await db.execute(
        select(AutoTestScenarioExecutionRecord)
        .where(
            AutoTestScenarioExecutionRecord.id == record_id,
            AutoTestScenarioExecutionRecord.scenario_id == scenario_id
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
async def run_scenario_data_driven(scenario_id: int, body: CaseRunRequest = None):
    """数据驱动执行测试场景"""
    env_id = body.env_id if body else None
    from fastapi_backend.services.autotest_scenario_runner import run_scenario_data_driven as execute_data_driven

    try:
        result_data = await execute_data_driven(scenario_id, env_id)

        allure_results_dir = AUTOTEST_DATA_DIR / "allure-results" / f"scenario_{scenario_id}"
        report_dir = AUTOTEST_DATA_DIR / "reports" / f"scenario_{scenario_id}"

        import shutil as _shutil
        if allure_results_dir.exists():
            try:
                _shutil.rmtree(str(allure_results_dir))
            except Exception:
                pass
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
                shell=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if cmd_result.returncode == 0:
                result_data["report_url"] = f"/reports/scenario_{scenario_id}/index.html"
            else:
                result_data["report_url"] = None
        except (FileNotFoundError, Exception):
            result_data["report_url"] = None

        return result_data
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


# ========== 定时任务管理接口 ==========

def _scenario_id_from_scheduler_task_id(task_id: str) -> Optional[int]:
    if task_id.startswith("auto_sched_"):
        try:
            return int(task_id[len("auto_sched_") :])
        except ValueError:
            return None
    return None


@router.get("/scheduler/tasks", response_model=List[ScheduleTaskResponse])
async def list_scheduler_tasks():
    """获取所有定时任务"""
    from fastapi_backend.services.autotest_scheduler import get_all_scheduled_tasks
    return get_all_tasks()


@router.get("/scheduler/tasks/{scenario_id}", response_model=List[ScheduleTaskResponse])
async def get_scenario_scheduler_tasks(scenario_id: int):
    """获取指定场景的定时任务"""
    from fastapi_backend.services.autotest_scheduler import get_tasks_by_scenario
    tasks = get_tasks_by_scenario(scenario_id)
    return tasks if tasks else []


@router.post("/scheduler/tasks", response_model=ScheduleTaskResponse)
async def create_scheduler_task(task: ScheduleTaskCreate):
    """创建定时任务"""
    from fastapi_backend.services.autotest_scheduler import add_scheduled_task
    from fastapi_backend.services.autotest_schedule_persistence import persist_schedule_to_db

    try:
        result = add_scheduled_task(
            scenario_id=int(task.scenario_id),
            cron_expression=task.cron_expression,
            env_id=int(task.env_id) if task.env_id is not None else None,
            webhook_url=task.webhook_url,
            task_name=task.name,
            is_active=task.is_active,
        )
        await persist_schedule_to_db(
            int(task.scenario_id),
            task.cron_expression,
            int(task.env_id) if task.env_id is not None else None,
            task.webhook_url,
            task.name,
            True if task.is_active is None else bool(task.is_active),
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建定时任务失败: {str(e)}")


@router.delete("/scheduler/tasks/{task_id}")
async def delete_scheduler_task(task_id: str):
    """删除定时任务"""
    from fastapi_backend.services.autotest_scheduler import get_scheduled_task, remove_scheduled_task
    from fastapi_backend.services.autotest_schedule_persistence import clear_schedule_from_db

    t = get_scheduled_task(task_id)
    scenario_id = t.get("scenario_id") if t else _scenario_id_from_scheduler_task_id(task_id)
    success = remove_scheduled_task(task_id)
    if success:
        if scenario_id is not None:
            await clear_schedule_from_db(int(scenario_id))
        return {"message": "删除成功"}
    raise HTTPException(status_code=404, detail="任务不存在或删除失败")


@router.post("/scheduler/tasks/{task_id}/run")
async def run_scheduler_task_now(task_id: str):
    """立即执行定时任务（手动触发）"""
    import asyncio
    from fastapi_backend.services.autotest_scheduler import get_scheduled_task, execute_scenario_job

    task = get_scheduled_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    scenario_id = task.get("scenario_id")
    if scenario_id:
        from fastapi_backend.core.autotest_database import AsyncSessionLocal
        from fastapi_backend.models.autotest import AutoTestScenario
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
            scenario = result.scalar_one_or_none()
            if not scenario or not scenario.is_active:
                raise HTTPException(status_code=400, detail="场景已停用，禁止执行")

    try:
        async def _execute_job_safe():
            try:
                await execute_scenario_job(task["scenario_id"], task.get("env_id"), task_id)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"定时任务执行失败 task_id={task_id}: {e}", exc_info=True)

        asyncio.create_task(_execute_job_safe())
        return {"message": "任务已触发执行"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发执行失败: {str(e)}")


@router.post("/scheduler/tasks/{task_id}/toggle")
async def toggle_scheduler_task(task_id: str):
    """切换定时任务的启用/暂停状态"""
    from fastapi_backend.services.autotest_scheduler import get_scheduled_task, toggle_task_status
    from fastapi_backend.services.autotest_schedule_persistence import persist_schedule_is_active_db

    task = get_scheduled_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    try:
        result = toggle_task_status(task_id)
        t2 = get_scheduled_task(task_id)
        sid = (t2 or {}).get("scenario_id") or _scenario_id_from_scheduler_task_id(task_id)
        if sid is not None:
            await persist_schedule_is_active_db(int(sid), bool(result.get("is_active")))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"切换状态失败: {str(e)}")


# ========== 邮件配置 API ==========

@router.get("/email/config")
async def get_email_config():
    """获取当前邮件配置"""
    from fastapi_backend.core.autotest_settings import get_settings
    settings = get_settings()
    return {
        "enabled": getattr(settings, "EMAIL_ENABLED", False),
        "smtpHost": getattr(settings, "EMAIL_SMTP_HOST", "smtp.gmail.com"),
        "smtpPort": getattr(settings, "EMAIL_SMTP_PORT", 465),
        "smtpUser": getattr(settings, "EMAIL_SMTP_USER", ""),
        "smtpPassword": getattr(settings, "EMAIL_SMTP_PASSWORD", ""),
        "fromEmail": getattr(settings, "EMAIL_FROM", ""),
        "adminToEmail": getattr(settings, "EMAIL_ADMIN_TO", ""),
        "enableSSL": getattr(settings, "EMAIL_ENABLE_SSL", True),
        "baseUrl": getattr(settings, "BASE_URL", ""),
    }


@router.post("/email/config")
async def save_email_config(config: EmailConfig):
    """保存邮件配置到内存"""
    from fastapi_backend.core.autotest_settings import get_settings
    settings = get_settings()
    setattr(settings, "EMAIL_ENABLED", config.enabled)
    setattr(settings, "EMAIL_SMTP_HOST", config.smtpHost)
    setattr(settings, "EMAIL_SMTP_PORT", config.smtpPort)
    setattr(settings, "EMAIL_SMTP_USER", config.smtpUser)
    setattr(settings, "EMAIL_SMTP_PASSWORD", config.smtpPassword)
    setattr(settings, "EMAIL_FROM", config.fromEmail)
    setattr(settings, "EMAIL_ADMIN_TO", config.adminToEmail)
    setattr(settings, "EMAIL_ENABLE_SSL", config.enableSSL)
    setattr(settings, "BASE_URL", config.baseUrl)

    from fastapi_backend.services.autotest_email_notifier import get_email_notifier
    import fastapi_backend.services.autotest_email_notifier as email_notifier_module
    email_notifier_module._email_notifier_instance = None
    get_email_notifier()

    return {"message": "配置保存成功"}


@router.post("/email/test")
async def send_test_email(request: TestEmailRequest):
    """发送测试邮件验证配置是否正确"""
    from fastapi_backend.services.autotest_email_notifier import get_email_notifier
    from fastapi_backend.core.autotest_settings import get_settings
    settings = get_settings()

    notifier = get_email_notifier()
    success = notifier.send_scenario_result(
        to_email=request.to_email,
        scenario_name="测试场景",
        scenario_id=0,
        status="success",
        total_steps=3,
        success_steps=3,
        failed_steps=0,
        skipped_steps=0,
        total_time=1250,
        report_url="",
        base_url=settings.BASE_URL,
    )
    if not success:
        raise HTTPException(status_code=500, detail="测试邮件发送失败，请检查配置")
    return {"message": "测试邮件发送成功"}


# ========== 导入导出 API ==========

@router.post("/import/postman")
async def import_postman(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """导入 Postman Collection"""
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {str(e)}")

    # 确保 Postman 根分组
    root_name = data.get("info", {}).get("name", "Postman Import")
    result = await db.execute(select(AutoTestGroup).where(AutoTestGroup.name == root_name))
    root_group = result.scalar_one_or_none()
    if not root_group:
        root_group = AutoTestGroup(name=root_name, parent_id=None)
        db.add(root_group)
        await db.commit()
        await db.refresh(root_group)

    imported_count = 0

    async def _import_items(items, parent_id):
        nonlocal imported_count
        for item in items:
            if "item" in item:
                # 这是一个子文件夹
                sub_group = AutoTestGroup(name=item.get("name", "SubFolder"), parent_id=parent_id)
                db.add(sub_group)
                await db.flush()
                await _import_items(item["item"], sub_group.id)
            elif "request" in item:
                # 这是一个请求
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
                body = req.get("body")
                if body and body.get("mode") == "raw":
                    try:
                        payload = json.loads(body.get("raw", "{}"))
                    except Exception:
                        payload = {"raw": body.get("raw", "")}

                case = AutoTestCase(
                    group_id=parent_id,
                    name=item.get("name", "Unnamed"),
                    method=method.upper(),
                    url=url,
                    headers=headers if headers else None,
                    payload=payload,
                )
                db.add(case)
                imported_count += 1

    await _import_items(data.get("item", []), root_group.id)
    await db.commit()

    return {"message": f"导入成功，共导入 {imported_count} 个用例", "imported_count": imported_count}


@router.post("/import/swagger")
async def import_swagger(file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    """导入 Swagger/OpenAPI 文档"""
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {str(e)}")

    root_name = data.get("info", {}).get("title", "Swagger Import")
    result = await db.execute(select(AutoTestGroup).where(AutoTestGroup.name == root_name))
    root_group = result.scalar_one_or_none()
    if not root_group:
        root_group = AutoTestGroup(name=root_name, parent_id=None)
        db.add(root_group)
        await db.commit()
        await db.refresh(root_group)

    imported_count = 0
    paths = data.get("paths", {})
    base_url = ""

    servers = data.get("servers", [])
    if servers:
        base_url = servers[0].get("url", "")

    for path, methods in paths.items():
        for method, details in methods.items():
            if method.upper() not in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}:
                continue

            url = base_url + path
            operation_id = details.get("operationId", "")
            summary = details.get("summary", operation_id or f"{method.upper()} {path}")

            # 替换路径参数 {id} -> {{id}}
            import re
            url = re.sub(r'\{(\w+)\}', r'{{\1}}', url)

            headers = {}
            for param in details.get("parameters", []):
                if param.get("in") == "header":
                    headers[param.get("name", "")] = f"{{{{{param.get('name', '')}}}}}"

            payload = None
            request_body = details.get("requestBody")
            if request_body:
                content_obj = request_body.get("content", {})
                for ct, ct_details in content_obj.items():
                    headers["Content-Type"] = ct
                    if ct_details.get("schema"):
                        payload = {"schema": ct_details["schema"]}
                    break

            case = AutoTestCase(
                group_id=root_group.id,
                name=summary,
                method=method.upper(),
                url=url,
                headers=headers if headers else None,
                payload=payload,
            )
            db.add(case)
            imported_count += 1

    await db.commit()
    return {"message": f"导入成功，共导入 {imported_count} 个用例", "imported_count": imported_count}


# ========== Allure 报告辅助函数 ==========
# 已提取到 fastapi_backend.utils.autotest_helpers.write_allure_results
