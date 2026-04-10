"""
定时任务调度器模块
使用 APScheduler 实现定时执行测试场景
"""
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore

# 全局调度器实例
scheduler: Optional[AsyncIOScheduler] = None

# 任务存储（用于记录任务配置）
scheduled_tasks: Dict[str, Dict[str, Any]] = {}


def get_scheduler() -> AsyncIOScheduler:
    """获取全局调度器实例"""
    global scheduler
    if scheduler is None:
        scheduler = AsyncIOScheduler(
            jobstores={
                'default': MemoryJobStore()
            },
            job_defaults={
                'coalesce': True,
                'max_instances': 1,
                'misfire_grace_time': 300  # 5分钟内可以执行错过的任务
            }
        )
    return scheduler


async def execute_scenario_job(scenario_id: int, env_id: Optional[int], task_id: str):
    """
    执行场景任务的异步函数

    Args:
        scenario_id: 场景 ID
        env_id: 环境 ID
        task_id: 任务 ID（用于记录状态）
    """
    from services.scenario_runner import run_scenario as execute_scenario
    import subprocess
    from pathlib import Path

    print(f"[Scheduler] 开始执行任务 {task_id}, 场景 {scenario_id}")

    # 更新任务状态
    if task_id in scheduled_tasks:
        scheduled_tasks[task_id]["last_run"] = datetime.now().isoformat()
        scheduled_tasks[task_id]["status"] = "running"

    try:
        # 执行场景
        result = await execute_scenario(scenario_id, env_id)

        # 生成 Allure 报告
        base_dir = Path(__file__).parent.parent.absolute()
        allure_results_dir = base_dir / "allure-results" / f"scenario_{scenario_id}"
        report_dir = base_dir / "reports" / f"scenario_{scenario_id}"

        allure_results_dir.mkdir(parents=True, exist_ok=True)

        history_id = str(uuid.uuid4())[:8]

        # 写入结果
        _write_allure_result(allure_results_dir, scenario_id, result, history_id)

        # 生成报告
        try:
            cmd_result = subprocess.run(
                ["allure", "generate", str(allure_results_dir), "-o", str(report_dir), "--clean"],
                capture_output=True,
                timeout=60,
                shell=True  # Windows 上需要 shell=True 才能运行 .cmd 文件
            )
            # 检查命令执行结果
            if cmd_result.returncode == 0:
                report_url = f"/reports/scenario_{scenario_id}/index.html"
                print(f"[Scheduler] Allure 报告生成成功: {report_url}")
            else:
                print(f"[Scheduler] Allure 报告生成失败, returncode={cmd_result.returncode}")
                print(f"[Scheduler] stderr: {cmd_result.stderr.decode('utf-8', errors='ignore')}")
                report_url = None
        except FileNotFoundError as e:
            print(f"[Scheduler] Allure 命令未找到，请安装 Allure: {e}")
            report_url = None
        except Exception as e:
            print(f"[Scheduler] Allure 报告生成异常: {e}")
            report_url = None

        # 更新任务状态
        if task_id in scheduled_tasks:
            scheduled_tasks[task_id]["last_status"] = "success" if result.get("failed_steps", 1) == 0 else "failed"
            scheduled_tasks[task_id]["last_result"] = result
            scheduled_tasks[task_id]["report_url"] = report_url
            scheduled_tasks[task_id]["status"] = "idle"

        print(f"[Scheduler] 任务 {task_id} 执行完成, 成功: {result.get('success_steps', 0)}, 失败: {result.get('failed_steps', 0)}")

    except Exception as e:
        print(f"[Scheduler] 任务 {task_id} 执行失败: {str(e)}")
        if task_id in scheduled_tasks:
            scheduled_tasks[task_id]["last_status"] = "error"
            scheduled_tasks[task_id]["last_error"] = str(e)
            scheduled_tasks[task_id]["status"] = "idle"


