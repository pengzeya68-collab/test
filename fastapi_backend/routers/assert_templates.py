"""
断言模板库路由

提供预置的断言模板，覆盖最常见的测试场景
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/assert-templates", tags=["断言模板"])

# 预置断言模板
ASSERTION_TEMPLATES = [
    {
        "id": "status_200",
        "category": "HTTP 状态码",
        "name": "状态码 = 200",
        "description": "验证响应状态码为 200 OK",
        "rules": [{"type": "status_code", "operator": "eq", "expected": 200}],
        "code_snippet": """# Pytest 断言示例
assert response.status_code == 200""",
    },
    {
        "id": "status_201",
        "category": "HTTP 状态码",
        "name": "状态码 = 201",
        "description": "验证响应状态码为 201 Created（常用于POST创建接口）",
        "rules": [{"type": "status_code", "operator": "eq", "expected": 201}],
        "code_snippet": """assert response.status_code == 201""",
    },
    {
        "id": "status_not_500",
        "category": "HTTP 状态码",
        "name": "状态码 ≠ 500",
        "description": "验证服务端无内部错误",
        "rules": [{"type": "status_code", "operator": "neq", "expected": 500}],
        "code_snippet": """assert response.status_code != 500""",
    },
    {
        "id": "json_valid",
        "category": "响应结构",
        "name": "响应为合法 JSON",
        "description": "验证响应体是合法的 JSON 格式",
        "rules": [
            {
                "type": "content_type",
                "operator": "contains",
                "expected": "application/json",
            }
        ],
        "code_snippet": """import json
data = response.json()  # 如果抛出异常则断言失败""",
    },
    {
        "id": "field_exists",
        "category": "响应结构",
        "name": "字段存在性检查",
        "description": "验证响应 JSON 中包含指定字段（如 id, code, message）",
        "rules": [
            {
                "type": "json_field_exists",
                "operator": "contains",
                "expected": "id,code,message",
            }
        ],
        "code_snippet": """data = response.json()
assert "id" in data
assert "code" in data
assert "message" in data""",
    },
    {
        "id": "field_not_null",
        "category": "响应结构",
        "name": "字段非空检查",
        "description": "验证响应中关键字段不为 null/空列表/空字符串",
        "rules": [{"type": "json_field_not_null", "operator": "neq", "expected": "null"}],
        "code_snippet": """data = response.json()
assert data.get("id") is not None
assert len(data.get("list", [])) > 0""",
    },
    {
        "id": "response_time",
        "category": "性能",
        "name": "响应时间 < 2000ms",
        "description": "验证接口响应时间在 2 秒以内",
        "rules": [{"type": "response_time", "operator": "lt", "expected": 2000}],
        "code_snippet": """assert response.elapsed.total_seconds() < 2.0""",
    },
    {
        "id": "response_time_500",
        "category": "性能",
        "name": "响应时间 < 500ms",
        "description": "验证接口响应时间在 500ms 以内（严格性能要求）",
        "rules": [{"type": "response_time", "operator": "lt", "expected": 500}],
        "code_snippet": """assert response.elapsed.total_seconds() < 0.5""",
    },
    {
        "id": "array_not_empty",
        "category": "数据结构",
        "name": "列表非空检查",
        "description": "验证列表接口返回不为空数组",
        "rules": [{"type": "json_array_length", "operator": "gt", "expected": 0}],
        "code_snippet": """data = response.json()
assert isinstance(data.get("list", []), list)
assert len(data["list"]) > 0""",
    },
    {
        "id": "array_length",
        "category": "数据结构",
        "name": "列表长度检查",
        "description": "验证分页接口返回指定数量的数据（page_size）",
        "rules": [{"type": "json_array_length", "operator": "eq", "expected": 10}],
        "code_snippet": """data = response.json()
assert len(data["list"]) == 10  # page_size""",
    },
    {
        "id": "pagination",
        "category": "业务逻辑",
        "name": "分页字段完整性",
        "description": "验证分页接口返回 total/page/page_size 等标准字段",
        "rules": [
            {
                "type": "json_field_exists",
                "operator": "contains",
                "expected": "total,page,page_size",
            },
            {"type": "json_field_type", "operator": "eq", "expected": "int"},
        ],
        "code_snippet": """data = response.json()
assert "total" in data
assert "page" in data
assert "page_size" in data
assert isinstance(data["total"], int)""",
    },
    {
        "id": "error_response",
        "category": "业务逻辑",
        "name": "错误响应格式检查",
        "description": "验证失败时返回标准的错误信息（code/message）",
        "rules": [
            {
                "type": "json_field_exists",
                "operator": "contains",
                "expected": "code,message",
            }
        ],
        "code_snippet": """data = response.json()
assert "code" in data, "缺少错误码"
assert "message" in data, "缺少错误信息"
assert data["code"] != 0, "错误码不应为0""",
    },
    {
        "id": "field_type_check",
        "category": "数据结构",
        "name": "字段类型校验",
        "description": "验证关键字段的数据类型正确（id为int, name为str, price为float）",
        "rules": [{"type": "json_field_type", "operator": "eq", "expected": "id:int,name:str"}],
        "code_snippet": """data = response.json()
assert isinstance(data["id"], int)
assert isinstance(data["name"], str)
assert isinstance(data.get("price"), (int, float))""",
    },
    {
        "id": "field_value_range",
        "category": "业务逻辑",
        "name": "字段取值范围",
        "description": "验证字段值在合理范围内（如 status 在指定枚举中）",
        "rules": [{"type": "json_field_in", "operator": "in", "expected": "active,inactive"}],
        "code_snippet": """data = response.json()
valid_status = ["active", "inactive", "pending"]
assert data["status"] in valid_status""",
    },
    {
        "id": "combo_template",
        "category": "综合模板",
        "name": "完整检查（推荐）",
        "description": "综合验证：状态码200 + JSON合法 + 字段存在 + 响应时间",
        "rules": [
            {"type": "status_code", "operator": "eq", "expected": 200},
            {
                "type": "content_type",
                "operator": "contains",
                "expected": "application/json",
            },
            {
                "type": "json_field_exists",
                "operator": "contains",
                "expected": "code,message",
            },
            {"type": "response_time", "operator": "lt", "expected": 2000},
        ],
        "code_snippet": """# 完整测试断言
assert response.status_code == 200
assert "application/json" in response.headers["Content-Type"]
data = response.json()
assert "code" in data
assert "message" in data
assert response.elapsed.total_seconds() < 2.0""",
    },
]


@router.get("/categories")
async def get_assertion_categories():
    """获取断言模板分类"""
    cats = list(set(t["category"] for t in ASSERTION_TEMPLATES))
    return {"categories": sorted(cats)}


@router.get("")
async def get_assertion_templates(category: str = None):
    """获取断言模板列表，可按分类筛选"""
    templates = ASSERTION_TEMPLATES
    if category:
        templates = [t for t in templates if t["category"] == category]
    return {"templates": templates, "total": len(templates)}
