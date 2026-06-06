"""
AutoTest 任务状态持久化服务
从 routers/autotest_execution.py 的任务存储函数下沉
"""
import asyncio
import copy
import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, Optional

_logger = logging.getLogger(__name__)

_task_store: Dict[str, dict] = {}
_thread_lock = threading.Lock()  # 用于保护 _task_store 的线程安全

_async_lock = None
_async_lock_create_lock = threading.Lock()  # 保护 _async_lock 创建的线程锁

def _get_async_lock():
    """延迟创建 asyncio.Lock，避免模块导入时绑定到错误的事件循环，线程安全"""
    global _async_lock
    if _async_lock is None:
        with _async_lock_create_lock:
            if _async_lock is None:
                _async_lock = asyncio.Lock()
    return _async_lock

TASK_TTL_SECONDS = 24 * 60 * 60
CLEANUP_INTERVAL_SECONDS = 60 * 60
_cleanup_task: Optional[asyncio.Task] = None


def _get_tasks_dir() -> Path:
    from fastapi_backend.core.config import PROJECT_ROOT
    tasks_dir = PROJECT_ROOT / "instance" / "tasks"
    tasks_dir.mkdir(parents=True, exist_ok=True)
    return tasks_dir


async def load_all_tasks() -> None:
    async with _get_async_lock():
        with _thread_lock:
            _task_store.clear()
        tasks_dir = _get_tasks_dir()
        for json_file in tasks_dir.glob("*.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    task_data = json.load(f)
                    task_id = task_data.get("task_id")
                    if task_id:
                        with _thread_lock:
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
    except Exception as e:
        _logger.warning(f"保存任务文件失败 {task_id}: {e}")


def _delete_task_file(task_id: str) -> None:
    tasks_dir = _get_tasks_dir()
    task_file = tasks_dir / f"{task_id}.json"
    try:
        if task_file.exists():
            task_file.unlink()
    except Exception:
        pass


async def get_task(task_id: str) -> Optional[dict]:
    async with _get_async_lock():
        with _thread_lock:
            if task_id in _task_store:
                return copy.deepcopy(_task_store[task_id])
    tasks_dir = _get_tasks_dir()
    task_file = tasks_dir / f"{task_id}.json"
    if task_file.exists():
        try:
            with open(task_file, "r", encoding="utf-8") as f:
                task_data = json.load(f)
                with _thread_lock:
                    _task_store[task_id] = task_data
                return copy.deepcopy(task_data)
        except Exception:
            pass
    return None


def get_task_sync(task_id: str) -> Optional[dict]:
    """同步版本的 get_task，供 Celery 等非 async 上下文使用"""
    with _thread_lock:
        if task_id in _task_store:
            return copy.deepcopy(_task_store[task_id])
    tasks_dir = _get_tasks_dir()
    task_file = tasks_dir / f"{task_id}.json"
    if task_file.exists():
        try:
            with open(task_file, "r", encoding="utf-8") as f:
                task_data = json.load(f)
                with _thread_lock:
                    _task_store[task_id] = task_data
                return copy.deepcopy(task_data)
        except Exception:
            pass
    return None


async def update_task(task_id: str, task_info: dict) -> None:
    if "created_at" not in task_info:
        task_info["created_at"] = time.time()
    async with _get_async_lock():
        with _thread_lock:
            # 合并而非替换：保留其他协程/线程已写入的字段（如 cancelled）
            existing = _task_store.get(task_id, {})
            merged = {**existing, **task_info}
            _task_store[task_id] = merged
        _save_task_to_file(task_id, merged)


def update_task_sync(task_id: str, task_info: dict) -> None:
    """同步版本的 update_task，供 Celery 等非 async 上下文使用"""
    if "created_at" not in task_info:
        task_info["created_at"] = time.time()
    with _thread_lock:
        # 合并而非替换：保留其他协程/线程已写入的字段（如 cancelled）
        existing = _task_store.get(task_id, {})
        merged = {**existing, **task_info}
        _task_store[task_id] = merged
    _save_task_to_file(task_id, merged)


async def delete_task(task_id: str) -> None:
    async with _get_async_lock():
        with _thread_lock:
            _task_store.pop(task_id, None)
        _delete_task_file(task_id)


async def cancel_task(task_id: str) -> None:
    """标记任务为取消状态，保留已生成的用例"""
    async with _get_async_lock():
        with _thread_lock:
            if task_id in _task_store:
                _task_store[task_id]["status"] = "cancelled"
                _task_store[task_id]["cancelled"] = True
                _save_task_to_file(task_id, _task_store[task_id])
                return
        # 如果内存中没有，尝试从文件加载
        tasks_dir = _get_tasks_dir()
        task_file = tasks_dir / f"{task_id}.json"
        if task_file.exists():
            try:
                with open(task_file, "r", encoding="utf-8") as f:
                    task_data = json.load(f)
                task_data["status"] = "cancelled"
                task_data["cancelled"] = True
                with _thread_lock:
                    _task_store[task_id] = task_data
                _save_task_to_file(task_id, task_data)
            except Exception:
                pass


def is_task_cancelled(task_id: str) -> bool:
    """检查任务是否被取消（线程安全，供 Celery worker 等同步上下文使用）"""
    with _thread_lock:
        if task_id in _task_store:
            return _task_store[task_id].get("cancelled", False)
    return False


async def get_all_tasks() -> Dict[str, dict]:
    async with _get_async_lock():
        with _thread_lock:
            return copy.deepcopy(_task_store)


async def _cleanup_expired_tasks() -> None:
    while True:
        await asyncio.sleep(CLEANUP_INTERVAL_SECONDS)
        try:
            now = time.time()
            expired_ids = []
            async with _get_async_lock():
                with _thread_lock:
                    for task_id, task_info in list(_task_store.items()):
                        status = task_info.get("status", "")
                        if status in ("completed", "failed", "cancelled"):
                            created_at = task_info.get("created_at", 0)
                            if created_at and (now - created_at) > TASK_TTL_SECONDS:
                                expired_ids.append(task_id)
                    for task_id in expired_ids:
                        _task_store.pop(task_id, None)
            # 文件删除在锁外执行，避免阻塞
            for task_id in expired_ids:
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


def _load_all_tasks_sync() -> None:
    """同步加载所有任务文件到内存（模块初始化时调用，不持异步锁）"""
    tasks_dir = _get_tasks_dir()
    for json_file in tasks_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                task_data = json.load(f)
                task_id = task_data.get("task_id")
                if task_id:
                    with _thread_lock:
                        _task_store[task_id] = task_data
        except Exception:
            pass


_load_all_tasks_sync()
