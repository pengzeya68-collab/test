"""
后台管理子路由 - 备份/审计/系统
从 admin_manage.py 拆分
"""
from typing import Optional, Any
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy import select, func, or_, and_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db, AsyncSessionLocal
from fastapi_backend.core.exceptions import NotFoundException
from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import User, Exercise, LearningPath, Exam, ExamQuestion, Post, Comment, InterviewQuestion, Submission, Progress
from fastapi_backend.services.auth_service import AuthService
import os
import shutil
import json
import platform
import asyncio
from fastapi.responses import FileResponse
router = APIRouter(prefix="/api/v1/admin", tags=["Admin-系统管理"])

@router.get("/backups")
async def list_backups(
    current_user: User = Depends(require_admin),
):
    """获取备份列表"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backups = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        if f.endswith(".db") or f.endswith(".zip"):
            filepath = os.path.join(BACKUP_DIR, f)
            stat = os.stat(filepath)
            backups.append({
                "name": f,
                "size": stat.st_size,
                "createTime": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            })
    return {"list": backups, "total": len(backups)}


@router.post("/backups")
async def create_backup(
    current_user: User = Depends(require_admin),
):
    """创建数据库备份"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_name = f"backup_{timestamp}.db"

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "instance", "testmaster.db")
    db_path = os.path.abspath(db_path)
    if os.path.exists(db_path):
        await asyncio.to_thread(shutil.copy2, db_path, os.path.join(BACKUP_DIR, backup_name))
        return {"message": "备份创建成功", "name": backup_name}
    else:
        return {"message": "数据库文件不存在，跳过备份", "name": None}


@router.delete("/backups/old")
async def delete_old_backups(
    current_user: User = Depends(require_admin),
):
    """清理旧备份（保留最近5个）"""
    os.makedirs(BACKUP_DIR, exist_ok=True)
    files = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.endswith(".db") or f.endswith(".zip")]
    )

    if len(files) <= 5:
        return {"message": "没有需要清理的旧备份"}

    deleted = 0
    for f in files[:-5]:
        os.remove(os.path.join(BACKUP_DIR, f))
        deleted += 1

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
):
    backup_path = _safe_backup_path(name)
    if not os.path.exists(backup_path):
        raise HTTPException(status_code=404, detail="备份文件不存在")

    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "instance", "testmaster.db")
    db_path = os.path.abspath(db_path)
    await asyncio.to_thread(shutil.copy2, backup_path, db_path)
    return {"message": "备份恢复成功"}


@router.delete("/backups/{name}")
async def delete_backup(
    name: str,
    current_user: User = Depends(require_admin),
):
    filepath = _safe_backup_path(name)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="备份文件不存在")

    os.remove(filepath)
    return {"message": "备份删除成功"}


# ============== 审计日志 ==============

@router.get("/audit-logs")
async def list_audit_logs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取审计日志（基于用户操作记录）"""
    total = await db.scalar(select(func.count(Submission.id))) or 0
    offset = (page - 1) * size

    query = select(Submission).order_by(desc(Submission.created_at)).offset(offset).limit(size)
    result = await db.execute(query)
    submissions = result.scalars().all()

    logs = []
    for s in submissions:
        user_result = await db.execute(select(User).where(User.id == s.user_id))
        user = user_result.scalar_one_or_none()
        q_result = await db.execute(select(InterviewQuestion).where(InterviewQuestion.id == s.question_id))
        question = q_result.scalar_one_or_none()
        logs.append({
            "id": s.id,
            "user": user.username if user else "unknown",
            "action": "代码提交",
            "detail": f"提交了面试题 \"{question.title if question else '未知'}\" 的代码",
            "status": s.execution_status,
            "createTime": s.created_at.isoformat() if s.created_at else None,
        })

    return {"list": logs, "total": total, "page": page, "size": size}


# ============== 系统指标 ==============

@router.get("/system/metrics")
async def get_system_metrics(
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """获取系统指标"""
    # 数据库统计
    total_users = await db.scalar(select(func.count(User.id))) or 0
    total_submissions = await db.scalar(select(func.count(Submission.id))) or 0
    total_exercises = await db.scalar(select(func.count(Exercise.id))) or 0
    total_paths = await db.scalar(select(func.count(LearningPath.id))) or 0
    total_questions = await db.scalar(select(func.count(InterviewQuestion.id))) or 0
    total_exams = await db.scalar(select(func.count(Exam.id))) or 0

    # 数据库文件大小
    db_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "instance", "testmaster.db")
    db_path = os.path.abspath(db_path)
    db_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    # 备份目录大小
    backup_size = 0
    if os.path.exists(BACKUP_DIR):
        for f in os.listdir(BACKUP_DIR):
            fp = os.path.join(BACKUP_DIR, f)
            if os.path.isfile(fp):
                backup_size += os.path.getsize(fp)

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
        },
        "backups": {
            "size_bytes": backup_size,
            "size_mb": round(backup_size / 1024 / 1024, 2),
            "count": len(os.listdir(BACKUP_DIR)) if os.path.exists(BACKUP_DIR) else 0,
        }
    }


