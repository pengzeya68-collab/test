"""
定时任务调度器模块（迁移自 auto_test_platform/services/scheduler.py）
使用 APScheduler 实现定时执行测试场景
"""
import asyncio
import json
import logging
import uuid
from datetime import datetime

_logger = logging.getLogger(__name__)

from fastapi_backend.services.autotest_report_service import write_allure_results
from pathlib import Path
from typing import Dict, Any, Optional, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

from fastapi_backend.core.autotest_database import INSTANCE_DIR

# 项目根目录
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
AUTOTEST_DATA_DIR = PROJECT_ROOT / "fastapi_backend" / "autotest_data"

# 全局调度器实例
scheduler: Optional[AsyncIOScheduler] = None

# 任务存储
scheduled_tasks: Dict[str, Dict[str, Any]] = {}


def _schedule_meta_from_db(scenario_id: int) -> Dict[str, Any]:
    """从 AutoTest SQLite 读取定时配置（内存丢失或从 Job 重建时补全 Webhook 等）。"""
    import sqlite3

    path = INSTANCE_DIR / "auto_test.db"
    if not path.exists():
        return {}
    con = sqlite3.connect(str(path))
    try:
        cur = con.execute(
            "SELECT schedule_webhook_url, schedule_cron_expression, schedule_env_id, "
            "schedule_task_name, schedule_is_active FROM test_scenarios WHERE id=?",
            (scenario_id,),
        )
        row = cur.fetchone()
        if not row:
            return {}
        return {
            "webhook_url": row[0],
            "cron_expression": row[1] or "",
            "env_id": row[2],
            "name": row[3],
            "is_active": True if row[4] is None else bool(row[4]),
        }
    finally:
        con.close()


def _failed_step_count(result: Optional[dict]) -> int:
    if not result:
        return 0
    v = result.get("failed_steps")
    if v is not None:
        return int(v)
    v2 = result.get("failed_count")
    if v2 is not None:
        return int(v2)
    return 0


def get_scheduler() -> AsyncIOScheduler:
    """获取全局调度器实例"""
    global scheduler
    if scheduler is None:
        jobstore_url = f"sqlite:///{INSTANCE_DIR / 'scheduler_jobs.db'}"
        scheduler = AsyncIOScheduler(
            jobstores={'default': SQLAlchemyJobStore(url=jobstore_url)},
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 300
            }
        )
    return scheduler


