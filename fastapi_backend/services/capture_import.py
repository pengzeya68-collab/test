"""Normalization and redaction for browser network capture import candidates."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


MAX_CAPTURE_EXCHANGES = 500
MAX_CAPTURE_BATCH = 100
MAX_CAPTURE_BODY_BYTES = 1024 * 1024
_SENSITIVE = re.compile(r"password|passwd|secret|token|api[_-]?key|authorization|cookie|session|id_?card|phone", re.I)
_HEADER_NAME = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")


class CaptureImportError(ValueError):
    pass


def _placeholder(name: str) -> str:
    return "{{" + re.sub(r"[^A-Za-z0-9_]", "_", name).upper()[:80] + "}}"


def _redact_value(value: Any, field_name: str = "value") -> Any:
    if _SENSITIVE.search(field_name):
        return _placeholder(field_name)
    if isinstance(value, dict):
        return {str(key): _redact_value(item, str(key)) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_value(item, field_name) for item in value]
    if isinstance(value, str) and len(value.encode("utf-8", errors="ignore")) > MAX_CAPTURE_BODY_BYTES:
        return "[body omitted: size limit exceeded]"
    return value


def _safe_json(value: Any, field_name: str = "value") -> Any:
    redacted = _redact_value(value, field_name)
    try:
        size = len(json.dumps(redacted, ensure_ascii=True, default=str).encode("utf-8"))
    except (TypeError, ValueError) as exc:
        raise CaptureImportError("capture payload is not serializable") from exc
    return redacted if size <= MAX_CAPTURE_BODY_BYTES else "[body omitted: size limit exceeded]"


def _redact_headers(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, str] = {}
    for raw_name, raw_value in value.items():
        name = str(raw_name).strip()
        if not name or not _HEADER_NAME.fullmatch(name) or name.lower() in {"cookie", "set-cookie"}:
            continue
        result[name] = _placeholder(name) if _SENSITIVE.search(name) else str(raw_value)[:8192]
    return result


def _redact_url(raw_url: Any) -> tuple[str, dict[str, str]]:
    url = str(raw_url or "").strip()
    parts = urlsplit(url)
    if parts.scheme not in {"http", "https"} or not parts.netloc:
        raise CaptureImportError("captured URL must be an absolute HTTP(S) URL")
    params: dict[str, str] = {}
    pairs = []
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        safe_value = _placeholder(key) if _SENSITIVE.search(key) else value
        params[key] = safe_value
        pairs.append((key, safe_value))
    return urlunsplit(
        (parts.scheme, parts.netloc, parts.path or "/", urlencode(pairs, doseq=True, safe="{}"), "")
    ), params


def _safe_page_url(raw_url: Any) -> str | None:
    """Keep page correlation without retaining credential-bearing query text."""
    if not raw_url:
        return None
    try:
        redacted, _params = _redact_url(raw_url)
    except CaptureImportError:
        return None
    return redacted[:4000]


def redact_capture_source_url(raw_url: Any) -> str | None:
    """Redact an optional capture origin before it is persisted as session metadata."""
    return _safe_page_url(raw_url)


def _body_type(content_type: str, body: Any) -> str:
    if body in (None, "", "[non-JSON request body omitted]"):
        return "none"
    lowered = content_type.lower()
    if "multipart/form-data" in lowered:
        return "form-data"
    if "application/x-www-form-urlencoded" in lowered:
        return "form"
    return "raw"


def _fingerprint(method: str, url: str, body_type: str, payload: Any) -> str:
    canonical = json.dumps(
        {"method": method, "url": url, "body_type": body_type, "payload": payload},
        ensure_ascii=True,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def normalize_captured_exchange(value: Any) -> dict[str, Any]:
    """Return a server-redacted, bounded candidate from a desktop network event."""
    if not isinstance(value, dict):
        raise CaptureImportError("capture exchange must be an object")
    resource_type = str(value.get("resourceType") or value.get("resource_type") or "").lower()
    if resource_type and resource_type not in {"xhr", "fetch"}:
        raise CaptureImportError("only XHR and fetch exchanges can become API candidates")
    method = str(value.get("method") or "GET").upper()
    if method not in {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}:
        raise CaptureImportError("unsupported HTTP method")
    url, params = _redact_url(value.get("url"))
    request_headers = _redact_headers(value.get("requestHeaders") or value.get("request_headers"))
    response_headers = _redact_headers(value.get("responseHeaders") or value.get("response_headers"))
    content_type = (
        str(request_headers.get("content-type") or request_headers.get("Content-Type") or "application/json")
        .split(";", 1)[0]
        .strip()
        .lower()
    )
    payload = _safe_json(value.get("requestBody", value.get("request_body")), "request_body")
    body_type = _body_type(content_type, payload)
    try:
        status = int(value.get("status") or 0)
    except (TypeError, ValueError):
        status = 0
    try:
        timing_ms = max(0, min(int(value.get("timingMs", value.get("timing_ms", 0)) or 0), 600_000))
    except (TypeError, ValueError):
        timing_ms = 0
    response_body = _safe_json(value.get("responseBody", value.get("response_body")), "response_body")
    failure_reason = (
        str(value.get("failureReason") or value.get("failure_reason") or value.get("error") or "").strip()[:1000]
        or None
    )
    fingerprint = _fingerprint(method, url, body_type, payload)
    return {
        "method": method,
        "url": url,
        "headers": request_headers,
        "params": params,
        "body_type": body_type,
        "content_type": content_type,
        "payload": payload,
        "assert_rules": ([{"field": "status_code", "operator": "equals", "expected": status}] if status else []),
        "response": {"status": status, "headers": response_headers, "body": response_body},
        "fingerprint": fingerprint,
        "resource_type": resource_type or "xhr",
        "page_url": _safe_page_url(value.get("pageUrl") or value.get("page_url")),
        "timing_ms": timing_ms or None,
        "failure_reason": failure_reason,
    }


def candidate_from_exchange(exchange: Any) -> dict[str, Any]:
    request = exchange.request_redacted or {}
    response = exchange.response_redacted or {}
    return {
        "id": exchange.id,
        "name": f"{exchange.method} {urlsplit(exchange.url).path or '/'}"[:200],
        "method": exchange.method,
        "url": exchange.url,
        "headers": request.get("headers") or {},
        "params": request.get("params") or {},
        "body_type": request.get("body_type") or "none",
        "content_type": request.get("content_type") or "application/json",
        "payload": request.get("payload"),
        "assert_rules": request.get("assert_rules") or [],
        "response_status": response.get("status") or 0,
        "fingerprint": exchange.fingerprint,
        "selected": exchange.selected,
        "timing_ms": exchange.timing_ms,
        "failure_reason": exchange.failure_reason,
        "page_url": exchange.page_url,
    }
