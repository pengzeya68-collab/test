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
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Body, Form
from pydantic import BaseModel
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
    import_jmx_to_full_tree,
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


@router.post("/import/jmeter/tree")
async def import_jmeter_full_tree(
    file: UploadFile = File(...),
):
    """导入JMX文件为完整树结构(保留所有节点和层级)"""
    if not file.filename.endswith(".jmx"):
        raise HTTPException(status_code=400, detail="只支持 .jmx 文件")
    content = await file.read()
    xml_content = content.decode("UTF-8", errors="replace")
    try:
        tree = import_jmx_to_full_tree(xml_content)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {"tree": tree, "message": "JMX完整树解析成功"}


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
    file_stream = io.BytesIO(jmx_content.encode("UTF-8"))

    encoded_filename = quote(filename, safe='')

    return StreamingResponse(
        file_stream,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}",
            "Access-Control-Expose-Headers": "Content-Disposition",
        },
    )


@router.post("/preview/jmeter/jmx")
async def preview_jmeter_jmx(
    body: Dict[str, Any] = Body(...),
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
        select(AutoTestCase).where(AutoTestCase.id.in_(case_ids))
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
async def export_tree_to_jmx(body: Dict[str, Any] = Body(...)):
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
    
    return {"jmx_content": jmx_content, "elements": _count_elements(tree)}


# ========== 快速并发压测（在线验证） ==========

import asyncio
import time
import uuid
import logging
import aiohttp
import httpx

# 压测任务状态存储（内存，不持久化）
_bench_tasks: dict = {}
_bench_lock = asyncio.Lock()


@router.post("/jmeter/quick-bench")
async def quick_benchmark_submit(body: Dict[str, Any] = Body(...)):
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
    
    task_id = str(uuid.uuid4())
    config = {
        "targets": targets,
        "concurrency": min(int(body.get("concurrency", 10)), 200),
        "duration": min(int(body.get("duration", 10)), 60),
        "ramp_up": min(int(body.get("ramp_up", 2)), 10),
    }

    async with _bench_lock:
        _bench_tasks[task_id] = {
            "status": "pending",
            "progress": "等待执行",
            "percent": 0,
            "config": config,
            "result": None,
            "snapshots": [],
        }

    # 后台异步执行，不阻塞当前请求
    asyncio.create_task(_run_bench(task_id, config))

    return {"task_id": task_id, "status": "pending"}


@router.get("/jmeter/quick-bench/{task_id}")
async def quick_benchmark_status(task_id: str):
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
    _sample_seq = [0]
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
                            if k.lower() != 'content-length':
                                hdr_str += f"{k}: {v}\r\n"
                            else:
                                try:
                                    sent_bytes = int(v)
                                except: pass
                        headers_size = len(hdr_str.encode('utf-8')) if hdr_str else 0

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

                            _sample_seq[0] += 1
                            entry = {
                                "name": name,
                                "method": method,
                                "url": url,
                                "status": resp.status,
                                "response_message": resp.reason or ("OK" if 200 <= resp.status < 400 else "Error"),
                                "elapsed_ms": round(elapsed, 1),
                                "connect_time_ms": round((resp._connection_info or {}).get('connect_time', 0) * 1000, 1) if hasattr(resp, '_connection_info') else None,
                                "latency_ms": round(elapsed * 0.6, 1),
                                "body_size": body_len,
                                "sent_bytes": sent_bytes,
                                "headers_size": headers_size,
                                "worker": worker_id,
                                "thread_name": f"线程组 1-{worker_id + 1}",
                                "start_time": req_start_iso,
                                "data_type": "text",
                                "error": None,
                                "request_body": (req_body[:10000] if req_body else ""),
                                "response_body": raw_body[:50000].decode('utf-8', errors='replace') if body_len > 0 else "",
                                "request_headers": {k: v for k, v in headers.items()},
                                "response_headers": resp_headers,
                                "http_fields": {
                                    "content_type": content_type,
                                    "encoding": data_encoding,
                                },
                            }
                            results.append(entry)

                            _body_captured_count[url] = _body_captured_count.get(url, 0) + 1
                            if _body_captured_count[url] <= 5 and body_len > 0:
                                body_samples.append({
                                    "url": url, "name": name,
                                    "status": resp.status,
                                    "body": raw_body[:30000].decode('utf-8', errors='replace'),
                                    "headers": resp_headers,
                                })
                    except asyncio.CancelledError:
                        return
                    except Exception as e:
                        err_msg = str(e)[:500]
                        elapsed_err = (time.time() - req_start) * 1000
                        results.append({
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
                            "start_time": req_start_iso if 'req_start_iso' in dir() else "-",
                            "data_type": "text",
                            "error": err_msg,
                            "request_body": (target.get("body", "") or "")[:10000],
                            "response_body": f"[请求失败] {err_msg}",
                            "request_headers": dict(target.get("headers", {}) or {}),
                            "response_headers": {},
                            "http_fields": {"content_type": "", "encoding": ""},
                        })
                        errors.append(err_msg)

                    # 每50个请求更新一次进度
                    if len(results) % 50 == 0:
                        async with _bench_lock:
                            _bench_tasks[task_id]["percent"] = min(
                                int((time.time() - start_time) / duration * 100), 99
                            )
                            _bench_tasks[task_id]["progress"] = (
                                f"已发送 {len(results)} 请求，{len(errors)} 失败"
                            )

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
            def percentile(data, p):
                if not data: return 0
                idx = int(len(data) * p / 100)
                return round(data[min(idx, len(data) - 1)], 1)
            p95_now = percentile(recent_elapsed, 95)
            p99_now = percentile(recent_elapsed, 99)
            async with _bench_lock:
                _bench_tasks[task_id]["snapshots"].append({
                    "t": elapsed_seconds,
                    "tps": tps_now,
                    "avg": avg_now,
                    "p95": p95_now,
                    "p99": p99_now,
                    "total": total_now,
                    "errors": err_now,
                })
            last_count = total_now
            last_ts = now

    workers = []
    snapshot_task = asyncio.create_task(snapshot_collector())

    for i in range(concurrency):
        w = asyncio.create_task(worker(i))
        workers.append(w)
        if ramp_up > 0 and i < concurrency - 1:
            await asyncio.sleep(ramp_up / concurrency)

    await asyncio.wait(workers, timeout=duration + 10)
    total_time = time.time() - start_time

    # 计算结果
    if not results:
        result = {
            "total": 0, "success": 0, "failed": 0,
            "avg_ms": 0, "min_ms": 0, "max_ms": 0,
            "p50_ms": 0, "p95_ms": 0, "p99_ms": 0,
            "tps": 0, "status_distribution": {}, "errors": errors[:20],
            "per_url": [], "samples": [],
        }
    else:
        elapsed_list = [r["elapsed_ms"] for r in results]
        elapsed_sorted = sorted(elapsed_list)
        success_count = sum(1 for r in results if 200 <= r["status"] < 400)

        status_dist = {}
        for r in results:
            s = str(r.get("status", 0))
            status_dist[s] = status_dist.get(s, 0) + 1

        def percentile(data, p):
            if not data:
                return 0
            idx = int(len(data) * p / 100)
            return data[min(idx, len(data) - 1)]

        # 按 URL 统计（≈ 聚合报告）
        url_map = {}
        for r in results:
            u = r.get("url", "")
            if u not in url_map:
                url_map[u] = {"url": u, "name": r.get("name", u), "method": r.get("method", "GET"), "count": 0, "success": 0, "failed": 0, "times": []}
            url_map[u]["count"] += 1
            if 200 <= r["status"] < 400:
                url_map[u]["success"] += 1
            else:
                url_map[u]["failed"] += 1
            url_map[u]["times"].append(r["elapsed_ms"])
        per_url = []
        for u, s in url_map.items():
            t = sorted(s["times"])
            per_url.append({
                "url": u,
                "name": s.get("name", u),
                "method": s.get("method", "GET"),
                "count": s["count"],
                "success": s["success"],
                "failed": s["failed"],
                "success_rate": round(s["success"] / s["count"] * 100, 1) if s["count"] > 0 else 0,
                "avg_ms": round(sum(t) / len(t), 1),
                "p50_ms": round(percentile(t, 50), 1),
                "p95_ms": round(percentile(t, 95), 1),
                "p99_ms": round(percentile(t, 99), 1),
                "min_ms": round(t[0], 1),
                "max_ms": round(t[-1], 1),
            })

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

        result = {
            "total": len(results),
            "success": success_count,
            "failed": len(results) - success_count,
            "avg_ms": round(sum(elapsed_list) / len(elapsed_list), 1),
            "min_ms": round(elapsed_sorted[0], 1),
            "max_ms": round(elapsed_sorted[-1], 1),
            "p50_ms": round(percentile(elapsed_sorted, 50), 1),
            "p95_ms": round(percentile(elapsed_sorted, 95), 1),
            "p99_ms": round(percentile(elapsed_sorted, 99), 1),
            "tps": round(len(results) / total_time, 1) if total_time > 0 else 0,
            "status_distribution": status_dist,
            "errors": errors[:20],
            "per_url": per_url,
            "samples": samples,
            "body_samples": [{ "url": bs["url"], "status": bs["status"], "body": bs["body"][:500] } for bs in body_samples],
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

@router.post("/analyze-result")
async def analyze_bench_result(req: BenchAnalyzeRequest, db: AsyncSession = Depends(get_db)):
    from sqlalchemy import select
    from fastapi_backend.models.models import AIConfig
    from fastapi_backend.core.config import settings
    
    try:
        ai_result = await db.execute(select(AIConfig).where(AIConfig.is_active))
        config = ai_result.scalar_one_or_none()
    except Exception:
        config = None

    api_key = None
    base_url = None
    model = None
    provider = "openai"

    if config:
        api_key = config.api_key
        base_url = config.base_url
        model = config.model
        provider = config.provider.lower() if config.provider else "openai"
    elif settings.AI_API_KEY and settings.AI_API_KEY != "your_model_api_key_here":
        api_key = settings.AI_API_KEY
        base_url = settings.AI_BASE_URL
        model = settings.AI_MODEL
        provider = getattr(settings, 'AI_PROVIDER', 'openai').lower()

    if not api_key:
        return {"analysis": _build_offline_analysis(req)}

    r = req.result
    per_url_text = ""
    if r.get("per_url"):
        for pu in r["per_url"]:
            per_url_text += f"  - {pu.get('url','')}: {pu.get('count',0)}次, 成功{pu.get('success',0)}, 失败{pu.get('failed',0)}, 平均{pu.get('avg_ms',0)}ms, P95={pu.get('p95_ms',0)}ms\n"

    errors_text = ""
    if r.get("errors"):
        for e in r["errors"][:10]:
            errors_text += f"  - {e}\n"

    status_text = ""
    if r.get("status_distribution"):
        for code, count in r["status_distribution"].items():
            status_text += f"  HTTP {code}: {count}次\n"

    prompt = f"""你是一个性能测试分析专家。请分析以下压测结果并给出专业建议。

【压测概况】
- 计划名称: {req.plan_name}
- 并发用户数: {req.concurrency}
- 持续时间: {req.duration}秒
- 总请求数: {r.get('total', 0)}
- 成功: {r.get('success', 0)} / 失败: {r.get('failed', 0)}
- TPS (每秒事务数): {r.get('tps', 0)}
- 平均响应时间: {r.get('avg_ms', 0)}ms
- 中位数 P50: {r.get('p50_ms', 0)}ms
- P95 响应时间: {r.get('p95_ms', 0)}ms
- P99 响应时间: {r.get('p99_ms', 0)}ms
- 最小响应时间: {r.get('min_ms', 0)}ms
- 最大响应时间: {r.get('max_ms', 0)}ms

【状态码分布】
{status_text if status_text else "无"}

【错误信息】
{errors_text if errors_text else "无"}

【按接口统计】
{per_url_text if per_url_text else "无"}

请从以下几个维度分析（用中文回答，简洁专业，300字以内）：
1. 整体性能评估（优秀/良好/一般/较差）
2. 是否存在性能瓶颈（P95和P99差距分析）
3. 失败原因分析（如有失败）
4. 优化建议（给出2-3条可操作建议）"""

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "你是一个性能测试分析专家，回答简洁专业。"},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 800,
                    "temperature": 0.5,
                }
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"analysis": content.strip()}
            else:
                return {"analysis": _build_offline_analysis(req)}
    except Exception:
        return {"analysis": _build_offline_analysis(req)}


