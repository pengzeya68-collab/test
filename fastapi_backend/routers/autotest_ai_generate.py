"""
AutoTest 路由 - AI 智能生成测试用例

路径前缀: /api/auto-test/ai-generate
功能: 从 Swagger/OpenAPI 文档自动分析接口，利用 AI 生成完整测试用例
架构: 异步任务 + 进度轮询，避免大量接口时 504 超时
"""

import asyncio
import json
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import get_autotest_db as get_db
from fastapi_backend.core.database import get_db as get_main_db
from fastapi_backend.deps.ai_points import require_ai_points_batch
from fastapi_backend.deps.auth import get_current_active_user
from fastapi_backend.models.autotest import AutoTestCase, AutoTestGroup, AutoTestScenario, AutoTestScenarioStep
from fastapi_backend.models.models import User
from fastapi_backend.services.autotest_ai_generator import (
    AITestCaseGenerator,
    create_task_id,
    _run_generation,
)
from fastapi_backend.services.autotest_task_store import get_task, update_task, cancel_task

_logger = logging.getLogger(__name__)


def _parse_swagger_content(content: bytes) -> dict:
    """解析 Swagger/OpenAPI 内容，支持 JSON 和 YAML 格式"""
    text = content.decode("utf-8")
    # 先尝试 JSON
    try:
        result = json.loads(text)
        if isinstance(result, dict):
            return result
    except (json.JSONDecodeError, ValueError):
        pass
    # 再尝试 YAML
    try:
        import yaml

        result = yaml.safe_load(text)
        if isinstance(result, dict):
            return result
        raise ValueError(f"YAML 解析结果不是字典，而是 {type(result).__name__}")
    except ImportError:
        raise ValueError("服务器未安装 PyYAML，无法解析 YAML 文件。请使用 JSON 格式。")
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"YAML 解析失败: {str(e)}")
    raise ValueError("无法解析文件，请确保是有效的 JSON 或 YAML 格式")


def _should_run_locally() -> bool:
    """开发环境兜底：没有可用 Celery worker 或任务未注册时，回退到当前 FastAPI 进程异步执行。"""
    try:
        from fastapi_backend.tasks import celery_app

        broker_url = str(celery_app.conf.broker_url or "")
        if broker_url.startswith("memory://"):
            return True

        # 检查目标任务是否已注册
        task_name = "fastapi_backend.services.autotest_ai_generator.ai_generate_task"
        if task_name not in celery_app._tasks:
            _logger.warning("Celery 任务 %s 未注册，回退到本地异步执行", task_name)
            return True

        inspect = celery_app.control.inspect(timeout=0.5)
        active_workers = inspect.ping() or {}
        return not bool(active_workers)
    except Exception as e:
        _logger.warning("检查 Celery 可用性失败，回退到本地异步执行: %s", e)
        return True


router = APIRouter(
    prefix="/api/auto-test/ai-generate",
    tags=["AutoTest-AI生成用例"],
)


# ========== 启动生成任务 ==========


@router.post("/from-swagger")
async def generate_from_swagger(
    file: UploadFile = File(...),
    max_cases_per_api: int = Form(4),
    include_boundary: bool = Form(True),
    include_auth: bool = Form(True),
    include_chain: bool = Form(True),
    current_user: User = Depends(get_current_active_user),
    main_db: AsyncSession = Depends(get_main_db),
    _batch_check=Depends(require_ai_points_batch("ai_generate_cases", batch_desc="批次")),
):
    """
    从 Swagger/OpenAPI 文件启动 AI 生成测试用例任务

    立即返回 task_id，前端通过 GET /tasks/{task_id} 轮询进度。
    """
    try:
        content = await file.read()
        _logger.info("收到 Swagger 文件: %s, 大小: %d bytes", file.filename, len(content))

        # 1. 解析文件内容
        try:
            swagger_data = _parse_swagger_content(content)
        except ValueError as e:
            _logger.warning("Swagger 文件解析失败: %s", e)
            raise HTTPException(status_code=400, detail=str(e))

        if not isinstance(swagger_data, dict):
            raise HTTPException(
                status_code=400, detail=f"解析结果不是有效的字典对象，类型: {type(swagger_data).__name__}"
            )

        _logger.info("Swagger 解析成功, paths 数量: %d", len(swagger_data.get("paths", {})))

        # 2. 构建选项
        options = {
            "max_cases_per_api": max_cases_per_api,
            "include_boundary": include_boundary,
            "include_auth": include_auth,
            "include_chain": include_chain,
        }

        # 3. 创建任务并分发
        return await _dispatch_generation_task(swagger_data, options, current_user.id, _batch_check, main_db)

    except HTTPException:
        raise
    except Exception as e:
        _logger.exception("启动 AI 生成任务异常: %s", e)
        raise HTTPException(status_code=500, detail=f"启动失败: {type(e).__name__}: {str(e)}")


