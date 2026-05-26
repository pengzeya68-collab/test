"""
AutoTest JMeter 导出/导入路由

功能：
1. 将接口用例/场景导出为 JMeter .jmx 文件
2. 解析 JMeter .jmx 文件并导入为接口用例
"""
import io
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi.responses import StreamingResponse

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_user
from fastapi_backend.models.autotest import (
    AutoTestCase,
    AutoTestScenario,
    AutoTestScenarioStep,
)
from fastapi_backend.services.autotest_jmeter_service import (
    export_cases_to_jmx,
    import_jmx_to_cases,
)

router = APIRouter(prefix="/api/auto-test", tags=["AutoTest-JMeter"], dependencies=[Depends(get_current_user)])


async def _resolve_group_id(db: AsyncSession, group_id: Optional[int]) -> int:
    from fastapi_backend.models.autotest import AutoTestGroup

    if group_id is not None:
        group_result = await db.execute(select(AutoTestGroup.id).where(AutoTestGroup.id == group_id))
        if group_result.scalar_one_or_none() is not None:
            return group_id
        raise HTTPException(status_code=404, detail="目标分组不存在")

    default_name = "JMeter Import"
    group_result = await db.execute(
        select(AutoTestGroup).where(AutoTestGroup.name == default_name, AutoTestGroup.parent_id.is_(None))
    )
    group = group_result.scalar_one_or_none()
    if not group:
        group = AutoTestGroup(name=default_name, parent_id=None)
        db.add(group)
        await db.flush()
    return group.id


