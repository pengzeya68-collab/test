"""Backup management – PostgreSQL pg_dump based backups."""

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException

from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import User
from fastapi_backend.core.config import settings

router = APIRouter(prefix="/api/v1/admin/backups", tags=["backup-management"])

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
BACKUP_DIR = PROJECT_ROOT / "backups"
MAX_BACKUPS = 10

BACKUP_DIR.mkdir(parents=True, exist_ok=True)


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


def _list_backups() -> list[dict]:
    backups = []
    if not BACKUP_DIR.exists():
        return []
    for f in BACKUP_DIR.iterdir():
        if f.is_file() and f.name.startswith("testmaster_backup_") and f.suffix == ".sql":
            stat = f.stat()
            backups.append(
                {
                    "name": f.name,
                    "size": round(stat.st_size / (1024 * 1024), 2),
                    "time": int(stat.st_mtime * 1000),
                }
            )
    backups.sort(key=lambda x: x["time"], reverse=True)
    return backups


async def _create_backup() -> tuple[str | None, str | None]:
    params = _pg_connection_params()
    if not params:
        return None, "数据库不是 PostgreSQL，无法使用 pg_dump"

    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    name = f"testmaster_backup_{ts}.sql"
    dst = str(BACKUP_DIR / name)

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
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        if proc.returncode != 0:
            return None, f"pg_dump 失败: {stderr.decode(errors='replace')[:200]}"

        with open(dst, "w", encoding="utf-8") as f:
            f.write(stdout.decode(errors="replace"))

        return name, None
    except FileNotFoundError:
        return None, "pg_dump 命令未找到，请确保 PostgreSQL 客户端工具已安装"
    except subprocess.TimeoutExpired:
        return None, "pg_dump 超时"
    except Exception as e:
        if os.path.exists(dst):
            try:
                os.remove(dst)
            except OSError:
                pass
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
    name, error = await _create_backup()
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
    backup_path = (BACKUP_DIR / backup_name).resolve()
    if not str(backup_path).startswith(str(BACKUP_DIR.resolve())):
        raise HTTPException(status_code=400, detail="无效的备份文件名")
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="备份文件不存在")

    params = _pg_connection_params()
    if not params:
        raise HTTPException(status_code=500, detail="数据库不是 PostgreSQL，无法恢复")

    await _create_backup()

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
        str(backup_path),
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=env,
            timeout=300,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=f"恢复失败: {result.stderr[:200]}")
        return {"message": "备份恢复成功"}
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="psql 命令未找到，请确保 PostgreSQL 客户端工具已安装",
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="恢复超时")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复失败: {e}")


@router.delete("/{backup_name:path}")
async def delete_backup(
    backup_name: str,
    current_user: User = Depends(require_admin),
):
    """删除备份"""
    backup_path = (BACKUP_DIR / backup_name).resolve()
    if not str(backup_path).startswith(str(BACKUP_DIR.resolve())):
        raise HTTPException(status_code=400, detail="无效的备份文件名")
    ok, error = _delete_backup(backup_name)
    if error:
        raise HTTPException(status_code=500, detail=f"删除失败: {error}")
    return {"message": "备份删除成功"}
