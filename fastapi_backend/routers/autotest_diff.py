"""
API Diff 对比工具路由

对比两个环境的API响应差异
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List
import json

from fastapi_backend.core.autotest_database import get_autotest_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestCase
from fastapi_backend.models.models import User

router = APIRouter(prefix="/api/auto-test/diff", tags=["API-Diff"])


def _deep_diff(a: Any, b: Any, path: str = "") -> List[Dict]:
    """深度比较两个 JSON 对象，返回差异列表"""
    diffs = []

    # 类型比较：bool 和 int 视为不同类型，int 和 float 可比较
    if isinstance(a, bool) != isinstance(b, bool):
        diffs.append({"path": path or "$", "type": "type_changed", "from": type(a).__name__, "to": type(b).__name__})
        return diffs
    if isinstance(a, (int, float)) != isinstance(b, (int, float)):
        diffs.append({"path": path or "$", "type": "type_changed", "from": type(a).__name__, "to": type(b).__name__})
        return diffs
    if not isinstance(a, (int, float)) and type(a) != type(b):
        diffs.append({"path": path or "$", "type": "type_changed", "from": type(a).__name__, "to": type(b).__name__})
        return diffs

    if isinstance(a, dict):
        a_keys = set(a.keys())
        b_keys = set(b.keys())
        for k in a_keys - b_keys:
            diffs.append({"path": f"{path}.{k}" if path else k, "type": "removed", "from": a[k], "to": None})
        for k in b_keys - a_keys:
            diffs.append({"path": f"{path}.{k}" if path else k, "type": "added", "from": None, "to": b[k]})
        for k in a_keys & b_keys:
            diffs.extend(_deep_diff(a[k], b[k], f"{path}.{k}" if path else str(k)))
    elif isinstance(a, list):
        for i in range(min(len(a), len(b))):
            diffs.extend(_deep_diff(a[i], b[i], f"{path}[{i}]"))
        if len(a) > len(b):
            for i in range(len(b), len(a)):
                diffs.append({"path": f"{path}[{i}]", "type": "removed", "from": a[i], "to": None})
        elif len(b) > len(a):
            for i in range(len(a), len(b)):
                diffs.append({"path": f"{path}[{i}]", "type": "added", "from": None, "to": b[i]})
    else:
        if a != b:
            diffs.append({"path": path or "$", "type": "value_changed", "from": a, "to": b})

    return diffs


@router.post("/compare")
async def compare_responses(
    body: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
):
    """
    比较两个 JSON 响应的差异

    Request: {"response_a": {...}, "response_b": {...}}
    Response: {"diffs": [...], "total": N, "has_changes": bool}
    """
    a = body.get("response_a")
    b = body.get("response_b")
    if a is None or b is None:
        raise HTTPException(400, "请提供 response_a 和 response_b")

    if isinstance(a, str):
        try:
            a = json.loads(a)
        except (json.JSONDecodeError, TypeError):
            raise HTTPException(status_code=400, detail="请求体A不是有效的JSON")
    if isinstance(b, str):
        try:
            b = json.loads(b)
        except (json.JSONDecodeError, TypeError):
            raise HTTPException(status_code=400, detail="请求体B不是有效的JSON")

    diffs = _deep_diff(a, b)
    return {
        "diffs": diffs,
        "total": len(diffs),
        "has_changes": len(diffs) > 0,
        "summary": {
            "added": sum(1 for d in diffs if d["type"] == "added"),
            "removed": sum(1 for d in diffs if d["type"] == "removed"),
            "value_changed": sum(1 for d in diffs if d["type"] == "value_changed"),
            "type_changed": sum(1 for d in diffs if d["type"] == "type_changed"),
        },
    }


@router.get("/cases")
async def list_diffable_cases(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_autotest_db),
):
    """列出可进行 Diff 对比的接口用例"""
    result = await db.execute(
        select(AutoTestCase)
        .where(
            AutoTestCase.user_id == current_user.id,
        )
        .limit(50)
    )
    cases = result.scalars().all()
    return {"cases": [{"id": c.id, "name": c.name, "method": c.method, "url": c.url} for c in cases]}
