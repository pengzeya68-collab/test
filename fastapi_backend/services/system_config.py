"""
系统配置管理服务

提供动态配置管理功能，包括缓存配置、限流配置、日志级别等
"""
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

_logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_FILE = Path(__file__).parent.parent.parent / "instance" / "system_config.json"

# 默认配置
DEFAULT_CONFIG = {
    "cache": {
        "enabled": True,
        "ttl_seconds": 300,  # 5 分钟
        "max_size": 1000,
    },
    "rate_limit": {
        "enabled": True,
        "requests_per_minute": 60,
        "burst_size": 10,
    },
    "ai_rate_limit": {
        "enabled": True,
        "requests_per_window": 10,
        "window_seconds": 60,
    },
    "logging": {
        "level": "INFO",
        "format": "json",  # json 或 text
        "output": "file",  # file 或 console
    },
    "features": {
        "email_notifications": False,
        "webhook_notifications": False,
        "ai_tutor": True,
        "code_sandbox": True,
        "auto_test": True,
    },
}


class SystemConfigManager:
    """系统配置管理器"""
    
    _instance = None
    _config: Dict[str, Any] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self._load_config()
            self.initialized = True
    
    def _load_config(self):
        """加载配置"""
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
                _logger.info(f"系统配置已加载: {CONFIG_FILE}")
            except Exception as e:
                _logger.error(f"加载系统配置失败: {e}")
                self._config = DEFAULT_CONFIG.copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
            self._save_config()
    
    def _save_config(self):
        """保存配置"""
        try:
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            _logger.info(f"系统配置已保存: {CONFIG_FILE}")
        except Exception as e:
            _logger.error(f"保存系统配置失败: {e}")
    
    def get_all_config(self) -> Dict[str, Any]:
        """获取所有配置"""
        return self._config.copy()
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """获取配置节"""
        return self._config.get(section, {}).copy()
    
    def get_value(self, section: str, key: str, default=None) -> Any:
        """获取配置值"""
        return self._config.get(section, {}).get(key, default)
    
    def update_section(self, section: str, values: Dict[str, Any]) -> Dict[str, Any]:
        """更新配置节"""
        if section not in self._config:
            self._config[section] = {}
        
        self._config[section].update(values)
        self._save_config()
        
        # 如果是日志配置，动态调整日志级别
        if section == "logging":
            self._apply_logging_config()
        
        return self._config[section].copy()
    
    def update_value(self, section: str, key: str, value: Any) -> Any:
        """更新单个配置值"""
        if section not in self._config:
            self._config[section] = {}
        
        self._config[section][key] = value
        self._save_config()
        
        # 如果是日志配置，动态调整日志级别
        if section == "logging" and key == "level":
            self._apply_logging_config()
        
        return value
    
    def reset_to_default(self, section: Optional[str] = None):
        """重置配置为默认值"""
        if section:
            if section in DEFAULT_CONFIG:
                self._config[section] = DEFAULT_CONFIG[section].copy()
        else:
            self._config = DEFAULT_CONFIG.copy()
        
        self._save_config()
        _logger.info(f"配置已重置为默认值: {section or '全部'}")
    
    def _apply_logging_config(self):
        """应用日志配置"""
        logging_config = self._config.get("logging", {})
        level = logging_config.get("level", "INFO").upper()
        
        # 设置根日志级别
        numeric_level = getattr(logging, level, logging.INFO)
        logging.getLogger().setLevel(numeric_level)
        
        # 设置应用日志级别
        logging.getLogger("fastapi_backend").setLevel(numeric_level)
        
        _logger.info(f"日志级别已调整为: {level}")
    
    def get_feature_status(self, feature: str) -> bool:
        """获取功能开关状态"""
        return self._config.get("features", {}).get(feature, False)
    
    def toggle_feature(self, feature: str, enabled: bool):
        """切换功能开关"""
        self.update_value("features", feature, enabled)
        _logger.info(f"功能 {feature} 已{'启用' if enabled else '禁用'}")


# 全局单例
system_config = SystemConfigManager()