def _write_allure_result(allure_results_dir: Path, scenario_id: int, result: dict, history_id: str):
    """写入 Allure 结果文件（符合 Allure JSON 规范）"""
    import time as time_module

    # 计算时间戳（毫秒）
    start_time = result.get("start_time")
    if start_time:
        if isinstance(start_time, (int, float)):
            start_ms = int(start_time * 1000) if start_time < 1e10 else int(start_time)
        else:
            try:
                dt = datetime.fromisoformat(str(start_time).replace('Z', '+00:00'))
                start_ms = int(dt.timestamp() * 1000)
            except:
                start_ms = int(time_module.time() * 1000)
    else:
        start_ms = int(time_module.time() * 1000)

    duration_ms = int(result.get("duration", 0))
    stop_ms = start_ms + duration_ms

    failed_count = result.get("failed_steps", 0)
    status = "passed" if failed_count == 0 else "failed"

    step_results = result.get("step_results", [])
    scenario_name = result.get("scenario_name", f"场景 {scenario_id}")

    # 格式化步骤
    allure_steps = _format_steps_for_allure(scenario_id, step_results, start_ms, duration_ms)

    scenario_result = {
        "name": scenario_name,
        "uuid": f"scenario_{scenario_id}_{history_id}",
        "historyId": f"scenario_{scenario_id}",
        "status": status,
        "stage": "finished",
        "start": start_ms,
        "stop": stop_ms,
        "duration": duration_ms,
        "description": f"场景ID: {scenario_id}，执行步骤: {len(step_results)}",
        "labels": [
            {"name": "suite", "value": "API测试场景"},
            {"name": "severity", "value": "normal"},
            {"name": "scenario_id", "value": str(scenario_id)},
            {"name": "thread", "value": "main"},
            {"name": "host", "value": "localhost"}
        ],
        "parameters": [],
        "links": [],
        "steps": allure_steps,
        "attachments": []
    }

    output_file = allure_results_dir / f"scenario-{scenario_id}-{history_id}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(scenario_result, f, ensure_ascii=False, indent=2)


def _format_steps_for_allure(scenario_id: int, step_results: list, base_start_ms: int, total_duration_ms: int) -> list:
    """将步骤格式化为 Allure 的 steps 数组"""
    allure_steps = []
    step_count = len(step_results)
    avg_step_duration = total_duration_ms // max(step_count, 1)

    for i, step in enumerate(step_results):
        step_start = base_start_ms + i * avg_step_duration
        step_duration = avg_step_duration
        step_stop = step_start + step_duration

        success = step.get("status", "success") != "failed"
        step_status = "passed" if success else "failed"

        api_case_name = step.get("api_case_name", f"步骤 {i+1}")
        method = step.get("method", "GET")
        url = step.get("url", "")
        status_code = step.get("status_code", 0)

        step_name = f"[{method}] {api_case_name}"
        if status_code:
            step_name += f" (HTTP {status_code})"

        response_info = ""
        if step.get("response"):
            resp_body = step["response"].get("body", "")
            if resp_body:
                if len(str(resp_body)) > 500:
                    resp_body = str(resp_body)[:500] + "..."
                response_info = str(resp_body)

        assertions_info = ""
        if step.get("assertions"):
            assertions = step["assertions"]
            failed = assertions.get("failed", [])
            if failed:
                assertion_msgs = []
                for f in failed:
                    if isinstance(f, dict):
                        assertion_msgs.append(f.get("reason", str(f)))
                    else:
                        assertion_msgs.append(str(f))
                assertions_info = " | ".join(assertion_msgs)

        step_details = f"API: {method} {url}\n状态码: {status_code}\n耗时: {step_duration}ms\n断言: {assertions_info if assertions_info else '通过'}\n响应: {response_info if response_info else '无响应体'}"

        allure_step = {
            "name": step_name,
            "uuid": f"step_{i}_{step_start}",
            "status": step_status,
            "stage": "finished",
            "start": step_start,
            "stop": step_stop,
            "duration": step_duration,
            "steps": [],
            "attachments": [
                {
                    "name": f"响应详情_{i+1}",
                    "type": "text/plain",
                    "source": f"response_{i+1}.txt",
                    "body": step_details
                }
            ]
        }

        if step.get("extracted_vars"):
            vars_info = ", ".join([f"{k}={v}" for k, v in step["extracted_vars"].items()])
            allure_step["attachments"].append({
                "name": f"提取变量_{i+1}",
                "type": "text/plain",
                "source": f"vars_{i+1}.txt",
                "body": vars_info
            })

        allure_steps.append(allure_step)

    return allure_steps


