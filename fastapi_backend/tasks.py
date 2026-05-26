"""
Celery tasks for TestMaster project.
"""
import logging
import time

from fastapi_backend.celery_config import app

_logger = logging.getLogger(__name__)


def _persist_task_result(task_id: str, result_data: dict) -> None:
    """同步写入任务结果到持久化存储（Celery 进程内调用）"""
    try:
        from fastapi_backend.services.autotest_task_store import (
            get_task, _task_store, _get_store_lock, _save_task_to_file
        )
        lock = _get_store_lock()
        stored = get_task(task_id)
        normalized_result = dict(result_data)
        if stored is not None:
            stored.update(result_data)
            stored["result"] = normalized_result
            stored["status"] = result_data.get("status", stored.get("status"))
            stored["completed_at"] = time.time()
        else:
            stored = {
                "task_id": task_id,
                "status": result_data.get("status", "unknown"),
                "completed_at": time.time(),
                "created_at": time.time(),
                "result": normalized_result,
            }
            stored.update(result_data)
        with lock:
            _task_store[task_id] = stored
            _save_task_to_file(task_id, stored)
        _logger.info(f"[Celery] 任务 {task_id} 状态已持久化: {stored['status']}")
    except Exception as e:
        _logger.warning(f"[Celery] 持久化任务 {task_id} 状态失败: {e}", exc_info=True)


@app.task(bind=True, name='fastapi_backend.tasks.run_scenario')
def task_run_scenario(self, scenario_id: int, env_id: int = None):
    """Celery任务：执行测试场景，实时上报步骤进度"""
    task_id = self.request.id

    try:
        import asyncio

        def on_progress(current_step, total_steps, step_name):
            percent = int((current_step / total_steps) * 100) if total_steps > 0 else 0
            
            # 更新 Celery 状态
            self.update_state(
                state='PROGRESS',
                meta={
                    'current_step': current_step,
                    'total_steps': total_steps,
                    'step_name': step_name,
                    'percent': percent,
                    'current': current_step,
                    'total': total_steps,
                    'current_api': step_name,
                }
            )
            
            # 同步更新持久化存储，确保前端轮询能获取最新进度
            try:
                from fastapi_backend.services.autotest_task_store import _task_store, _get_store_lock, _save_task_to_file
                lock = _get_store_lock()
                progress_data = {
                    "task_id": task_id,
                    "scenario_id": scenario_id,
                    "status": "PROGRESS",
                    "info": f"执行中: {step_name} ({current_step}/{total_steps})",
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
                with lock:
                    if task_id in _task_store:
                        _task_store[task_id].update(progress_data)
                    else:
                        _task_store[task_id] = progress_data
                    _save_task_to_file(task_id, _task_store[task_id])
            except Exception as e:
                _logger.warning(f"[Celery] 同步进度到持久化存储失败: {e}")

        from fastapi_backend.services.autotest_scenario_runner import run_scenario as execute_scenario_async

        result = asyncio.run(execute_scenario_async(scenario_id, env_id, progress_callback=on_progress))

        result['task_id'] = task_id
        result['status'] = 'completed'
        result['scenario_id'] = scenario_id

        from fastapi_backend.services.webhook_notify import notify_scenario_schedule_webhook_from_db
        wh_ok, wh_detail = notify_scenario_schedule_webhook_from_db(scenario_id, result)
        _logger.info(f"[Celery] schedule webhook: ok={wh_ok} {wh_detail[:300]}")

        _persist_task_result(task_id, result)

        return result
    except Exception as e:
        fail_payload = {
            'task_id': task_id,
            'scenario_id': scenario_id,
            'status': 'failed',
            'error': str(e)
        }
        try:
            from fastapi_backend.services.webhook_notify import notify_scenario_schedule_webhook_from_db
            wh_ok, wh_detail = notify_scenario_schedule_webhook_from_db(scenario_id, fail_payload)
            _logger.warning(f"[Celery] schedule webhook (failed run): ok={wh_ok} {wh_detail[:300]}")
        except Exception as e:
            logging.getLogger(__name__).warning(f"通知 webhook 失败: {e}")
        _persist_task_result(task_id, fail_payload)
        return fail_payload
    """Celery任务：执行单个用例"""
    task_id = self.request.id

    try:
        # 导入必要的模块
        from fastapi_backend.services.autotest_execution import quick_run_case
        from sqlalchemy import select
        from fastapi_backend.core.autotest_database import async_session
        from fastapi_backend.models.autotest import AutoTestCase, AutoTestEnvironment
        import asyncio

        # 从数据库获取用例和环境
        async def _execute():
            async with async_session() as db:
                # 获取用例
                result = await db.execute(select(AutoTestCase).where(AutoTestCase.id == case_id))
                case = result.scalar_one_or_none()
                if not case:
                    raise ValueError(f"用例 {case_id} 不存在")

                # 获取环境
                env = None
                if env_id:
                    result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.id == env_id))
                    env = result.scalar_one_or_none()
                else:
                    result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.is_default))
                    env = result.scalars().first()

                # 执行用例
                result_data = await quick_run_case(case, env)
                result_data['task_id'] = task_id
                result_data['status'] = 'completed'
                return result_data

        # 同步执行异步函数
        return asyncio.run(_execute())
    except Exception as e:
        return {
            'task_id': task_id,
            'case_id': case_id,
            'status': 'failed',
            'error': str(e)
        }

@app.task(bind=True, name='fastapi_backend.tasks.send_email')
def task_send_email(self, to_email: str, subject: str, content: str):
    """Celery任务：发送邮件"""
    task_id = self.request.id

    try:
        # 这里简单模拟邮件发送
        time.sleep(1)  # 模拟发送延迟

        return {
            'task_id': task_id,
            'status': 'completed',
            'to_email': to_email,
            'subject': subject,
            'sent': True
        }
    except Exception as e:
        return {
            'task_id': task_id,
            'status': 'failed',
            'error': str(e)
        }

# 创建Celery应用实例
celery_app = app
