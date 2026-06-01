"""
AutoTest 路由 - AI 智能生成测试用例

路径前缀: /api/auto-test/ai-generate
功能: 从 Swagger/OpenAPI 文档自动分析接口，利用 AI 生成完整测试用例
"""

import json
import logging

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.autotest import AutoTestCase, AutoTestGroup, AutoTestScenario, AutoTestScenarioStep
from fastapi_backend.services.autotest_ai_generator import AITestCaseGenerator

_logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/auto-test/ai-generate",
    tags=["AutoTest-AI生成用例"],
    dependencies=[Depends(get_current_user)],
)


@router.post("/from-swagger")
async def generate_from_swagger(
    file: UploadFile = File(...),
    max_cases_per_api: int = Form(3),
    include_boundary: bool = Form(True),
    include_auth: bool = Form(True),
    include_chain: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    """
    从 Swagger/OpenAPI 文件 AI 生成测试用例（预览模式）

    返回生成的用例列表和场景链，不写入数据库。用户确认后调用 /confirm 导入。
    """
    content = await file.read()
    try:
        swagger_data = json.loads(content.decode("utf-8"))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {str(e)}")

    generator = AITestCaseGenerator(db)
    result = await generator.generate(
        swagger_data,
        {
            "max_cases_per_api": max_cases_per_api,
            "include_boundary": include_boundary,
            "include_auth": include_auth,
            "include_chain": include_chain,
        },
    )

    return {
        "cases": result.get("cases", []),
        "scenarios": result.get("scenarios", []),
        "message": result.get("message", f"生成完成，共 {len(result.get('cases', []))} 个用例"),
        "total": len(result.get("cases", [])),
    }


@router.post("/from-swagger-url")
async def generate_from_swagger_url(
    url: str = Form(...),
    max_cases_per_api: int = Form(3),
    include_boundary: bool = Form(True),
    include_auth: bool = Form(True),
    include_chain: bool = Form(True),
    db: AsyncSession = Depends(get_db),
):
    """
    从 Swagger URL AI 生成测试用例（预览模式）

    自动拉取远程 Swagger 文档并生成用例。
    """
    import httpx

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            swagger_data = resp.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"获取 Swagger 文档失败: {str(e)}")

    generator = AITestCaseGenerator(db)
    result = await generator.generate(
        swagger_data,
        {
            "max_cases_per_api": max_cases_per_api,
            "include_boundary": include_boundary,
            "include_auth": include_auth,
            "include_chain": include_chain,
        },
    )

    return {
        "cases": result.get("cases", []),
        "scenarios": result.get("scenarios", []),
        "message": result.get("message", f"生成完成，共 {len(result.get('cases', []))} 个用例"),
        "total": len(result.get("cases", [])),
    }


@router.post("/confirm")
async def confirm_import(
    data: dict,
    db: AsyncSession = Depends(get_db),
):
    """
    确认导入 AI 生成的测试用例到数据库

    请求体:
    {
        "cases": [...],           # 要导入的用例列表
        "scenarios": [...],       # 要导入的场景链（可选）
        "group_name": "AI生成"    # 目标分组名（可选，默认 "AI生成用例"）
    }
    """
    cases = data.get("cases", [])
    scenarios = data.get("scenarios", [])
    group_name = data.get("group_name", "AI生成用例")

    if not isinstance(cases, list) or not cases:
        raise HTTPException(status_code=400, detail="cases 必须是非空列表")
    if scenarios and not isinstance(scenarios, list):
        raise HTTPException(status_code=400, detail="scenarios 必须是列表")

    # 找到或创建根分组
    result = await db.execute(
        select(AutoTestGroup).where(
            AutoTestGroup.name == group_name,
            AutoTestGroup.parent_id.is_(None),
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        group = AutoTestGroup(name=group_name, parent_id=None)
        db.add(group)
        await db.flush()

    # 按接口分组创建子分组
    api_groups = {}
    created_cases = []

    for case_data in cases:
        # 提取接口标签作为子分组
        tag = case_data.get("tag", "")
        if not tag:
            url = case_data.get("url", "")
            # 从 URL 提取第一段路径作为分组
            path_parts = [p for p in url.split("/") if p and not p.startswith("{{") and not p.startswith("http")]
            tag = path_parts[0] if path_parts else "其他"

        if tag not in api_groups:
            sub_result = await db.execute(
                select(AutoTestGroup).where(
                    AutoTestGroup.name == tag,
                    AutoTestGroup.parent_id == group.id,
                )
            )
            sub_group = sub_result.scalar_one_or_none()
            if not sub_group:
                sub_group = AutoTestGroup(name=tag, parent_id=group.id)
                db.add(sub_group)
                await db.flush()
            api_groups[tag] = sub_group

        sub_group = api_groups[tag]

        # 解析 headers
        headers = case_data.get("headers")
        if isinstance(headers, str):
            try:
                headers = json.loads(headers)
            except Exception:
                headers = None

        # 解析 payload
        payload = case_data.get("payload")
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = None

        # 解析 assert_rules
        assert_rules = case_data.get("assert_rules")
        if isinstance(assert_rules, str):
            try:
                assert_rules = json.loads(assert_rules)
            except Exception:
                assert_rules = None

        # 解析 extractors
        extractors = case_data.get("extractors")
        if isinstance(extractors, str):
            try:
                extractors = json.loads(extractors)
            except Exception:
                extractors = None

        case = AutoTestCase(
            group_id=sub_group.id,
            name=case_data.get("name", "未命名用例"),
            method=case_data.get("method", "GET"),
            url=case_data.get("url", ""),
            headers=headers,
            payload=payload,
            body_type="raw" if payload else "none",
            content_type="application/json",
            assert_rules=assert_rules,
            extractors=extractors,
            description=case_data.get("description", ""),
        )
        db.add(case)
        await db.flush()
        created_cases.append(case)

    # 导入场景链
    created_scenarios = []
    if scenarios:
        for scenario_data in scenarios:
            scenario = AutoTestScenario(
                name=scenario_data.get("name", "AI生成场景"),
                description=scenario_data.get("description", ""),
            )
            db.add(scenario)
            await db.flush()

            for step_idx, step_data in enumerate(scenario_data.get("steps", [])):
                api_index = int(step_data.get("api_index", 0))
                linked_case = created_cases[api_index] if 0 <= api_index < len(created_cases) else None

                step = AutoTestScenarioStep(
                    scenario_id=scenario.id,
                    api_case_id=linked_case.id if linked_case else None,
                    step_order=step_idx,
                    variable_overrides=step_data.get("use_variables"),
                )
                db.add(step)

            created_scenarios.append(scenario)

    await db.commit()

    return {
        "message": f"导入成功：{len(created_cases)} 个用例，{len(created_scenarios)} 个场景",
        "imported_cases": len(created_cases),
        "imported_scenarios": len(created_scenarios),
        "group_name": group_name,
    }
