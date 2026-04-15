"""
Celery tasks for TestMaster project.
"""
import json
import time
from pathlib import Path

from fastapi_backend.celery_config import app
from fastapi_backend.services.autotest_scenario_runner import run_scenario as execute_scenario
from fastapi_backend.services.autotest_execution import quick_run_case
from sqlalchemy import select
from fastapi_backend.core.autotest_database import async_session
from fastapi_backend.models.autotest import AutoTestCase, AutoTestEnvironment

@app.task(bind=True, name='fastapi_backend.tasks.run_scenario')
def task_run_scenario(self, scenario_id: int, env_id: int = None):
    """Celery任务：执行测试场景，实时上报步骤进度"""
    task_id = self.request.id

    try:
        import asyncio

        def on_progress(current_step, total_steps, step_name):
            percent = int((current_step / total_steps) * 100) if total_steps > 0 else 0
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

        from fastapi_backend.services.autotest_scenario_runner import run_scenario as execute_scenario_async

        result = asyncio.run(execute_scenario_async(scenario_id, env_id, progress_callback=on_progress))

        result['task_id'] = task_id
        result['status'] = 'completed'

        from fastapi_backend.services.webhook_notify import notify_scenario_schedule_webhook_from_db
        wh_ok, wh_detail = notify_scenario_schedule_webhook_from_db(scenario_id, result)
        print(f"[Celery] schedule webhook: ok={wh_ok} {wh_detail[:300]}")

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
            print(f"[Celery] schedule webhook (failed run): ok={wh_ok} {wh_detail[:300]}")
        except Exception:
            pass
        return fail_payload

@app.task(bind=True, name='fastapi_backend.tasks.run_case')
def task_run_case(self, case_id: int, env_id: int = None):
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
                    result = await db.execute(select(AutoTestEnvironment).where(AutoTestEnvironment.is_default == True))
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