@router.post("/from-swagger-url")
async def generate_from_swagger_url(
    url: str = Form(...),
    max_cases_per_api: int = Form(4),
    include_boundary: bool = Form(True),
    include_auth: bool = Form(True),
    include_chain: bool = Form(True),
    current_user: User = Depends(get_current_active_user),
    main_db: AsyncSession = Depends(get_main_db),
    _batch_check=Depends(require_ai_points_batch("ai_generate_cases", batch_desc="批次")),
):
    """
    从 Swagger URL 启动 AI 生成测试用例任务

    自动拉取远程 Swagger 文档并启动生成任务。立即返回 task_id。
    """
    try:
        from fastapi_backend.core.ssrf_guard import validate_url_safety

        safe, reason = validate_url_safety(url)
        if not safe:
            raise HTTPException(status_code=400, detail=f"URL安全校验失败: {reason}")

        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(url)
            resp.raise_for_status()
            swagger_data = _parse_swagger_content(resp.content)

        if not isinstance(swagger_data, dict):
            raise HTTPException(
                status_code=400, detail=f"URL 内容解析结果不是字典，类型: {type(swagger_data).__name__}"
            )

        options = {
            "max_cases_per_api": max_cases_per_api,
            "include_boundary": include_boundary,
            "include_auth": include_auth,
            "include_chain": include_chain,
        }

        return await _dispatch_generation_task(swagger_data, options, current_user.id, _batch_check, main_db)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        _logger.exception("启动 AI 从 URL 生成任务异常: %s", e)
        raise HTTPException(status_code=500, detail=f"启动失败: {type(e).__name__}: {str(e)}")


async def _dispatch_generation_task(
    swagger_data: dict, options: dict, user_id: int, _batch_check=None, db=None
) -> dict:
    """创建任务记录并分发到 Celery 或本地异步执行"""
    task_id = create_task_id()

    # 解析 swagger 获取接口数量，用于初始进度
    generator = AITestCaseGenerator()
    parsed = generator._parse_swagger(swagger_data)
    total_apis = len(parsed["apis"])
    total_batches = (total_apis + 4) // 5  # BATCH_SIZE = 5

    # 预扣所有批次的积分
    if _batch_check is not None:
        check_batch, confirm = _batch_check
        await check_batch(total_batches)
        await confirm()  # 确认扣费

    # 初始化任务记录
    await update_task(
        task_id,
        {
            "task_id": task_id,
            "status": "PENDING",
            "progress": 0.0,
            "phase": "pending",
            "phase_label": "任务已提交，等待处理...",
            "total_apis": total_apis,
            "processed_apis": 0,
            "total_batches": total_batches,
            "current_batch": 0,
            "cases": [],
            "scenarios": [],
            "message": "",
            "error": None,
            "created_at": time.time(),
            "user_id": user_id,
        },
    )

    use_local = _should_run_locally()

    if use_local:
        _logger.info("未检测到可用 Celery worker，AI 生成切换为本地异步模式: task_id=%s", task_id)
        asyncio.create_task(_run_generation(task_id, swagger_data, options))
    else:
        try:
            from fastapi_backend.tasks import celery_app

            celery_app.send_task(
                "fastapi_backend.services.autotest_ai_generator.ai_generate_task",
                args=[task_id, swagger_data, options],
            )
            _logger.info("发送 Celery AI 生成任务: task_id=%s", task_id)
        except Exception as e:
            _logger.warning("Celery dispatch 失败，回退到本地异步: %s", e)
            asyncio.create_task(_run_generation(task_id, swagger_data, options))

    return {"task_id": task_id, "status": "PENDING"}


