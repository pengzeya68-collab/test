"""
AutoTest settings - 持久化内存单例，支持运行时读写配置
从 system_config.json 读取邮件配置，支持持久化
"""

import logging
import threading

_logger = logging.getLogger(__name__)

_lock = threading.Lock()
_instance = None

# 邮件配置字段映射
EMAIL_CONFIG_KEYS = [
    "EMAIL_ENABLED",
    "EMAIL_SMTP_HOST",
    "EMAIL_SMTP_PORT",
    "EMAIL_SMTP_USER",
    "EMAIL_SMTP_PASSWORD",
    "EMAIL_FROM_ADDRESS",
    "EMAIL_USE_SSL",
    "EMAIL_ADMIN_TO",
    "EMAIL_TEST_TO",
    "AUTO_TEST_BASE_URL",
]


class _AutoTestSettings:
    _initialized = False

    def __init__(self):
        if _AutoTestSettings._initialized:
            return
        self._load_from_config()
        _AutoTestSettings._initialized = True

    def _load_from_config(self):
        """加载配置：优先从 system_config.json 读取，否则从环境配置读取"""
        from fastapi_backend.core.config import settings as env_settings
        from fastapi_backend.services.system_config import system_config

        # 尝试从持久化配置读取邮件配置
        email_config = system_config.get_section("email")

        if email_config:
            # 从持久化配置读取
            self.EMAIL_ENABLED = email_config.get("EMAIL_ENABLED", env_settings.EMAIL_ENABLED)
            self.EMAIL_SMTP_HOST = email_config.get("EMAIL_SMTP_HOST", env_settings.EMAIL_SMTP_HOST)
            self.EMAIL_SMTP_PORT = email_config.get("EMAIL_SMTP_PORT", env_settings.EMAIL_SMTP_PORT)
            self.EMAIL_SMTP_USER = email_config.get("EMAIL_SMTP_USER", env_settings.EMAIL_SMTP_USER)
            self.EMAIL_SMTP_PASSWORD = email_config.get("EMAIL_SMTP_PASSWORD", env_settings.EMAIL_SMTP_PASSWORD)
            self.EMAIL_FROM_ADDRESS = email_config.get("EMAIL_FROM_ADDRESS", env_settings.EMAIL_FROM_ADDRESS)
            self.EMAIL_USE_SSL = email_config.get("EMAIL_USE_SSL", env_settings.EMAIL_USE_SSL)
            self.EMAIL_ADMIN_TO = email_config.get("EMAIL_ADMIN_TO", env_settings.EMAIL_ADMIN_TO)
            self.EMAIL_TEST_TO = email_config.get("EMAIL_TEST_TO", env_settings.EMAIL_TEST_TO)
            self.AUTO_TEST_BASE_URL = email_config.get("AUTO_TEST_BASE_URL", env_settings.AUTO_TEST_BASE_URL)
            _logger.info("邮件配置已从 system_config.json 加载")
        else:
            # 从环境配置读取默认值
            self.EMAIL_ENABLED = env_settings.EMAIL_ENABLED
            self.EMAIL_SMTP_HOST = env_settings.EMAIL_SMTP_HOST
            self.EMAIL_SMTP_PORT = env_settings.EMAIL_SMTP_PORT
            self.EMAIL_SMTP_USER = env_settings.EMAIL_SMTP_USER
            self.EMAIL_SMTP_PASSWORD = env_settings.EMAIL_SMTP_PASSWORD
            self.EMAIL_FROM_ADDRESS = env_settings.EMAIL_FROM_ADDRESS
            self.EMAIL_USE_SSL = env_settings.EMAIL_USE_SSL
            self.EMAIL_ADMIN_TO = env_settings.EMAIL_ADMIN_TO
            self.EMAIL_TEST_TO = env_settings.EMAIL_TEST_TO
            self.AUTO_TEST_BASE_URL = env_settings.AUTO_TEST_BASE_URL
            _logger.info("邮件配置已从环境变量加载")

        self.CELERY_BROKER_URL = env_settings.CELERY_BROKER_URL
        self.CELERY_RESULT_BACKEND = env_settings.CELERY_RESULT_BACKEND

    def reload(self):
        self._load_from_config()

    def save_to_persistent(self):
        """将当前配置保存到 system_config.json"""
        from fastapi_backend.services.system_config import system_config

        email_config = {
            "EMAIL_ENABLED": self.EMAIL_ENABLED,
            "EMAIL_SMTP_HOST": self.EMAIL_SMTP_HOST,
            "EMAIL_SMTP_PORT": self.EMAIL_SMTP_PORT,
            "EMAIL_SMTP_USER": self.EMAIL_SMTP_USER,
            "EMAIL_SMTP_PASSWORD": self.EMAIL_SMTP_PASSWORD,
            "EMAIL_FROM_ADDRESS": self.EMAIL_FROM_ADDRESS,
            "EMAIL_USE_SSL": self.EMAIL_USE_SSL,
            "EMAIL_ADMIN_TO": self.EMAIL_ADMIN_TO,
            "EMAIL_TEST_TO": self.EMAIL_TEST_TO,
            "AUTO_TEST_BASE_URL": self.AUTO_TEST_BASE_URL,
        }
        system_config.update_section("email", email_config)
        _logger.info("邮件配置已保存到 system_config.json")


def get_settings() -> _AutoTestSettings:
    global _instance
    if _instance is None:
        with _lock:
            if _instance is None:
                _instance = _AutoTestSettings()
    return _instance


class _LazySettingsProxy:
    def __getattr__(self, name):
        return getattr(get_settings(), name)


autotest_settings = _LazySettingsProxy()