async def execute_scenario_job(scenario_id: int, env_id: Optional[int], task_id: str):
    """执行场景任务的异步函数 - 通过Celery发送任务"""
    import subprocess
    import asyncio

    _logger.info(f"[Scheduler] 开始执行任务 {task_id}, 场景 {scenario_id}")

    try:
        from fastapi_backend.core.autotest_database import AsyncSessionLocal
        from fastapi_backend.models.autotest import AutoTestScenario
        from sqlalchemy import select

        async with AsyncSessionLocal() as db:
            result = await db.execute(select(AutoTestScenario).where(AutoTestScenario.id == scenario_id))
            scenario = result.scalar_one_or_none()
            if not scenario or not scenario.is_active:
                _logger.info(f"[Scheduler] 场景 {scenario_id} 已停用或不存在，跳过执行")
                if task_id in scheduled_tasks:
                    scheduled_tasks[task_id]["status"] = "skipped"
                    scheduled_tasks[task_id]["last_error"] = "场景已停用，跳过执行"
                return
    except Exception as e:
        _logger.info(f"[Scheduler] 检查场景状态失败: {e}")

    if task_id in scheduled_tasks:
        scheduled_tasks[task_id]["last_run"] = datetime.now().isoformat()
        scheduled_tasks[task_id]["status"] = "running"

    try:
        # 通过Celery发送任务
        from fastapi_backend.tasks import task_run_scenario

        # 创建Celery任务
        _logger.info(f"[Scheduler] 发送Celery任务: scenario_id={scenario_id}, env_id={env_id}")
        celery_task = task_run_scenario.delay(scenario_id, env_id)

        if not celery_task:
            raise ValueError("Celery任务创建失败，task为None")

        celery_task_id = celery_task.id
        if not celery_task_id:
            raise ValueError("Celery任务ID为空，任务可能未成功发送")

        _logger.info(f"[Scheduler] Celery任务已发送，任务ID: {celery_task_id}")

        # 等待任务完成（异步等待）
        max_wait_time = 300  # 5分钟超时
        wait_interval = 2    # 每2秒检查一次
        result = None

        try:
            for i in range(max_wait_time // wait_interval):
                try:
                    await asyncio.sleep(wait_interval)
                except asyncio.CancelledError:
                    _logger.info(f"[Scheduler] 任务 {task_id} 等待被取消，正在更新任务状态")
                    if task_id in scheduled_tasks:
                        scheduled_tasks[task_id]["last_status"] = "cancelled"
                        scheduled_tasks[task_id]["status"] = "idle"
                    raise  # 重新抛出，让外层处理

                # 检查任务状态
                from celery.result import AsyncResult
                from fastapi_backend.tasks import app as celery_app

                task_result = AsyncResult(celery_task_id, app=celery_app)

                if task_result.ready():
                    if task_result.successful():
                        result = task_result.result
                        _logger.info(f"[Scheduler] Celery任务完成: {celery_task_id}")
                        break
                    else:
                        error_msg = str(task_result.result) if task_result.result else "任务执行失败"
                        raise Exception(f"Celery任务执行失败: {error_msg}")
            else:
                raise TimeoutError(f"Celery任务超时: {celery_task_id}")
        except asyncio.CancelledError:
            _logger.info(f"[Scheduler] 任务 {task_id} 执行被完全取消")
            if task_id in scheduled_tasks:
                scheduled_tasks[task_id]["last_status"] = "cancelled"
                scheduled_tasks[task_id]["status"] = "idle"
            return  # 直接返回，不继续执行后续代码

        # 生成Allure报告
        allure_results_dir = AUTOTEST_DATA_DIR / "allure-results" / f"scenario_{scenario_id}"
        report_dir = AUTOTEST_DATA_DIR / "reports" / f"scenario_{scenario_id}"

        import shutil
        if allure_results_dir.exists():
            try:
                shutil.rmtree(str(allure_results_dir))
            except Exception:
                pass
        allure_results_dir.mkdir(parents=True, exist_ok=True)

        history_id = str(uuid.uuid4())[:8]
        write_allure_results(allure_results_dir, scenario_id, result, history_id)

        try:
            import shutil
            old_report_history = report_dir / "history"
            new_results_history = allure_results_dir / "history"
            if old_report_history.exists() and old_report_history.is_dir():
                if new_results_history.exists():
                    shutil.rmtree(str(new_results_history))
                shutil.copytree(str(old_report_history), str(new_results_history))

            cmd_result = subprocess.run(
                ["allure", "generate", str(allure_results_dir), "-o", str(report_dir), "--clean"],
                capture_output=True,
                timeout=60,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            if cmd_result.returncode == 0:
                report_url = f"/reports/scenario_{scenario_id}/index.html"
            else:
                report_url = None
        except (FileNotFoundError, Exception):
            report_url = None

        if task_id in scheduled_tasks:
            if result:
                failed_steps = _failed_step_count(result)
                scheduled_tasks[task_id]["last_status"] = "success" if failed_steps == 0 else "failed"
                scheduled_tasks[task_id]["last_result"] = result
            else:
                scheduled_tasks[task_id]["last_status"] = "unknown"
                scheduled_tasks[task_id]["last_result"] = None
            scheduled_tasks[task_id]["report_url"] = report_url
            scheduled_tasks[task_id]["status"] = "idle"

            webhook_url = scheduled_tasks[task_id].get("webhook_url")
            if webhook_url:
                try:
                    import requests as _req
                    webhook_payload = {
                        "scenario_id": scenario_id,
                        "status": scheduled_tasks[task_id]["last_status"],
                        "report_url": report_url,
                        "total_steps": result.get("total_steps", 0) if result else 0,
                        "failed_steps": _failed_step_count(result),
                    }
                    await asyncio.to_thread(
                        _req.post, webhook_url, json=webhook_payload, timeout=10
                    )
                except Exception as wh_err:
                    _logger.warning(f"Webhook 通知失败 {webhook_url}: {wh_err}")

    except asyncio.CancelledError:
        _logger.info(f"[Scheduler] 任务 {task_id} 被取消执行")
        if task_id in scheduled_tasks:
            scheduled_tasks[task_id]["last_status"] = "cancelled"
            scheduled_tasks[task_id]["status"] = "idle"
    except Exception as e:
        _logger.info(f"[Scheduler] 任务 {task_id} 执行失败: {str(e)}")
        if task_id in scheduled_tasks:
            scheduled_tasks[task_id]["last_status"] = "error"
            scheduled_tasks[task_id]["last_error"] = str(e)
            scheduled_tasks[task_id]["status"] = "idle"


def write_allure_results(allure_results_dir: Path, scenario_id: int, result: dict, history_id: str):
    """写入 Allure 结果文件 - 每个步骤生成独立的测试用例JSON，模拟 Pytest Class 架构"""
    import time as time_module

    start_time = result.get("start_time")
    if start_time:
        if isinstance(start_time, (int, float)):
            base_start_ms = int(start_time * 1000) if start_time < 1e10 else int(start_time)
        else:
            try:
                dt = datetime.fromisoformat(str(start_time).replace('Z', '+00:00'))
                base_start_ms = int(dt.timestamp() * 1000)
            except:
                base_start_ms = int(time_module.time() * 1000)
    else:
        base_start_ms = int(time_module.time() * 1000)

    step_results = result.get("step_results", [])
    scenario_name = result.get("scenario_name", f"场景 {scenario_id}")

    cumulative_ms = 0

    for i, step in enumerate(step_results):
        i_plus_1 = i + 1
        step_duration = step.get("duration", 0)
        step_start_ms = base_start_ms + cumulative_ms
        step_stop_ms = step_start_ms + step_duration
        cumulative_ms += step_duration

        step_status_raw = step.get("status", "success")
        if step_status_raw == "skipped":
            step_status = "skipped"
            status_details = {"message": step.get("skipped_reason", "步骤被跳过")}
        else:
            success = step_status_raw != "failed"
            status_code = step.get("status_code", 0)
            url = step.get("url", "")
            is_really_success = success and status_code > 0 and url

            if is_really_success:
                step_status = "passed"
                status_details = {}
            else:
                step_status = "failed"
                error_msg = step.get("error", "")
                if not error_msg:
                    assertions = step.get("assertions", {})
                    failed_asserts = assertions.get("failed", [])
                    if failed_asserts:
                        msgs = []
                        for fa in failed_asserts:
                            if isinstance(fa, dict):
                                msgs.append(fa.get("reason", str(fa)))
                            else:
                                msgs.append(str(fa))
                        error_msg = "; ".join(msgs)
                    if not error_msg:
                        if success and (status_code == 0 or not url):
                            error_msg = f"请求未成功发出 (status_code={status_code}, url为空)"
                        else:
                            error_msg = f"期望 2xx/3xx, 实际返回 {status_code}"
                status_details = {"message": error_msg}

        api_case_name = step.get("api_case_name", f"步骤 {i_plus_1}")
        method = step.get("method", "GET")
        step_title = f"用例{i_plus_1}: {api_case_name}"

        sub_steps = []

        request_step = {
            "name": f"1. 发起HTTP请求: {method} {url}",
            "status": step_status,
            "stage": "finished",
            "start": step_start_ms,
            "stop": step_start_ms + max(step_duration // 3, 1),
            "duration": max(step_duration // 3, 1),
            "steps": [],
            "attachments": [],
        }
        request_info = {"url": url, "method": method, "headers": step.get("headers", {}), "payload": step.get("payload", {})}
        request_step["attachments"].append({
            "name": "请求信息",
            "type": "application/json",
            "source": f"request_{i_plus_1}.json",
            "body": json.dumps(request_info, ensure_ascii=False, indent=2)
        })
        sub_steps.append(request_step)

        response_step = {
            "name": "2. 获取响应信息",
            "status": step_status,
            "stage": "finished",
            "start": step_start_ms + max(step_duration // 3, 1),
            "stop": step_start_ms + max(step_duration * 2 // 3, 1),
            "duration": max(step_duration // 3, 1),
            "steps": [],
            "attachments": [],
        }
        response_body = ""
        if step.get("response"):
            response_body = step["response"].get("body", "")
        response_info = {"status_code": status_code, "response_time_ms": step.get("response_time", 0), "body": str(response_body)[:2000] if response_body else ""}
        response_step["attachments"].append({
            "name": "响应信息",
            "type": "application/json",
            "source": f"response_{i_plus_1}.json",
            "body": json.dumps(response_info, ensure_ascii=False, indent=2)
        })
        sub_steps.append(response_step)

        assertion_step = {
            "name": "3. 执行断言校验",
            "status": step_status,
            "stage": "finished",
            "start": step_start_ms + max(step_duration * 2 // 3, 1),
            "stop": step_stop_ms,
            "duration": max(step_duration // 3, 1),
            "steps": [],
            "attachments": [],
        }
        if step.get("extracted_vars"):
            vars_info = ", ".join([f"{k}={v}" for k, v in step["extracted_vars"].items()])
            assertion_step["attachments"].append({
                "name": f"提取变量_{i_plus_1}",
                "type": "text/plain",
                "source": f"vars_{i_plus_1}.txt",
                "body": vars_info
            })
        sub_steps.append(assertion_step)

        step_uuid = str(uuid.uuid4())
        test_case_result = {
            "name": step_title,
            "uuid": step_uuid,
            "historyId": f"TestScenario{scenario_id}.test_step_{i_plus_1}",
            "fullName": f"TestScenario{scenario_id}.test_step_{i_plus_1}",
            "status": step_status,
            "stage": "finished",
            "start": step_start_ms,
            "stop": step_stop_ms,
            "duration": step_duration,
            "description": f"[{method}] {api_case_name}",
            "labels": [
                {"name": "suite", "value": scenario_name},
                {"name": "feature", "value": scenario_name},
                {"name": "severity", "value": "normal"},
                {"name": "scenario_id", "value": str(scenario_id)},
                {"name": "thread", "value": "main"},
                {"name": "host", "value": "localhost"},
            ],
            "parameters": [],
            "links": [],
            "steps": sub_steps,
            "attachments": [],
        }
        if status_details:
            test_case_result["statusDetails"] = status_details

        output_file = allure_results_dir / f"scenario-{scenario_id}-step-{i_plus_1}-{history_id}.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(test_case_result, f, ensure_ascii=False, indent=2)




def add_scheduled_task(
    scenario_id: int,
    cron_expression: str,
    env_id: Optional[int] = None,
    webhook_url: Optional[str] = None,
    task_name: Optional[str] = None,
    is_active: Optional[bool] = True
) -> Dict[str, Any]:
    """添加定时任务"""
    global scheduled_tasks

    parts = cron_expression.split()
    if len(parts) != 5:
        raise ValueError("Cron 表达式格式错误，应为 5 位：分 时 日 月 周")

    minute, hour, day, month, day_of_week = parts
    # 每场景固定一个 Job ID，便于持久化与前端展示，并用 replace_existing 更新同一调度
    task_id = f"auto_sched_{scenario_id}"

    job = get_scheduler().add_job(
        func=execute_scenario_job,
        trigger=CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=day_of_week),
        args=[scenario_id, env_id, task_id],
        id=task_id,
        name=task_name or f"场景 {scenario_id} 定时执行",
        replace_existing=True,
    )

    # 根据is_active参数设置作业状态
    sched = get_scheduler()
    if is_active is False:
        sched.pause_job(task_id)

    task_info = {
        "task_id": task_id,
        "job_id": job.id,
        "scenario_id": scenario_id,
        "env_id": env_id,
        "cron_expression": cron_expression,
        "webhook_url": webhook_url,
        "name": task_name or f"场景 {scenario_id} 定时执行",
        "created_at": datetime.now().isoformat(),
        "last_run": None,
        "last_status": None,
        "last_error": None,
        "last_result": None,
        "report_url": None,
        "status": "idle",
        "is_active": is_active if is_active is not None else True,
        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
    }

    scheduled_tasks[task_id] = task_info
    return task_info


def remove_scheduled_task(task_id: str) -> bool:
    """删除定时任务"""
    global scheduled_tasks
    try:
        sched = get_scheduler()
        sched.remove_job(task_id)
        if task_id in scheduled_tasks:
            del scheduled_tasks[task_id]
        return True
    except Exception:
        return False


def toggle_task_status(task_id: str) -> Dict[str, Any]:
    """切换定时任务的启用/暂停状态"""
    global scheduled_tasks
    task_info = scheduled_tasks.get(task_id)
    if not task_info:
        raise ValueError(f"任务 {task_id} 不存在")

    is_active = task_info.get("is_active", True)
    sched = get_scheduler()

    _logger.info(f"[Scheduler] 切换任务状态: {task_id}, 当前is_active={is_active}, 调度器运行状态: {sched.running}")

    if is_active:
        # 暂停任务
        _logger.info(f"[Scheduler] 暂停任务: {task_id}")
        sched.pause_job(task_id)
        task_info["is_active"] = False
        task_info["status"] = "paused"
    else:
        # 恢复任务
        _logger.info(f"[Scheduler] 恢复任务: {task_id}")
        sched.resume_job(task_id)
        task_info["is_active"] = True
        task_info["status"] = "idle"

    # 验证作业状态
    job = sched.get_job(task_id)
    if job:
        _logger.info(f"[Scheduler] 作业状态: pending={job.pending}, next_run_time={job.next_run_time}")

    return {
        "task_id": task_id,
        "is_active": task_info["is_active"],
        "status": task_info["status"],
        "message": f"任务已{'启用' if task_info['is_active'] else '暂停'}"
    }


def get_scheduled_task(task_id: str) -> Optional[Dict[str, Any]]:
    """获取任务信息"""
    # 首先检查内存字典
    if task_id in scheduled_tasks:
        return scheduled_tasks.get(task_id)

    # 如果内存中没有，检查调度器中是否有此任务
    sched = get_scheduler()
    job = sched.get_job(task_id)
    if job:
        # 从作业重建基本任务信息
        args = job.args if job.args else []
        scenario_id = args[0] if len(args) > 0 else 0
        env_id = args[1] if len(args) > 1 else None

        # 解析cron表达式
        cron_expr = ""
        if hasattr(job.trigger, 'fields'):
            # CronTrigger
            fields = job.trigger.fields
            cron_expr = f"{fields[0]} {fields[1]} {fields[2]} {fields[3]} {fields[4]}"

        meta = _schedule_meta_from_db(scenario_id)
        task_info = {
            "task_id": task_id,
            "job_id": job.id,
            "scenario_id": scenario_id,
            "env_id": env_id if env_id is not None else meta.get("env_id"),
            "cron_expression": cron_expr or meta.get("cron_expression") or "",
            "webhook_url": meta.get("webhook_url"),
            "name": (meta.get("name") or job.name or f"场景 {scenario_id} 定时执行"),
            "created_at": datetime.now().isoformat(),  # 无法获取原始创建时间
            "last_run": None,
            "last_status": None,
            "last_error": None,
            "last_result": None,
            "report_url": None,
            "status": "idle",
            "is_active": not job.pending,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
        }
        scheduled_tasks[task_id] = task_info
        return task_info

    return None


def get_all_scheduled_tasks() -> List[Dict[str, Any]]:
    """获取所有定时任务"""
    sched = get_scheduler()

    # 首先确保scheduled_tasks包含所有调度器中的作业
    for job in sched.get_jobs():
        task_id = job.id
        if task_id not in scheduled_tasks:
            # 从作业重建任务信息
            args = job.args if job.args else []
            scenario_id = args[0] if len(args) > 0 else 0
            env_id = args[1] if len(args) > 1 else None

            # 解析cron表达式
            cron_expr = ""
            if hasattr(job.trigger, 'fields'):
                # CronTrigger
                fields = job.trigger.fields
                cron_expr = f"{fields[0]} {fields[1]} {fields[2]} {fields[3]} {fields[4]}"

            meta = _schedule_meta_from_db(scenario_id)
            task_info = {
                "task_id": task_id,
                "job_id": job.id,
                "scenario_id": scenario_id,
                "env_id": env_id if env_id is not None else meta.get("env_id"),
                "cron_expression": cron_expr or meta.get("cron_expression") or "",
                "webhook_url": meta.get("webhook_url"),
                "name": (meta.get("name") or job.name or f"场景 {scenario_id} 定时执行"),
                "created_at": datetime.now().isoformat(),
                "last_run": None,
                "last_status": None,
                "last_error": None,
                "last_result": None,
                "report_url": None,
                "status": "idle",
                "is_active": not job.pending,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
            }
            scheduled_tasks[task_id] = task_info

    # 更新next_run_time；若内存中无 Webhook，从 DB 补全（避免仅内存字段丢失）
    for task_id, task_info in scheduled_tasks.items():
        try:
            job = sched.get_job(task_id)
            if job and job.next_run_time:
                task_info["next_run_time"] = job.next_run_time.isoformat()
            # 更新活动状态
            if job:
                task_info["is_active"] = not job.pending
        except Exception:
            pass
        sid = task_info.get("scenario_id")
        if sid is not None and not (task_info.get("webhook_url") or "").strip():
            m = _schedule_meta_from_db(int(sid))
            if m.get("webhook_url"):
                task_info["webhook_url"] = m.get("webhook_url")

    return list(scheduled_tasks.values())


def get_tasks_by_scenario(scenario_id: int) -> List[Dict[str, Any]]:
    """获取指定场景的所有定时任务"""
    return [task for task in scheduled_tasks.values() if task["scenario_id"] == scenario_id]


def start_scheduler():
    """启动调度器"""
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        _logger.info("[Scheduler] 调度器已启动")


def stop_scheduler():
    """停止调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        _logger.info("[Scheduler] 调度器已停止")
    scheduler = None
