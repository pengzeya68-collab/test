"""
系统监控服务

提供系统资源监控、健康检查、请求统计等功能
"""

import time
import psutil
import logging
from datetime import datetime, timezone
from typing import Dict, Any, List
from collections import defaultdict

_logger = logging.getLogger(__name__)


class RequestStats:
    """请求统计"""

    _instance = None
    _stats: Dict[str, Any] = {}
    _window_stats: List[Dict[str, Any]] = []
    _max_window_size = 1000  # 保留最近 1000 条请求记录

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            self._total_requests = 0
            self._error_requests = 0
            self._start_time = time.time()
            self._path_stats = defaultdict(lambda: {"count": 0, "errors": 0, "avg_time": 0})
            self.initialized = True

    def record_request(self, path: str, method: str, status_code: int, duration_ms: float):
        """记录请求"""
        self._total_requests += 1
        if status_code >= 400:
            self._error_requests += 1

        path_key = f"{method} {path}"
        stats = self._path_stats[path_key]
        stats["count"] += 1
        if status_code >= 400:
            stats["errors"] += 1
        # 移动平均计算响应时间
        stats["avg_time"] = (stats["avg_time"] * (stats["count"] - 1) + duration_ms) / stats["count"]

        # 窗口统计
        self._window_stats.append(
            {
                "path": path,
                "method": method,
                "status_code": status_code,
                "duration_ms": round(duration_ms, 2),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        if len(self._window_stats) > self._max_window_size:
            self._window_stats = self._window_stats[-self._max_window_size :]

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = time.time() - self._start_time
        requests_per_second = self._total_requests / uptime if uptime > 0 else 0

        return {
            "total_requests": self._total_requests,
            "error_requests": self._error_requests,
            "error_rate": round(self._error_requests / self._total_requests * 100, 2)
            if self._total_requests > 0
            else 0,
            "requests_per_second": round(requests_per_second, 2),
            "uptime_seconds": round(uptime, 2),
            "path_stats": dict(self._path_stats),
            "recent_requests": self._window_stats[-50:],  # 最近 50 条
        }


class SystemMonitor:
    """系统监控"""

    def __init__(self):
        self.request_stats = RequestStats()

    def get_system_info(self) -> Dict[str, Any]:
        """获取系统信息"""
        import platform

        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk_path = "C:\\" if platform.system() == "Windows" else "/"
        disk = psutil.disk_usage(disk_path)

        return {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count(),
                "frequency": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else None,
            },
            "memory": {
                "total_gb": round(memory.total / (1024**3), 2),
                "available_gb": round(memory.available / (1024**3), 2),
                "used_gb": round(memory.used / (1024**3), 2),
                "percent": memory.percent,
            },
            "disk": {
                "total_gb": round(disk.total / (1024**3), 2),
                "used_gb": round(disk.used / (1024**3), 2),
                "free_gb": round(disk.free / (1024**3), 2),
                "percent": disk.percent,
            },
            "boot_time": datetime.fromtimestamp(psutil.boot_time(), tz=timezone.utc).isoformat(),
        }

    def get_process_info(self) -> Dict[str, Any]:
        """获取进程信息"""
        process = psutil.Process()
        with process.oneshot():
            return {
                "pid": process.pid,
                "status": process.status(),
                "create_time": datetime.fromtimestamp(process.create_time(), tz=timezone.utc).isoformat(),
                "cpu_percent": process.cpu_percent(),
                "memory_info": {
                    "rss_mb": round(process.memory_info().rss / (1024**2), 2),
                    "vms_mb": round(process.memory_info().vms / (1024**2), 2),
                },
                "threads": process.num_threads(),
                "open_files": len(process.open_files()),
                "connections": len(process.connections()),
            }

    def get_health_status(self, db_check_func=None, redis_check_func=None) -> Dict[str, Any]:
        """获取健康状态"""
        health = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "checks": {},
        }

        # 数据库检查
        if db_check_func:
            try:
                db_check_func()
                health["checks"]["database"] = {"status": "ok"}
            except Exception as e:
                health["checks"]["database"] = {"status": "error", "message": str(e)}
                health["status"] = "degraded"

        # Redis 检查
        if redis_check_func:
            try:
                redis_check_func()
                health["checks"]["redis"] = {"status": "ok"}
            except Exception as e:
                health["checks"]["redis"] = {"status": "error", "message": str(e)}
                health["status"] = "degraded"

        # 磁盘检查
        disk_path = "C:\\" if platform.system() == "Windows" else "/"
        disk = psutil.disk_usage(disk_path)
        if disk.percent > 90:
            health["checks"]["disk"] = {"status": "warning", "percent": disk.percent}
            health["status"] = "degraded"
        else:
            health["checks"]["disk"] = {"status": "ok", "percent": disk.percent}

        # 内存检查
        memory = psutil.virtual_memory()
        if memory.percent > 90:
            health["checks"]["memory"] = {
                "status": "warning",
                "percent": memory.percent,
            }
            health["status"] = "degraded"
        else:
            health["checks"]["memory"] = {"status": "ok", "percent": memory.percent}

        return health

    def get_request_stats(self) -> Dict[str, Any]:
        """获取请求统计"""
        return self.request_stats.get_stats()


# 全局单例
system_monitor = SystemMonitor()
