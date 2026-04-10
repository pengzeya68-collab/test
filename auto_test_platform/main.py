"""
FastAPI 主入口
零代码接口自动化测试平台

按照用户 Prompt 1-4 要求实现

启动命令: uvicorn main:app --reload --port 5002
"""
import os
from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, desc

from auto_test_platform.database import init_db, async_session_maker, async_session
from auto_test_platform.models import ApiGroup, ApiCase, Environment, TestHistory
from auto_test_platform.schemas import (
    TestHistoryResponse,
    CaseExecutionResult,
    EnvironmentResponse
)
from auto_test_platform.services.execution import quick_run_case, run_case_with_pytest


# 获取当前目录
BASE_DIR = Path(__file__).parent.absolute()


def get_env_flag(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def get_cors_origins():
    configured = os.getenv("AUTO_TEST_CORS_ORIGINS", "").strip()
    if configured:
        return [origin.strip() for origin in configured.split(",") if origin.strip()]

    return [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5000",
        "http://127.0.0.1:5000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化数据库和调度器
    """
    # 启动时执行
    print("[startup] Initializing database...")
    await init_db()
    print("[startup] Database initialized")

    # 创建必要的目录
    (BASE_DIR / "reports").mkdir(exist_ok=True)
    (BASE_DIR / "temp_run_data").mkdir(exist_ok=True)
    (BASE_DIR / "allure-results").mkdir(exist_ok=True)
    (BASE_DIR / "backups").mkdir(exist_ok=True)

    # 启动时自动恢复数据（从Flask后端同步接口用例）
    print("[startup] Checking for data sync from Flask backend...")
    try:
        from auto_test_platform.init_on_startup import sync_from_flask
        synced = await sync_from_flask()
        if synced:
            print(f"[startup] Data sync completed: {synced} cases")
        else:
            print("[startup] No data to sync or sync skipped")
    except Exception as e:
        print(f"[startup] Data sync failed: {e}")

    # 启动调度器
    from auto_test_platform.services.scheduler import start_scheduler
    start_scheduler()

    yield

    # 关闭调度器和数据库连接
    from auto_test_platform.services.scheduler import stop_scheduler
    stop_scheduler()
    print("[shutdown] Application closed")


# 创建 FastAPI 应用
app = FastAPI(
    title="零代码接口自动化测试平台",
    description="""
基于 FastAPI + SQLAlchemy + Pytest + Allure 的接口自动化测试平台。

## 功能特性:

- 🌳 **树状分组管理** - 支持多级接口分组
- 📝 **用例 CRUD** - 完整的接口用例管理
- 🔧 **环境变量** - 多环境配置与变量替换
- ⚡ **快速执行** - 一键运行单个用例
- 📊 **Allure 报告** - 漂亮的测试报告
- 🔍 **模糊搜索** - 按名称或 URL 搜索用例

## 变量占位符

在 URL、Headers、Payload 中使用 `{{variable_name}}` 格式的占位符，
系统会在执行时自动替换为环境变量中的值。

## 快速开始

1. 创建环境（设置 base_url 和 variables）
2. 创建分组
3. 创建用例
4. 点击"运行"执行测试
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=get_env_flag("AUTO_TEST_ALLOW_CREDENTIALS", True),
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录（Allure 报告）
# 🔒【S0级钉死】路径与 Celery 任务输出完全对齐：backend/reports/
# 所有报告都强制输出到 backend/reports 目录，FastAPI 直接挂载这个目录，绝对不会错位
import os
import auto_test_platform.settings as settings
PROJECT_ROOT = BASE_DIR.parent  # TestMasterProject
BACKEND_DIR = os.path.join(PROJECT_ROOT, 'backend')
# 允许通过配置自定义报告路径，默认为 backend/reports
REPORTS_DIR = getattr(settings, 'REPORTS_DIR', os.path.join(BACKEND_DIR, 'reports'))
from pathlib import Path
reports_dir = Path(REPORTS_DIR)
reports_dir.mkdir(exist_ok=True, parents=True)  # 确保目录存在
# html=True 允许直接访问目录自动返回 index.html
# 使用绝对路径挂载，彻底解决 404
app.mount("/reports", StaticFiles(directory=str(reports_dir.resolve()), html=True), name="reports")


# ========== 导入路由 ==========

from auto_test_platform.routers.groups import router as groups_router
from auto_test_platform.routers.cases import router as cases_router
from auto_test_platform.routers.environments import router as environments_router
from auto_test_platform.routers.scenarios import router as scenarios_router
from auto_test_platform.routers.import_export import router as import_export_router

# 注册路由
app.include_router(groups_router, prefix="/api")
app.include_router(cases_router, prefix="/api")
app.include_router(environments_router, prefix="/api")
app.include_router(scenarios_router, prefix="/api")
app.include_router(import_export_router, prefix="/api/auto-test")


# ========== 首页和健康检查 ==========

@app.get("/", tags=["首页"])
async def root():
    """首页"""
    return {
        "name": "零代码接口自动化测试平台",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# ========== 变量解析预览接口 ==========

@app.post("/api/utils/preview", tags=["工具"])
async def preview_variables(
    text: str,
    variables: dict = {}
):
    """
    预览变量替换效果

    用于在保存用例前预览 {{variable}} 会被替换成什么值
    """
    from utils.parser import replace_variables, find_variables

    result = replace_variables(text, variables)
    found = find_variables(text)

    return {
        "original": text,
        "result": result,
        "found_variables": found
    }


# ========== 用例执行接口 ==========

@app.post("/api/cases/{case_id}/run", response_model=TestHistoryResponse, tags=["执行测试"])
async def run_case(case_id: int, env_id: int = None, background_tasks: BackgroundTasks = None):
    """
    执行用例并保存历史记录

    点击"运行"按钮时调用此接口
    - 如果只需要快速测试（不保存历史），请使用 /api/cases/{case_id}/quick-run
    - 此接口会保存执行历史，并生成 Allure 报告
    """
    async with async_session() as session:
        # 获取用例
        result = await session.execute(select(ApiCase).where(ApiCase.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail="用例不存在")

        # 获取环境
        env = None
        if env_id:
            result = await session.execute(select(Environment).where(Environment.id == env_id))
            env = result.scalar_one_or_none()
        else:
            # 获取默认环境
            result = await session.execute(select(Environment).where(Environment.is_default == True))
            env = result.scalar_one_or_none()
            if not env:
                # 获取第一个环境
                result = await session.execute(select(Environment))
                env = result.scalars().first()

        # 创建历史记录
        history = TestHistory(
            case_id=case_id,
            status="running",
            execution_time=0
        )
        session.add(history)
        await session.commit()
        await session.refresh(history)

        # 在后台执行测试（避免超时）
        # 注意：这里直接调用，不使用 background_tasks，因为我们需要等待结果
        result_data = await quick_run_case(case, env)

        # 更新历史记录
        history.status = "success" if result_data["success"] else "failed"
        history.execution_time = result_data.get("execution_time", 0)
        history.response_data = result_data.get("response")
        history.error_message = result_data.get("error")

        await session.commit()
        await session.refresh(history)

        return history


@app.post("/api/cases/{case_id}/quick-run", response_model=CaseExecutionResult, tags=["快速执行"])
async def quick_run(case_id: int, env_id: int = Query(None, description="环境ID")):
    """
    快速执行用例（不保存历史记录）

    用于调试和即时测试
    """
    async with async_session() as session:
        # 获取用例
        result = await session.execute(select(ApiCase).where(ApiCase.id == case_id))
        case = result.scalar_one_or_none()
        if not case:
            raise HTTPException(status_code=404, detail="用例不存在")

        # 获取环境
        env = None
        # env_id 必须是有效的正整数才会查询
        if env_id and isinstance(env_id, int) and env_id > 0:
            result = await session.execute(select(Environment).where(Environment.id == env_id))
            env = result.scalar_one_or_none()
        
        # 如果没有获取到环境，尝试获取默认环境
        if env is None:
            result = await session.execute(select(Environment).where(Environment.is_default == True))
            env = result.scalars().first()  # 使用 first() 而非 scalar_one_or_none()，避免多个默认环境时报错
            if not env:
                result = await session.execute(select(Environment))
                env = result.scalars().first()

        # 执行
        result_data = await quick_run_case(case, env)
        return CaseExecutionResult(**result_data)


# ========== 批量执行接口 ==========

@app.post("/api/cases/batch-run", tags=["批量执行"])
async def batch_run(case_ids: list[int], env_id: int = None):
    """
    批量执行多个用例
    """
    async with async_session() as session:
        # 获取用例
        result = await session.execute(select(ApiCase).where(ApiCase.id.in_(case_ids)))
        cases = result.scalars().all()

        # 获取环境
        env = None
        if env_id:
            result = await session.execute(select(Environment).where(Environment.id == env_id))
            env = result.scalar_one_or_none()
        else:
            result = await session.execute(select(Environment).where(Environment.is_default == True))
            env = result.scalar_one_or_none()
            if not env:
                result = await session.execute(select(Environment))
                env = result.scalars().first()

        # 逐个执行
        results = []
        total = len(cases)
        success_count = 0

        for case in cases:
            exec_result = await quick_run_case(case, env)
            success_count += 1 if exec_result["success"] else 0
            results.append({
                "case_id": case.id,
                "case_name": case.name,
                **exec_result
            })

        return {
            "total": total,
            "success": success_count,
            "failed": total - success_count,
            "results": results
        }


# ========== 测试历史接口 ==========

@app.get("/api/history", response_model=list[TestHistoryResponse], tags=["历史记录"])
async def get_history(
    case_id: int = None,
    limit: int = 50,
    offset: int = 0
):
    """
    获取执行历史记录

    - case_id: 可选，按用例ID筛选
    - limit: 返回数量，默认 50
    - offset: 偏移量，默认 0
    """
    async with async_session() as session:
        query = select(TestHistory).order_by(desc(TestHistory.created_at))

        if case_id:
            query = query.where(TestHistory.case_id == case_id)

        query = query.offset(offset).limit(limit)
        result = await session.execute(query)
        history = result.scalars().all()

        return [TestHistoryResponse.model_validate(h) for h in history]


@app.delete("/api/history/{history_id}", status_code=204, tags=["历史记录"])
async def delete_history(history_id: int):
    """
    删除历史记录
    """
    async with async_session() as session:
        result = await session.execute(
            select(TestHistory).where(TestHistory.id == history_id)
        )
        history = result.scalar_one_or_none()
        if not history:
            raise HTTPException(status_code=404, detail="历史记录不存在")

        await session.delete(history)
        await session.commit()
        return None


@app.get("/api/history/{history_id}", response_model=TestHistoryResponse, tags=["历史记录"])
async def get_history_detail(history_id: int):
    """
    获取历史记录详情
    """
    async with async_session() as session:
        result = await session.execute(
            select(TestHistory).where(TestHistory.id == history_id)
        )
        history = result.scalar_one_or_none()
        if not history:
            raise HTTPException(status_code=404, detail="历史记录不存在")

        return history


# ========== 环境详情接口 ==========

@app.get("/api/environments/{env_id}", response_model=EnvironmentResponse, tags=["环境管理"])
async def get_environment_detail(env_id: int):
    """
    获取环境详情
    """
    async with async_session() as session:
        result = await session.execute(
            select(Environment).where(Environment.id == env_id)
        )
        env = result.scalar_one_or_none()
        if not env:
            raise HTTPException(status_code=404, detail="环境不存在")

        return env


# ========== 场景执行接口 ==========

@app.post("/api/scenarios/{scenario_id}/run", tags=["场景执行"])
async def run_scenario(scenario_id: int, env_id: int = None):
    """
    执行测试场景

    按顺序执行场景中的每个步骤，通过全局上下文传递变量。
    第一步（如登录）提取的 token 会自动传递给后续步骤使用。
    执行完成后生成 Allure 报告。
    """
    from auto_test_platform.services.scenario_runner import run_scenario as execute_scenario
    import subprocess
    import uuid
    from pathlib import Path

    try:
        result = await execute_scenario(scenario_id, env_id)

        # 生成 Allure 报告
        base_dir = Path(__file__).parent.absolute()
        allure_results_dir = base_dir / "allure-results" / f"scenario_{scenario_id}"
        
        # 允许通过配置自定义报告路径
        import auto_test_platform.settings as settings
        if hasattr(settings, 'REPORTS_DIR'):
            report_dir = Path(settings.REPORTS_DIR) / f"scenario_{scenario_id}"
        else:
            report_dir = base_dir / "reports" / f"scenario_{scenario_id}"

        # 确保目录存在
        allure_results_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一的 history_id
        history_id = str(uuid.uuid4())[:8]

        # 将执行结果写入 Allure 结果文件
        _write_allure_results(allure_results_dir, scenario_id, result, history_id)

        # 生成 Allure 报告
        try:
            cmd_result = subprocess.run(
                ["allure", "generate", str(allure_results_dir), "-o", str(report_dir), "--clean"],
                capture_output=True,
                timeout=60,
                shell=True  # Windows 上需要 shell=True 才能运行 .cmd 文件
            )
            # 检查命令执行结果
            if cmd_result.returncode == 0:
                result["report_url"] = f"/reports/scenario_{scenario_id}/index.html"
                print(f"[API] Allure 报告生成成功: {result['report_url']}")
            else:
                print(f"[API] Allure 报告生成失败, returncode={cmd_result.returncode}")
                print(f"[API] stderr: {cmd_result.stderr.decode('utf-8', errors='ignore')}")
                result["report_url"] = None
        except FileNotFoundError as e:
            print(f"[API] Allure 命令未找到，请安装 Allure: {e}")
            result["report_url"] = None
        except Exception as e:
            print(f"[API] Allure 报告生成异常: {e}")
            result["report_url"] = None

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


# ========== 获取场景执行历史接口 ==========
from auto_test_platform.models import ScenarioExecutionRecord
from sqlalchemy import select
from sqlalchemy.orm import selectinload

@app.get("/api/scenarios/{scenario_id}/history", tags=["场景执行"])
async def get_scenario_execution_history(scenario_id: int, limit: int = 20):
    """
    获取某个场景的执行历史记录列表
    """
    async with async_session() as session:
        # 检查场景是否存在
        from auto_test_platform.models import TestScenario
        scenario_result = await session.execute(
            select(TestScenario).where(TestScenario.id == scenario_id)
        )
        scenario = scenario_result.scalar_one_or_none()
        if not scenario:
            raise HTTPException(status_code=404, detail="场景不存在")

        # 查询执行历史，按创建时间倒序
        history_result = await session.execute(
            select(ScenarioExecutionRecord)
            .where(ScenarioExecutionRecord.scenario_id == scenario_id)
            .order_by(ScenarioExecutionRecord.created_at.desc())
            .limit(limit)
        )
        history = history_result.scalars().all()

        return {
            "scenario_id": scenario_id,
            "scenario_name": scenario.name,
            "total": len(history),
            "items": [
                {
                    "id": rec.id,
                    "status": rec.status,
                    "total_steps": rec.total_steps,
                    "success_steps": rec.success_steps,
                    "failed_steps": rec.failed_steps,
                    "skipped_steps": rec.skipped_steps,
                    "total_time": rec.total_time,
                    "report_url": rec.report_url,
                    "created_at": rec.created_at
                } for rec in history
            ]
        }


def _write_allure_results(allure_results_dir: Path, scenario_id: int, result: dict, history_id: str):
    """
    将场景执行结果写入 Allure 结果文件（符合 Allure JSON 规范）

    Args:
        allure_results_dir: Allure 结果目录
        scenario_id: 场景 ID
        result: 执行结果字典
        history_id: 历史记录 ID
    """
    import json
    import time

    # 计算时间戳（毫秒）
    start_time = result.get("start_time")
    if start_time:
        if isinstance(start_time, (int, float)):
            start_ms = int(start_time * 1000) if start_time < 1e10 else int(start_time)
        else:
            # ISO 字符串
            from datetime import datetime
            try:
                dt = datetime.fromisoformat(str(start_time).replace('Z', '+00:00'))
                start_ms = int(dt.timestamp() * 1000)
            except:
                start_ms = int(time.time() * 1000)
    else:
        start_ms = int(time.time() * 1000)

    duration_ms = int(result.get("duration", 0))
    stop_ms = start_ms + duration_ms

    # 转换状态：success -> passed, 其他 -> failed
    failed_count = result.get("failed_steps", 0)
    status = "passed" if failed_count == 0 else "failed"

    # 获取步骤结果
    step_results = result.get("step_results", [])
    scenario_name = result.get("scenario_name", f"场景 {scenario_id}")

    # 构建 Allure 兼容的主测试结果
    # Allure JSON 格式要求：name, uuid, historyId, status, stage, start, stop, duration
    # 以及 labels 数组（用于分类）
    scenario_result = {
        "name": scenario_name,
        "uuid": f"scenario_{scenario_id}_{history_id}",
        "historyId": f"scenario_{scenario_id}",
        "status": status,
        "stage": "finished",
        "start": start_ms,
        "stop": stop_ms,
        "duration": duration_ms,
        "description": f"场景ID: {scenario_id}，执行步骤: {len(step_results)}",
        "labels": [
            {"name": "suite", "value": "API测试场景"},
            {"name": "severity", "value": "normal"},
            {"name": "scenario_id", "value": str(scenario_id)},
            {"name": "thread", "value": "main"},
            {"name": "host", "value": "localhost"}
        ],
        "parameters": [],
        "links": [],
        "steps": _format_allure_steps(step_results),
        "attachments": []
    }

    # 写入主测试结果文件
    output_file = allure_results_dir / f"scenario-{scenario_id}-{history_id}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(scenario_result, f, ensure_ascii=False, indent=2)


def _format_allure_steps(step_results: list) -> list:
    """
    将步骤结果格式化为 Allure 的 steps 数组
    每个步骤在 Allure 中显示为可展开的嵌套结构
    """
    import time

    allure_steps = []
    current_time = int(time.time() * 1000)

    for i, step in enumerate(step_results):
        step_start = current_time
        step_duration = step.get("duration", 0)
        step_stop = step_start + step_duration

        # 判断步骤状态
        success = step.get("success", False)
        step_status = "passed" if success else "failed"

        # 提取关键信息用于展示
        api_case_name = step.get("api_case_name", f"步骤 {i+1}")
        method = step.get("method", "GET")
        url = step.get("url", "")
        status_code = step.get("status_code", 0)

        # 构建步骤名称
        step_name = f"[{method}] {api_case_name}"
        if status_code:
            step_name += f" (HTTP {status_code})"

        # 获取响应信息（截断过长内容）
        response_info = ""
        if step.get("response"):
            resp_body = step["response"].get("body", "")
            if resp_body:
                # 截断到 500 字符
                if len(str(resp_body)) > 500:
                    resp_body = str(resp_body)[:500] + "..."
                response_info = str(resp_body)

        # 获取断言信息
        assertions_info = ""
        if step.get("assertions"):
            assertions = step["assertions"]
            failed = assertions.get("failed", [])
            if failed:
                assertion_msgs = []
                for f in failed:
                    if isinstance(f, dict):
                        assertion_msgs.append(f.get("reason", str(f)))
                    else:
                        assertion_msgs.append(str(f))
                assertions_info = " | ".join(assertion_msgs)

        # 构建步骤详情（作为 attachment 内容）
        step_details = f"""API: {method} {url}
状态码: {status_code}
耗时: {step_duration}ms
断言: {assertions_info if assertions_info else '通过'}
响应: {response_info if response_info else '无响应体'}"""

        allure_step = {
            "name": step_name,
            "uuid": f"step_{i}_{current_time}",
            "status": step_status,
            "stage": "finished",
            "start": step_start,
            "stop": step_stop,
            "duration": step_duration,
            "steps": [],
            "attachments": [
                {
                    "name": f"响应详情_{i+1}",
                    "type": "text/plain",
                    "source": f"response_{i+1}.txt",
                    "body": step_details
                }
            ]
        }

        # 如果有提取的变量
        if step.get("extracted_vars"):
            vars_info = ", ".join([f"{k}={v}" for k, v in step["extracted_vars"].items()])
            allure_step["attachments"].append({
                "name": f"提取变量_{i+1}",
                "type": "text/plain",
                "source": f"vars_{i+1}.txt",
                "body": vars_info
            })

        allure_steps.append(allure_step)

    return allure_steps


@app.post("/api/scenarios/{scenario_id}/run-data-driven", tags=["场景执行"])
async def run_scenario_data_driven(scenario_id: int, env_id: int = None):
    """
    数据驱动执行测试场景

    如果场景配置了数据集（data_matrix），则按数据行数循环执行。
    每一行数据会驱动场景执行一次，所有结果汇总返回。

    等同于 Pytest 的 @pytest.mark.parametrize 装饰器功能。
    """
    from services.scenario_runner import run_scenario_data_driven as execute_data_driven
    import subprocess
    import uuid
    from pathlib import Path

    try:
        result = await execute_data_driven(scenario_id, env_id)

        # 生成 Allure 报告
        base_dir = Path(__file__).parent.absolute()
        allure_results_dir = base_dir / "allure-results" / f"scenario_{scenario_id}"
        
        import auto_test_platform.settings as settings
        if hasattr(settings, 'REPORTS_DIR'):
            report_dir = Path(settings.REPORTS_DIR) / f"scenario_{scenario_id}"
        else:
            report_dir = base_dir / "reports" / f"scenario_{scenario_id}"

        # 确保目录存在
        allure_results_dir.mkdir(parents=True, exist_ok=True)

        # 生成唯一的 history_id
        history_id = str(uuid.uuid4())[:8]

        # 将执行结果写入 Allure 结果文件
        _write_allure_results(allure_results_dir, scenario_id, result, history_id)

        # 生成 Allure 报告
        try:
            cmd_result = subprocess.run(
                ["allure", "generate", str(allure_results_dir), "-o", str(report_dir), "--clean"],
                capture_output=True,
                timeout=60,
                shell=True  # Windows 上需要 shell=True 才能运行 .cmd 文件
            )
            # 检查命令执行结果
            if cmd_result.returncode == 0:
                result["report_url"] = f"/reports/scenario_{scenario_id}/index.html"
                print(f"[API] Allure 报告生成成功: {result['report_url']}")
            else:
                print(f"[API] Allure 报告生成失败, returncode={cmd_result.returncode}")
                print(f"[API] stderr: {cmd_result.stderr.decode('utf-8', errors='ignore')}")
                result["report_url"] = None
        except FileNotFoundError as e:
            print(f"[API] Allure 命令未找到，请安装 Allure: {e}")
            result["report_url"] = None
        except Exception as e:
            print(f"[API] Allure 报告生成异常: {e}")
            result["report_url"] = None

        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"执行失败: {str(e)}")


# ========== 定时任务管理接口 ==========

from pydantic import BaseModel
from typing import Optional, List
from auto_test_platform.schemas import OptionalInt


class ScheduleTaskCreate(BaseModel):
    """创建定时任务请求"""
    scenario_id: int
    cron_expression: str
    env_id: OptionalInt = None
    name: Optional[str] = None


class ScheduleTaskResponse(BaseModel):
    """定时任务响应"""
    task_id: str
    job_id: str
    scenario_id: int
    env_id: OptionalInt
    cron_expression: str
    name: str
    created_at: str
    last_run: Optional[str]
    last_status: Optional[str]
    last_error: Optional[str]
    report_url: Optional[str]
    status: str
    next_run_time: Optional[str]


@app.get("/api/scheduler/tasks", response_model=List[ScheduleTaskResponse], tags=["定时任务"])
async def list_scheduler_tasks():
    """
    获取所有定时任务
    """
    from auto_test_platform.services.scheduler import get_all_scheduled_tasks
    return get_all_scheduled_tasks()


@app.get("/api/scheduler/tasks/{scenario_id}", response_model=List[ScheduleTaskResponse], tags=["定时任务"])
async def get_scenario_scheduler_tasks(scenario_id: int):
    """
    获取指定场景的定时任务
    """
    from auto_test_platform.services.scheduler import get_tasks_by_scenario
    tasks = get_tasks_by_scenario(scenario_id)
    if not tasks:
        return []
    return tasks


@app.post("/api/scheduler/tasks", response_model=ScheduleTaskResponse, tags=["定时任务"])
async def create_scheduler_task(task: ScheduleTaskCreate):
    """
    创建定时任务

    Args:
        scenario_id: 场景 ID
        cron_expression: Cron 表达式，支持以下格式：
            - "0 2 * * *" 每天凌晨2点
            - "0 */6 * * *" 每6小时
            - "0 9 * * 1" 每周一早上9点
            - "30 18 * * *" 每天下午6点半
        env_id: 环境 ID（可选）
        name: 任务名称（可选）
    """
    from auto_test_platform.services.scheduler import add_scheduled_task

    try:
        result = add_scheduled_task(
            scenario_id=task.scenario_id,
            cron_expression=task.cron_expression,
            env_id=task.env_id,
            task_name=task.name
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建定时任务失败: {str(e)}")


@app.delete("/api/scheduler/tasks/{task_id}", tags=["定时任务"])
async def delete_scheduler_task(task_id: str):
    """
    删除定时任务
    """
    from auto_test_platform.services.scheduler import remove_scheduled_task

    success = remove_scheduled_task(task_id)
    if success:
        return {"message": "删除成功"}
    else:
        raise HTTPException(status_code=404, detail="任务不存在或删除失败")


@app.post("/api/scheduler/tasks/{task_id}/run", tags=["定时任务"])
async def run_scheduler_task_now(task_id: str):
    """
    立即执行定时任务（手动触发）
    """
    from auto_test_platform.services.scheduler import get_scheduled_task, execute_scenario_job
    import asyncio

    task = get_scheduled_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")

    try:
        # 在后台异步执行
        asyncio.create_task(
            execute_scenario_job(task["scenario_id"], task.get("env_id"), task_id)
        )
        return {"message": "任务已触发执行"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"触发执行失败: {str(e)}")


# ========== 邮件配置 API ==========

from pydantic import BaseModel
from typing import Optional

class EmailConfig(BaseModel):
    enabled: bool
    smtpHost: str
    smtpPort: int
    smtpUser: str
    smtpPassword: str
    fromEmail: str
    adminToEmail: str
    enableSSL: bool
    baseUrl: str
    testToEmail: Optional[str] = ""

@app.get("/auto-test/api/email/config", tags=["邮件配置"])
async def get_email_config():
    """
    获取当前邮件配置
    """
    import auto_test_platform.settings as settings
    return {
        "enabled": getattr(settings, "EMAIL_ENABLED", False),
        "smtpHost": getattr(settings, "EMAIL_SMTP_HOST", "smtp.gmail.com"),
        "smtpPort": getattr(settings, "EMAIL_SMTP_PORT", 465),
        "smtpUser": getattr(settings, "EMAIL_SMTP_USER", ""),
        "smtpPassword": getattr(settings, "EMAIL_SMTP_PASSWORD", ""),
        "fromEmail": getattr(settings, "EMAIL_FROM", ""),
        "adminToEmail": getattr(settings, "EMAIL_ADMIN_TO", ""),
        "enableSSL": getattr(settings, "EMAIL_ENABLE_SSL", True),
        "baseUrl": getattr(settings, "BASE_URL", ""),
    }

@app.post("/auto-test/api/email/config", tags=["邮件配置"])
async def save_email_config(config: EmailConfig):
    """
    保存邮件配置到内存（重启后需要重新配置，建议修改 settings.py 或设置环境变量永久生效）
    """
    import auto_test_platform.settings as settings
    # 更新内存中的配置
    setattr(settings, "EMAIL_ENABLED", config.enabled)
    setattr(settings, "EMAIL_SMTP_HOST", config.smtpHost)
    setattr(settings, "EMAIL_SMTP_PORT", config.smtpPort)
    setattr(settings, "EMAIL_SMTP_USER", config.smtpUser)
    setattr(settings, "EMAIL_SMTP_PASSWORD", config.smtpPassword)
    setattr(settings, "EMAIL_FROM", config.fromEmail)
    setattr(settings, "EMAIL_ADMIN_TO", config.adminToEmail)
    setattr(settings, "EMAIL_ENABLE_SSL", config.enableSSL)
    setattr(settings, "BASE_URL", config.baseUrl)

    # 重新初始化邮件发送器
    from auto_test_platform.utils.email_notifier import get_email_notifier
    import auto_test_platform.utils.email_notifier as email_notifier_module
    email_notifier_module._email_notifier_instance = None
    get_email_notifier()

    return {"message": "配置保存成功"}

class TestEmailRequest(BaseModel):
    to_email: str

@app.post("/auto-test/api/email/test", tags=["邮件配置"])
async def send_test_email(request: TestEmailRequest):
    """
    发送测试邮件验证配置是否正确
    """
    from auto_test_platform.utils.email_notifier import get_email_notifier
    import auto_test_platform.settings as settings

    notifier = get_email_notifier()
    success = notifier.send_scenario_result(
        to_email=request.to_email,
        scenario_name="测试场景",
        scenario_id=0,
        status="success",
        total_steps=3,
        success_steps=3,
        failed_steps=0,
        skipped_steps=0,
        total_time=1250,
        report_url="",
        base_url=settings.BASE_URL
    )

    if not success:
        raise HTTPException(status_code=500, detail="测试邮件发送失败，请检查配置")

    return {"message": "测试邮件发送成功"}


# ========== 数据库备份 API ==========
import os
import shutil
from pathlib import Path

# 数据库路径（SQLite）
DB_PATH = BASE_DIR / "auto_test.db"
BACKUP_DIR = BASE_DIR / "backups"

@app.get("/auto-test/api/admin/backups", tags=["数据库备份"])
async def list_backups():
    """
    获取所有备份文件列表
    """
    if not BACKUP_DIR.exists():
        return {"backups": []}

    backups = []
    for file in BACKUP_DIR.glob("*.db"):
        if file.is_file():
            stat = file.stat()
            backups.append({
                "name": file.name,
                "size": stat.st_size / (1024 * 1024),  # MB
                "time": stat.st_mtime * 1000  # 毫秒时间戳
            })

    # 按时间倒序排序（最新的在前）
    backups.sort(key=lambda x: x["time"], reverse=True)
    return {"backups": backups}

@app.post("/auto-test/api/admin/backups", tags=["数据库备份"])
async def create_backup():
    """
    创建数据库备份
    """
    try:
        if not DB_PATH.exists():
            raise HTTPException(status_code=404, detail="数据库文件不存在")

        BACKUP_DIR.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"auto_test_backup_{timestamp}.db"
        backup_path = BACKUP_DIR / backup_name

        # 使用 shutil.copy2 复制文件（保留元数据）
        shutil.copy2(DB_PATH, backup_path)
        print(f"[BACKUP] 数据库备份创建成功: {backup_path}")

        return {"message": "备份创建成功", "filename": backup_name}
    except Exception as e:
        print(f"[BACKUP] 创建备份失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"创建备份失败: {str(e)}")

@app.delete("/auto-test/api/admin/backups/old", tags=["数据库备份"])
async def clean_old_backups():
    """
    清理旧备份，只保留最新的10个
    """
    try:
        if not BACKUP_DIR.exists():
            return {"message": "没有备份文件需要清理"}

        backups = sorted(
            BACKUP_DIR.glob("*.db"),
            key=lambda f: f.stat().st_mtime,
            reverse=True
        )

        if len(backups) <= 10:
            return {"message": "备份数量少于10个，无需清理"}

        # 删除超过10个的旧备份
        deleted = 0
        for backup in backups[10:]:
            backup.unlink()
            deleted += 1

        print(f"[BACKUP] 清理完成，删除了 {deleted} 个旧备份")
        return {"message": f"清理完成，删除了 {deleted} 个旧备份", "deleted_count": deleted}
    except Exception as e:
        print(f"[BACKUP] 清理旧备份失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"清理失败: {str(e)}")

@app.delete("/auto-test/api/admin/backups/{filename}", tags=["数据库备份"])
async def delete_backup(filename: str):
    """
    删除指定备份文件
    """
    try:
        # 安全检查：只允许删除 .db 文件
        if not filename.endswith('.db'):
            raise HTTPException(status_code=400, detail="只允许删除 .db 备份文件")

        backup_path = BACKUP_DIR / filename
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="备份文件不存在")

        backup_path.unlink()
        print(f"[BACKUP] 备份文件删除成功: {filename}")
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"[BACKUP] 删除备份失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@app.post("/auto-test/api/admin/backups/{filename}/restore", tags=["数据库备份"])
async def restore_backup(filename: str):
    """
    从指定备份恢复数据库
    恢复前会先创建一个紧急备份
    """
    try:
        # 安全检查
        if not filename.endswith('.db'):
            raise HTTPException(status_code=400, detail="只允许恢复 .db 备份文件")

        backup_path = BACKUP_DIR / filename
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="备份文件不存在")

        # 恢复前先创建紧急备份
        if DB_PATH.exists():
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            emergency_backup = BACKUP_DIR / f"emergency_restore_backup_{timestamp}.db"
            shutil.copy2(DB_PATH, emergency_backup)
            print(f"[BACKUP] 创建紧急备份: {emergency_backup}")

        # 恢复：复制备份文件覆盖原数据库
        shutil.copy2(backup_path, DB_PATH)
        print(f"[BACKUP] 数据库恢复成功，来自: {filename}")

        return {"message": "备份恢复成功，请重启服务使更改生效"}
    except Exception as e:
        print(f"[BACKUP] 恢复备份失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")


# ========== 启动入口 ==========

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5002,
        reload=True,
        log_level="info"
    )
