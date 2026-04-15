"""Send text notifications to Feishu / DingTalk / WeCom bot webhooks."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Tuple
from urllib import error as urllib_error
from urllib import request as urllib_request


def _is_feishu_webhook(webhook_url: str) -> bool:
    u = webhook_url.lower()
    return "open.feishu.cn" in u or "feishu.cn" in u or "larksuite.com" in u


def _public_backend_base_url() -> str:
    try:
        from fastapi_backend.core import autotest_settings as _s

        base = getattr(_s, "BASE_URL", None) or ""
        return (base or "http://localhost:5001").strip().rstrip("/")
    except Exception:
        return "http://localhost:5001"


def absolute_report_url(report_path: Optional[str]) -> Optional[str]:
    """将 /reports/... 转为可点击的完整 URL（依赖 BASE_URL / 邮件配置里的服务地址）。"""
    if not (report_path or "").strip():
        return None
    p = report_path.strip()
    if p.startswith(("http://", "https://")):
        return p
    base = _public_backend_base_url()
    return f"{base}/{p.lstrip('/')}"


def _build_payload(webhook_url: str, text: str) -> Tuple[Dict[str, Any], Dict[str, str]]:
    u = webhook_url.lower()
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if _is_feishu_webhook(webhook_url):
        return {"msg_type": "text", "content": {"text": text}}, headers
    if "dingtalk.com" in u or "oapi.dingtalk.com" in u:
        return {"msgtype": "text", "text": {"content": text}}, headers
    if "qyapi.weixin.qq.com" in u:
        return {"msgtype": "markdown", "markdown": {"content": text}}, headers
    # Default: 按飞书文本
    return {"msg_type": "text", "content": {"text": text}}, headers


def _feishu_interactive_card_payload(
    scenario_id: int,
    scenario_name: str,
    ok: bool,
    failed: int,
    total: int,
    total_time_ms: Optional[int],
    public_report_url: Optional[str],
    error_text: Optional[str],
    env_name: Optional[str] = None,
    skipped: int = 0,
) -> Dict[str, Any]:
    """飞书机器人 interactive 卡片消息：动态颜色标题 + 核心指标 + 统计 + 报告按钮。"""
    passed = max(0, total - failed - skipped) if total > 0 else 0
    pass_rate = f"{round((passed / total) * 100)}%" if total > 0 else "N/A"
    sec = f"{total_time_ms / 1000.0:.2f}s" if total_time_ms is not None else "N/A"
    template = "green" if ok and not error_text else "red"
    header_title = f"🟢 {scenario_name or '场景'} - 执行成功" if ok and not error_text else f"🚨 {scenario_name or '场景'} - 执行失败"

    md_lines = [
        f"**场景名称：** {scenario_name or '—'}",
        f"**执行环境：** {env_name or '—'}",
        f"**执行耗时：** {sec}",
        f"**通过率：** {pass_rate}",
        "",
        f"**总步骤数：** {total} ｜ **成功：** {passed} ｜ **失败：** {failed} ｜ **跳过：** {skipped}",
    ]
    if error_text:
        md_lines.append("")
        md_lines.append(f"**错误信息：** {error_text[:500]}")

    card: Dict[str, Any] = {
        "header": {
            "template": template,
            "title": {"tag": "plain_text", "content": header_title},
        },
        "elements": [
            {
                "tag": "markdown",
                "content": "\n".join(md_lines),
            }
        ],
    }

    if public_report_url:
        card["elements"].append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "text": {"tag": "plain_text", "content": "📊 查看 Allure 详细报告"},
                        "type": "primary",
                        "url": public_report_url,
                    }
                ],
            }
        )

    return {
        "msg_type": "interactive",
        "card": card,
    }


def _feishu_post_schedule_payload(
    scenario_id: int,
    scenario_name: str,
    ok: bool,
    failed: int,
    total: int,
    total_time_ms: Optional[int],
    public_report_url: Optional[str],
    error_text: Optional[str],
    env_name: Optional[str] = None,
    skipped: int = 0,
) -> Dict[str, Any]:
    """飞书自定义机器人推送（优先使用 interactive 卡片）。"""
    return _feishu_interactive_card_payload(
        scenario_id,
        scenario_name,
        ok,
        failed,
        total,
        total_time_ms,
        public_report_url,
        error_text,
        env_name,
        skipped,
    )


def send_bot_webhook(
    webhook_url: str,
    text: str = "",
    *,
    payload_override: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    if not (webhook_url or "").strip():
        return False, "empty url"
    wu = webhook_url.strip()
    if payload_override is not None:
        payload = payload_override
        headers = {"Content-Type": "application/json; charset=utf-8"}
    else:
        payload, headers = _build_payload(wu, text)
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib_request.Request(wu, data=data, headers=headers, method="POST")
    try:
        with urllib_request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            if resp.status >= 400:
                return False, f"HTTP {resp.status}: {body[:500]}"
            # Feishu returns JSON with code != 0 on business error
            try:
                j = json.loads(body)
                if isinstance(j, dict) and j.get("code") not in (None, 0):
                    return False, body[:500]
            except json.JSONDecodeError:
                pass
            return True, body[:200]
    except urllib_error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace") if e.fp else ""
        return False, f"HTTPError {e.code}: {err_body[:500]}"
    except Exception as e:
        return False, str(e)[:500]


def _failed_step_count_payload(result: Optional[dict]) -> int:
    if not result:
        return 0
    if result.get("failed_steps") is not None:
        return int(result["failed_steps"])
    if result.get("failed_count") is not None:
        return int(result["failed_count"])
    return 0


def notify_scenario_schedule_webhook_from_db(scenario_id: int, result: dict) -> Tuple[bool, str]:
    """
    场景在 Celery 中执行结束后调用：从 DB 读 schedule_webhook_url 并推送。
    与 FastAPI 调度进程是否被 WatchFiles reload 无关。
    """
    from fastapi_backend.services.autotest_schedule_persistence import read_schedule_webhook_sync

    url = read_schedule_webhook_sync(scenario_id)
    if not url:
        return False, "no schedule_webhook_url in db"

    err = None
    if result.get("status") == "failed" or result.get("error"):
        err = str(result.get("error") or result.get("detail") or result)[:1500]

    failed = _failed_step_count_payload(result)
    total = int(result.get("total_steps") or len(result.get("step_results") or []))
    skipped = int(result.get("skipped_steps") or result.get("skipped_count") or 0)
    hard_fail = result.get("status") == "failed" or bool(result.get("error"))
    ok = (not hard_fail) and failed == 0 and not err
    name = str(result.get("scenario_name") or "")
    ru_path = result.get("report_url")
    public_ru = absolute_report_url(ru_path) if ru_path else None
    total_time = result.get("total_time")
    total_time_ms = int(total_time) if total_time is not None else None

    if _is_feishu_webhook(url):
        env_name = str(result.get("env_name") or "")
        post = _feishu_post_schedule_payload(
            scenario_id,
            name,
            ok,
            failed,
            total,
            total_time_ms,
            public_ru,
            err,
            env_name,
            skipped,
        )
        return send_bot_webhook(url, payload_override=post)

    # 钉钉 / 企微等：纯文本 + 完整报告链接
    lines = [
        "【TestMaster】接口自动化执行结果",
        f"场景：{name or '—'}（ID {scenario_id}）",
        f"结果：{'通过' if ok else '失败'}",
    ]
    if total > 0:
        passed = max(0, total - failed - skipped)
        lines.append(f"步骤：通过 {passed}，失败 {failed}，跳过 {skipped}，共 {total} 步")
    if total_time_ms is not None:
        lines.append(f"耗时：{total_time_ms} ms")
    if err:
        lines.append(f"错误：{err[:800]}")
    if public_ru:
        lines.append(f"报告：{public_ru}")
    elif ru_path:
        lines.append(f"报告（需配置 BASE_URL 才能点击）：{ru_path}")

    return send_bot_webhook(url, "\n".join(lines))
