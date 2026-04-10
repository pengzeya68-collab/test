from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Any
import json

from auto_test_platform.database import get_session
from auto_test_platform.models import ApiGroup, ApiCase

router = APIRouter(prefix="/import", tags=["导入导出"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB


async def _ensure_root_group(session: AsyncSession, name: str) -> int:
    result = await session.execute(select(ApiGroup).where(ApiGroup.name == name))
    group = result.scalar_one_or_none()
    if not group:
        group = ApiGroup(name=name, parent_id=0)
        session.add(group)
        await session.commit()
        await session.refresh(group)
    return group.id


def _safe_json_loads(text: str) -> Any:
    try:
        return json.loads(text)
    except Exception:
        return None


def _normalize_method(m: Any) -> str:
    m = (str(m or "GET")).strip().upper()
    if m not in {"GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"}:
        return "GET"
    return m


def _replace_path_params(path: str) -> str:
    # /users/{id} -> /users/{{id}}
    out = ""
    i = 0
    while i < len(path):
        if path[i] == "{" and "}" in path[i:]:
            j = path.find("}", i + 1)
            key = path[i + 1 : j].strip()
            if key:
                out += "{{" + key + "}}"
            else:
                out += "{}"
            i = j + 1
        else:
            out += path[i]
            i += 1
    return out


def _append_query_params(url: str, query_params: list[dict]) -> str:
    if not query_params:
        return url
    parts = []
    for p in query_params:
        name = str(p.get("name") or "").strip()
        if not name:
            continue
        parts.append(f"{name}={{{{{name}}}}}")
    if not parts:
        return url
    joiner = "&" if "?" in url else "?"
    return url + joiner + "&".join(parts)


def _make_default_assert_rules() -> dict:
    return {"status_code": 200}


def _extract_postman_cases(items: list, target_group_id: int) -> list[dict]:
    cases: list[dict] = []
    for item in items or []:
        if not isinstance(item, dict):
            continue

        # folder
        if isinstance(item.get("item"), list):
            cases.extend(_extract_postman_cases(item["item"], target_group_id))
            continue

        req = item.get("request")
        if not isinstance(req, dict):
            continue

        method = _normalize_method(req.get("method"))

        # url
        url = ""
        req_url = req.get("url")
        if isinstance(req_url, dict):
            url = req_url.get("raw") or ""
        elif isinstance(req_url, str):
            url = req_url
        url = str(url or "")

        name = str(item.get("name") or f"{method} {url}" or "未命名接口")

        # headers -> dict
        headers_dict: dict = {}
        for h in req.get("header") or []:
            if not isinstance(h, dict):
                continue
            k = str(h.get("key") or "").strip()
            if not k:
                continue
            headers_dict[k] = str(h.get("value") or "")

        # payload -> dict|None
        payload_obj = None
        body = req.get("body")
        if isinstance(body, dict):
            mode = body.get("mode")
            if mode == "raw":
                raw = body.get("raw") or ""
                parsed = _safe_json_loads(raw) if isinstance(raw, str) else None
                payload_obj = parsed if isinstance(parsed, dict) else None
            elif mode == "formdata":
                payload_obj = {}
                for fd in body.get("formdata") or []:
                    if not isinstance(fd, dict):
                        continue
                    k = str(fd.get("key") or "").strip()
                    if not k:
                        continue
                    payload_obj[k] = fd.get("value")

        cases.append(
            {
                "group_id": target_group_id,
                "name": name,
                "method": method,
                "url": url,
                "headers": headers_dict or None,
                "payload": payload_obj,
                "assert_rules": _make_default_assert_rules(),
                "description": None,
            }
        )
    return cases


def _schema_to_example(schema: Any) -> Any:
    """
    将 Swagger/OpenAPI schema 粗略转成一个“可编辑”的示例 payload。
    目标是稳定，不追求完全覆盖 schema 细节。
    """
    if not isinstance(schema, dict):
        return {}

    # OpenAPI 3: {"type":"object","properties":{...}}
    t = schema.get("type")
    if t == "object" or "properties" in schema:
        props = schema.get("properties") or {}
        out = {}
        if isinstance(props, dict):
            for k, v in props.items():
                if not k:
                    continue
                out[k] = _schema_to_example(v)
        return out

    if t == "array":
        items = schema.get("items") or {}
        return [_schema_to_example(items)]

    # primitive
    fmt = schema.get("format")
    if t in {"integer", "number"}:
        return 0
    if t == "boolean":
        return False
    if t == "string":
        if fmt in {"date-time"}:
            return "2026-01-01T00:00:00Z"
        return ""
    return {}


def _extract_swagger_cases(swagger_data: dict, target_group_id: int) -> list[dict]:
    """
    兼容 Swagger 2.0 / OpenAPI 3.x（JSON）
    """
    paths = swagger_data.get("paths") or {}
    if not isinstance(paths, dict) or not paths:
        raise HTTPException(status_code=400, detail="找不到 paths 节点，可能不是有效的 Swagger/OpenAPI JSON")

    # swagger2: basePath
    base_path = str(swagger_data.get("basePath") or "").strip()
    # openapi3: servers[0].url（只取 path 部分不做强依赖）
    servers = swagger_data.get("servers") or []
    server_url = ""
    if isinstance(servers, list) and servers:
        first = servers[0]
        if isinstance(first, dict):
            server_url = str(first.get("url") or "").strip()

    cases: list[dict] = []
    for raw_path, methods in paths.items():
        if not isinstance(methods, dict):
            continue

        path = _replace_path_params(str(raw_path))

        for m, details in methods.items():
            method = _normalize_method(m)
            if method not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
                continue
            if not isinstance(details, dict):
                details = {}

            summary = details.get("summary") or details.get("operationId") or f"{method} {raw_path}"
            name = str(summary)

            # 参数解析（swagger2: parameters; openapi3: parameters + requestBody）
            params = details.get("parameters") or []
            query_params: list[dict] = []
            header_params: list[dict] = []
            path_params: list[dict] = []
            body_schema = None
            form_params: list[dict] = []

            if isinstance(params, list):
                for p in params:
                    if not isinstance(p, dict):
                        continue
                    loc = p.get("in")
                    if loc == "query":
                        query_params.append(p)
                    elif loc == "header":
                        header_params.append(p)
                    elif loc == "path":
                        path_params.append(p)
                    elif loc == "formData":
                        form_params.append(p)
                    elif loc == "body":
                        body_schema = p.get("schema")

            # openapi3 requestBody
            if body_schema is None and isinstance(details.get("requestBody"), dict):
                rb = details["requestBody"]
                content = rb.get("content") or {}
                if isinstance(content, dict):
                    # 优先 application/json
                    json_ct = content.get("application/json")
                    if isinstance(json_ct, dict) and isinstance(json_ct.get("schema"), dict):
                        body_schema = json_ct.get("schema")
                    else:
                        # 兜底取任意一个
                        for _, v in content.items():
                            if isinstance(v, dict) and isinstance(v.get("schema"), dict):
                                body_schema = v.get("schema")
                                break

            # URL 拼接：默认用 {{base_url}}；如果 swagger 定义了 server_url 也不强行覆盖，避免破坏环境变量逻辑
            full_url = "{{base_url}}" + (base_path or "") + path
            full_url = _append_query_params(full_url, query_params)

            # headers：将 header 参数作为可编辑占位符
            headers: dict = {}
            for hp in header_params:
                n = str(hp.get("name") or "").strip()
                if not n:
                    continue
                headers[n] = "{{" + n + "}}"

            # payload：POST/PUT/PATCH 生成 body 示例；GET/DELETE 默认 None
            payload_obj = None
            if method in {"POST", "PUT", "PATCH"}:
                if form_params:
                    payload_obj = {}
                    for fp in form_params:
                        n = str(fp.get("name") or "").strip()
                        if not n:
                            continue
                        payload_obj[n] = "{{" + n + "}}"
                elif isinstance(body_schema, dict):
                    payload_obj = _schema_to_example(body_schema)
                else:
                    payload_obj = {}

            cases.append(
                {
                    "group_id": target_group_id,
                    "name": name,
                    "method": method,
                    "url": full_url,
                    "headers": headers or None,
                    "payload": payload_obj,
                    "assert_rules": _make_default_assert_rules(),
                    "description": None,
                }
            )

    return cases

@router.post("/postman")
async def import_postman(
    file: UploadFile = File(...),
    target_group_id: Optional[int] = Form(None),
    dry_run: bool = Form(False),
    session: AsyncSession = Depends(get_session)
):
    try:
        content = await file.read()
        if content and len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="文件过大，最大允许 10MB")
        collection = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"文件解析失败: {str(e)}")

    if "item" not in collection:
        raise HTTPException(status_code=400, detail="无效的 Postman Collection 格式")
        
    # 如果没有指定 group_id，默认使用或创建一个根分组
    if not target_group_id:
        target_group_id = await _ensure_root_group(session, "Postman 导入")

    cases = _extract_postman_cases(collection["item"], target_group_id)
    
    if dry_run:
        return {"cases": cases}
        
    db_cases = [ApiCase(**case_data) for case_data in cases]
    session.add_all(db_cases)
    await session.commit()
    return {"imported_count": len(db_cases), "message": "导入成功"}