def _build_offline_analysis(req) -> str:
    r = req.result
    total = r.get("total", 0)
    failed = r.get("failed", 0)
    success = r.get("success", 0)
    tps = r.get("tps", 0)
    avg = r.get("avg_ms", 0)
    p95 = r.get("p95_ms", 0)
    p99 = r.get("p99_ms", 0)
    fail_rate = (failed / total * 100) if total > 0 else 0

    lines = ["📊 离线分析报告（未配置AI，基于规则自动生成）", ""]

    if fail_rate == 0:
        lines.append("✅ 整体评估：优秀 - 所有请求均成功。")
    elif fail_rate < 1:
        lines.append(f"⚠️ 整体评估：良好 - 失败率 {fail_rate:.1f}%，在可接受范围内。")
    elif fail_rate < 5:
        lines.append(f"⚠️ 整体评估：一般 - 失败率 {fail_rate:.1f}%，建议排查失败原因。")
    else:
        lines.append(f"🔴 整体评估：较差 - 失败率 {fail_rate:.1f}%，系统可能存在严重问题。")

    lines.append("")
    lines.append(f"📈 性能指标：TPS={tps}, 平均响应={avg}ms, P95={p95}ms, P99={p99}ms")

    if avg < 100:
        lines.append("   → 平均响应时间优秀（<100ms）")
    elif avg < 500:
        lines.append("   → 平均响应时间良好（<500ms）")
    elif avg < 1000:
        lines.append("   → 平均响应时间一般（<1000ms）")
    else:
        lines.append("   → 平均响应时间较慢（>1000ms），建议优化")

    if p95 > 0 and avg > 0 and p95 / max(avg, 1) > 3:
        lines.append("   → P95远高于平均值，存在长尾延迟，可能有少数慢请求拖累整体")
    if p99 > 0 and p95 > 0 and p99 / max(p95, 1) > 2:
        lines.append("   → P99与P95差距大，存在极端慢请求（异常值）")

    lines.append("")
    lines.append("💡 优化建议：")
    lines.append("   1. 关注失败请求，检查服务端日志排查具体错误原因")
    if avg > 500:
        lines.append("   2. 考虑优化数据库查询、增加缓存层降低响应时间")
    if tps < 10:
        lines.append("   3. TPS较低，检查是否有连接池限制或接口内部串行调用")
    else:
        lines.append("   3. 持续监控P95/P99指标，设置告警阈值及时发现问题")

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
