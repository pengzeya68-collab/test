"""
后台管理 - 系统管理路由

提供系统配置、监控、日志管理等 API 接口
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Dict, Any, Optional

from fastapi_backend.deps.auth import require_admin
from fastapi_backend.models.models import User
from fastapi_backend.services.system_config import system_config
from fastapi_backend.services.system_monitor import system_monitor
from fastapi_backend.services.log_manager import log_manager

router = APIRouter(
    prefix="/api/v1/admin/system",
    tags=["Admin-系统管理"],
    dependencies=[Depends(require_admin)],
)


# ==================== 系统配置接口 ====================


class ConfigUpdateRequest(BaseModel):
    section: str
    values: Dict[str, Any]


class ConfigValueRequest(BaseModel):
    section: str
    key: str
    value: Any


class FeatureToggleRequest(BaseModel):
    feature: str
    enabled: bool


@router.get("/config")
async def get_system_config(current_user: User = Depends(require_admin)):
    """获取系统配置"""
    return {
        "config": system_config.get_all_config(),
        "config_file": str(system_config.__class__.__module__.replace(".", "/") + "/system_config.json"),
    }


@router.get("/config/{section}")
async def get_config_section(section: str, current_user: User = Depends(require_admin)):
    """获取配置节"""
    section_data = system_config.get_section(section)
    if not section_data:
        raise HTTPException(status_code=404, detail=f"配置节 '{section}' 不存在")
    return {"section": section, "config": section_data}


@router.put("/config")
async def update_config_section(req: ConfigUpdateRequest, current_user: User = Depends(require_admin)):
    """更新配置节"""
    updated = system_config.update_section(req.section, req.values)
    return {"message": "配置已更新", "section": req.section, "config": updated}


@router.put("/config/value")
async def update_config_value(req: ConfigValueRequest, current_user: User = Depends(require_admin)):
    """更新单个配置值"""
    value = system_config.update_value(req.section, req.key, req.value)
    return {
        "message": "配置值已更新",
        "section": req.section,
        "key": req.key,
        "value": value,
    }


@router.post("/config/reset")
async def reset_config(
    section: Optional[str] = Query(None, description="要重置的配置节，不填则重置全部"),
    current_user: User = Depends(require_admin),
):
    """重置配置为默认值"""
    system_config.reset_to_default(section)
    return {"message": "配置已重置", "section": section or "全部"}


@router.get("/features")
async def get_features(current_user: User = Depends(require_admin)):
    """获取功能开关列表"""
    return system_config.get_section("features")


@router.put("/features/toggle")
async def toggle_feature(req: FeatureToggleRequest, current_user: User = Depends(require_admin)):
    """切换功能开关"""
    system_config.toggle_feature(req.feature, req.enabled)
    return {"message": f"功能 '{req.feature}' 已{'启用' if req.enabled else '禁用'}"}


# ==================== 系统监控接口 ====================


@router.get("/health")
async def get_health_status(current_user: User = Depends(require_admin)):
    """获取系统健康状态"""

    def db_check():
        # 简化版数据库检查，实际应该查询数据库
        pass

    def redis_check():
        # 简化版 Redis 检查，实际应该 ping Redis
        pass

    return system_monitor.get_health_status(db_check, redis_check)


@router.get("/system-info")
async def get_system_info(current_user: User = Depends(require_admin)):
    """获取系统信息"""
    return system_monitor.get_system_info()


@router.get("/process-info")
async def get_process_info(current_user: User = Depends(require_admin)):
    """获取进程信息"""
    return system_monitor.get_process_info()


@router.get("/request-stats")
async def get_request_stats(current_user: User = Depends(require_admin)):
    """获取请求统计"""
    return system_monitor.get_request_stats()


# ==================== 日志管理接口 ====================


class LogLevelRequest(BaseModel):
    level: str


class LogQueryRequest(BaseModel):
    filename: str = "app.log"
    lines: int = 100
    level: Optional[str] = None
    keyword: Optional[str] = None


class ClearLogsRequest(BaseModel):
    days: int = 30


@router.get("/logs/files")
async def get_log_files(current_user: User = Depends(require_admin)):
    """获取日志文件列表"""
    return {"files": log_manager.get_log_files()}


@router.get("/logs/stats")
async def get_log_stats(current_user: User = Depends(require_admin)):
    """获取日志统计信息"""
    return log_manager.get_log_stats()


@router.get("/logs/content")
async def get_log_content(
    filename: str = Query("app.log", description="日志文件名"),
    lines: int = Query(100, ge=1, le=1000, description="读取行数"),
    level: Optional[str] = Query(None, description="日志级别过滤"),
    keyword: Optional[str] = Query(None, description="关键词过滤"),
    current_user: User = Depends(require_admin),
):
    """获取日志内容"""
    logs = log_manager.read_log_lines(filename, lines, level, keyword)
    return {
        "filename": filename,
        "count": len(logs),
        "logs": logs,
    }


@router.put("/logs/level")
async def set_log_level(req: LogLevelRequest, current_user: User = Depends(require_admin)):
    """设置日志级别"""
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if req.level.upper() not in valid_levels:
        raise HTTPException(status_code=400, detail=f"无效的日志级别，可选值: {valid_levels}")

    success = log_manager.set_log_level(req.level)
    if not success:
        raise HTTPException(status_code=500, detail="设置日志级别失败")

    return {"message": f"日志级别已设置为 {req.level.upper()}"}


@router.get("/logs/level")
async def get_log_level(current_user: User = Depends(require_admin)):
    """获取当前日志级别"""
    return {"level": log_manager.get_current_log_level()}


@router.post("/logs/clear")
async def clear_old_logs(req: ClearLogsRequest, current_user: User = Depends(require_admin)):
    """清理旧日志文件"""
    if req.days < 1:
        raise HTTPException(status_code=400, detail="天数必须大于 0")

    deleted = log_manager.clear_old_logs(req.days)
    return {"message": f"已清理 {deleted} 个旧日志文件", "deleted": deleted}
