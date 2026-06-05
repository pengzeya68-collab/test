"""
Celery tasks for TestMaster project.
"""

import logging
import time

from fastapi_backend.celery_config import app

# 确保 AI 生成任务被 Celery worker 发现和注册
import fastapi_backend.services.autotest_ai_generator  # noqa: F401

_logger = logging.getLogger(__name__)


def _persist_task_result(task_id: str, result_data: dict) -> None:
    """同步写入任务结果到持久化存储（Celery 进程内调用）"""
    try:
        from fastapi_backend.services.autotest_task_store import (
            get_task_sync,
            _task_store,
            _save_task_to_file,
        )

        stored = get_task_sync(task_id)
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
        _task_store[task_id] = stored
        _save_task_to_file(task_id, stored)
        _logger.info(f"[Celery] 任务 {task_id} 状态已持久化: {stored['status']}")
    except Exception as e:
        _logger.warning(f"[Celery] 持久化任务 {task_id} 状态失败: {e}", exc_info=True)


@app.task(bind=True, name="fastapi_backend.tasks.run_scenario")
def task_run_scenario(self, scenario_id: int, env_id: int = None, user_id: int = None):
    """Celery任务：执行测试场景，实时上报步骤进度"""
    task_id = self.request.id

    try:
        import asyncio
        import gc

        def on_progress(current_step, total_steps, step_name):
            percent = int((current_step / total_steps) * 100) if total_steps > 0 else 0

            self.update_state(
                state="PROGRESS",
                meta={
                    "current_step": current_step,
                    "total_steps": total_steps,
                    "step_name": step_name,
                    "percent": percent,
                    "current": current_step,
                    "total": total_steps,
                    "current_api": step_name,
                },
            )

            try:
                from fastapi_backend.services.autotest_task_store import (
                    _task_store,
                    _save_task_to_file,
                )

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
                if task_id in _task_store:
                    _task_store[task_id].update(progress_data)
                else:
                    _task_store[task_id] = progress_data
                _save_task_to_file(task_id, _task_store[task_id])
            except Exception as e:
                _logger.warning(f"[Celery] 同步进度到持久化存储失败: {e}")

        from fastapi_backend.services.autotest_scenario_runner import (
            run_scenario as execute_scenario_async,
        )
        from fastapi_backend.core.config import settings as _settings
        from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine

        def _normalize_url(url):
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+asyncpg://", 1)
            return url

        _celery_engine = _create_async_engine(
            _normalize_url(_settings.DATABASE_URL),
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=2,
            max_overflow=4,
        )

        async def _run_with_cleanup():
            try:
                result = await execute_scenario_async(scenario_id, env_id, progress_callback=on_progress, user_id=user_id)
                return result
            finally:
                await _celery_engine.dispose()

        result = asyncio.run(_run_with_cleanup())

        # Force garbage collection to clean up any lingering async references
        gc.collect()

        if not isinstance(result, dict):
            result = {"raw_result": str(result)}
        result["task_id"] = task_id
        result["status"] = "completed"
        result["scenario_id"] = scenario_id

        from fastapi_backend.services.webhook_notify import (
            notify_scenario_schedule_webhook_from_db,
        )

        try:
            wh_ok, wh_detail = notify_scenario_schedule_webhook_from_db(scenario_id, result, user_id=user_id)
            _logger.info(f"[Celery] schedule webhook: ok={wh_ok} {wh_detail[:300]}")
        except Exception as we:
            _logger.warning(f"通知 schedule webhook 失败（不影响执行结果）: {we}")

        _persist_task_result(task_id, result)

        return result
    except Exception as e:
        fail_payload = {
            "task_id": task_id,
            "scenario_id": scenario_id,
            "status": "failed",
            "error": str(e),
        }
        try:
            from fastapi_backend.services.webhook_notify import (
                notify_scenario_schedule_webhook_from_db,
            )

            wh_ok, wh_detail = notify_scenario_schedule_webhook_from_db(scenario_id, fail_payload, user_id=user_id)
            _logger.warning(f"[Celery] schedule webhook (failed run): ok={wh_ok} {wh_detail[:300]}")
        except Exception as we:
            _logger.warning(f"通知 webhook 失败: {we}")
        _persist_task_result(task_id, fail_payload)
        return fail_payload


@app.task(bind=True, max_retries=2, name="fastapi_backend.tasks.send_email")
def task_send_email(self, to_email: str, subject: str, body: str, html_body: str = None):
    """发送邮件的 Celery 任务"""
    task_id = self.request.id

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from fastapi_backend.utils.encryption import decrypt
        from fastapi_backend.services.system_config import get_system_config_sync

        config = get_system_config_sync()
        smtp_host = config.get("smtpHost", "")
        smtp_port = int(config.get("smtpPort", 465))
        smtp_user = config.get("smtpUser", "")
        smtp_password_encrypted = config.get("smtpPassword", "")
        smtp_use_ssl = config.get("smtpUseSSL", config.get("enableSSL", True))
        from_email = config.get("smtpFromEmail", smtp_user)

        if not smtp_host or not smtp_user:
            _logger.warning("SMTP 未配置，邮件发送跳过")
            return {"status": "skipped", "reason": "SMTP not configured", "task_id": task_id}

        smtp_password = decrypt(smtp_password_encrypted) if smtp_password_encrypted else ""

        msg = MIMEMultipart("alternative")
        msg["From"] = from_email
        msg["To"] = to_email
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain", "utf-8"))
        if html_body:
            msg.attach(MIMEText(html_body, "html", "utf-8"))

        # 根据端口和配置选择 SSL 或 TLS 模式
        if smtp_use_ssl or smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, [to_email], msg.as_string())
        else:
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(from_email, [to_email], msg.as_string())

        return {"status": "sent", "to": to_email, "task_id": task_id}
    except Exception as e:
        _logger.error(f"邮件发送失败: {e}")
        raise self.retry(exc=e, countdown=30)


celery_app = app
