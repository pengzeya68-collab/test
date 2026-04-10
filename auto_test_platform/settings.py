"""
配置文件
使用环境变量或直接修改这里
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
# 基础 URL，用于邮件中生成完整的报告链接
BASE_URL = os.getenv("BASE_URL", "http://localhost:5002")