@router.post("/swagger")
async def import_swagger(
    file: Optional[UploadFile] = File(None),
    url: Optional[str] = Form(None),
    target_group_id: Optional[int] = Form(None),
    dry_run: bool = Form(False),
    session: AsyncSession = Depends(get_session)
):
    import httpx
    
    swagger_data = None
    if file:
        content = await file.read()
        if content and len(content) > MAX_UPLOAD_BYTES:
            raise HTTPException(status_code=413, detail="文件过大，最大允许 10MB")
        try:
            swagger_data = json.loads(content.decode("utf-8"))
        except:
            raise HTTPException(status_code=400, detail="文件解析失败，请确保是合法的 JSON")
    elif url:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10.0)
                swagger_data = resp.json()
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"从 URL 获取失败: {str(e)}")
    else:
        raise HTTPException(status_code=400, detail="请提供文件或 URL")

    # 如果没有指定 group_id，默认使用或创建一个根分组
    if not target_group_id:
        target_group_id = await _ensure_root_group(session, "Swagger 导入")

    if not isinstance(swagger_data, dict):
        raise HTTPException(status_code=400, detail="Swagger/OpenAPI JSON 顶层必须是对象")

    cases = _extract_swagger_cases(swagger_data, target_group_id)

    if dry_run:
        return {"cases": cases}
        
    db_cases = [ApiCase(**case_data) for case_data in cases]
    session.add_all(db_cases)
    await session.commit()
    return {"imported_count": len(db_cases), "message": "导入成功"}