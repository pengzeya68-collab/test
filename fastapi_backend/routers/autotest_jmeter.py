"""
AutoTest JMeter 导出/导入路由

功能：
1. 将接口用例/场景导出为 JMeter .jmx 文件
2. 解析 JMeter .jmx 文件并导入为接口用例
"""

import io
import json
from typing import List, Optional, Dict, Any
from urllib.parse import quote
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Form, Request
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi.responses import StreamingResponse

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import (
    AutoTestCase,
    AutoTestScenario,
    AutoTestScenarioStep,
)
from fastapi_backend.models.models import User
from fastapi_backend.services.autotest_jmeter_service import (
    export_cases_to_jmx,
    import_jmx_to_cases,
    import_jmx_to_full_tree,
)
from fastapi_backend.core.ssrf_guard import validate_url_safety
from fastapi_backend.deps.ai_points import require_ai_points

router = APIRouter(prefix="/api/auto-test", tags=["AutoTest-JMeter"])


async def _resolve_group_id(db: AsyncSession, group_id: Optional[int], user_id: int) -> int:
    from fastapi_backend.models.autotest import AutoTestGroup

    if group_id is not None:
        group_result = await db.execute(
            select(AutoTestGroup.id).where(AutoTestGroup.id == group_id, AutoTestGroup.user_id == user_id)
        )
        if group_result.scalar_one_or_none() is not None:
            return group_id
        raise HTTPException(status_code=404, detail="目标分组不存在")

    default_name = "JMeter Import"
    group_result = await db.execute(
        select(AutoTestGroup).where(
            AutoTestGroup.name == default_name, AutoTestGroup.parent_id.is_(None), AutoTestGroup.user_id == user_id
        )
    )
    group = group_result.scalar_one_or_none()
    if not group:
        group = AutoTestGroup(name=default_name, parent_id=None, user_id=user_id)
        db.add(group)
        await db.flush()
    return group.id


