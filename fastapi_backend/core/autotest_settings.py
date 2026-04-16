"""
AutoTest settings - now delegates to the unified config.py
"""
import logging

_logger = logging.getLogger(__name__)


class _AutoTestSettings:
    def __init__(self):
        self._load_from_config()

    def _load_from_config(self):
        from fastapi_backend.core.config import settings
        self.EMAIL_SMTP_HOST = settings.EMAIL_SMTP_HOST
        self.EMAIL_SMTP_PORT = settings.EMAIL_SMTP_PORT
        self.EMAIL_SMTP_USER = settings.EMAIL_SMTP_USER
        self.EMAIL_SMTP_PASSWORD = settings.EMAIL_SMTP_PASSWORD
        self.EMAIL_FROM_ADDRESS = settings.EMAIL_FROM_ADDRESS
        self.EMAIL_USE_SSL = settings.EMAIL_USE_SSL
        self.EMAIL_ENABLED = settings.EMAIL_ENABLED
        self.AUTO_TEST_BASE_URL = settings.AUTO_TEST_BASE_URL
        self.CELERY_BROKER_URL = settings.CELERY_BROKER_URL
        self.CELERY_RESULT_BACKEND = settings.CELERY_RESULT_BACKEND

    def reload(self):
        self._load_from_config()


def get_settings() -> _AutoTestSettings:
    return _AutoTestSettings()


autotest_settings = get_settings()