def add_scheduled_task(
    scenario_id: int,
    cron_expression: str,
    env_id: Optional[int] = None,
    task_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    添加定时任务

    Args:
        scenario_id: 场景 ID
        cron_expression: Cron 表达式（如 "0 2 * * *" 表示每天凌晨2点）
        env_id: 环境 ID（可选）
        task_name: 任务名称（可选）

    Returns:
        任务信息字典
    """
    global scheduled_tasks

    # 解析 cron 表达式
    parts = cron_expression.split()
    if len(parts) != 5:
        raise ValueError("Cron 表达式格式错误，应为 5 位：分 时 日 月 周")

    minute, hour, day, month, day_of_week = parts

    # 创建任务 ID
    task_id = f"scenario_{scenario_id}_{uuid.uuid4().hex[:8]}"

    # 构建任务
    job = get_scheduler().add_job(
        func=execute_scenario_job,
        trigger=CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week
        ),
        args=[scenario_id, env_id, task_id],
        id=task_id,
        name=task_name or f"场景 {scenario_id} 定时执行",
        replace_existing=False
    )

    # 记录任务信息
    task_info = {
        "task_id": task_id,
        "job_id": job.id,
        "scenario_id": scenario_id,
        "env_id": env_id,
        "cron_expression": cron_expression,
        "name": task_name or f"场景 {scenario_id} 定时执行",
        "created_at": datetime.now().isoformat(),
        "last_run": None,
        "last_status": None,
        "last_error": None,
        "last_result": None,
        "report_url": None,
        "status": "idle",
        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
    }

    scheduled_tasks[task_id] = task_info

    print(f"[Scheduler] 添加定时任务 {task_id}, 场景 {scenario_id}, Cron: {cron_expression}")

    return task_info


def remove_scheduled_task(task_id: str) -> bool:
    """
    删除定时任务

    Args:
        task_id: 任务 ID

    Returns:
        是否删除成功
    """
    global scheduled_tasks

    try:
        scheduler = get_scheduler()
        scheduler.remove_job(task_id)
        if task_id in scheduled_tasks:
            del scheduled_tasks[task_id]
        print(f"[Scheduler] 删除定时任务 {task_id}")
        return True
    except Exception as e:
        print(f"[Scheduler] 删除定时任务失败 {task_id}: {e}")
        return False


def get_scheduled_task(task_id: str) -> Optional[Dict[str, Any]]:
    """获取任务信息"""
    return scheduled_tasks.get(task_id)


def get_all_scheduled_tasks() -> List[Dict[str, Any]]:
    """获取所有定时任务"""
    # 更新 next_run_time
    scheduler = get_scheduler()
    for task_id, task_info in scheduled_tasks.items():
        try:
            job = scheduler.get_job(task_id)
            if job and job.next_run_time:
                task_info["next_run_time"] = job.next_run_time.isoformat()
        except:
            pass
    return list(scheduled_tasks.values())


def get_tasks_by_scenario(scenario_id: int) -> List[Dict[str, Any]]:
    """获取指定场景的所有定时任务"""
    return [
        task for task in scheduled_tasks.values()
        if task["scenario_id"] == scenario_id
    ]


def start_scheduler():
    """启动调度器"""
    sched = get_scheduler()
    if not sched.running:
        sched.start()
        print("[Scheduler] 调度器已启动")


def stop_scheduler():
    """停止调度器"""
    global scheduler
    if scheduler and scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] 调度器已停止")
    scheduler = None