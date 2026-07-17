from copy import deepcopy
from typing import Any, Dict
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi_backend.utils.encryption import decrypt, encrypt


_PREFIX = "enc:v1:"
_MASK = "******"
_AUTH_SECRET_FIELDS = {"token", "password", "value"}


def _encrypt_value(value: Any) -> Any:
    if value in (None, "", _MASK):
        return value
    text = str(value)
    if text.startswith(_PREFIX):
        return text
    return _PREFIX + encrypt(text)


def _decrypt_value(value: Any) -> Any:
    if not isinstance(value, str) or not value.startswith(_PREFIX):
        return value
    return decrypt(value[len(_PREFIX):])


def protect_request_config(config: Dict[str, Any] | None) -> Dict[str, Any]:
    result = deepcopy(config or {})
    auth = result.get("auth")
    if isinstance(auth, dict):
        for field in _AUTH_SECRET_FIELDS:
            if field in auth:
                auth[field] = _encrypt_value(auth[field])
    cookies = result.get("cookies")
    if isinstance(cookies, dict):
        result["cookies"] = {key: _encrypt_value(value) for key, value in cookies.items()}
    return result


def reveal_request_config(config: Dict[str, Any] | None) -> Dict[str, Any]:
    result = deepcopy(config or {})
    auth = result.get("auth")
    if isinstance(auth, dict):
        for field in _AUTH_SECRET_FIELDS:
            if field in auth:
                auth[field] = _decrypt_value(auth[field])
    cookies = result.get("cookies")
    if isinstance(cookies, dict):
        result["cookies"] = {key: _decrypt_value(value) for key, value in cookies.items()}
    return result


def mask_request_config(config: Dict[str, Any] | None) -> Dict[str, Any]:
    result = reveal_request_config(config)
    auth = result.get("auth")
    if isinstance(auth, dict):
        for field in _AUTH_SECRET_FIELDS:
            if auth.get(field) not in (None, ""):
                auth[field] = _MASK
    cookies = result.get("cookies")
    if isinstance(cookies, dict):
        result["cookies"] = {key: _MASK for key in cookies}
    return result


def merge_request_config(existing: Dict[str, Any] | None, incoming: Dict[str, Any] | None) -> Dict[str, Any]:
    base = reveal_request_config(existing)

    def merge(left, right):
        if not isinstance(left, dict) or not isinstance(right, dict):
            return left if right == _MASK else deepcopy(right)
        result = deepcopy(left)
        for key, value in right.items():
            result[key] = merge(result.get(key), value) if key in result else deepcopy(value)
        return result

    return protect_request_config(merge(base, incoming or {}))


def sanitize_request_headers(headers: Dict[str, Any] | None, config: Dict[str, Any] | None = None) -> Dict[str, Any]:
    sensitive = {"authorization", "proxy-authorization", "cookie", "set-cookie", "x-api-key", "api-key"}
    auth = (config or {}).get("auth") if isinstance((config or {}).get("auth"), dict) else {}
    if auth.get("type") == "api_key" and (auth.get("in") or auth.get("location") or "header") == "header":
        sensitive.add(str(auth.get("key") or "").lower())
    return {key: (_MASK if key.lower() in sensitive else value) for key, value in (headers or {}).items()}


def sanitize_request_url(url: str) -> str:
    parts = urlsplit(url or "")
    sensitive = {"token", "access_token", "api_key", "apikey", "key", "secret", "password"}
    query = urlencode([(key, _MASK if key.lower() in sensitive else value) for key, value in parse_qsl(parts.query, keep_blank_values=True)])
    return urlunsplit(parts._replace(query=query))
