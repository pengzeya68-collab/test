"""
AutoTest 配置模块

替代 auto_test_platform/settings.py，
所有配置项通过环境变量读取，支持运行时修改。
"""
import os

# ========== 邮件通知配置 ==========
# 是否启用邮件通知
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"

# SMTP 服务器配置
EMAIL_SMTP_HOST = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
EMAIL_SMTP_PORT = int(os.getenv("EMAIL_SMTP_PORT", "465"))
EMAIL_SMTP_USER = os.getenv("EMAIL_SMTP_USER", "")
EMAIL_SMTP_PASSWORD = os.getenv("EMAIL_SMTP_PASSWORD", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", EMAIL_SMTP_USER)

# 管理员收件邮箱
EMAIL_ADMIN_TO = os.getenv("EMAIL_ADMIN_TO", "")

# 是否启用 SSL
EMAIL_ENABLE_SSL = os.getenv("EMAIL_ENABLE_SSL", "True").lower() == "true"

# ========== 服务配置 ==========
# 基础 URL，用于邮件/飞书中生成完整的报告链接
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:5001")


def get_settings():
    """
    返回当前模块作为设置对象（支持运行时 setattr 修改）。
    用法: settings = get_settings(); settings.EMAIL_ENABLED = True
    """
    import sys
    return sys.modules[__name__]
