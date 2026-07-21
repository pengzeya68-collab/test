"""Security-bound import normalization for API testing assets.

The import centre deliberately keeps only redacted, executable request metadata.
It does not retain source documents or credentials after preview/commit.
"""

from __future__ import annotations

import hashlib
import json
import re
import shlex
from collections.abc import Iterable
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

import yaml

from fastapi_backend.services.curl_parser import parse_curl
from fastapi_backend.services.har_import import HarImportError, parse_har


MAX_IMPORT_BYTES = 25 * 1024 * 1024
MAX_IMPORT_CANDIDATES = 1000
MAX_IMPORT_DEPTH = 50
MAX_BODY_BYTES = 1024 * 1024
SUPPORTED_SOURCE_TYPES = {"auto", "har", "postman", "openapi", "swagger", "curl", "apipost"}
_SENSITIVE = re.compile(r"password|passwd|secret|token|api[_-]?key|authorization|cookie|session|id_?card|phone", re.I)
_HEADER_NAME = re.compile(r"^[!#$%&'*+.^_`|~0-9A-Za-z-]+$")
_HTTP_METHODS = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}


class ImportSourceError(ValueError):
    """A user-correctable source document or import option error."""


def _placeholder(name: str) -> str:
    return "{{" + re.sub(r"[^A-Za-z0-9_]", "_", name).upper()[:80] + "}}"


def _safe_text(value: Any, limit: int = 8192) -> str:
    return str(value or "").replace("\x00", "")[:limit]


def _redact_value(value: Any, field_name: str = "value", depth: int = 0) -> Any:
    if depth > MAX_IMPORT_DEPTH:
        raise ImportSourceError("导入内容层级超过限制")
    if _SENSITIVE.search(field_name):
        return _placeholder(field_name)
    if isinstance(value, dict):
        return {str(key)[:200]: _redact_value(item, str(key), depth + 1) for key, item in value.items()}
    if isinstance(value, list):
        return [_redact_value(item, field_name, depth + 1) for item in value[:1000]]
    if isinstance(value, str):
        return value[:MAX_BODY_BYTES]
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return _safe_text(value)


def _json_size_limited(value: Any) -> Any:
    try:
        encoded = json.dumps(value, ensure_ascii=True, default=str, separators=(",", ":")).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ImportSourceError("请求体无法安全序列化") from exc
    if len(encoded) > MAX_BODY_BYTES:
        return {"_omitted": "request body exceeds 1 MB", "_size_bytes": len(encoded)}
    return value


def _normalize_url(raw_url: Any) -> tuple[str, dict[str, str], str]:
    raw = _safe_text(raw_url, 8192).strip()
    if not raw:
        raise ImportSourceError("请求缺少 URL")
    parts = urlsplit(raw)
    if parts.scheme:
        if parts.scheme.lower() not in {"http", "https"} or not parts.netloc:
            raise ImportSourceError("仅支持 HTTP(S) URL")
        host = parts.hostname.lower() if parts.hostname else ""
        port = parts.port
        netloc = host
        if parts.username or parts.password:
            raise ImportSourceError("URL 不允许包含用户凭据")
        if port and not (
            (parts.scheme.lower() == "http" and port == 80) or (parts.scheme.lower() == "https" and port == 443)
        ):
            netloc = f"{host}:{port}"
        scheme = parts.scheme.lower()
    else:
        if not raw.startswith("/"):
            raise ImportSourceError("URL 必须是 HTTP(S) 地址或以 / 开头的路径")
        scheme = ""
        netloc = ""
    pairs = []
    params: dict[str, str] = {}
    for key, value in parse_qsl(parts.query, keep_blank_values=True):
        clean_key = _safe_text(key, 200)
        clean_value = _placeholder(clean_key) if _SENSITIVE.search(clean_key) else _safe_text(value, 8192)
        pairs.append((clean_key, clean_value))
        params[clean_key] = clean_value
    pairs.sort(key=lambda item: (item[0], item[1]))
    path = parts.path or "/"
    url = urlunsplit((scheme, netloc, path, urlencode(pairs, doseq=True, safe="{}"), ""))
    canonical_url = urlunsplit((scheme, netloc, path, urlencode([(key, "") for key, _ in pairs], doseq=True), ""))
    return url, params, canonical_url


