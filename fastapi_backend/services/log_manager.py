"""
日志管理服务

提供日志查询、日志级别动态调整、日志文件管理等功能
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

_logger = logging.getLogger(__name__)

LOG_DIR = Path(__file__).parent.parent.parent / "logs"
LOG_FILE = LOG_DIR / "app.log"


class LogManager:
    """日志管理器"""

    @staticmethod
    def get_log_files() -> List[Dict[str, Any]]:
        """获取日志文件列表"""
        if not LOG_DIR.exists():
            return []

        files = []
        for log_file in LOG_DIR.glob("*.log*"):
            stat = log_file.stat()
            files.append(
                {
                    "name": log_file.name,
                    "path": str(log_file),
                    "size_bytes": stat.st_size,
                    "size_mb": round(stat.st_size / (1024**2), 2),
                    "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                }
            )

        # 按修改时间排序
        files.sort(key=lambda x: x["modified"], reverse=True)
        return files

    @staticmethod
    def read_log_lines(
        filename: str = "app.log",
        lines: int = 100,
        level: Optional[str] = None,
        keyword: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """读取日志文件内容"""
        log_file = LOG_DIR / filename
        if not log_file.exists():
            return []

        result = []
        try:
            with open(log_file, "r", encoding="utf-8") as f:
                all_lines = f.readlines()

            # 只取最后 N 行
            target_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines

            for line in target_lines:
                line = line.strip()
                if not line:
                    continue

                # 过滤日志级别
                if level:
                    if level.upper() not in line.upper():
                        continue

                # 过滤关键词
                if keyword and keyword.lower() not in line.lower():
                    continue

                # 解析日志行
                parsed = LogManager._parse_log_line(line)
                result.append(parsed)
        except Exception as e:
            _logger.error(f"读取日志文件失败: {e}")

        return result

    @staticmethod
    def _parse_log_line(line: str) -> Dict[str, Any]:
        """解析单行日志"""
        # 简单解析，实际可能需要更复杂的逻辑
        parts = line.split(" - ", 3)
        if len(parts) >= 4:
            return {
                "timestamp": parts[0],
                "level": parts[1],
                "logger": parts[2],
                "message": parts[3],
                "raw": line,
            }
        return {
            "timestamp": None,
            "level": None,
            "logger": None,
            "message": line,
            "raw": line,
        }

    @staticmethod
    def get_log_stats() -> Dict[str, Any]:
        """获取日志统计信息"""
        if not LOG_FILE.exists():
            return {"total_lines": 0, "level_counts": {}}

        level_counts = {"DEBUG": 0, "INFO": 0, "WARNING": 0, "ERROR": 0, "CRITICAL": 0}
        total_lines = 0

        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    total_lines += 1
                    for level in level_counts:
                        if level in line:
                            level_counts[level] += 1
                            break
        except Exception as e:
            _logger.error(f"统计日志失败: {e}")

        return {
            "total_lines": total_lines,
            "level_counts": level_counts,
            "file_size_mb": round(LOG_FILE.stat().st_size / (1024**2), 2) if LOG_FILE.exists() else 0,
        }

    @staticmethod
    def clear_old_logs(days: int = 30) -> int:
        """清理旧日志文件"""
        if not LOG_DIR.exists():
            return 0

        import time

        cutoff = time.time() - (days * 86400)
        deleted = 0

        for log_file in LOG_DIR.glob("*.log*"):
            if log_file.stat().st_mtime < cutoff:
                try:
                    log_file.unlink()
                    deleted += 1
                    _logger.info(f"已删除旧日志文件: {log_file.name}")
                except Exception as e:
                    _logger.error(f"删除日志文件失败 {log_file.name}: {e}")

        return deleted

    @staticmethod
    def set_log_level(level: str) -> bool:
        """动态设置日志级别"""
        numeric_level = getattr(logging, level.upper(), None)
        if numeric_level is None:
            return False

        # 设置根日志级别
        logging.getLogger().setLevel(numeric_level)

        # 设置应用日志级别
        logging.getLogger("fastapi_backend").setLevel(numeric_level)

        _logger.info(f"日志级别已设置为: {level.upper()}")
        return True

    @staticmethod
    def get_current_log_level() -> str:
        """获取当前日志级别"""
        root_logger = logging.getLogger()
        return logging.getLevelName(root_logger.level)


# 全局实例
log_manager = LogManager()
