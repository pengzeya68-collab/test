"""
断言模板库路由

提供预置 + 用户自定义的断言模板，覆盖最常见的测试场景。
模板的 type/operator 严格对齐前端下拉选项，避免应用后显示空白。

type 取值: status_code / response_body / response_header / response_time
operator 取值: == / != / contains / not_contains / < / > / <= / >= / range / regex / not_empty / empty / exists / not_exists
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.database import get_db
from fastapi_backend.models.autotest import AssertTemplate
from fastapi_backend.models.models import User
from fastapi_backend.core.rbac import require_permissions

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/assert-templates", tags=["断言模板"])


# ========== 内置模板（type/operator 对齐前端下拉） ==========

BUILTIN_TEMPLATES = [
    {
        "id": "status_200",
        "category": "HTTP 状态码",
        "name": "状态码 = 200",
        "description": "验证响应状态码为 200 OK",
        "rules": [{"type": "status_code", "operator": "==", "expected": "200", "expression": ""}],
        "code_snippet": "assert response.status_code == 200",
    },
    {
        "id": "status_201",
        "category": "HTTP 状态码",
        "name": "状态码 = 201",
        "description": "验证响应状态码为 201 Created（常用于POST创建接口）",
        "rules": [{"type": "status_code", "operator": "==", "expected": "201", "expression": ""}],
        "code_snippet": "assert response.status_code == 201",
    },
    {
        "id": "status_not_500",
        "category": "HTTP 状态码",
        "name": "状态码 ≠ 500",
        "description": "验证服务端无内部错误",
        "rules": [{"type": "status_code", "operator": "!=", "expected": "500", "expression": ""}],
        "code_snippet": "assert response.status_code != 500",
    },
    {
        "id": "status_2xx",
        "category": "HTTP 状态码",
        "name": "状态码 2xx",
        "description": "验证状态码在 200-299 范围内",
        "rules": [{"type": "status_code", "operator": "range", "expected": "2xx", "expression": ""}],
        "code_snippet": "assert 200 <= response.status_code < 300",
    },
    {
        "id": "json_content_type",
        "category": "响应结构",
        "name": "响应头含 application/json",
        "description": "验证响应头 Content-Type 包含 application/json",
        "rules": [
            {
                "type": "response_header",
                "operator": "contains",
                "expected": "application/json",
                "expression": "Content-Type",
            }
        ],
        "code_snippet": 'assert "application/json" in response.headers["Content-Type"]',
    },
    {
        "id": "field_code_exists",
        "category": "响应结构",
        "name": "字段 code 存在",
        "description": "验证响应 JSON 中存在 code 字段",
        "rules": [
            {
                "type": "response_body",
                "operator": "exists",
                "expected": "",
                "expression": "$.code",
            }
        ],
        "code_snippet": 'assert "code" in response.json()',
    },
    {
        "id": "field_message_exists",
        "category": "响应结构",
        "name": "字段 message 存在",
        "description": "验证响应 JSON 中存在 message 字段",
        "rules": [
            {
                "type": "response_body",
                "operator": "exists",
                "expected": "",
                "expression": "$.message",
            }
        ],
        "code_snippet": 'assert "message" in response.json()',
    },
    {
        "id": "field_data_not_empty",
        "category": "响应结构",
        "name": "data 字段非空",
        "description": "验证响应 JSON 中 data 字段不为空",
        "rules": [
            {
                "type": "response_body",
                "operator": "not_empty",
                "expected": "",
                "expression": "$.data",
            }
        ],
        "code_snippet": 'assert response.json().get("data")',
    },
    {
        "id": "field_id_exists",
        "category": "响应结构",
        "name": "data.id 字段存在",
        "description": "验证响应中 data.id 字段存在（常用于创建接口）",
        "rules": [
            {
                "type": "response_body",
                "operator": "exists",
                "expected": "",
                "expression": "$.data.id",
            }
        ],
        "code_snippet": 'assert "id" in response.json().get("data", {})',
    },
    {
        "id": "list_not_empty",
        "category": "数据结构",
        "name": "列表非空检查",
        "description": "验证 data.list 列表字段不为空",
        "rules": [
            {
                "type": "response_body",
                "operator": "not_empty",
                "expected": "",
                "expression": "$.data.list",
            }
        ],
        "code_snippet": 'assert len(response.json()["data"]["list"]) > 0',
    },
    {
        "id": "code_equals_0",
        "category": "业务逻辑",
        "name": "code = 0（成功）",
        "description": "验证业务码 code 等于 0（表示成功）",
        "rules": [
            {
                "type": "response_body",
                "operator": "==",
                "expected": "0",
                "expression": "$.code",
            }
        ],
        "code_snippet": 'assert response.json()["code"] == 0',
    },
    {
        "id": "code_equals_200",
        "category": "业务逻辑",
        "name": "code = 200（成功）",
        "description": "验证业务码 code 等于 200（表示成功）",
        "rules": [
            {
                "type": "response_body",
                "operator": "==",
                "expected": "200",
                "expression": "$.code",
            }
        ],
        "code_snippet": 'assert response.json()["code"] == 200',
    },
    {
        "id": "response_time_2000",
        "category": "性能",
        "name": "响应时间 < 2000ms",
        "description": "验证接口响应时间在 2 秒以内",
        "rules": [{"type": "response_time", "operator": "<", "expected": "2000", "expression": ""}],
        "code_snippet": "assert response.elapsed.total_seconds() < 2.0",
    },
    {
        "id": "response_time_500",
        "category": "性能",
        "name": "响应时间 < 500ms",
        "description": "验证接口响应时间在 500ms 以内（严格性能要求）",
        "rules": [{"type": "response_time", "operator": "<", "expected": "500", "expression": ""}],
        "code_snippet": "assert response.elapsed.total_seconds() < 0.5",
    },
    {
        "id": "combo_basic",
        "category": "综合模板",
        "name": "基础检查（推荐）",
        "description": "状态码200 + 响应时间 < 2s",
        "rules": [
            {"type": "status_code", "operator": "==", "expected": "200", "expression": ""},
            {"type": "response_time", "operator": "<", "expected": "2000", "expression": ""},
        ],
        "code_snippet": "assert response.status_code == 200\nassert response.elapsed.total_seconds() < 2.0",
    },
    {
        "id": "combo_full",
        "category": "综合模板",
        "name": "完整检查（推荐）",
        "description": "状态码200 + Content-Type + code/message 存在 + 响应时间",
        "rules": [
            {"type": "status_code", "operator": "==", "expected": "200", "expression": ""},
            {
                "type": "response_header",
                "operator": "contains",
                "expected": "application/json",
                "expression": "Content-Type",
            },
            {"type": "response_body", "operator": "exists", "expected": "", "expression": "$.code"},
            {"type": "response_body", "operator": "exists", "expected": "", "expression": "$.message"},
            {"type": "response_time", "operator": "<", "expected": "2000", "expression": ""},
        ],
        "code_snippet": (
            "assert response.status_code == 200\n"
            'assert "application/json" in response.headers["Content-Type"]\n'
            "data = response.json()\n"
            'assert "code" in data\n'
            'assert "message" in data\n'
            "assert response.elapsed.total_seconds() < 2.0"
        ),
    },
]


# ========== Schemas ==========


class AssertTemplateRule(BaseModel):
    type: str = Field(..., description="status_code/response_body/response_header/response_time")
    operator: str = Field(
        ..., description="==/!=/contains/not_contains/</>/<=/>=/range/regex/not_empty/empty/exists/not_exists"
    )
    expected: str = Field("", description="期望值")
    expression: str = Field("", description="JSONPath 表达式或响应头名")


class AssertTemplateCreate(BaseModel):
    name: str = Field(..., max_length=128)
    description: Optional[str] = None
    category: str = Field("自定义", max_length=64)
    rules: List[AssertTemplateRule]
    code_snippet: Optional[str] = None


class AssertTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=64)
    rules: Optional[List[AssertTemplateRule]] = None
    code_snippet: Optional[str] = None


class AssertTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    category: str
    rules: list
    code_snippet: Optional[str] = None
    is_builtin: bool
    user_id: Optional[int] = None


# ========== 种子化 ==========


async def seed_builtin_templates(db: AsyncSession) -> None:
    """启动时若表为空，把内置模板插入为 is_builtin=True 的记录。"""
    count_stmt = select(func.count()).select_from(AssertTemplate)
    count = (await db.execute(count_stmt)).scalar_one()
    if count > 0:
        return

    for tpl in BUILTIN_TEMPLATES:
        db.add(
            AssertTemplate(
                name=tpl["name"],
                description=tpl["description"],
                category=tpl["category"],
                rules=tpl["rules"],
                code_snippet=tpl.get("code_snippet"),
                is_builtin=True,
                user_id=None,
            )
        )
    await db.commit()
    logger.info(f"已种子化 {len(BUILTIN_TEMPLATES)} 个内置断言模板")


# ========== 路由 ==========


@router.get("/categories")
async def get_assertion_categories(db: AsyncSession = Depends(get_db)):
    """获取断言模板分类"""
    stmt = select(AssertTemplate.category).distinct()
    result = await db.execute(stmt)
    cats = sorted({row[0] for row in result.fetchall()})
    return {"categories": cats}


@router.get("")
async def get_assertion_templates(
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """获取断言模板列表，可按分类筛选（内置 + 用户自定义）"""
    stmt = select(AssertTemplate).order_by(AssertTemplate.is_builtin.desc(), AssertTemplate.id)
    if category:
        stmt = stmt.where(AssertTemplate.category == category)
    result = await db.execute(stmt)
    rows = result.scalars().all()
    templates = [
        {
            "id": r.id,
            "name": r.name,
            "description": r.description,
            "category": r.category,
            "rules": r.rules or [],
            "code_snippet": r.code_snippet,
            "is_builtin": r.is_builtin,
            "user_id": r.user_id,
        }
        for r in rows
    ]
    return {"templates": templates, "total": len(templates)}


@router.post("")
async def create_assert_template(
    payload: AssertTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("case:execute")),
):
    """创建用户自定义断言模板"""
    tpl = AssertTemplate(
        name=payload.name,
        description=payload.description,
        category=payload.category or "自定义",
        rules=[r.model_dump() for r in payload.rules],
        code_snippet=payload.code_snippet,
        is_builtin=False,
        user_id=current_user.id,
    )
    db.add(tpl)
    await db.commit()
    await db.refresh(tpl)
    return {
        "id": tpl.id,
        "name": tpl.name,
        "description": tpl.description,
        "category": tpl.category,
        "rules": tpl.rules,
        "code_snippet": tpl.code_snippet,
        "is_builtin": tpl.is_builtin,
        "user_id": tpl.user_id,
    }


@router.put("/{tpl_id}")
async def update_assert_template(
    tpl_id: int,
    payload: AssertTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("case:execute")),
):
    """更新断言模板（内置模板不可改，自定义模板只能改自己的）"""
    tpl = await db.get(AssertTemplate, tpl_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="断言模板不存在")
    if tpl.is_builtin:
        raise HTTPException(status_code=400, detail="内置模板不可修改")
    if tpl.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能修改自己创建的模板")

    if payload.name is not None:
        tpl.name = payload.name
    if payload.description is not None:
        tpl.description = payload.description
    if payload.category is not None:
        tpl.category = payload.category
    if payload.rules is not None:
        tpl.rules = [r.model_dump() for r in payload.rules]
    if payload.code_snippet is not None:
        tpl.code_snippet = payload.code_snippet

    await db.commit()
    await db.refresh(tpl)
    return {"message": "更新成功", "id": tpl.id}


@router.delete("/{tpl_id}")
async def delete_assert_template(
    tpl_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permissions("case:execute")),
):
    """删除断言模板（内置不可删，自定义只能删自己的）"""
    tpl = await db.get(AssertTemplate, tpl_id)
    if not tpl:
        raise HTTPException(status_code=404, detail="断言模板不存在")
    if tpl.is_builtin:
        raise HTTPException(status_code=400, detail="内置模板不可删除")
    if tpl.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="只能删除自己创建的模板")

    await db.delete(tpl)
    await db.commit()
    return {"message": "删除成功", "id": tpl_id}
