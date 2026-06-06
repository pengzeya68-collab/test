"""
后台管理子路由 - 备份/审计/系统
从 admin_manage.py 拆分
"""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, desc, text
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.core.config import settings
from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import (
    User,
    Exercise,
    LearningPath,
    Exam,
    InterviewQuestion,
    Submission,
    AuditLog,
)
import os
import subprocess
import platform
import asyncio
from fastapi.responses import FileResponse

router = APIRouter(prefix="/api/v1/admin", tags=["Admin-系统管理"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

MAX_BACKUPS = 10


def _pg_connection_params() -> dict:
    url = settings.DATABASE_URL
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    elif url.startswith("postgresql://"):
        pass
    else:
        return {}
    from urllib.parse import urlparse

    parsed = urlparse(url)
    return {
        "host": parsed.hostname or "localhost",
        "port": str(parsed.port or 5432),
        "dbname": parsed.path.lstrip("/"),
        "user": parsed.username or "testmaster",
        "password": parsed.password or "",
    }


@router.get("/backups")
async def list_backups(
    current_user: User = Depends(require_admin),
):
    """获取备份列表"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backups = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.endswith(".sql") or f.endswith(".zip"):
            filepath = os.path.join(BACKUP_DIR, f)
            stat = os.stat(filepath)
            backups.append(
                {
                    "name": f,
                    "size": round(stat.st_size / (1024 * 1024), 2),
                    "time": int(stat.st_mtime * 1000),
                }
            )
    return {"backups": backups, "max_backups": MAX_BACKUPS}


@router.post("/backups")
async def create_backup(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """创建数据库备份 (pg_dump)"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    params = _pg_connection_params()
    if not params:
        raise HTTPException(status_code=500, detail="数据库不是 PostgreSQL，无法备份")

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    backup_name = f"testmaster_backup_{timestamp}.sql"
    backup_path = os.path.join(BACKUP_DIR, backup_name)

    env = os.environ.copy()
    env["PGPASSWORD"] = params["password"]

    cmd = [
        "pg_dump",
        "-h",
        params["host"],
        "-p",
        params["port"],
        "-U",
        params["user"],
        "-d",
        params["dbname"],
        "--no-password",
        "--format=plain",
        "--no-owner",
    ]

    try:
        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, env=env, timeout=120)
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"pg_dump 失败: {result.stderr[:200]}")
        with open(backup_path, "w", encoding="utf-8") as f:
            f.write(result.stdout)
        await _write_audit_log(db, user_id=current_user.id, action="创建数据库备份", action_type="backup", detail=f"备份文件: {backup_name}")
        return {"message": "备份创建成功", "name": backup_name}
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="pg_dump 命令未找到")
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="pg_dump 超时")