# ========== 轮询进度 ==========


@router.get("/tasks/{task_id}")
async def get_generation_task_status(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    轮询 AI 生成任务进度

    返回任务状态、进度百分比、当前阶段、已生成的用例和场景等。
    """
    stored = await get_task(task_id)
    if not stored:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    if stored.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")

    return {
        "task_id": stored.get("task_id", task_id),
        "status": stored.get("status", "UNKNOWN"),
        "progress": stored.get("progress", 0.0),
        "phase": stored.get("phase", ""),
        "phase_label": stored.get("phase_label", ""),
        "total_apis": stored.get("total_apis", 0),
        "processed_apis": stored.get("processed_apis", 0),
        "total_batches": stored.get("total_batches", 0),
        "current_batch": stored.get("current_batch", 0),
        "cases": stored.get("cases", []),
        "scenarios": stored.get("scenarios", []),
        "message": stored.get("message", ""),
        "error": stored.get("error"),
        "start_time": stored.get("start_time"),
    }


@router.post("/tasks/{task_id}/cancel")
async def cancel_generation_task(
    task_id: str,
    current_user: User = Depends(get_current_active_user),
):
    """
    取消 AI 生成任务

    立即标记任务为取消状态，后台任务会在下一批次前检查到取消标志并停止。
    已生成的用例会被保留，可在预览页查看并导入。
    """
    stored = await get_task(task_id)
    if not stored:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")
    if stored.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="任务不存在或已过期")

    # 只有进行中的任务才能取消
    if stored.get("status") not in ("PENDING", "PROGRESS"):
        return {
            "message": f"任务状态为 {stored.get('status')}，无法取消",
            "existing_cases": len(stored.get("cases", [])),
        }

    await update_task(
        task_id,
        {
            **stored,
            "status": "cancelling",
            "cancelled": True,
            "phase_label": "正在中止生成任务...",
        },
    )

    await cancel_task(task_id)

    return {
        "message": "任务已标记为取消，后台将在下一批次前停止。已生成的用例会保留。",
        "existing_cases": len(stored.get("cases", [])),
    }


# ========== 确认导入 ==========


@router.post("/confirm")
async def confirm_import(
    data: dict,
    current_user: User = Depends(get_current_active_user),
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
            AutoTestGroup.user_id == current_user.id,
        )
    )
    group = result.scalar_one_or_none()
    if not group:
        group = AutoTestGroup(name=group_name, parent_id=None, user_id=current_user.id)
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
                    AutoTestGroup.user_id == current_user.id,
                )
            )
            sub_group = sub_result.scalar_one_or_none()
            if not sub_group:
                sub_group = AutoTestGroup(name=tag, parent_id=group.id, user_id=current_user.id)
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
            user_id=current_user.id,
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
                user_id=current_user.id,
            )
            db.add(scenario)
            await db.flush()

            for step_idx, step_data in enumerate(scenario_data.get("steps", [])):
                api_index = int(step_data.get("api_index", 0))
                linked_case = created_cases[api_index] if 0 <= api_index < len(created_cases) else None

                if linked_case is None:
                    _logger.warning(
                        f"场景 '{scenario_data.get('name')}' 步骤 {step_idx} 的 api_index={api_index} 越界，跳过该步骤"
                    )
                    continue

                step = AutoTestScenarioStep(
                    scenario_id=scenario.id,
                    api_case_id=linked_case.id,
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
