"""
API Mock 服务路由

提供动态 Mock 接口，用于接口测试教学和练习
"""

import random
import string
from datetime import datetime, timezone
from typing import Dict, Any

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/mock", tags=["Mock服务"])

# 内存 Mock 存储
_mock_rules: Dict[str, dict] = {}


def _generate_mock_data(schema: dict) -> Any:
    """根据 schema 生成 Mock 数据"""
    stype = schema.get("type", "string")
    if stype == "string":
        return schema.get(
            "value",
            "mock_string_" + "".join(random.choices(string.ascii_lowercase, k=6)),
        )
    elif stype == "number":
        vmin, vmax = schema.get("min", 0), schema.get("max", 100)
        return schema.get("value", random.randint(vmin, vmax))
    elif stype == "boolean":
        return schema.get("value", random.choice([True, False]))
    elif stype == "array":
        count = schema.get("count", 3)
        item_schema = schema.get("items", {"type": "string"})
        return [_generate_mock_data(item_schema) for _ in range(count)]
    elif stype == "object":
        props = schema.get("properties", {})
        return {k: _generate_mock_data(v) for k, v in props.items()}
    elif stype == "uuid":
        import uuid

        return str(uuid.uuid4())
    elif stype == "timestamp":
        return int(datetime.now(timezone.utc).timestamp())
    elif stype == "email":
        return f"user{random.randint(1, 9999)}@test.com"
    elif stype == "phone":
        return f"1{random.randint(30, 99)}{random.randint(10000000, 99999999)}"
    return None


@router.post("/rules")
async def create_mock_rule(body: Dict[str, Any]):
    """创建 Mock 规则"""
    path = body.get("path", "").strip()
    if not path:
        raise HTTPException(status_code=400, detail="path 不能为空")
    method = body.get("method", "GET").upper()
    key = f"{method}:{path}"
    _mock_rules[key] = {
        "path": path,
        "method": method,
        "status_code": body.get("status_code", 200),
        "response_schema": body.get("response_schema", {}),
        "delay_ms": body.get("delay_ms", 0),
        "description": body.get("description", ""),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    return {"message": "Mock 规则已创建", "key": key}


@router.get("/rules")
async def list_mock_rules():
    """列出所有 Mock 规则"""
    return {"rules": list(_mock_rules.values())}


@router.delete("/rules/{rule_key:path}")
async def delete_mock_rule(rule_key: str):
    """删除 Mock 规则"""
    if rule_key in _mock_rules:
        del _mock_rules[rule_key]
        return {"message": "已删除"}
    raise HTTPException(status_code=404, detail="规则不存在")


@router.api_route("/api/{rest_of_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def mock_endpoint(request: Request, rest_of_path: str):
    """动态 Mock 端点 - 匹配规则并返回 Mock 数据"""
    method = request.method
    path = f"/api/{rest_of_path}"
    key = f"{method}:{path}"

    rule = _mock_rules.get(key)
    if not rule:
        # 尝试通配符匹配
        for rk, rv in _mock_rules.items():
            if rv["method"] == method and rv["path"].replace("*", "") in path:
                rule = rv
                break

    if not rule:
        return JSONResponse(
            status_code=404,
            content={"error": "No mock rule found", "path": path, "method": method},
        )

    # 模拟延迟
    delay = rule.get("delay_ms", 0)
    if delay > 0:
        import asyncio

        await asyncio.sleep(delay / 1000)

    data = _generate_mock_data(rule.get("response_schema", {}))
    return JSONResponse(status_code=rule.get("status_code", 200), content=data)
