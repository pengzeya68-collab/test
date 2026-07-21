"""Safe HAR 1.2 parsing into redacted API test-case candidates."""

from __future__ import annotations

import hashlib
import base64
import json
import re
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit

MAX_HAR_BYTES = 25 * 1024 * 1024
MAX_ENTRIES = 1000
MAX_BODY_BYTES = 1024 * 1024
_SENSITIVE = re.compile(r"password|passwd|secret|token|api[_-]?key|authorization|cookie|session|id_?card|phone", re.I)
_SKIPPED_RESOURCE_TYPES = {"image", "font", "stylesheet", "media", "script"}


class HarImportError(ValueError):
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
    return value


def _redact_url(url: str) -> str:
    parts = urlsplit(url)
    query = [
        (key, _placeholder(key) if _SENSITIVE.search(key) else value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query, doseq=True, safe="{}"), ""))


def _headers(values: list[dict[str, Any]]) -> dict[str, str]:
    output: dict[str, str] = {}
    for item in values or []:
        key = str(item.get("name") or "").strip()
        value = str(item.get("value") or "")
        if not key or key.lower() in {"cookie", "set-cookie"}:
            continue
        output[key] = _placeholder(key) if _SENSITIVE.search(key) else value
    return output


def _request_body(post_data: dict[str, Any] | None) -> tuple[str, str, Any]:
    if not isinstance(post_data, dict):
        return "none", "application/json", None
    mime_type = str(post_data.get("mimeType") or "application/json").split(";", 1)[0].strip().lower()
    text = str(post_data.get("text") or "")
    if len(text.encode("utf-8", errors="ignore")) > MAX_BODY_BYTES:
        return "none", mime_type, None
    if mime_type == "application/json":
        try:
            return "raw", mime_type, _redact_value(json.loads(text))
        except json.JSONDecodeError:
            return "raw", mime_type, {"raw": "[unparseable JSON omitted]"}
    if mime_type in {"application/x-www-form-urlencoded", "multipart/form-data"}:
        params = post_data.get("params") or []
        payload = {}
        for item in params:
            if not isinstance(item, dict) or not item.get("name"):
                continue
            name = str(item.get("name"))
            filename = str(item.get("fileName") or item.get("filename") or "").replace("\\", "/").split("/")[-1]
            if filename:
                payload[name] = {
                    "filename": filename[:255],
                    "content_type": str(item.get("contentType") or "application/octet-stream")[:200],
                    "requires_file_selection": True,
                }
            else:
                payload[name] = _redact_value(str(item.get("value") or ""), name)
        return ("form-data" if mime_type == "multipart/form-data" else "form"), mime_type, payload
    return "none", mime_type, None


def _fingerprint(method: str, url: str, body_type: str, payload: Any) -> str:
    canonical = json.dumps(
        {"method": method, "url": url, "body_type": body_type, "payload": payload},
        ensure_ascii=True,
        sort_keys=True,
        default=str,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _redirect_target(raw_url: str, response: dict[str, Any]) -> str | None:
    status = int(response.get("status") or 0)
    if not 300 <= status < 400:
        return None
    target = str(response.get("redirectURL") or "").strip()
    if not target:
        for header in response.get("headers") or []:
            if isinstance(header, dict) and str(header.get("name") or "").lower() == "location":
                target = str(header.get("value") or "").strip()
                break
    return urljoin(raw_url, target) if target else None


def _response_metadata(response: dict[str, Any]) -> dict[str, Any]:
    content = response.get("content") if isinstance(response, dict) else None
    if not isinstance(content, dict):
        return {}
    text = str(content.get("text") or "")
    encoding = str(content.get("encoding") or "").lower()
    raw = b""
    if text:
        if encoding == "base64":
            try:
                raw = base64.b64decode(text, validate=True)
            except (ValueError, TypeError):
                raw = text.encode("utf-8", errors="replace")
        else:
            raw = text.encode("utf-8", errors="replace")
    try:
        declared_size = max(0, int(content.get("size") or len(raw) or 0))
    except (TypeError, ValueError):
        declared_size = len(raw)
    metadata: dict[str, Any] = {
        "mime_type": str(content.get("mimeType") or "")[:200] or None,
        "size_bytes": declared_size,
        "encoding": encoding or None,
    }
    if raw:
        metadata["sha256"] = hashlib.sha256(raw).hexdigest()
        if len(raw) <= MAX_BODY_BYTES and "json" in str(metadata["mime_type"] or "").lower():
            try:
                metadata["json_sample"] = _redact_value(json.loads(raw.decode("utf-8-sig")))
            except (UnicodeDecodeError, json.JSONDecodeError):
                metadata["json_sample"] = "[unparseable JSON omitted]"
    return metadata


def parse_har(content: bytes) -> list[dict[str, Any]]:
    if len(content) > MAX_HAR_BYTES:
        raise HarImportError("HAR 文件超过 25 MB 限制")
    try:
        document = json.loads(content.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HarImportError("HAR 必须是 UTF-8 JSON 文件") from exc
    entries = document.get("log", {}).get("entries") if isinstance(document, dict) else None
    if not isinstance(entries, list):
        raise HarImportError("不是有效的 HAR 1.2 文件")

    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()
    redirect_chains: dict[str, list[dict[str, Any]]] = {}
    for entry in entries[:MAX_ENTRIES]:
        if not isinstance(entry, dict):
            continue
        resource_type = str(entry.get("_resourceType") or entry.get("resourceType") or "").lower()
        request = entry.get("request") or {}
        response = entry.get("response") or {}
        method = str(request.get("method") or "GET").upper()
        raw_url = str(request.get("url") or "")
        parts = urlsplit(raw_url)
        if resource_type in _SKIPPED_RESOURCE_TYPES or parts.scheme not in {"http", "https"}:
            continue
        redirect_target = _redirect_target(raw_url, response)
        if redirect_target:
            chain = redirect_chains.pop(raw_url, [])
            chain.append(
                {
                    "status": int(response.get("status") or 0),
                    "from": _redact_url(raw_url),
                    "to": _redact_url(redirect_target),
                }
            )
            redirect_chains[redirect_target] = chain
            continue
        body_type, content_type, payload = _request_body(request.get("postData"))
        url = _redact_url(raw_url)
        fingerprint = _fingerprint(method, url, body_type, payload)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        response_status = int(response.get("status") or 0)
        candidates.append(
            {
                "id": fingerprint,
                "name": f"{method} {parts.path or '/'}"[:200],
                "method": method,
                "url": url,
                "headers": _headers(request.get("headers") or []),
                "params": {
                    key: (_placeholder(key) if _SENSITIVE.search(key) else value)
                    for key, value in parse_qsl(parts.query, keep_blank_values=True)
                },
                "body_type": body_type,
                "content_type": content_type,
                "payload": payload,
                "assert_rules": (
                    [{"field": "status_code", "operator": "equals", "expected": response_status}]
                    if response_status
                    else []
                ),
                "response_status": response_status,
                "fingerprint": fingerprint,
                "timing_ms": entry.get("time"),
                "source_metadata": {
                    "redirect_chain": redirect_chains.pop(raw_url, []),
                    "response": _response_metadata(response),
                },
            }
        )
    return candidates
