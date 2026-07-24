"""
后台管理子路由 - 备份/审计/系统
从 admin_manage.py 拆分
"""

from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func, text
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
import platform
import random
import psutil
from fastapi_backend.routers import backup as backup_management

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
    """Compatibility route backed by the single shared backup implementation."""
    return await backup_management.get_backups(current_user)


@router.post("/backups")
async def create_backup(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    response = await backup_management.create_new_backup(current_user)
    backup_name = response["backup_name"]
    await _write_audit_log(db, user_id=current_user.id, action="创建数据库备份", action_type="backup", detail=f"备份文件: {backup_name}")
    return {"message": "备份创建成功", "name": backup_name}


@router.delete("/backups/old")
async def delete_old_backups(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    response = await backup_management.clean_old(current_user)
    await _write_audit_log(db, user_id=current_user.id, action="清理旧备份", action_type="backup", detail=response["message"])
    return response


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
    return await backup_management.download_backup(name, current_user)


@router.post("/backups/{name}/restore")
async def restore_backup(
    name: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    await _write_audit_log(db, user_id=current_user.id, action="恢复数据库备份", action_type="backup", detail=f"恢复文件: {name}")
    return await backup_management.restore_backup(name, current_user)


@router.delete("/backups/{name}")
async def delete_backup(
    name: str,
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    response = await backup_management.delete_backup(name, current_user)
    await _write_audit_log(db, user_id=current_user.id, action="删除备份文件", action_type="backup", detail=f"删除文件: {name}")
    return response


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


# ============== 系统指标 ==============
# 注意：审计日志查询接口已迁移至 fastapi_backend/routers/audit_logs.py
# 路径：GET /api/v1/admin/audit-logs（支持多维度过滤、统计、导出）


def _generate_system_load_7d():
    """生成最近 7 天的系统负载模拟数据（基于当前系统负载 + 随机波动）"""
    labels = [(datetime.now() - timedelta(days=6 - i)).strftime("%m-%d") for i in range(7)]
    try:
        current_load = psutil.cpu_percent(interval=None)
    except Exception:
        current_load = 0
    values = [round(max(0, min(100, current_load + random.uniform(-15, 15))), 1) for _ in range(7)]
    return {"labels": labels, "values": values}


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
            "system_load_7d": _generate_system_load_7d(),
        },
    }
