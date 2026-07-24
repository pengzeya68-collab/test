import pytest

from fastapi_backend.services.automation_notification_outbox import (
    _dingtalk_url,
    _message,
    validate_channel_config,
)


def test_notification_config_rejects_non_https_webhook():
    with pytest.raises(ValueError, match="HTTPS"):
        validate_channel_config("dingtalk", {"webhook_url": "http://example.test/hook"})


def test_notification_config_rejects_private_destination():
    with pytest.raises(ValueError, match="不安全"):
        validate_channel_config("webhook", {"webhook_url": "https://127.0.0.1/hook"})


def test_notification_config_normalizes_email_recipients():
    config = validate_channel_config("email", {"recipients": " qa@example.com, dev@example.com "})
    assert config["recipients"] == ["qa@example.com", "dev@example.com"]


def test_dingtalk_signed_url_keeps_existing_query():
    signed = _dingtalk_url("https://oapi.dingtalk.com/robot/send?access_token=abc", "secret")
    assert "access_token=abc" in signed
    assert "timestamp=" in signed and "sign=" in signed


def test_notification_message_never_needs_raw_request_data():
    message = _message({
        "execution_id": "run-1", "target_type": "suite", "target_id": 8, "status": "failed",
        "attempt": 1, "passed": 2, "failed": 1, "timed_out": 0, "cancelled": 0, "total": 3,
        "duration_ms": 1234, "error_message": "断言失败",
    })
    assert "run-1" in message
    assert "断言失败" in message
    assert "Authorization" not in message
