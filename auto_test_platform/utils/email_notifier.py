"""
邮件通知工具
企业级测试结果邮件通知，使用 Python 原生 smtplib 和 email 模块
支持 HTML 格式邮件，包含测试结果和 Allure 报告链接
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

import auto_test_platform.settings as settings


class EmailNotifier:
    """
    邮件通知器
    发送测试结果通知邮件
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: Optional[str] = None,
        enable_ssl: Optional[bool] = None,
    ):
        """
        初始化邮件通知器

        Args:
            smtp_host: SMTP 服务器地址，默认从配置读取
            smtp_port: SMTP 端口，默认从配置读取
            smtp_user: SMTP 用户名，默认从配置读取
            smtp_password: SMTP 密码，默认从配置读取
            from_email: 发件人邮箱，默认从配置读取
            enable_ssl: 是否启用 SSL，默认从配置读取
        """
        self.smtp_host = smtp_host or getattr(settings, "EMAIL_SMTP_HOST", "")
        self.smtp_port = smtp_port or getattr(settings, "EMAIL_SMTP_PORT", 465)
        self.smtp_user = smtp_user or getattr(settings, "EMAIL_SMTP_USER", "")
        self.smtp_password = smtp_password or getattr(settings, "EMAIL_SMTP_PASSWORD", "")
        self.from_email = from_email or getattr(settings, "EMAIL_FROM", self.smtp_user)
        self.enable_ssl = enable_ssl if enable_ssl is not None else getattr(settings, "EMAIL_ENABLE_SSL", True)
        self.enabled = getattr(settings, "EMAIL_ENABLED", True)

    def send_scenario_result(
        self,
        to_email: str,
        scenario_name: str,
        scenario_id: int,
        status: str,
        total_steps: int,
        success_steps: int,
        failed_steps: int,
        skipped_steps: int,
        total_time: int,
        report_url: str,
        base_url: str = "",
    ) -> bool:
        """
        发送场景执行结果通知邮件

        Args:
            to_email: 收件人邮箱
            scenario_name: 场景名称
            scenario_id: 场景 ID
            status: 执行状态 success/failed/error
            total_steps: 总步骤数
            success_steps: 成功步骤数
            failed_steps: 失败步骤数
            skipped_steps: 跳过步骤数
            total_time: 总耗时（毫秒）
            report_url: Allure 报告相对路径
            base_url: 前端/后端基础 URL，用于拼接完整报告链接

        Returns:
            bool: 发送成功返回 True，失败返回 False
        """
        if not self.enabled:
            return False

        if not self.smtp_host or not self.smtp_user or not self.smtp_password:
            print("[EmailNotifier] 邮件配置不完整，跳过发送")
            return False

        # 拼接完整报告链接
        full_report_url = report_url
        if base_url and not report_url.startswith("http"):
            full_report_url = base_url.rstrip("/") + "/" + report_url.lstrip("/")

        # 构建 HTML 内容
        html_content = self._build_html_content(
            scenario_name=scenario_name,
            scenario_id=scenario_id,
            status=status,
            total_steps=total_steps,
            success_steps=success_steps,
            failed_steps=failed_steps,
            skipped_steps=skipped_steps,
            total_time=total_time,
            report_url=full_report_url,
        )

        # 创建邮件
        msg = MIMEMultipart("alternative")
        status_text = "成功" if status == "success" else "失败"
        msg["Subject"] = f"[TestMaster] 场景执行完成: {scenario_name} - {status_text}"
        msg["From"] = self.from_email
        msg["To"] = to_email

        part = MIMEText(html_content, "html", "utf-8")
        msg.attach(part)

        try:
            # 连接 SMTP 服务器
            if self.enable_ssl:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            else:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()

            # 登录
            server.login(self.smtp_user, self.smtp_password)

            # 发送
            server.sendmail(self.from_email, [to_email], msg.as_string())
            server.quit()

            print(f"[EmailNotifier] 场景执行结果邮件发送成功: {scenario_name} -> {to_email}")
            return True

        except Exception as e:
            print(f"[EmailNotifier] 邮件发送失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

    def _build_html_content(
        self,
        scenario_name: str,
        scenario_id: int,
        status: str,
        total_steps: int,
        success_steps: int,
        failed_steps: int,
        skipped_steps: int,
        total_time: int,
        report_url: str,
    ) -> str:
        """
        构建 HTML 邮件内容

        Returns:
            str: HTML 字符串
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_time_seconds = total_time / 1000

        # 状态颜色
        if status == "success":
            status_color = "#28a745"
            status_text = "执行成功"
        elif status == "failed":
            status_color = "#dc3545"
            status_text = "执行失败"
        else:
            status_color = "#ffc107"
            status_text = "执行异常"

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>TestMaster 场景执行结果</title>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; }}
                .container {{ max-width: 600px; margin: 20px auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                .header h1 {{ margin: 0; color: #333; font-size: 20px; }}
                .status {{ font-size: 24px; font-weight: bold; color: {status_color}; padding: 10px 0; text-align: center; }}
                .info-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                .info-table td {{ border: 1px solid #dee2e6; padding: 8px 12px; }}
                .info-table .label {{ background-color: #f8f9fa; font-weight: bold; width: 40%; }}
                .success {{ color: #28a745; font-weight: bold; }}
                .failed {{ color: #dc3545; font-weight: bold; }}
                .button {{ text-align: center; margin: 30px 0; }}
                .button a {{ display: inline-block; background-color: #007bff; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; }}
                .button a:hover {{ background-color: #0056b3; }}
                .footer {{ text-align: center; color: #6c757d; font-size: 12px; margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>TestMaster 自动化测试平台</h1>
                </div>

                <div class="status">
                    {status_text}
                </div>

                <table class="info-table">
                    <tr>
                        <td class="label">场景名称</td>
                        <td>{scenario_name} (ID: {scenario_id})</td>
                    </tr>
                    <tr>
                        <td class="label">执行时间</td>
                        <td>{now}</td>
                    </tr>
                    <tr>
                        <td class="label">总耗时</td>
                        <td>{total_time_seconds:.2f} 秒</td>
                    </tr>
                    <tr>
                        <td class="label">步骤统计</td>
                        <td>
                            总步骤: {total_steps} |
                            <span class="success">成功: {success_steps}</span> |
                            <span class="failed">失败: {failed_steps}</span> |
                            跳过: {skipped_steps}
                        </td>
                    </tr>
                </table>

                <div class="button">
                    <a href="{report_url}" target="_blank">点击查看详细 Allure 报告</a>
                </div>

                <div class="footer">
                    <p>此邮件由 TestMaster 自动化测试平台自动发送，请勿回复</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html


# 单例实例
_email_notifier_instance: Optional[EmailNotifier] = None


def get_email_notifier() -> EmailNotifier:
    """获取邮件通知器单例"""
    global _email_notifier_instance
    if _email_notifier_instance is None:
        _email_notifier_instance = EmailNotifier()
    return _email_notifier_instance
