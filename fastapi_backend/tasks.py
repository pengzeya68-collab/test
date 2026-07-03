"""
Celery tasks for TestMaster project.
"""

import logging
import threading
import time

from fastapi_backend.celery_config import app
from celery.exceptions import Ignore

# 确保 AI 生成任务被 Celery worker 发现和注册
import fastapi_backend.services.autotest_ai_generator  # noqa: F401

_logger = logging.getLogger(__name__)


# 模块级全局共享engine，避免每次Celery任务创建新AsyncEngine
_celery_engine = None
_celery_engine_lock = threading.Lock()


def _get_celery_engine():
    """懒加载全局共享AsyncEngine（线程安全），Celery任务复用，不在任务结束时dispose。"""
    global _celery_engine
    if _celery_engine is None:
        with _celery_engine_lock:
            if _celery_engine is None:
                from sqlalchemy.ext.asyncio import create_async_engine as _create_async_engine

                from fastapi_backend.core.config import settings as _settings

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
    return _celery_engine


def _persist_task_result(task_id: str, result_data: dict) -> None:
    """同步写入任务结果到持久化存储（Celery 进程内调用）"""
    try:
        from fastapi_backend.services.autotest_task_store import (
            get_task_sync,
            update_task_sync,
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
        update_task_sync(task_id, stored)
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
                    get_task_sync,
                    update_task_sync,
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
                stored = get_task_sync(task_id)
                if stored is not None:
                    stored.update(progress_data)
                else:
                    stored = progress_data
                update_task_sync(task_id, stored)
            except Exception as e:
                _logger.warning(f"[Celery] 同步进度到持久化存储失败: {e}")

        from fastapi_backend.services.autotest_scenario_runner import (
            run_scenario as execute_scenario_async,
        )

        # 复用全局共享engine，不在任务结束时dispose
        # 内层全部使用await，asyncio.run仅在最外层调用
        _get_celery_engine()

        async def _run_scenario_async():
            # 所有async操作内层使用await，禁止在此处再调用asyncio.run
            return await execute_scenario_async(
                scenario_id, env_id, progress_callback=on_progress, user_id=user_id
            )

        # 确保asyncio.run在最外层；若已在事件循环中（异常情况），使用线程池隔离避免嵌套
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            # 无运行中的事件循环，安全使用asyncio.run
            result = asyncio.run(_run_scenario_async())
        else:
            # 已在事件循环中，使用线程池隔离执行，避免嵌套asyncio.run
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                result = pool.submit(asyncio.run, _run_scenario_async()).result()

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
        # 显式标记 Celery 任务状态为 FAILURE，避免误报 SUCCESS
        self.update_state(state="FAILURE", meta=fail_payload)
        raise Ignore()


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


@app.task(bind=True, name="fastapi_backend.tasks.run_jmeter_bench")
def task_run_jmeter_bench(self, run_id: int):
    """执行真实 JMeter 压测任务

    流程:
    1. 同步加载 JmeterBenchRun（用 _get_celery_engine 创建同步 session）
    2. 更新状态 running + started_at
    3. 调用 JmeterEngine.run(jmx_content, run_id, props)
    4. 解析 .jtl → 聚合指标
    5. 写入 JmeterBenchRun.summary_json + html_report_path + jtl_path + finished_at
    6. 自动匹配基线检查回归
    7. 更新状态 success/failed
    """
    task_id = self.request.id

    try:
        import asyncio
        import gc
        import json as _json
        from datetime import datetime as _dt
        from sqlalchemy import create_engine as _create_sync_engine
        from sqlalchemy.orm import sessionmaker as _sessionmaker
        from fastapi_backend.core.config import settings as _settings
        from fastapi_backend.core.jmeter_settings import is_jmeter_available, JMETER_REPORT_DIR
        from fastapi_backend.services.jmeter_engine import JmeterEngine, JtlParser
        from fastapi_backend.services.autotest_jmeter_service import export_tree_to_jmx
        from fastapi_backend.services.jmeter_bench_service import check_regression
        from fastapi_backend.models.autotest_jmeter_models import (
            JmeterBenchRun, JmeterBenchSnapshot, JmeterPerformanceBaseline,
        )

        def _normalize_url(url: str) -> str:
            if url.startswith("postgresql+asyncpg://"):
                return url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
            if url.startswith("postgresql://"):
                return url.replace("postgresql://", "postgresql+psycopg2://", 1)
            return url

        # 创建同步 engine 供 Celery 任务使用
        sync_engine = _create_sync_engine(
            _normalize_url(_settings.DATABASE_URL),
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=2,
            max_overflow=4,
        )
        SyncSession = _sessionmaker(bind=sync_engine, expire_on_commit=False)

        # 1. 加载 run 记录 + 更新状态为 running
        with SyncSession() as sync_db:
            run = sync_db.query(JmeterBenchRun).filter(JmeterBenchRun.id == run_id).one_or_none()
            if not run:
                raise RuntimeError(f"JmeterBenchRun not found: {run_id}")
            if run.status in ("stopped", "cancelled"):
                _logger.info("[JMeter] run_id=%s 已被停止,跳过", run_id)
                return {"status": "skipped", "run_id": run_id}
            run.task_id = task_id
            run.status = "running"
            run.started_at = _dt.utcnow()
            sync_db.commit()

            config = _json.loads(run.config_json) if run.config_json else {}
            # 若无 jmx_path，从 config 中的 script_tree 重新生成 JMX
            jmx_content = config.get("jmx_content", "")

        # 2. 执行 JMeter（async）
        async def _run_jmeter_async():
            # 写 snapshot 的 helper（用新同步 session 避免跨线程）
            def _write_snapshot(percent: int, tps: float, avg_ms: float, p95_ms: float, error_rate: float, active: int):
                try:
                    with SyncSession() as snap_db:
                        snap = JmeterBenchSnapshot(
                            run_id=run_id, percent=percent, tps=tps,
                            avg_ms=avg_ms, p95_ms=p95_ms, error_rate=error_rate,
                            active_threads=active,
                        )
                        snap_db.add(snap)
                        snap_db.commit()
                except Exception as e:
                    _logger.warning("[JMeter] 写 snapshot 失败: %s", e)

            # 进度心跳（JMeter subprocess 期间无法精确进度，这里仅做存活心跳）
            _write_snapshot(10, 0, 0, 0, 0, config.get("concurrency", 1))
            self.update_state(state="PROGRESS", meta={"percent": 10, "status": "running"})

            engine_result = await JmeterEngine.run(
                jmx_content=jmx_content,
                run_id=str(run_id),
                props=config.get("props", {}),
            )

            _write_snapshot(90, 0, 0, 0, 0, config.get("concurrency", 1))
            return engine_result

        # 在最外层用 asyncio.run，处理已存在事件循环的情况
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            engine_result = asyncio.run(_run_jmeter_async())
        else:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                engine_result = pool.submit(asyncio.run, _run_jmeter_async()).result()

        gc.collect()

        # 3. 检查停止信号
        with SyncSession() as sync_db:
            run = sync_db.query(JmeterBenchRun).filter(JmeterBenchRun.id == run_id).one_or_none()
            if run and run.status == "stopped":
                _logger.info("[JMeter] run_id=%s 执行中收到停止信号,放弃结果", run_id)
                return {"status": "stopped", "run_id": run_id}

        # 4. 解析 .jtl → 聚合指标
        summary = {}
        if engine_result.get("jtl_path"):
            summary = JtlParser.parse(engine_result["jtl_path"])

        # 5. 写入最终结果 + 基线检查
        with SyncSession() as sync_db:
            run = sync_db.query(JmeterBenchRun).filter(JmeterBenchRun.id == run_id).one_or_none()
            if not run:
                raise RuntimeError(f"JmeterBenchRun disappeared: {run_id}")

            run.jmx_path = engine_result.get("jmx_path")
            run.jtl_path = engine_result.get("jtl_path")
            run.html_report_path = engine_result.get("report_dir")
            run.summary_json = _json.dumps(summary, ensure_ascii=False)
            run.finished_at = _dt.utcnow()

            # 基线检查（Stage E 提前接入，避免后续再次修改）- 同步查询避免 async/sync 混用
            if run.script_hash:
                baseline = (
                    sync_db.query(JmeterPerformanceBaseline)
                    .filter(JmeterPerformanceBaseline.script_hash == run.script_hash)
                    .order_by(JmeterPerformanceBaseline.created_at.desc())
                    .first()
                )
                if baseline:
                    is_regression = check_regression(summary, baseline)
                    run.regression = 1 if is_regression else 0

            # 状态判定
            if engine_result.get("exit_code") == 0 and summary.get("total", 0) > 0:
                run.status = "success"
            else:
                run.status = "failed"
                run.error_msg = (
                    f"JMeter exit_code={engine_result.get('exit_code')}\n"
                    f"stderr={engine_result.get('stderr', '')[:2000]}"
                )
            sync_db.commit()

            # 最终 snapshot
            snap = JmeterBenchSnapshot(
                run_id=run_id, percent=100,
                tps=summary.get("tps", 0), avg_ms=summary.get("avg_ms", 0),
                p95_ms=summary.get("p95_ms", 0), error_rate=summary.get("error_rate", 0),
                active_threads=0,
            )
            sync_db.add(snap)
            sync_db.commit()

        sync_engine.dispose()
        _logger.info("[JMeter] run_id=%s 完成: status=%s", run_id, run.status)

        return {
            "run_id": run_id,
            "task_id": task_id,
            "status": run.status,
            "summary": summary,
        }

    except Exception as e:
        _logger.error("[JMeter] run_id=%s 失败: %s", run_id, e, exc_info=True)
        fail_payload = {
            "run_id": run_id,
            "task_id": task_id,
            "status": "failed",
            "error": str(e),
        }
        # 更新 DB 状态
        try:
            from sqlalchemy import create_engine as _ce
            from sqlalchemy.orm import sessionmaker as _sm
            from fastapi_backend.core.config import settings as _s
            from datetime import datetime as _dt_fail
            _url = _s.DATABASE_URL
            if _url.startswith("postgresql+asyncpg://"):
                _url = _url.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
            elif _url.startswith("postgresql://"):
                _url = _url.replace("postgresql://", "postgresql+psycopg2://", 1)
            _eng = _ce(_url, pool_pre_ping=True)
            _SS = _sm(bind=_eng)
            with _SS() as _db:
                _r = _db.query(JmeterBenchRun).filter(JmeterBenchRun.id == run_id).one_or_none()
                if _r:
                    _r.status = "failed"
                    _r.error_msg = str(e)[:5000]
                    _r.finished_at = _dt_fail.utcnow()
                    _db.commit()
            _eng.dispose()
        except Exception as inner:
            _logger.error("[JMeter] 写失败状态到 DB 出错: %s", inner)

        try:
            self.update_state(state="FAILURE", meta=fail_payload)
        except Exception:
            pass
        raise Ignore()


celery_app = app