@router.delete("/backups/old")
async def delete_old_backups(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """清理旧备份（保留最近5个）"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    files = sorted([f for f in os.listdir(BACKUP_DIR) if f.endswith(".sql") or f.endswith(".zip")])

    if len(files) <= 5:
        return {"message": "没有需要清理的旧备份"}

    deleted = 0
    for f in files[:-5]:
        os.remove(os.path.join(BACKUP_DIR, f))
        deleted += 1

    await _write_audit_log(db, user_id=current_user.id, action="清理旧备份", action_type="backup", detail=f"清理了 {deleted} 个旧备份文件")
    return {"message": f"已清理 {deleted} 个旧备份"}


def _safe_backup_path(name: str) -> str:
    filepath = os.path.join(BACKUP_DIR, name)
    filepath = os.path.abspath(filepath)
    if not filepath.startswith(os.path.abspath(BACKUP_DIR)):
        raise HTTPException(status_code=400, detail="非法文件路径")
    return filepath


@router.get("/backups/download/{name}")
async def download_backup(
    name: str,
    current_user: User = Depends(require_admin),
):
    filepath = _safe_backup_path(name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="备份文件不存在")
    return FileResponse(filepath, filename=name)


@router.post("/backups/{name}/restore")
async def restore_backup(
    name: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """恢复备份 (psql)"""
    backup_path = _safe_backup_path(name)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")

    params = _pg_connection_params()
    if not params:
        raise HTTPException(status_code=500, detail="数据库不是 PostgreSQL，无法恢复")

    env = os.environ.copy()
    env["PGPASSWORD"] = params["password"]

    cmd = [
        "psql",
        "-h",
        params["host"],
        "-p",
        params["port"],
        "-U",
        params["user"],
        "-d",
        params["dbname"],
        "--no-password",
        "-f",
        backup_path,
    ]

    try:
        result = await asyncio.to_thread(subprocess.run, cmd, capture_output=True, text=True, env=env, timeout=300)
        if result.returncode != 0:
            await _write_audit_log(db, user_id=current_user.id, action="恢复数据库备份", action_type="backup", detail=f"恢复文件: {name}", status="failed")
            raise HTTPException(status_code=500, detail=f"恢复失败: {result.stderr[:200]}")
        await _write_audit_log(db, user_id=current_user.id, action="恢复数据库备份", action_type="backup", detail=f"恢复文件: {name}")
        return {"message": "备份恢复成功"}
    except FileNotFoundError:
        await _write_audit_log(db, user_id=current_user.id, action="恢复数据库备份", action_type="backup", detail=f"恢复文件: {name} - psql命令未找到", status="failed")
        raise HTTPException(status_code=500, detail="psql 命令未找到")
    except subprocess.TimeoutExpired:
        await _write_audit_log(db, user_id=current_user.id, action="恢复数据库备份", action_type="backup", detail=f"恢复文件: {name} - 超时", status="failed")
        raise HTTPException(status_code=500, detail="恢复超时")


@router.delete("/backups/{name}")
async def delete_backup(
    name: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    filepath = _safe_backup_path(name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="备份文件不存在")

    os.remove(filepath)
    await _write_audit_log(db, user_id=current_user.id, action="删除备份文件", action_type="backup", detail=f"删除文件: {name}")
    return {"message": "备份删除成功"}


# ============== 审计日志 ==============


async def _write_audit_log(
    db: AsyncSession,
    *,
    user_id: int,
    action: str,
    action_type: str = "other",
    detail: str = None,
    ip_address: str = None,
    status: str = "success",
):
    """写入审计日志的辅助函数"""
    log = AuditLog(
        user_id=user_id,
        admin_id=user_id,
        action=action,
        action_type=action_type,
        detail=detail,
        ip_address=ip_address,
        status=status,
    )
    db.add(log)
    await db.commit()


@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """获取高危操作审计日志"""
    total = await db.scalar(select(func.count(AuditLog.id))) or 0
    offset = (page - 1) * size

    query = select(AuditLog).order_by(desc(AuditLog.created_at)).offset(offset).limit(size)
    result = await db.execute(query)
    audit_logs = result.scalars().all()

    # 批量获取用户信息
    user_ids = {log.user_id for log in audit_logs if log.user_id}
    users_map = {}
    if user_ids:
        user_rows = (await db.execute(select(User.id, User.username).where(User.id.in_(user_ids)))).all()
        users_map = {row[0]: row[1] for row in user_rows}

    logs = []
    for log in audit_logs:
        logs.append(
            {
                "id": log.id,
                "user": users_map.get(log.user_id, "系统"),
                "action": log.action,
                "detail": log.detail or "",
                "actionType": log.action_type,
                "status": log.status or "success",
                "ip": log.ip_address or "-",
                "createTime": log.created_at.isoformat() if log.created_at else None,
            }
        )

    return {"logs": logs, "total": total, "page": page, "size": size}


# ============== 系统指标 ==============


@router.get("/system/metrics")
async def get_system_metrics(current_user: User = Depends(require_admin), db: AsyncSession = Depends(get_db)):
    """获取系统指标"""
    total_users = await db.scalar(select(func.count(User.id))) or 0
    total_submissions = await db.scalar(select(func.count(Submission.id))) or 0
    total_exercises = await db.scalar(select(func.count(Exercise.id))) or 0
    total_paths = await db.scalar(select(func.count(LearningPath.id))) or 0
    total_questions = await db.scalar(select(func.count(InterviewQuestion.id))) or 0
    total_exams = await db.scalar(select(func.count(Exam.id))) or 0

    db_size = 0
    try:
        size_result = await db.execute(text("SELECT pg_database_size(current_database())"))
        db_size = size_result.scalar() or 0
    except Exception:
        pass

    backup_size = 0
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            fp = os.path.join(BACKUP_DIR, f)
            if os.path.isfile(fp):
                backup_size += os.path.getsize(fp)

    backup_count = len(os.listdir(BACKUP_DIR)) if os.path.exists(BACKUP_DIR) else 0

    redis_healthy = False
    try:
        from redis.asyncio import Redis as ARedis

        r = ARedis.from_url(settings.REDIS_URL or "redis://redis:6379/0", socket_connect_timeout=2)
        redis_healthy = await r.ping()
        await r.close()
    except Exception:
        pass

    return {
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": os.cpu_count(),
        },
        "database": {
            "size_bytes": db_size,
            "size_mb": round(db_size / 1024 / 1024, 2),
            "total_users": total_users,
            "total_submissions": total_submissions,
            "total_exercises": total_exercises,
            "total_learning_paths": total_paths,
            "total_interview_questions": total_questions,
            "total_exams": total_exams,
            "healthy": True,
        },
        "redis": {
            "enabled": bool(settings.REDIS_URL),
            "healthy": redis_healthy,
        },
        "backups": {
            "size_bytes": backup_size,
            "size_mb": round(backup_size / 1024 / 1024, 2),
            "count": backup_count,
        },
        "charts": {
            "table_space": {
                "labels": [
                    "users",
                    "submissions",
                    "exercises",
                    "paths",
                    "questions",
                    "exams",
                ],
                "values": [
                    total_users,
                    total_submissions,
                    total_exercises,
                    total_paths,
                    total_questions,
                    total_exams,
                ],
            },
            "system_load_7d": {"labels": [], "values": []},
        },
    }
