"""
JMeter 压测业务编排层 - 协调 DB 记录、Celery 任务、引擎调用

职责:
- submit_bench: 创建 JmeterBenchRun 记录 + 发送 Celery 任务
- get_run: 查询单次运行状态 + 最新 snapshot
- list_runs: 历史列表(分页)
- get_snapshots: 时序快照数组(前端轮询图表)
- stop_run: Celery revoke + 子进程 SIGTERM
- get_html_report: 读取 HTML 报告内容
- compare_runs: 多次压测结果对比
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.jmeter_settings import is_jmeter_available
from fastapi_backend.models.autotest_jmeter_models import (
    JmeterBenchRun,
    JmeterBenchSample,
    JmeterBenchSnapshot,
    JmeterPerformanceBaseline,
)

_logger = logging.getLogger(__name__)


def _compute_script_hash(jmx_content: str) -> str:
    """计算 JMX 内容的 SHA256,用于基线匹配"""
    return hashlib.sha256(jmx_content.encode("utf-8")).hexdigest()


async def submit_bench(
    db: AsyncSession,
    user_id: int,
    plan_name: str,
    jmx_content: str,
    config: Dict[str, Any],
    engine_type: str = "jmeter",
) -> Dict[str, Any]:
    """提交压测任务,创建 DB 记录并发送 Celery 任务

    Args:
        db: 异步 DB 会话
        user_id: 用户 ID
        plan_name: 计划名称
        jmx_content: JMX 文件内容
        config: 配置(concurrency/duration/ramp_up/props 等)
        engine_type: 'mock' | 'jmeter'

    Returns:
        {"run_id": int, "task_id": str, "status": "pending"}
    """
    script_hash = _compute_script_hash(jmx_content)
    run = JmeterBenchRun(
        user_id=user_id,
        plan_name=plan_name,
        config_json=json.dumps(config, ensure_ascii=False),
        engine_type=engine_type,
        status="pending",
        script_hash=script_hash,
    )
    db.add(run)
    await db.commit()
    await db.refresh(run)

    # 发送 Celery 任务(仅 JMeter 引擎模式)
    task_id = None
    if engine_type == "jmeter":
        if not is_jmeter_available():
            # 引擎不可用时,标记为 failed
            run.status = "failed"
            run.error_msg = "JMeter 引擎未启用或可执行文件不存在"
            run.finished_at = datetime.utcnow()
            await db.commit()
            return {
                "run_id": run.id,
                "task_id": None,
                "status": "failed",
                "error": run.error_msg,
            }
        from fastapi_backend.tasks import task_run_jmeter_bench

        celery_result = task_run_jmeter_bench.delay(run.id)
        task_id = celery_result.id
        run.task_id = task_id
        await db.commit()

    return {"run_id": run.id, "task_id": task_id, "status": "pending"}


async def get_run(db: AsyncSession, run_id: int, user_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """查询单次运行状态 + 最新 snapshot"""
    stmt = select(JmeterBenchRun).where(JmeterBenchRun.id == run_id)
    if user_id is not None:
        stmt = stmt.where(JmeterBenchRun.user_id == user_id)
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        return None

    # 查最新 snapshot
    snap_stmt = (
        select(JmeterBenchSnapshot)
        .where(JmeterBenchSnapshot.run_id == run_id)
        .order_by(desc(JmeterBenchSnapshot.ts))
        .limit(1)
    )
    snap_result = await db.execute(snap_stmt)
    snapshot = snap_result.scalar_one_or_none()

    return {
        "id": run.id,
        "plan_name": run.plan_name,
        "engine_type": run.engine_type,
        "status": run.status,
        "task_id": run.task_id,
        "config": json.loads(run.config_json) if run.config_json else {},
        "summary": json.loads(run.summary_json) if run.summary_json else None,
        "error_msg": run.error_msg,
        "regression": bool(run.regression),
        "html_report_available": bool(run.html_report_path),
        "latest_snapshot": {
            "percent": snapshot.percent,
            "active_threads": snapshot.active_threads,
            "tps": snapshot.tps,
            "avg_ms": snapshot.avg_ms,
            "p95_ms": snapshot.p95_ms,
            "error_rate": snapshot.error_rate,
            "ts": snapshot.ts.isoformat() if snapshot.ts else None,
        }
        if snapshot
        else None,
        "started_at": run.started_at.isoformat() if run.started_at else None,
        "finished_at": run.finished_at.isoformat() if run.finished_at else None,
        "created_at": run.created_at.isoformat() if run.created_at else None,
    }


async def list_runs(
    db: AsyncSession, user_id: Optional[int] = None, limit: int = 20, offset: int = 0
) -> List[Dict[str, Any]]:
    """历史压测列表"""
    stmt = select(JmeterBenchRun).order_by(desc(JmeterBenchRun.created_at)).limit(limit).offset(offset)
    if user_id is not None:
        stmt = stmt.where(JmeterBenchRun.user_id == user_id)
    result = await db.execute(stmt)
    runs = result.scalars().all()
    return [
        {
            "id": r.id,
            "plan_name": r.plan_name,
            "engine_type": r.engine_type,
            "status": r.status,
            "summary": json.loads(r.summary_json) if r.summary_json else None,
            "regression": bool(r.regression),
            "html_report_available": bool(r.html_report_path),
            "created_at": r.created_at.isoformat() if r.created_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r in runs
    ]


async def get_snapshots(db: AsyncSession, run_id: int) -> List[Dict[str, Any]]:
    """时序快照数组,前端轮询图表"""
    stmt = select(JmeterBenchSnapshot).where(JmeterBenchSnapshot.run_id == run_id).order_by(JmeterBenchSnapshot.ts)
    result = await db.execute(stmt)
    snapshots = result.scalars().all()
    return [
        {
            "ts": s.ts.isoformat() if s.ts else None,
            "percent": s.percent,
            "active_threads": s.active_threads,
            "tps": s.tps,
            "avg_ms": s.avg_ms,
            "p95_ms": s.p95_ms,
            "error_rate": s.error_rate,
        }
        for s in snapshots
    ]


async def stop_run(db: AsyncSession, run_id: int, user_id: Optional[int] = None) -> Dict[str, Any]:
    """停止压测任务:Celery revoke + 标记 stopped"""
    stmt = select(JmeterBenchRun).where(JmeterBenchRun.id == run_id)
    if user_id is not None:
        stmt = stmt.where(JmeterBenchRun.user_id == user_id)
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run:
        return {"ok": False, "error": "run not found"}

    if run.status in ("success", "failed", "stopped"):
        return {"ok": True, "already_done": True, "status": run.status}

    # Celery revoke
    if run.task_id:
        try:
            from fastapi_backend.celery_config import app as celery_app

            celery_app.control.revoke(run.task_id, terminate=True, signal="SIGTERM")
        except Exception as e:
            _logger.warning("Celery revoke 失败(忽略): %s", e)

    # 标记 stopped
    run.status = "stopped"
    run.finished_at = datetime.utcnow()
    await db.commit()

    _logger.info("[JMeter] run_id=%s 已停止", run_id)
    return {"ok": True, "status": "stopped"}


async def get_html_report(db: AsyncSession, run_id: int) -> Optional[str]:
    """读取 HTML 报告内容(前端新窗口渲染)"""
    stmt = select(JmeterBenchRun).where(JmeterBenchRun.id == run_id)
    result = await db.execute(stmt)
    run = result.scalar_one_or_none()
    if not run or not run.html_report_path:
        return None

    import os

    index_path = os.path.join(run.html_report_path, "index.html")
    if not os.path.exists(index_path):
        return None
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()


async def compare_runs(db: AsyncSession, run_ids: List[int]) -> List[Dict[str, Any]]:
    """对比多次压测结果(Stage E 使用)"""
    if not run_ids:
        return []
    stmt = select(JmeterBenchRun).where(JmeterBenchRun.id.in_(run_ids)).order_by(JmeterBenchRun.created_at)
    result = await db.execute(stmt)
    runs = result.scalars().all()
    return [
        {
            "id": r.id,
            "plan_name": r.plan_name,
            "engine_type": r.engine_type,
            "summary": json.loads(r.summary_json) if r.summary_json else None,
            "regression": bool(r.regression),
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in runs
    ]


# ===== 基线管理(Stage E)=====


async def create_baseline(
    db: AsyncSession,
    user_id: int,
    name: str,
    script_hash: str,
    p95_threshold_ms: Optional[int] = None,
    p99_threshold_ms: Optional[int] = None,
    tps_threshold: Optional[float] = None,
    error_rate_threshold: Optional[float] = None,
) -> Dict[str, Any]:
    baseline = JmeterPerformanceBaseline(
        user_id=user_id,
        name=name,
        script_hash=script_hash,
        p95_threshold_ms=p95_threshold_ms,
        p99_threshold_ms=p99_threshold_ms,
        tps_threshold=tps_threshold,
        error_rate_threshold=error_rate_threshold,
    )
    db.add(baseline)
    await db.commit()
    await db.refresh(baseline)
    return {"id": baseline.id, "name": baseline.name, "script_hash": baseline.script_hash}


async def list_baselines(
    db: AsyncSession, user_id: Optional[int] = None, script_hash: Optional[str] = None
) -> List[Dict[str, Any]]:
    stmt = select(JmeterPerformanceBaseline).order_by(desc(JmeterPerformanceBaseline.created_at))
    if user_id is not None:
        stmt = stmt.where(JmeterPerformanceBaseline.user_id == user_id)
    if script_hash:
        stmt = stmt.where(JmeterPerformanceBaseline.script_hash == script_hash)
    result = await db.execute(stmt)
    baselines = result.scalars().all()
    return [
        {
            "id": b.id,
            "name": b.name,
            "script_hash": b.script_hash,
            "p95_threshold_ms": b.p95_threshold_ms,
            "p99_threshold_ms": b.p99_threshold_ms,
            "tps_threshold": b.tps_threshold,
            "error_rate_threshold": b.error_rate_threshold,
            "created_at": b.created_at.isoformat() if b.created_at else None,
        }
        for b in baselines
    ]


async def delete_baseline(db: AsyncSession, baseline_id: int) -> bool:
    stmt = select(JmeterPerformanceBaseline).where(JmeterPerformanceBaseline.id == baseline_id)
    result = await db.execute(stmt)
    baseline = result.scalar_one_or_none()
    if not baseline:
        return False
    await db.delete(baseline)
    await db.commit()
    return True


async def match_baseline_by_hash(db: AsyncSession, script_hash: str) -> Optional[JmeterPerformanceBaseline]:
    """根据 script_hash 自动匹配基线(压测完成后调用)"""
    stmt = (
        select(JmeterPerformanceBaseline)
        .where(JmeterPerformanceBaseline.script_hash == script_hash)
        .order_by(desc(JmeterPerformanceBaseline.created_at))
        .limit(1)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


def check_regression(summary: Dict[str, Any], baseline: JmeterPerformanceBaseline) -> bool:
    """检查是否性能回归 - 任一指标超阈值即回归"""
    if not summary:
        return False
    if baseline.p95_threshold_ms is not None and summary.get("p95_ms", 0) > baseline.p95_threshold_ms:
        return True
    if baseline.p99_threshold_ms is not None and summary.get("p99_ms", 0) > baseline.p99_threshold_ms:
        return True
    if baseline.tps_threshold is not None and summary.get("tps", 0) < baseline.tps_threshold:
        return True
    if baseline.error_rate_threshold is not None and summary.get("error_rate", 0) > baseline.error_rate_threshold:
        return True
    return False


# ===== 采样器详情(Stage F.4 修复 BUG 2 引入)=====


async def save_samples(
    db: AsyncSession,
    run_id: int,
    user_id: int,
    samples: List[Dict[str, Any]],
    max_samples: int = 500,
) -> int:
    """把 JtlParser 解析出的每条 sample 写入 jmeter_bench_samples 表。

    Args:
        samples: JtlParser._parse_csv_full / _parse_xml_full 返回的样本列表
        max_samples: 最多落库条数,防止 10w+ 请求把表撑爆

    Returns:
        实际写入条数
    """
    if not samples:
        return 0
    # 截断:保留前 max_samples 条 + 失败/错误的所有条目
    truncated = samples[:max_samples] if len(samples) > max_samples else samples
    rows = [
        JmeterBenchSample(
            run_id=run_id,
            user_id=user_id,
            label=(s.get("label") or "")[:500],
            method=(s.get("method") or "")[:20],
            url=(s.get("url") or "")[:2000],
            response_code=(s.get("response_code") or "")[:20],
            response_message=(s.get("response_message") or "")[:255],
            elapsed_ms=int(s.get("elapsed", 0) or 0),
            latency_ms=int(s.get("latency", 0) or 0),
            bytes_received=int(s.get("bytes", 0) or 0),
            bytes_sent=int(s.get("sent_bytes", 0) or 0),
            success=bool(s.get("success", True)),
            failure_message=(s.get("failure_message") or "")[:2000],
            request_data=(s.get("request_data") or "")[:2000],
            response_data=(s.get("response_data") or "")[:2000],
            request_headers=(s.get("request_headers") or "")[:2000],
            response_headers=(s.get("response_headers") or "")[:2000],
            thread_name=(s.get("thread_name") or "")[:255],
        )
        for s in truncated
    ]
    db.add_all(rows)
    await db.commit()
    return len(rows)


async def list_samples(
    db: AsyncSession,
    run_id: int,
    user_id: int,
    limit: int = 100,
    only_failures: bool = False,
) -> List[Dict[str, Any]]:
    """查询某次压测的采样器详情(供前端"采样器列表"面板使用)。

    Args:
        limit: 返回最多条数
        only_failures: True 时只返回失败采样(便于定位 500 错误)
    """
    stmt = select(JmeterBenchSample).where(
        JmeterBenchSample.run_id == run_id,
        JmeterBenchSample.user_id == user_id,
    )
    if only_failures:
        stmt = stmt.where(JmeterBenchSample.success == False)  # noqa: E712
    stmt = stmt.order_by(desc(JmeterBenchSample.id)).limit(min(limit, 500))
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "label": r.label,
            "method": r.method,
            "url": r.url,
            "status": r.response_code,  # 前端用 bs.status
            "response_message": r.response_message,
            "elapsed_ms": r.elapsed_ms,
            "latency_ms": r.latency_ms,
            "bytes_received": r.bytes_received,
            "bytes_sent": r.bytes_sent,
            "success": r.success,
            "failure_message": r.failure_message,
            "request_body": r.request_data,
            "response_body": r.response_data,
            "request_headers": r.request_headers,
            "response_headers": r.response_headers,
            "thread_name": r.thread_name,
            "ts": r.ts.isoformat() if r.ts else None,
        }
        for r in rows
    ]