@router.post("/export/jmeter/case/{case_id}")
async def export_case_to_jmeter(
    case_id: int,
    thread_group_config: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(get_current_active_user),
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
    result = await db.execute(
        select(AutoTestCase).where(AutoTestCase.id == case_id, AutoTestCase.user_id == current_user.id)
    )
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
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    将多个接口用例导出为 JMeter .jmx 文件
    兼容两种前端协议：
    1. 直接传 [1,2,3]
    2. 传 { case_ids: [...], group_id: 1, thread_group_config: {...} }
    """
    try:
        body = await request.json()
    except Exception:
        body = None

    case_ids: List[int] = []
    group_id: Optional[int] = None
    thread_group_config: Optional[Dict[str, Any]] = None

    if isinstance(body, list):
        try:
            case_ids = [int(case_id) for case_id in body]
        except (ValueError, TypeError):
            raise HTTPException(status_code=400, detail="case_ids 包含无效的数字")
    elif isinstance(body, dict):
        raw_case_ids = body.get("case_ids") or []
        if raw_case_ids:
            try:
                case_ids = [int(case_id) for case_id in raw_case_ids]
            except (ValueError, TypeError):
                raise HTTPException(status_code=400, detail="case_ids 包含无效的数字")
        group_id = body.get("group_id")
        thread_group_config = body.get("thread_group_config")

    if not case_ids and group_id is not None:
        result = await db.execute(
            select(AutoTestCase).where(
                AutoTestCase.group_id == group_id,
                AutoTestCase.user_id == current_user.id,
            )
        )
        group_cases = result.scalars().all()
        case_ids = [case.id for case in group_cases]

    if not case_ids:
        raise HTTPException(status_code=400, detail="请提供 case_ids 或 group_id")

    # 查询用例
    result = await db.execute(
        select(AutoTestCase).where(
            AutoTestCase.id.in_(case_ids),
            AutoTestCase.user_id == current_user.id,
        )
    )
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
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    GET 兼容入口，支持 query 参数导出
    """
    if not case_ids and group_id is not None:
        result = await db.execute(
            select(AutoTestCase).where(
                AutoTestCase.group_id == group_id,
                AutoTestCase.user_id == current_user.id,
            )
        )
        group_cases = result.scalars().all()
        case_ids = [case.id for case in group_cases]

    if not case_ids:
        raise HTTPException(status_code=400, detail="请提供 case_ids 或 group_id")

    result = await db.execute(
        select(AutoTestCase).where(
            AutoTestCase.id.in_(case_ids),
            AutoTestCase.user_id == current_user.id,
        )
    )
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
    current_user: User = Depends(get_current_active_user),
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
        .where(AutoTestScenario.id == scenario_id, AutoTestScenario.user_id == current_user.id)
        .options(selectinload(AutoTestScenario.steps).selectinload(AutoTestScenarioStep.api_case))
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
    current_user: User = Depends(get_current_active_user),
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
    if not file.filename or not file.filename.endswith(".jmx"):
        raise HTTPException(status_code=400, detail="只支持 .jmx 文件")

    # 读取文件内容（限制大小 10MB）
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小超过 10MB 限制")
    xml_content = content.decode("UTF-8", errors="replace")

    # 解析 JMeter XML
    cases = import_jmx_to_cases(xml_content)

    if not cases:
        raise HTTPException(status_code=400, detail="未能从文件中解析出接口用例")

    target_group_id = await _resolve_group_id(db, group_id, current_user.id)

    # 保存到数据库
    created_cases = []
    for case_data in cases:
        # 处理 headers_data
        headers_data = case_data.get("headers") or {}
        if isinstance(headers_data, str):
            try:
                import json as _json

                headers_data = _json.loads(headers_data)
            except (ValueError, TypeError):
                headers_data = {}

        case = AutoTestCase(
            group_id=target_group_id,
            user_id=current_user.id,
            name=case_data.get("name", "Imported Case"),
            method=case_data.get("method", "GET"),
            url=case_data.get("url", ""),
            headers=headers_data if isinstance(headers_data, dict) else case_data.get("headers"),
            params=case_data.get("params"),
            body_type=case_data.get("body_type", "none"),
            content_type=headers_data.get("Content-Type")
            if isinstance(headers_data, dict)
            else case_data.get("content_type"),
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
        result.append(
            {
                "id": case.id,
                "name": case.name,
                "method": case.method,
                "url": case.url,
            }
        )

    return {
        "message": f"成功导入 {len(result)} 个接口用例",
        "cases": result,
    }


@router.post("/import/jmeter/tree")
async def import_jmeter_full_tree(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
):
    """导入JMX文件为完整树结构(保留所有节点和层级)"""
    if not file.filename or not file.filename.endswith(".jmx"):
        raise HTTPException(status_code=400, detail="只支持 .jmx 文件")
    content = await file.read()
    xml_content = content.decode("UTF-8", errors="replace")
    try:
        tree = import_jmx_to_full_tree(xml_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"tree": tree, "message": "JMX完整树解析成功"}


def _percentile(data, p):
    """计算百分位数（线性插值法）"""
    if not data:
        return 0
    arr = sorted(data)
    n = len(arr)
    idx = p / 100 * (n - 1)
    lo = int(idx)
    hi = min(lo + 1, n - 1)
    frac = idx - lo
    return round(arr[lo] * (1 - frac) + arr[hi] * frac, 1)


def _parse_start_time_offset(start_time_str: str, bench_start_time: float) -> float:
    """将请求的 start_time 字符串解析为相对于压测开始时间的偏移秒数"""
    try:
        from datetime import datetime as _dt

        req_dt = _dt.strptime(start_time_str, "%Y-%m-%d %H:%M:%S").timestamp()
        return req_dt - bench_start_time
    except (ValueError, TypeError):
        return -1


def _safe_json_loads(val, default=None):
    if val is None:
        return default
    if isinstance(val, (dict, list)):
        return val
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default if default is not None else val


def _case_to_dict(case: AutoTestCase) -> Dict[str, Any]:
    """将 AutoTestCase 对象转换为字典"""
    return {
        "name": case.name,
        "method": case.method,
        "url": case.url,
        "headers": _safe_json_loads(case.headers, {}),
        "params": _safe_json_loads(case.params, {}),
        "body_type": case.body_type or "none",
        "payload": _safe_json_loads(case.payload, {}),
        "assert_rules": _safe_json_loads(case.assert_rules, []),
        "extractors": _safe_json_loads(case.extractors, []),
    }


def _create_jmx_response(jmx_content: str, filename: str) -> StreamingResponse:
    """创建 JMeter .jmx 文件响应"""
    file_stream = io.BytesIO(jmx_content.encode("UTF-8"))

    encoded_filename = quote(filename, safe="")

    return StreamingResponse(
        file_stream,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition,X-JMeter-Compatibility",
            "X-JMeter-Compatibility": "JMeter 5.0+ (compatible with 5.1.1/5.2+/5.3+/5.4+/5.5+/5.6+)",
        },
    )


@router.post("/preview/jmeter/jmx")
async def preview_jmeter_jmx(
    body: Dict[str, Any] = Body(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    预览生成的 JMeter JMX 脚本（不下载）

    Request Body:
        case_ids: [1, 2, 3]
        config: {
            test_plan_name, num_threads, ramp_time, loop_count, duration,
            think_time, timer_type (none/constant/uniform),
            add_assertion, add_response_assertion,
        }
    """
    case_ids = body.get("case_ids", [])
    config = body.get("config", {})

    if not case_ids:
        raise HTTPException(status_code=400, detail="请提供 case_ids")

    # 查询用例
    result = await db.execute(
        select(AutoTestCase).where(AutoTestCase.id.in_(case_ids), AutoTestCase.user_id == current_user.id)
    )
    cases = result.scalars().all()

    if not cases:
        raise HTTPException(status_code=404, detail="未找到用例")

    case_dicts = [_case_to_dict(c) for c in cases]

    # 构建线程组配置
    tg_config = {
        "num_threads": config.get("num_threads", 1),
        "ramp_time": config.get("ramp_time", 1),
        "loop_count": config.get("loop_count", 1),
        "duration": config.get("duration", 60),
        "think_time": config.get("think_time", 0),
        "timer_type": config.get("timer_type", "none"),
        "add_assertion": config.get("add_assertion", True),
        "add_response_assertion": config.get("add_response_assertion", False),
    }

    jmx_content = export_cases_to_jmx(
        cases=case_dicts,
        test_plan_name=config.get("test_plan_name", "TestMaster Performance Test"),
        thread_group_config=tg_config,
    )

    return {
        "jmx_content": jmx_content,
        "case_count": len(case_dicts),
        "cases": [{"id": c.id, "name": c.name, "method": c.method, "url": c.url} for c in cases],
    }


# ========== 树形导出 ==========


@router.post("/export/jmeter/tree")
async def export_tree_to_jmx(body: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_active_user)):
    """
    将树形脚本结构导出为 JMX

    Request Body:
        tree: [{type: "ThreadGroup", name: "...", props: {...}, children: [...]}, ...]
        plan_name: "Test Plan"
        plan_variables: [{name: "BASE_URL", value: "..."}]
    """
    from fastapi_backend.services.autotest_jmeter_service import export_tree_to_jmx

    tree = body.get("tree", [])
    plan_name = body.get("plan_name", "TestMaster Test Plan")
    plan_variables = body.get("plan_variables", [])

    jmx_content = export_tree_to_jmx(tree, plan_name, plan_variables)

    return {
        "jmx_content": jmx_content,
        "elements": _count_elements(tree),
        "jmeter_compatibility": "JMeter 5.0+ (compatible with 5.1.1/5.2+/5.3+/5.4+/5.5+/5.6+)",
    }


# ========== 快速并发压测（在线验证） ==========

import asyncio
import time
import uuid
import aiohttp
import httpx

# 压测任务状态存储（内存，不持久化）
_bench_tasks: dict = {}
_bench_lock = asyncio.Lock()


@router.post("/jmeter/quick-bench")
async def quick_benchmark_submit(
    body: Dict[str, Any] = Body(...), current_user: User = Depends(get_current_active_user)
):
    """
    提交快速并发压测任务
    立即返回 task_id，通过 GET /jmeter/quick-bench/{task_id} 轮询结果

    Request Body:
        requests: [{"method", "url", "headers", "body"}, ...]
        concurrency: 并发数（默认10，最大200）
        duration: 持续秒数（默认10，最大60）
        ramp_up: 预热秒数（默认2）

    Response:
        task_id: 任务ID
        status: pending / running / done
    """
    targets = body.get("requests", [])
    if not targets:
        raise HTTPException(status_code=400, detail="请提供至少一个请求")

    for t in targets:
        t_url = t.get("url", "")
        if t_url:
            safe, reason = validate_url_safety(t_url)
            if not safe:
                raise HTTPException(status_code=400, detail=reason)

    task_id = str(uuid.uuid4())
    config = {
        "targets": targets,
        "concurrency": max(min(int(body.get("concurrency", 10)), 200), 1),
        "duration": max(min(int(body.get("duration", 10)), 60), 1),
        "ramp_up": max(min(int(body.get("ramp_up", 2)), 10), 0),
    }

    async with _bench_lock:
        _bench_tasks[task_id] = {
            "status": "pending",
            "progress": "等待执行",
            "percent": 0,
            "config": config,
            "result": None,
            "snapshots": [],
            "user_id": current_user.id,
        }

    # 后台异步执行，不阻塞当前请求
    asyncio.create_task(_run_bench(task_id, config))

    return {"task_id": task_id, "status": "pending"}


@router.get("/jmeter/quick-bench/{task_id}")
async def quick_benchmark_status(task_id: str, current_user: User = Depends(get_current_active_user)):
    """
    查询压测任务状态

    Response (status=pending/running):
        status, progress, percent

    Response (status=done):
        status: "done"
        result: { total, success, failed, avg_ms, min_ms, max_ms,
                  p50_ms, p95_ms, p99_ms, tps, status_distribution, errors }
    """
    task = _bench_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")

    # 校验任务归属
    if task.get("user_id") and task["user_id"] != current_user.id:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")

    if task["status"] == "done":
        return {
            "status": "done",
            "progress": "执行完成",
            "percent": 100,
            "result": task["result"],
            "config": task["config"],
            "snapshots": task.get("snapshots", []),
        }

    return {
        "status": task["status"],
        "progress": task["progress"],
        "percent": task["percent"],
        "config": task["config"],
        "snapshots": task.get("snapshots", []),
    }


async def _run_bench(task_id: str, config: dict):
    """后台执行压测任务"""
    targets = config["targets"]
    concurrency = config["concurrency"]
    duration = config["duration"]
    ramp_up = config["ramp_up"]

    async with _bench_lock:
        _bench_tasks[task_id]["status"] = "running"
        _bench_tasks[task_id]["progress"] = f"正在启动 {concurrency} 个并发..."

    results = []
    errors = []
    body_samples = []
    _body_captured_count = {}
    start_time = time.time()

    async def worker(worker_id: int):
        timeout_obj = aiohttp.ClientTimeout(total=8, connect=3)
        async with aiohttp.ClientSession(timeout=timeout_obj) as session:
            while True:
                if time.time() - start_time > duration:
                    break
                for target in targets:
                    if time.time() - start_time > duration:
                        break
                    req_start = time.time()
                    req_start_iso = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(req_start))
                    try:
                        method = target.get("method", "GET").upper()
                        url = target.get("url", "")
                        name = target.get("name", url)
                        headers = target.get("headers", {}) or {}
                        req_body = target.get("body", "")

                        sent_bytes = len(req_body) if req_body else 0
                        hdr_str = ""
                        for k, v in headers.items():
                            if k.lower() != "content-length":
                                hdr_str += f"{k}: {v}\r\n"
                            else:
                                try:
                                    sent_bytes = int(v)
                                except (ValueError, TypeError):
                                    pass
                        headers_size = len(hdr_str.encode("utf-8")) if hdr_str else 0

                        kwargs = {"headers": headers}
                        if req_body and method in ("POST", "PUT", "PATCH"):
                            kwargs["data"] = req_body

                        async with session.request(method, url, **kwargs) as resp:
                            elapsed = (time.time() - req_start) * 1000
                            raw_body = await resp.read()
                            body_len = len(raw_body)
                            resp_headers = dict(resp.headers)

                            content_type = resp_headers.get("Content-Type", "").split(";")[0].strip()
                            data_encoding = resp_headers.get("Content-Encoding", "")

                            entry = {
                                "name": name,
                                "method": method,
                                "url": url,
                                "status": resp.status,
                                "response_message": resp.reason or ("OK" if 200 <= resp.status < 400 else "Error"),
                                "elapsed_ms": round(elapsed, 1),
                                "connect_time_ms": None,
                                "latency_ms": round(elapsed, 1),
                                "body_size": body_len,
                                "sent_bytes": sent_bytes,
                                "headers_size": headers_size,
                                "worker": worker_id,
                                "thread_name": f"线程组 1-{worker_id + 1}",
                                "start_time": req_start_iso,
                                "data_type": "text",
                                "error": None,
                                "request_body": "",
                                "response_body": "",
                                "request_headers": {},
                                "response_headers": {},
                                "http_fields": {
                                    "content_type": content_type,
                                    "encoding": data_encoding,
                                },
                            }
                            results.append(entry)

                            if not (200 <= resp.status < 400):
                                errors.append(entry)

                            _body_captured_count[url] = _body_captured_count.get(url, 0) + 1
                            if _body_captured_count[url] <= 5 and body_len > 0:
                                body_samples.append(
                                    {
                                        "url": url,
                                        "name": name,
                                        "status": resp.status,
                                        "body": raw_body[:30000].decode("utf-8", errors="replace"),
                                        "headers": resp_headers,
                                    }
                                )
                    except asyncio.CancelledError:
                        return
                    except Exception as e:
                        err_msg = str(e)[:500]
                        elapsed_err = (time.time() - req_start) * 1000
                        err_entry = {
                            "name": target.get("name", target.get("url", "")),
                            "method": target.get("method", "GET").upper(),
                            "url": target.get("url", ""),
                            "status": 0,
                            "response_message": err_msg[:80],
                            "elapsed_ms": round(elapsed_err, 1),
                            "connect_time_ms": None,
                            "latency_ms": round(elapsed_err, 1),
                            "body_size": 0,
                            "sent_bytes": 0,
                            "headers_size": 0,
                            "worker": worker_id,
                            "thread_name": f"线程组 1-{worker_id + 1}",
                            "start_time": req_start_iso,
                            "data_type": "text",
                            "error": err_msg,
                            "request_body": (target.get("body", "") or "")[:10000],
                            "response_body": f"[请求失败] {err_msg}",
                            "request_headers": dict(target.get("headers", {}) or {}),
                            "response_headers": {},
                            "http_fields": {"content_type": "", "encoding": ""},
                        }
                        results.append(err_entry)
                        errors.append(err_entry)

                    # 每50个请求更新一次进度
                    if len(results) % 50 == 0:
                        async with _bench_lock:
                            _bench_tasks[task_id]["percent"] = min(int((time.time() - start_time) / duration * 100), 99)
                            _bench_tasks[task_id]["progress"] = f"已发送 {len(results)} 请求，{len(errors)} 失败"

    async def snapshot_collector():
        """每秒采集一次实时指标快照"""
        last_count = 0
        last_ts = start_time
        while True:
            await asyncio.sleep(1)
            now = time.time()
            if now - start_time > duration + 5:
                break
            elapsed_seconds = round(now - start_time, 1)
            total_now = len(results)
            err_now = len(errors)
            delta_count = total_now - last_count
            delta_sec = now - last_ts if now > last_ts else 1
            tps_now = round(delta_count / delta_sec, 1) if delta_sec > 0 else 0
            recent_elapsed = sorted([r["elapsed_ms"] for r in results[-delta_count:]]) if delta_count > 0 else []
            avg_now = round(sum(recent_elapsed) / len(recent_elapsed), 1) if recent_elapsed else 0
            p95_now = _percentile(recent_elapsed, 95)
            p99_now = _percentile(recent_elapsed, 99)
            async with _bench_lock:
                _bench_tasks[task_id]["snapshots"].append(
                    {
                        "t": elapsed_seconds,
                        "tps": tps_now,
                        "avg": avg_now,
                        "p95": p95_now,
                        "p99": p99_now,
                        "total": total_now,
                        "errors": err_now,
                    }
                )
            last_count = total_now
            last_ts = now

    workers = []
    snapshot_task = asyncio.create_task(snapshot_collector())

    for i in range(concurrency):
        w = asyncio.create_task(worker(i))
        workers.append(w)
        if ramp_up > 0 and i < concurrency - 1:
            await asyncio.sleep(ramp_up / concurrency)

    done, pending = await asyncio.wait(workers, timeout=duration + 10)
    for p in pending:
        p.cancel()
    if pending:
        await asyncio.wait(pending, timeout=5)
    snapshot_task.cancel()
    total_time = time.time() - start_time

    # 计算结果
    if not results:
        result = {
            "total": 0,
            "success": 0,
            "failed": 0,
            "avg_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
            "p50_ms": 0,
            "p95_ms": 0,
            "p99_ms": 0,
            "tps": 0,
            "status_distribution": {},
            "errors": errors[:20],
            "per_url": [],
            "samples": [],
        }
    else:
        elapsed_list = [r["elapsed_ms"] for r in results]
        elapsed_sorted = sorted(elapsed_list)
        success_count = sum(1 for r in results if 200 <= r["status"] < 400)

        status_dist = {}
        for r in results:
            s = str(r.get("status", 0))
            status_dist[s] = status_dist.get(s, 0) + 1

        # 按 URL + Method 统计（≈ 聚合报告）
        url_map = {}
        for r in results:
            u = r.get("url", "")
            m = r.get("method", "GET")
            key = f"{m}:{u}"
            if key not in url_map:
                url_map[key] = {
                    "url": u,
                    "name": r.get("name", u),
                    "method": m,
                    "count": 0,
                    "success": 0,
                    "failed": 0,
                    "times": [],
                }
            url_map[key]["count"] += 1
            if 200 <= r["status"] < 400:
                url_map[key]["success"] += 1
            else:
                url_map[key]["failed"] += 1
            url_map[key]["times"].append(r["elapsed_ms"])
        per_url = []
        for key, s in url_map.items():
            t = sorted(s["times"])
            per_url.append(
                {
                    "url": s["url"],
                    "name": s.get("name", s["url"]),
                    "method": s.get("method", "GET"),
                    "count": s["count"],
                    "success": s["success"],
                    "failed": s["failed"],
                    "success_rate": round(s["success"] / s["count"] * 100, 1) if s["count"] > 0 else 0,
                    "avg_ms": round(sum(t) / len(t), 1),
                    "p50_ms": _percentile(t, 50),
                    "p90_ms": _percentile(t, 90),
                    "p95_ms": _percentile(t, 95),
                    "p99_ms": _percentile(t, 99),
                    "min_ms": round(t[0], 1),
                    "max_ms": round(t[-1], 1),
                    "stddev_ms": round((sum((x - sum(t) / len(t)) ** 2 for x in t) / len(t)) ** 0.5, 1)
                    if len(t) > 1
                    else 0,
                }
            )

        # 请求详情样本（≈ 查看结果树）：所有失败 + 每个 URL 前 50 个成功
        seen_url_ok = {}
        samples = []
        for r in results:
            is_ok = 200 <= r["status"] < 400
            if not is_ok:
                samples.append(r)
            else:
                u = r["url"]
                seen_url_ok[u] = seen_url_ok.get(u, 0) + 1
                if seen_url_ok[u] <= 50:
                    samples.append(r)
            if len(samples) >= 200:
                break

        # 响应时间分布区间统计
        rt_buckets = {
            "<10ms": 0,
            "10-50ms": 0,
            "50-100ms": 0,
            "100-200ms": 0,
            "200-500ms": 0,
            "500-1000ms": 0,
            ">1000ms": 0,
        }
        for ms in elapsed_list:
            if ms < 10:
                rt_buckets["<10ms"] += 1
            elif ms < 50:
                rt_buckets["10-50ms"] += 1
            elif ms < 100:
                rt_buckets["50-100ms"] += 1
            elif ms < 200:
                rt_buckets["100-200ms"] += 1
            elif ms < 500:
                rt_buckets["200-500ms"] += 1
            elif ms < 1000:
                rt_buckets["500-1000ms"] += 1
            else:
                rt_buckets[">1000ms"] += 1

        # 吞吐量趋势（使用 snapshot_collector 采集的实时快照数据）
        snapshots = _bench_tasks.get(task_id, {}).get("snapshots", [])
        throughput_trend = []
        if snapshots:
            # 每5秒采样一次快照数据
            for i, snap in enumerate(snapshots):
                if i % 5 == 0:  # 每5秒一个数据点
                    throughput_trend.append(
                        {
                            "t": snap.get("t", 0),
                            "tps": snap.get("tps", 0),
                            "count": snap.get("total", 0),
                        }
                    )
        else:
            # 降级方案：如果没有快照数据，使用 start_time 判断时间窗口
            window = 5
            for i in range(0, int(total_time), window):
                w_count = sum(
                    1
                    for r in results
                    if r.get("start_time") and i <= _parse_start_time_offset(r["start_time"], start_time) < i + window
                )
                throughput_trend.append({"t": i, "tps": round(w_count / window, 1), "count": w_count})

        result = {
            "total": len(results),
            "success": success_count,
            "failed": len(results) - success_count,
            "avg_ms": round(sum(elapsed_list) / len(elapsed_list), 1),
            "min_ms": round(elapsed_sorted[0], 1),
            "max_ms": round(elapsed_sorted[-1], 1),
            "p50_ms": _percentile(elapsed_sorted, 50),
            "p90_ms": _percentile(elapsed_sorted, 90),
            "p95_ms": _percentile(elapsed_sorted, 95),
            "p99_ms": _percentile(elapsed_sorted, 99),
            "stddev_ms": round(
                (sum((x - sum(elapsed_list) / len(elapsed_list)) ** 2 for x in elapsed_list) / len(elapsed_list))
                ** 0.5,
                1,
            )
            if len(elapsed_list) > 1
            else 0,
            "tps": round(len(results) / total_time, 1) if total_time > 0 else 0,
            "status_distribution": status_dist,
            "rt_distribution": rt_buckets,
            "throughput_trend": throughput_trend,
            "errors": errors[:20],
            "per_url": per_url,
            "samples": samples,
            "body_samples": [
                {"url": bs["url"], "status": bs["status"], "body": bs["body"][:500]} for bs in body_samples
            ],
        }

    async with _bench_lock:
        _bench_tasks[task_id]["status"] = "done"
        _bench_tasks[task_id]["progress"] = f"完成：{result['total']} 请求，{result['failed']} 失败"
        _bench_tasks[task_id]["percent"] = 100
        _bench_tasks[task_id]["result"] = result

    # 10分钟后清理
    await asyncio.sleep(600)
    async with _bench_lock:
        _bench_tasks.pop(task_id, None)


class BenchAnalyzeRequest(BaseModel):
    plan_name: str = ""
    concurrency: int = 10
    duration: int = 10
    result: dict = {}


def _is_placeholder_api_key(key: Optional[str]) -> bool:
    if not key:
        return True
    key_lower = key.lower()
    placeholders = [
        "your_model_api_key_here",
        "your-openai-api-key",
        "your_api_key",
        "your-api-key",
        "sk-your",
        "change_me",
        "changeme",
        "placeholder",
    ]
    return any(p in key_lower for p in placeholders)


@router.post("/analyze-result")
async def analyze_bench_result(
    req: BenchAnalyzeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    _ai=Depends(require_ai_points("bench_ai_analysis")),
):
    from sqlalchemy import select
    from fastapi_backend.models.models import AIConfig
    from fastapi_backend.core.database import AsyncSessionLocal as MainAsyncSessionLocal
    from fastapi_backend.core.config import settings

    config = None
    try:
        async with MainAsyncSessionLocal() as main_db:
            ai_result = await main_db.execute(select(AIConfig).where(AIConfig.is_active))
            config = ai_result.scalar_one_or_none()
    except Exception:
        config = None

    api_key = None
    base_url = None
    model = None

    if config:
        api_key = config.api_key
        base_url = config.base_url
        model = config.model
        config.provider.lower() if config.provider else "openai"
    elif settings.AI_API_KEY and not _is_placeholder_api_key(settings.AI_API_KEY):
        api_key = settings.AI_API_KEY
        base_url = settings.AI_BASE_URL
        model = settings.AI_MODEL
        getattr(settings, "AI_PROVIDER", "openai").lower()

    if not api_key:
        return {"analysis": _build_offline_analysis(req)}

    r = req.result
    per_url_text = ""
    if r.get("per_url"):
        for pu in r["per_url"]:
            per_url_text += (
                f"  [{pu.get('name', '') or pu.get('url', '')}]\n"
                f"    请求: {pu.get('count', 0)}次 | 成功: {pu.get('success', 0)} | 失败: {pu.get('failed', 0)}\n"
                f"    响应: 平均{pu.get('avg_ms', 0)}ms | P50={pu.get('p50_ms', 0)}ms | P95={pu.get('p95_ms', 0)}ms | P99={pu.get('p99_ms', 0)}ms\n"
                f"    极值: 最小{pu.get('min_ms', 0)}ms | 最大{pu.get('max_ms', 0)}ms | 标准差{pu.get('stddev_ms', 0)}ms\n"
            )

    rt_dist_text = ""
    if r.get("rt_distribution"):
        rt_dist_text = "  响应时间分段统计:\n"
        for bucket, count in r["rt_distribution"].items():
            rt_dist_text += f"    {bucket}: {count}次\n"

    throughput_text = ""
    if r.get("throughput_trend"):
        throughput_text = "  吞吐量时序变化 (每5秒采样):\n"
        for tp in r["throughput_trend"][:20]:
            throughput_text += f"    T+{tp.get('t', 0)}s: TPS={tp.get('tps', 0)}, 请求数={tp.get('count', 0)}\n"

    errors_text = ""
    if r.get("errors"):
        for e in r["errors"][:10]:
            errors_text += f"  - {e}\n"

    status_text = ""
    if r.get("status_distribution"):
        for code, count in r["status_distribution"].items():
            status_text += f"  HTTP {code}: {count}次\n"

    prompt = f"""你是一位资深性能测试架构师，拥有10年以上大型分布式系统压测经验。请对以下压测结果进行**全方位多维度**深度分析。

【压测环境】
- 计划名称: {req.plan_name}
- 并发用户数: {req.concurrency} | 持续时间: {req.duration}秒
- 总请求: {r.get("total", 0)} | 成功: {r.get("success", 0)} | 失败: {r.get("failed", 0)}
- TPS: {r.get("tps", 0)} | 标准差: {r.get("stddev_ms", 0)}ms
- 平均: {r.get("avg_ms", 0)}ms | P50: {r.get("p50_ms", 0)}ms | P95: {r.get("p95_ms", 0)}ms | P99: {r.get("p99_ms", 0)}ms
- 最小: {r.get("min_ms", 0)}ms | 最大: {r.get("max_ms", 0)}ms

【响应时间分布 (分段直方图)】
{rt_dist_text if rt_dist_text else "无"}

【吞吐量时序趋势】
{throughput_text if throughput_text else "无"}

【状态码分布】
{status_text if status_text else "无"}

【错误信息 (前10条)】
{errors_text if errors_text else "无"}

【每个接口的详细数据 (含极值/标准差)】
{per_url_text if per_url_text else "无"}

请按以下6个维度输出分析报告（用中文，专业详尽，不缩写）：

## 一、整体健康度评估
- 性能等级（S/A/B/C/D）及评级依据（对照行业标准：P95<200ms=S, <500ms=A, <1s=B, <3s=C, >3s=D）
- 成功率评估（优秀>99%/良好>95%/一般>90%/差<90%）
- 系统稳定性分析：看标准差和吞吐趋势是否平稳（标准差/平均值<0.3为稳定，0.3-0.8为有抖动，>0.8为不稳定）
- 容量评估：当前{req.concurrency}并发下，系统是否已达到瓶颈或还有余量

## 二、逐接口深度剖析
对每个接口独立分析：
- **【接口名称/URL】**: 请求量占比、成功率、失败类型
- **延迟画像**: 平均/P50/P95/P99 对比，标准差解读（P50与P99差距>3倍=严重长尾，标准差>平均值的50%=响应抖动剧烈）
- **极值分析**: 最大响应时间是否异常（超过P99的2倍即为异常尖刺）
- **瓶颈判定**: 正常/关注/严重（附数据依据）
- **根因推断**: 从延迟分布形状推断（如P50低P99高=偶发性阻塞/GC停顿；整体高且均匀=计算瓶颈；标准差大=资源争抢）

## 三、响应时间分布解读
- 分析RT分布直方图的形态（单峰/双峰/长尾/均匀分布）
- 如果分布呈双峰，说明可能存在两种不同的处理路径（如缓存命中/未命中）
- 如果长尾严重，评估99分位用户的体验影响

## 四、吞吐量趋势分析
- 从吞吐时序图判断：系统是否在预热后趋于稳定，还是逐渐衰减
- 是否存在TPS突变点（突增或突降），可能原因（GC/连接池耗尽/限流触发）
- TPS与并发的比例关系是否合理（理想线性的偏差程度）

## 五、关键风险发现
- 最慢TOP3接口及瓶颈定位
- 失败最多的TOP3接口及错误模式归类
- 是否存在雪崩隐患（单点慢接口拖垮整体）
- 连接池/线程池/资源泄漏的迹象判断

## 六、优化方案 (按优先级，每条含预期效果)
1. 【紧急】立即修复的问题（会导致系统不可用的）
2. 【高优】性能瓶颈优化（ROI最高的1-2项）
3. 【中优】架构改进建议（需要一定开发工作量）
4. 【持续】监控和容量规划建议

数据驱动的分析原则：
- 用数据说话，每个结论都要引用具体的数值
- 区分脚本问题和服务端问题
- 从延迟分布形状、吞吐趋势变化中挖掘深层问题
- 对长尾延迟和异常尖刺给予特别关注
- 接口数量少时深挖微观，接口多时聚焦TOP瓶颈"""

    try:
        async with httpx.AsyncClient(timeout=180) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "你是一位资深性能测试架构师，擅长从接口维度进行深度瓶颈分析和根因定位，输出专业详尽的性能分析报告。",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 8192,
                    "temperature": 0.5,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                await _ai()
                return {"analysis": content.strip()}
            else:
                # AI 返回非200，不调用 _ai()，积分事务自动回滚退还
                return {"analysis": _build_offline_analysis(req)}
    except Exception:
        # AI 调用异常，不调用 _ai()，积分事务自动回滚退还
        return {"analysis": _build_offline_analysis(req)}


def _build_offline_analysis(req) -> str:
    r = req.result
    total = r.get("total", 0)
    failed = r.get("failed", 0)
    r.get("success", 0)
    tps = r.get("tps", 0)
    avg = r.get("avg_ms", 0)
    p95 = r.get("p95_ms", 0)
    p99 = r.get("p99_ms", 0)
    fail_rate = (failed / total * 100) if total > 0 else 0

    lines = ["📊 性能分析报告（规则引擎自动生成）", "=" * 40, ""]

    # 一、整体评估
    if fail_rate == 0:
        lines.append("## 一、整体评估：S级 - 所有请求成功 ✅")
    elif fail_rate < 1:
        lines.append(f"## 一、整体评估：良好 - 失败率 {fail_rate:.1f}%")
    elif fail_rate < 5:
        lines.append(f"## 一、整体评估：一般 - 失败率 {fail_rate:.1f}%，需关注")
    else:
        lines.append(f"## 一、整体评估：较差 - 失败率 {fail_rate:.1f}%，系统可能存在问题")

    lines.append(f"  并发={req.concurrency} | TPS={tps} | 平均={avg}ms | P95={p95}ms | P99={p99}ms")
    if avg < 100:
        lines.append("  响应时间等级：S（<100ms）")
    elif avg < 500:
        lines.append("  响应时间等级：A（<500ms）")
    elif avg < 1000:
        lines.append("  响应时间等级：B（<1s）")
    elif avg < 3000:
        lines.append("  响应时间等级：C（<3s）")
    else:
        lines.append("  响应时间等级：D（>3s，需优化）")
    if p99 > 0 and p95 > 0 and p99 / max(p95, 1) > 2:
        lines.append("  ⚠ P99远大于P95，存在极端长尾延迟")
    lines.append("")

    # 二、逐接口分析
    per_url_list = r.get("per_url", [])
    if per_url_list:
        lines.append("## 二、逐接口分析")
        lines.append("-" * 40)
        for i, pu in enumerate(per_url_list, 1):
            url = pu.get("url", pu.get("name", "未知接口"))
            c = pu.get("count", 0)
            s_ok = pu.get("success", 0)
            s_fail = pu.get("failed", 0)
            a = pu.get("avg_ms", 0)
            p95u = pu.get("p95_ms", 0)
            p99u = pu.get("p99_ms", 0)
            fr = (s_fail / c * 100) if c > 0 else 0

            # 评估等级
            if a < 100:
                grade = "🟢 S"
            elif a < 500:
                grade = "🟡 A"
            elif a < 1000:
                grade = "🟠 B"
            elif a < 3000:
                grade = "🔴 C"
            else:
                grade = "⛔ D"

            lines.append(f"\n  [{i}] {grade} | {url}")
            lines.append(f"      请求: {c}次 | 成功: {s_ok} | 失败: {s_fail} | 失败率: {fr:.1f}%")
            lines.append(f"      平均: {a}ms | P95: {p95u}ms | P99: {p99u}ms")

            stddev_u = pu.get("stddev_ms", 0)
            p50_u = pu.get("p50_ms", 0)
            min_u = pu.get("min_ms", 0)
            max_u = pu.get("max_ms", 0)
            lines.append(f"      响应: 平均{a}ms | P50={p50_u}ms | P95={p95u}ms | P99={p99u}ms | 标准差={stddev_u}ms")
            lines.append(f"      极值: 最小{min_u}ms | 最大{max_u}ms")

            if fr > 0:
                lines.append("      ⚠ 存在失败，检查错误类型")
            if p99u > 0 and p95u > 0 and p99u / max(p95u, 1) > 2:
                lines.append(f"      ⚠ P99({p99u}ms)>>P95({p95u}ms)，长尾瓶颈")
            if stddev_u > 0 and a > 0 and stddev_u / a > 0.5:
                lines.append(f"      ⚠ 标准差/均值={stddev_u / a:.2f}，响应抖动剧烈")
            if max_u > 0 and p99u > 0 and max_u > p99u * 2:
                lines.append(f"      ⚠ 最大{max_u}ms远超P99{p99u}ms，存在异常尖刺")
            if a > 1000:
                lines.append("      💡 建议：排查慢SQL/缓存/下游服务")
            if c > 1 and fr > 50:
                lines.append("      🚨 高失败率！立即排查")
    else:
        lines.append("## 二、逐接口分析")
        lines.append("   （无按接口统计数据）")

    lines.append("")

    # 三、稳定性分析
    lines.append("## 三、系统稳定性")
    lines.append("-" * 40)
    stddev_all = r.get("stddev_ms", 0)
    if stddev_all > 0 and avg > 0:
        cv = stddev_all / avg
        if cv < 0.3:
            lines.append(f"  变异系数={cv:.2f} - 系统稳定 ✅")
        elif cv < 0.8:
            lines.append(f"  变异系数={cv:.2f} - 存在抖动 ⚠")
        else:
            lines.append(f"  变异系数={cv:.2f} - 系统不稳定 🚨")
    lines.append("")

    # 四、吞吐趋势
    tp_list = r.get("throughput_trend", [])
    if len(tp_list) > 1:
        tps_values = [t.get("tps", 0) for t in tp_list]
        tps_std = (sum((x - sum(tps_values) / len(tps_values)) ** 2 for x in tps_values) / len(tps_values)) ** 0.5
        tps_avg = sum(tps_values) / len(tps_values)
        lines.append(f"  TPS均值={tps_avg:.1f} | 波动标准差={tps_std:.1f}")
        if tps_avg > 0 and tps_std / tps_avg > 0.3:
            lines.append("  ⚠ TPS波动较大，系统吞吐不稳定")
        else:
            lines.append("  ✅ TPS平稳，吞吐表现一致")
    lines.append("")

    # 五、错误分析与建议
    lines.append("## 四、关键发现 & 优化建议")
    lines.append("-" * 40)
    errs = r.get("errors", [])
    if errs:
        from collections import Counter

        lines.append(f"  错误总数: {len(errs)}")
        for err_type, cnt in Counter(str(e) for e in errs).most_common(5):
            lines.append(f"    - [{cnt}次] {err_type[:100]}")
    lines.append("")
    lines.append(f"  1. 总TPS={tps}，平均每接口TPS={tps / max(len(per_url_list), 1):.1f}")
    if avg > 500:
        lines.append("  2. 瓶颈在响应时间，排查慢SQL/外部调用/序列化开销")
    if tps < 10 and req.concurrency > 1:
        lines.append("  3. TPS偏低，检查连接池大小和并发模型")
    lines.append("  4. 建议对慢接口增加缓存层或异步化处理")
    lines.append("  5. 考虑对高频接口做CDN或边缘计算优化")

    return "\n".join(lines)


def _count_elements(tree):
    """统计树中各类元素数量"""
    counts = {}

    def walk(nodes):
        for n in nodes:
            counts[n.get("type", "unknown")] = counts.get(n.get("type", "unknown"), 0) + 1
            walk(n.get("children", []))

    walk(tree)
    return counts
