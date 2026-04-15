"""Backup management – migrated from Flask backend/api/backup.py."""
from __future__ import annotations

import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.deps.auth import require_admin, get_current_user
from fastapi_backend.models.models import User

router = APIRouter(prefix="/api/v1/admin/backups", tags=["backup-management"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups"
MAX_BACKUPS = 10

BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def _db_path() -> str:
    return str(PROJECT_ROOT / "instance" / "testmaster.db")


def _list_backups() -> list[dict]:
    backups = []
    if not BACKUP_DIR.exists():
        return []
    for f in BACKUP_DIR.iterdir():
        if f.is_file() and (f.name.startswith("testmaster_backup_") or f.name.startswith("testmaster_emergency_")) and f.suffix == ".db":
            stat = f.stat()
            backups.append({
                "name": f.name,
                "size": round(stat.st_size / (1024 * 1024), 2),
                "time": int(stat.st_mtime * 1000),
            })
    backups.sort(key=lambda x: x["time"], reverse=True)
    return backups


def _create_backup() -> tuple[str | None, str | None]:
    src = _db_path()
    if not os.path.exists(src):
        return None, "数据库文件不存在"
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = f"testmaster_backup_{ts}.db"
    dst = str(BACKUP_DIR / name)
    try:
        source = sqlite3.connect(src)
        backup = sqlite3.connect(dst)
        with backup:
            source.backup(backup)
        source.close()
        backup.close()
        return name, None
    except Exception as e:
        return None, str(e)


def _delete_backup(name: str) -> tuple[bool, str | None]:
    path = BACKUP_DIR / name
    if not path.exists():
        return False, "备份文件不存在"
    try:
        path.unlink()
        return True, None
    except Exception as e:
        return False, str(e)


def _clean_old() -> int:
    backups = _list_backups()
    if len(backups) <= MAX_BACKUPS:
        return 0
    deleted = 0
    for b in backups[MAX_BACKUPS:]:
        ok, _ = _delete_backup(b["name"])
        if ok:
            deleted += 1
    return deleted


@router.get("")
async def get_backups(
    current_user: User = Depends(require_admin),
):
    """获取备份列表"""
    return {"backups": _list_backups(), "max_backups": MAX_BACKUPS}


@router.post("")
async def create_new_backup(
    current_user: User = Depends(require_admin),
):
    """创建新备份"""
    name, error = _create_backup()
    if error:
        raise HTTPException(status_code=500, detail=f"创建备份失败: {error}")
    _clean_old()
    return {"message": "备份创建成功", "backup_name": name}


@router.delete("/old")
async def clean_old(
    current_user: User = Depends(require_admin),
):
    """清理旧备份"""
    deleted = _clean_old()
    return {"message": f"清理完成，删除了 {deleted} 个旧备份", "deleted": deleted}


@router.post("/{backup_name:path}/restore")
async def restore_backup(
    backup_name: str,
    current_user: User = Depends(require_admin),
):
    """恢复备份"""
    backup_path = BACKUP_DIR / backup_name
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="备份文件不存在")

    src_db = _db_path()
    # Create emergency backup before restore
    if os.path.exists(src_db):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(src_db, str(BACKUP_DIR / f"testmaster_emergency_{ts}.db"))

    try:
        shutil.copy2(str(backup_path), src_db)
        return {"message": "备份恢复成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复失败: {e}")


@router.delete("/{backup_name:path}")
async def delete_backup(
    backup_name: str,
    current_user: User = Depends(require_admin),
):
    """删除备份"""
    ok, error = _delete_backup(backup_name)
    if error:
        raise HTTPException(status_code=500, detail=f"删除失败: {error}")
    return {"message": "备份删除成功"}