@router.get("/export/jmeter/case/{case_id}")
@router.post("/export/jmeter/case/{case_id}")
async def export_case_to_jmeter(
    case_id: int,
    thread_group_config: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    将单个接口用例导出为 JMeter .jmx 文件
    
    Args:
        case_id: 用例ID
        thread_group_config: 线程组配置（可选）
            - num_threads: 线程数
            - ramp_time: ramp-up 时间（秒）
            - loop_count: 循环次数
            - duration: 持续时间（秒）
    """
    # 查询用例
    result = await db.execute(select(AutoTestCase).where(AutoTestCase.id == case_id))
    case = result.scalar_one_or_none()
    if not case:
        raise HTTPException(status_code=404, detail="用例不存在")
    
    # 转换为字典
    case_dict = _case_to_dict(case)
    
    # 生成 JMeter XML
    jmx_content = export_cases_to_jmx(
        cases=[case_dict],
        test_plan_name=f"TestMaster - {case.name}",
        thread_group_config=thread_group_config,
    )
    
    # 返回文件
    filename = f"{case.name.replace('/', '_').replace(' ', '_')}.jmx"
    return _create_jmx_response(jmx_content, filename)


@router.post("/export/jmeter/cases")
async def export_cases_to_jmeter(
    payload: Any = Body(default=None),
    thread_group_config: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    将多个接口用例导出为 JMeter .jmx 文件
    兼容两种前端协议：
    1. 直接传 [1,2,3]
    2. 传 { case_ids: [...], group_id: 1, thread_group_config: {...} }
    """
    case_ids: List[int] = []
    group_id: Optional[int] = None

    if isinstance(payload, list):
        case_ids = [int(case_id) for case_id in payload]
    elif isinstance(payload, dict):
        raw_case_ids = payload.get("case_ids") or []
        if raw_case_ids:
            case_ids = [int(case_id) for case_id in raw_case_ids]
        group_id = payload.get("group_id")
        thread_group_config = payload.get("thread_group_config") or thread_group_config

    if not case_ids and group_id is not None:
        result = await db.execute(select(AutoTestCase).where(AutoTestCase.group_id == group_id))
        group_cases = result.scalars().all()
        case_ids = [case.id for case in group_cases]

    if not case_ids:
        raise HTTPException(status_code=400, detail="请提供 case_ids 或 group_id")

    # 查询用例
    result = await db.execute(select(AutoTestCase).where(AutoTestCase.id.in_(case_ids)))
    cases = result.scalars().all()

    if not cases:
        raise HTTPException(status_code=404, detail="未找到用例")

    case_dicts = [_case_to_dict(case) for case in cases]

    jmx_content = export_cases_to_jmx(
        cases=case_dicts,
        test_plan_name="TestMaster - Batch Export",
        thread_group_config=thread_group_config,
    )

    filename = f"TestMaster_Export_{len(cases)}_cases.jmx"
    return _create_jmx_response(jmx_content, filename)


@router.get("/export/jmeter/cases")
async def export_cases_to_jmeter_get(
    case_ids: Optional[List[int]] = None,
    group_id: Optional[int] = None,
    thread_group_config: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    GET 兼容入口，支持 query 参数导出
    """
    if not case_ids and group_id is not None:
        result = await db.execute(select(AutoTestCase).where(AutoTestCase.group_id == group_id))
        group_cases = result.scalars().all()
        case_ids = [case.id for case in group_cases]

    if not case_ids:
        raise HTTPException(status_code=400, detail="请提供 case_ids 或 group_id")

    result = await db.execute(select(AutoTestCase).where(AutoTestCase.id.in_(case_ids)))
    cases = result.scalars().all()
    
    if not cases:
        raise HTTPException(status_code=404, detail="未找到用例")
    
    # 转换为字典
    case_dicts = [_case_to_dict(case) for case in cases]
    
    parsed_thread_group_config = None
    if thread_group_config:
        try:
            parsed_thread_group_config = json.loads(thread_group_config)
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="thread_group_config 格式错误，必须是 JSON 字符串") from exc

    # 生成 JMeter XML
    jmx_content = export_cases_to_jmx(
        cases=case_dicts,
        test_plan_name="TestMaster - Batch Export",
        thread_group_config=parsed_thread_group_config,
    )
    
    # 返回文件
    filename = f"TestMaster_Export_{len(cases)}_cases.jmx"
    return _create_jmx_response(jmx_content, filename)


@router.post("/export/jmeter/scenario/{scenario_id}")
async def export_scenario_to_jmeter(
    scenario_id: int,
    thread_group_config: Optional[Dict[str, Any]] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    将测试场景导出为 JMeter .jmx 文件
    
    Args:
        scenario_id: 场景ID
        thread_group_config: 线程组配置（可选）
    """
    # 查询场景和步骤
    result = await db.execute(
        select(AutoTestScenario)
        .where(AutoTestScenario.id == scenario_id)
        .options(
            selectinload(AutoTestScenario.steps).selectinload(AutoTestScenarioStep.api_case)
        )
    )
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="场景不存在")
    
    # 获取场景的所有步骤（按 step_order 排序）
    steps = sorted(scenario.steps, key=lambda s: s.step_order)
    
    # 转换为字典
    case_dicts = []
    for step in steps:
        if step.api_case:
            case_dict = _case_to_dict(step.api_case)
            case_dicts.append(case_dict)
    
    if not case_dicts:
        raise HTTPException(status_code=400, detail="场景中没有可用的接口用例")
    
    # 生成 JMeter XML
    jmx_content = export_cases_to_jmx(
        cases=case_dicts,
        test_plan_name=f"TestMaster - {scenario.name}",
        thread_group_config=thread_group_config,
    )
    
    # 返回文件
    filename = f"{scenario.name.replace('/', '_').replace(' ', '_')}.jmx"
    return _create_jmx_response(jmx_content, filename)


@router.post("/import/jmeter")
async def import_jmeter_file(
    file: UploadFile = File(...),
    group_id: Optional[int] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    导入 JMeter .jmx 文件，解析并创建接口用例
    
    Args:
        file: JMeter .jmx 文件
        group_id: 导入到的分组ID（可选）
    
    Returns:
        导入的用例列表
    """
    # 验证文件类型
    if not file.filename.endswith(".jmx"):
        raise HTTPException(status_code=400, detail="只支持 .jmx 文件")
    
    # 读取文件内容
    content = await file.read()
    xml_content = content.decode("UTF-8")
    
    # 解析 JMeter XML
    cases = import_jmx_to_cases(xml_content)
    
    if not cases:
        raise HTTPException(status_code=400, detail="未能从文件中解析出接口用例")
    
    target_group_id = await _resolve_group_id(db, group_id)

    # 保存到数据库
    created_cases = []
    for case_data in cases:
        case = AutoTestCase(
            group_id=target_group_id,
            name=case_data.get("name", "Imported Case"),
            method=case_data.get("method", "GET"),
            url=case_data.get("url", ""),
            headers=case_data.get("headers"),
            params=case_data.get("params"),
            body_type=case_data.get("body_type", "none"),
            content_type="application/json" if case_data.get("headers", {}).get("Content-Type") else None,
            payload=case_data.get("payload"),
            assert_rules=case_data.get("assert_rules"),
            extractors=case_data.get("extractors"),
            description=case_data.get("description"),
        )
        db.add(case)
        created_cases.append(case)
    
    await db.commit()
    
    # 返回创建的用例
    result = []
    for case in created_cases:
        await db.refresh(case)
        result.append({
            "id": case.id,
            "name": case.name,
            "method": case.method,
            "url": case.url,
        })
    
    return {
        "message": f"成功导入 {len(result)} 个接口用例",
        "cases": result,
    }


def _case_to_dict(case: AutoTestCase) -> Dict[str, Any]:
    """将 AutoTestCase 对象转换为字典"""
    return {
        "name": case.name,
        "method": case.method,
        "url": case.url,
        "headers": case.headers if isinstance(case.headers, dict) else (json.loads(case.headers) if case.headers else {}),
        "params": case.params if isinstance(case.params, dict) else (json.loads(case.params) if case.params else {}),
        "body_type": case.body_type or "none",
        "payload": case.payload if isinstance(case.payload, dict) else (json.loads(case.payload) if case.payload else {}),
        "assert_rules": case.assert_rules if isinstance(case.assert_rules, (dict, list)) else (json.loads(case.assert_rules) if case.assert_rules else []),
        "extractors": case.extractors if isinstance(case.extractors, list) else (json.loads(case.extractors) if case.extractors else []),
    }


def _create_jmx_response(jmx_content: str, filename: str) -> StreamingResponse:
    """创建 JMeter .jmx 文件响应"""
    # 创建文件流
    file_stream = io.BytesIO(jmx_content.encode("UTF-8"))
    
    # 返回文件响应
    return StreamingResponse(
        file_stream,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )
