"""
AutoTest 任务状态持久化服务
从 routers/autotest_execution.py 的任务存储函数下沉
"""
import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Dict, Optional

_logger = logging.getLogger(__name__)

_task_store: Dict[str, dict] = {}
_task_store_lock = asyncio.Lock()

TASK_TTL_SECONDS = 24 * 60 * 60
CLEANUP_INTERVAL_SECONDS = 60 * 60
_cleanup_task: Optional[asyncio.Task] = None


def _get_tasks_dir() -> Path:
    from fastapi_backend.core.autotest_database import INSTANCE_DIR
    tasks_dir = INSTANCE_DIR / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    return tasks_dir


def load_all_tasks() -> None:
    global _task_store
    _task_store = {}
    tasks_dir = _get_tasks_dir()
    for json_file in tasks_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                task_data = json.load(f)
                task_id = task_data.get("task_id")
                if task_id:
                    _task_store[task_id] = task_data
        except Exception:
            pass


def _save_task_to_file(task_id: str, task_info: dict) -> None:
    tasks_dir = _get_tasks_dir()
    task_file = tasks_dir / f"{task_id}.json"
    tmp_file = tasks_dir / f"{task_id}.json.tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(task_info, f, ensure_ascii=False, indent=2)
        tmp_file.replace(task_file)
    except Exception:
        pass


def _delete_task_file(task_id: str) -> None:
    tasks_dir = _get_tasks_dir()
    task_file = tasks_dir / f"{task_id}.json"
    try:
        if task_file.exists():
            task_file.unlink()
    except Exception:
        pass


def get_task(task_id: str) -> Optional[dict]:
    if task_id in _task_store:
        return _task_store[task_id]
    tasks_dir = _get_tasks_dir()
    task_file = tasks_dir / f"{task_id}.json"
    if task_file.exists():
        try:
            with open(task_file, "r", encoding="utf-8") as f:
                task_data = json.load(f)
                _task_store[task_id] = task_data
                return task_data
        except Exception:
            pass
    return None


async def update_task(task_id: str, task_info: dict) -> None:
    if "created_at" not in task_info:
        task_info["created_at"] = time.time()
    async with _task_store_lock:
        _task_store[task_id] = task_info
        _save_task_to_file(task_id, task_info)


async def delete_task(task_id: str) -> None:
    async with _task_store_lock:
        _task_store.pop(task_id, None)
        _delete_task_file(task_id)


def get_all_tasks() -> Dict[str, dict]:
    return dict(_task_store)


async def _cleanup_expired_tasks() -> None:
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        try:
            now = time.time()
            expired_ids = []
            async with _task_store_lock:
                for task_id, task_info in list(_task_store.items()):
                    status = task_info.get("status", "")
                    if status in ("completed", "failed", "cancelled"):
                        created_at = task_info.get("created_at", 0)
                        if created_at and (now - created_at) > TASK_TTL_SECONDS:
                            expired_ids.append(task_id)
                for task_id in expired_ids:
                    _task_store.pop(task_id, None)
                    _delete_task_file(task_id)
            if expired_ids:
                _logger.info("已清理 %d 个过期任务: %s", len(expired_ids), expired_ids)
        except Exception:
            _logger.exception("清理过期任务时出错")


def start_cleanup_task() -> None:
    global _cleanup_task
    if _cleanup_task is None or _cleanup_task.done():
        _cleanup_task = asyncio.create_task(_cleanup_expired_tasks())


def stop_cleanup_task() -> None:
    global _cleanup_task
    if _cleanup_task and not _cleanup_task.done():
        _cleanup_task.cancel()
        _cleanup_task = None


load_all_tasks()