def _normalize_headers(raw_headers: Any) -> dict[str, str]:
    if isinstance(raw_headers, list):
        pairs = (
            (item.get("key", item.get("name")), item.get("value")) for item in raw_headers if isinstance(item, dict)
        )
    elif isinstance(raw_headers, dict):
        pairs = raw_headers.items()
    else:
        return {}
    result: dict[str, str] = {}
    for raw_name, raw_value in pairs:
        name = _safe_text(raw_name, 200).strip()
        if not name or not _HEADER_NAME.fullmatch(name) or name.lower() in {"cookie", "set-cookie", "content-length"}:
            continue
        value = _placeholder(name) if _SENSITIVE.search(name) else _safe_text(raw_value)
        result[name] = value
    return result


def _structural_shape(value: Any, depth: int = 0) -> Any:
    if depth > MAX_IMPORT_DEPTH:
        return "depth-limit"
    if isinstance(value, dict):
        return {
            str(key): _structural_shape(item, depth + 1)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, list):
        return [_structural_shape(item, depth + 1) for item in value[:20]]
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    return "string"


def _candidate_fingerprint(
    method: str,
    canonical_url: str,
    headers: dict[str, str],
    params: dict[str, str],
    body_type: str,
    content_type: str,
    payload: Any,
) -> str:
    shape = {
        "method": method,
        "canonical_url": canonical_url,
        "headers": sorted(key.lower() for key in headers),
        "params": sorted(params),
        "body_type": body_type,
        "content_type": content_type.lower().split(";", 1)[0],
        "payload": _structural_shape(payload),
    }
    return hashlib.sha256(
        json.dumps(shape, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def _sensitive_fields(value: Any, prefix: str = "") -> list[str]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            if _SENSITIVE.search(str(key)):
                found.append(path)
            found.extend(_sensitive_fields(item, path))
    elif isinstance(value, list):
        for index, item in enumerate(value[:100]):
            found.extend(_sensitive_fields(item, f"{prefix}[{index}]"))
    return found[:100]


def normalize_candidate(
    *,
    source_type: str,
    name: Any,
    method: Any,
    url: Any,
    headers: Any = None,
    payload: Any = None,
    body_type: str | None = None,
    content_type: str | None = None,
    response_status: Any = None,
    source_name: str | None = None,
) -> dict[str, Any]:
    normalized_method = _safe_text(method or "GET", 10).upper()
    if normalized_method not in _HTTP_METHODS:
        raise ImportSourceError(f"不支持的 HTTP 方法: {normalized_method}")
    normalized_url, params, canonical_url = _normalize_url(url)
    normalized_headers = _normalize_headers(headers)
    normalized_content_type = (
        _safe_text(
            content_type
            or normalized_headers.get("Content-Type")
            or normalized_headers.get("content-type")
            or "application/json",
            200,
        )
        .lower()
        .split(";", 1)[0]
    )
    redacted_payload = _json_size_limited(_redact_value(payload, "payload")) if payload is not None else None
    normalized_body_type = body_type or ("none" if redacted_payload is None else "raw")
    if normalized_body_type not in {"none", "raw", "form", "form-data"}:
        normalized_body_type = "raw"
    if redacted_payload is None:
        normalized_body_type = "none"
    try:
        status = int(response_status) if response_status is not None else 0
    except (TypeError, ValueError):
        status = 0
    fingerprint = _candidate_fingerprint(
        normalized_method,
        canonical_url,
        normalized_headers,
        params,
        normalized_body_type,
        normalized_content_type,
        redacted_payload,
    )
    sensitive_fields = _sensitive_fields({"headers": normalized_headers, "params": params, "payload": redacted_payload})
    return {
        "id": fingerprint,
        "source_type": source_type,
        "source_name": _safe_text(source_name or name, 200),
        "name": _safe_text(name or f"{normalized_method} {urlsplit(normalized_url).path or '/'}", 200),
        "method": normalized_method,
        "url": normalized_url,
        "canonical_url": canonical_url,
        "headers": normalized_headers,
        "params": params,
        "body_type": normalized_body_type,
        "content_type": normalized_content_type,
        "payload": redacted_payload,
        "assert_rules": (
            [{"field": "status_code", "operator": "equals", "expected": status}] if 100 <= status <= 599 else []
        ),
        "response_status": status,
        "sensitive_fields": sensitive_fields,
        "fingerprint": fingerprint,
    }


def _document_depth(value: Any, depth: int = 0, seen: set[int] | None = None) -> None:
    if depth > MAX_IMPORT_DEPTH:
        raise ImportSourceError("导入文档层级超过限制")
    if not isinstance(value, (dict, list)):
        return
    seen = seen or set()
    pointer = id(value)
    if pointer in seen:
        return
    seen.add(pointer)
    children: Iterable[Any] = value.values() if isinstance(value, dict) else value
    for item in children:
        _document_depth(item, depth + 1, seen)


def _load_document(content: bytes) -> Any:
    if len(content) > MAX_IMPORT_BYTES:
        raise ImportSourceError("导入文件超过 25 MB 限制")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ImportSourceError("导入文件必须是 UTF-8 编码") from exc
    try:
        document = json.loads(text)
    except json.JSONDecodeError:
        try:
            document = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise ImportSourceError("文件不是有效的 JSON 或 YAML 文档") from exc
    _document_depth(document)
    return document


def _postman_url(value: Any) -> str:
    if isinstance(value, str):
        return value
    if not isinstance(value, dict):
        return ""
    raw = value.get("raw")
    if raw:
        return str(raw)
    protocol = value.get("protocol") or "https"
    host = value.get("host") or []
    path = value.get("path") or []
    query = value.get("query") or []
    host_text = ".".join(host) if isinstance(host, list) else str(host)
    path_text = "/".join(path) if isinstance(path, list) else str(path)
    query_pairs = [
        (str(item.get("key")), str(item.get("value") or ""))
        for item in query
        if isinstance(item, dict) and item.get("key")
    ]
    return urlunsplit((str(protocol), host_text, "/" + path_text.lstrip("/"), urlencode(query_pairs), ""))


def _postman_body(body: Any) -> tuple[Any, str, str]:
    if not isinstance(body, dict):
        return None, "none", "application/json"
    mode = str(body.get("mode") or "")
    if mode == "raw":
        raw = body.get("raw") or ""
        options = body.get("options") or {}
        language = str((options.get("raw") or {}).get("language") or "json").lower()
        if language in {"json", "application/json"}:
            try:
                return json.loads(raw), "raw", "application/json"
            except (TypeError, json.JSONDecodeError):
                return {"raw": _safe_text(raw, MAX_BODY_BYTES)}, "raw", "application/json"
        return {"raw": _safe_text(raw, MAX_BODY_BYTES)}, "raw", "text/plain"
    if mode in {"urlencoded", "formdata"}:
        fields: dict[str, Any] = {}
        for field in body.get(mode) or []:
            if not isinstance(field, dict) or field.get("disabled") or not field.get("key"):
                continue
            key = str(field["key"])
            fields[key] = "[file omitted]" if field.get("type") == "file" else field.get("value", "")
        return (
            fields,
            ("form-data" if mode == "formdata" else "form"),
            ("multipart/form-data" if mode == "formdata" else "application/x-www-form-urlencoded"),
        )
    return None, "none", "application/json"


def _parse_postman(document: Any) -> list[dict[str, Any]]:
    if not isinstance(document, dict) or not isinstance(document.get("item"), list):
        raise ImportSourceError("不是有效的 Postman Collection")
    info = document.get("info") or {}
    schema = str(info.get("schema") or "")
    if schema and "collection" not in schema:
        raise ImportSourceError("仅支持 Postman Collection v2.1")
    candidates: list[dict[str, Any]] = []

    def visit(items: Any, folder: str = "") -> None:
        if not isinstance(items, list):
            return
        for item in items:
            if not isinstance(item, dict):
                continue
            item_name = _safe_text(item.get("name") or "未命名请求", 200)
            next_folder = f"{folder} / {item_name}".strip(" / ")
            if isinstance(item.get("item"), list):
                visit(item["item"], next_folder)
                continue
            request = item.get("request")
            if not isinstance(request, dict):
                continue
            payload, body_type, content_type = _postman_body(request.get("body"))
            candidates.append(
                normalize_candidate(
                    source_type="postman",
                    name=item_name,
                    method=request.get("method"),
                    url=_postman_url(request.get("url")),
                    headers=request.get("header"),
                    payload=payload,
                    body_type=body_type,
                    content_type=content_type,
                    source_name=folder or str(info.get("name") or "Postman Collection"),
                )
            )

    visit(document["item"])
    return candidates


def _schema_example(schema: Any, depth: int = 0) -> Any:
    if depth > 8 or not isinstance(schema, dict):
        return {}
    if "example" in schema:
        return schema["example"]
    if "default" in schema:
        return schema["default"]
    if "enum" in schema and schema["enum"]:
        return schema["enum"][0]
    schema_type = schema.get("type")
    if schema_type == "object" or "properties" in schema:
        return {str(key): _schema_example(value, depth + 1) for key, value in (schema.get("properties") or {}).items()}
    if schema_type == "array":
        return [_schema_example(schema.get("items") or {}, depth + 1)]
    if schema_type in {"integer", "number"}:
        return 0
    if schema_type == "boolean":
        return False
    return ""


def _openapi_base_url(document: dict[str, Any], is_swagger: bool) -> str:
    if not is_swagger:
        servers = document.get("servers") or []
        if isinstance(servers, list):
            for server in servers:
                if isinstance(server, dict) and server.get("url"):
                    return str(server["url"]).rstrip("/")
        return ""
    host = str(document.get("host") or "").strip()
    if not host:
        return ""
    schemes = document.get("schemes") or ["https"]
    scheme = str(schemes[0] or "https")
    return f"{scheme}://{host}{str(document.get('basePath') or '').rstrip('/')}"


def _parameter_value(parameter: dict[str, Any]) -> Any:
    if "example" in parameter:
        return parameter["example"]
    schema = parameter.get("schema") if isinstance(parameter.get("schema"), dict) else parameter
    return _schema_example(schema)


def _parse_openapi(document: Any, is_swagger: bool) -> list[dict[str, Any]]:
    version_key = "swagger" if is_swagger else "openapi"
    if not isinstance(document, dict) or not document.get(version_key) or not isinstance(document.get("paths"), dict):
        raise ImportSourceError("不是有效的 API 规范文档")
    base_url = _openapi_base_url(document, is_swagger)
    candidates: list[dict[str, Any]] = []
    for path, path_item in document["paths"].items():
        if not isinstance(path_item, dict) or not isinstance(path, str):
            continue
        shared_parameters = path_item.get("parameters") or []
        for method, operation in path_item.items():
            normalized_method = str(method).upper()
            if normalized_method not in _HTTP_METHODS or not isinstance(operation, dict):
                continue
            headers: dict[str, Any] = {}
            query: dict[str, Any] = {}
            concrete_path = path
            parameters = [*shared_parameters, *(operation.get("parameters") or [])]
            payload = None
            body_type = "none"
            content_type = "application/json"
            for parameter in parameters:
                if not isinstance(parameter, dict):
                    continue
                location = parameter.get("in")
                name = str(parameter.get("name") or "")
                if not name:
                    continue
                value = _parameter_value(parameter)
                if location == "path":
                    concrete_path = concrete_path.replace("{" + name + "}", "{{" + name + "}}")
                elif location == "query":
                    query[name] = value
                elif location == "header":
                    headers[name] = value
                elif location == "body":
                    payload = _schema_example(parameter.get("schema") or {})
                    body_type = "raw"
            if not is_swagger:
                request_body = operation.get("requestBody") or {}
                if isinstance(request_body, dict):
                    content = request_body.get("content") or {}
                    if isinstance(content, dict) and content:
                        content_type, media = next(iter(content.items()))
                        if isinstance(media, dict):
                            payload = media.get("example", _schema_example(media.get("schema") or {}))
                            body_type = (
                                "form-data"
                                if content_type.startswith("multipart/")
                                else ("form" if "urlencoded" in content_type else "raw")
                            )
            else:
                consumes = operation.get("consumes") or document.get("consumes") or []
                if consumes:
                    content_type = str(consumes[0])
            if query:
                concrete_path = f"{concrete_path}?{urlencode(query, doseq=True, safe='{}')}"
            responses = operation.get("responses") or {}
            success_status = next(
                (int(str(code)) for code in responses if str(code).isdigit() and 200 <= int(str(code)) < 300), 0
            )
            candidates.append(
                normalize_candidate(
                    source_type="swagger" if is_swagger else "openapi",
                    name=operation.get("summary") or operation.get("operationId") or f"{normalized_method} {path}",
                    method=normalized_method,
                    url=f"{base_url}{concrete_path}",
                    headers=headers,
                    payload=payload,
                    body_type=body_type,
                    content_type=content_type,
                    response_status=success_status,
                    source_name=str((document.get("info") or {}).get("title") or version_key),
                )
            )
            if len(candidates) >= MAX_IMPORT_CANDIDATES:
                return candidates
    return candidates


def _parse_curl(content: bytes) -> list[dict[str, Any]]:
    if len(content) > MAX_IMPORT_BYTES:
        raise ImportSourceError("cURL 文本超过大小限制")
    try:
        command = content.decode("utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        raise ImportSourceError("cURL 文本必须是 UTF-8 编码") from exc
    if not command.lower().startswith("curl"):
        raise ImportSourceError("cURL 文本必须以 curl 开头")
    if any(marker in command for marker in (";", "&&", "||", "`", "$(`")):
        raise ImportSourceError("cURL 导入只接受单个请求命令")
    try:
        # Validate quotes first; the legacy parser then preserves its established flag support.
        shlex.split(command)
        parsed = parse_curl(command)
    except ValueError as exc:
        raise ImportSourceError(str(exc)) from exc
    return [
        normalize_candidate(
            source_type="curl",
            name=f"{parsed['method']} {urlsplit(parsed['url']).path or '/'}",
            method=parsed["method"],
            url=parsed["url"],
            headers=parsed["headers"],
            payload=parsed["body"],
            body_type=parsed["body_type"],
            content_type=parsed["content_type"],
            source_name="cURL",
        )
    ]


def _request_from_apipost(node: dict[str, Any], source_name: str) -> dict[str, Any] | None:
    request = node.get("request") if isinstance(node.get("request"), dict) else node
    method = request.get("method") or request.get("httpMethod")
    url = request.get("url") or request.get("rawUrl") or request.get("requestUrl")
    if not method or not url:
        return None
    headers = request.get("headers") or request.get("header") or []
    body = request.get("body") or request.get("requestBody")
    if isinstance(body, dict) and "raw" in body:
        raw = body.get("raw")
        try:
            body = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            body = {"raw": _safe_text(raw, MAX_BODY_BYTES)}
    return normalize_candidate(
        source_type="apipost",
        name=node.get("name") or node.get("title") or f"{method} {url}",
        method=method,
        url=url,
        headers=headers,
        payload=body,
        body_type=request.get("bodyType") or ("raw" if body is not None else "none"),
        content_type=request.get("contentType"),
        source_name=source_name,
    )


def _parse_apipost(document: Any) -> list[dict[str, Any]]:
    if not isinstance(document, (dict, list)):
        raise ImportSourceError("不是有效的 Apipost 导出")
    candidates: list[dict[str, Any]] = []
    seen_nodes: set[int] = set()

    def visit(node: Any, source_name: str = "Apipost") -> None:
        if len(candidates) >= MAX_IMPORT_CANDIDATES or not isinstance(node, (dict, list)):
            return
        pointer = id(node)
        if pointer in seen_nodes:
            return
        seen_nodes.add(pointer)
        if isinstance(node, list):
            for item in node:
                visit(item, source_name)
            return
        current_source = _safe_text(node.get("name") or node.get("title") or source_name, 200)
        candidate = _request_from_apipost(node, current_source)
        if candidate is not None:
            candidates.append(candidate)
        for key in ("items", "item", "children", "folders", "apis", "apiCollection", "data", "requests"):
            if key in node:
                visit(node[key], current_source)

    visit(document)
    if not candidates:
        raise ImportSourceError("Apipost 导出中没有可导入的 HTTP 请求")
    return candidates


def _deduplicate(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for candidate in candidates:
        if candidate["fingerprint"] in seen:
            continue
        seen.add(candidate["fingerprint"])
        result.append(candidate)
        if len(result) >= MAX_IMPORT_CANDIDATES:
            break
    return result


def detect_source_type(content: bytes, source_hint: str = "auto", filename: str = "") -> str:
    hint = str(source_hint or "auto").lower().strip()
    if hint not in SUPPORTED_SOURCE_TYPES:
        raise ImportSourceError("不支持的导入来源类型")
    if hint != "auto":
        return hint
    text = content.decode("utf-8-sig", errors="ignore").lstrip()
    if text.lower().startswith("curl"):
        return "curl"
    document = _load_document(content)
    if isinstance(document, dict):
        if isinstance(document.get("log"), dict) and isinstance(document["log"].get("entries"), list):
            return "har"
        if document.get("openapi"):
            return "openapi"
        if document.get("swagger"):
            return "swagger"
        info = document.get("info") or {}
        if isinstance(document.get("item"), list) and (
            "postman" in str(info.get("schema") or "").lower() or "collection" in str(info.get("schema") or "").lower()
        ):
            return "postman"
        if any(key in document for key in ("apiCollection", "apis", "requests", "apipost")):
            return "apipost"
    if isinstance(document, list):
        return "apipost"
    suffix = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    raise ImportSourceError(f"无法识别导入文件类型{('（.' + suffix + '）') if suffix else ''}")


def parse_import(content: bytes, *, source_hint: str = "auto", filename: str = "") -> tuple[str, list[dict[str, Any]]]:
    source_type = detect_source_type(content, source_hint, filename)
    try:
        if source_type == "har":
            raw_candidates = parse_har(content)
            candidates = [
                normalize_candidate(
                    source_type="har",
                    name=item.get("name"),
                    method=item.get("method"),
                    url=item.get("url"),
                    headers=item.get("headers"),
                    payload=item.get("payload"),
                    body_type=item.get("body_type"),
                    content_type=item.get("content_type"),
                    response_status=item.get("response_status"),
                    source_name=filename or "HAR",
                )
                for item in raw_candidates
            ]
        else:
            document = _load_document(content) if source_type != "curl" else None
            if source_type == "postman":
                candidates = _parse_postman(document)
            elif source_type == "openapi":
                candidates = _parse_openapi(document, False)
            elif source_type == "swagger":
                candidates = _parse_openapi(document, True)
            elif source_type == "curl":
                candidates = _parse_curl(content)
            else:
                candidates = _parse_apipost(document)
    except HarImportError as exc:
        raise ImportSourceError(str(exc)) from exc
    candidates = _deduplicate(candidates)
    if not candidates:
        raise ImportSourceError("导入源中没有可用的 HTTP 请求")
    return source_type, candidates


def candidate_from_case(case: Any) -> dict[str, Any]:
    return normalize_candidate(
        source_type="existing",
        name=case.name,
        method=case.method,
        url=case.url,
        headers=case.headers or {},
        payload=case.payload,
        body_type=case.body_type,
        content_type=case.content_type,
        source_name="existing",
    )
