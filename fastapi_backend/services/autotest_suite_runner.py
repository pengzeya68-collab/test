"""
测试套件执行引擎

功能：
- 按顺序执行套件内所有用例
- 复用 quick_run_case() 执行单条用例
- 记录每条用例的执行结果到 AutoTestHistory
- 支持并行执行（可选）
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi_backend.core.autotest_database import AsyncSessionLocal
from fastapi_backend.models.autotest import (
    AutoTestCase,
    AutoTestEnvironment,
    AutoTestHistory,
    TestSuite,
    TestSuiteCase,
    TestSuiteExecution,
)
from fastapi_backend.services.autotest_execution import quick_run_case

_logger = logging.getLogger(__name__)


class SuiteRunner:
    """测试套件执行引擎"""

    def __init__(self, suite_id: int, env_id: Optional[int] = None, progress_callback=None, user_id: int = None):
        self.suite_id = suite_id
        self.env_id = env_id
        self.progress_callback = progress_callback
        self.user_id = user_id

    async def execute(self) -> Dict[str, Any]:
        """执行测试套件"""
        start_time = time.time()

        # 在会话内提取所有需要的数据，避免 DetachedInstanceError
        suite_name = ""
        suite_cases_data = []
        env_data = None  # 存储环境配置的普通字典
        execution_id = None

        async with AsyncSessionLocal() as db:
            # 加载套件
            suite_query = select(TestSuite).where(TestSuite.id == self.suite_id)
            if self.user_id is not None:
                suite_query = suite_query.where(TestSuite.user_id == self.user_id)
            result = await db.execute(suite_query)
            suite = result.scalar_one_or_none()
            if not suite:
                raise ValueError(f"套件 {self.suite_id} 不存在")

            suite_name = suite.name

            # 加载套件内的用例
            result = await db.execute(
                select(TestSuiteCase)
                .where(TestSuiteCase.suite_id == self.suite_id)
                .order_by(TestSuiteCase.sort_order)
            )
            suite_cases = result.scalars().all()

            if not suite_cases:
                raise ValueError(f"套件 {self.suite_id} 中没有用例")

            # 提前提取 suite_cases 的 ID 列表
            suite_cases_data = [{"case_id": sc.case_id, "sort_order": sc.sort_order} for sc in suite_cases]

            # 加载环境
            env = None
            env_id = self.env_id or suite.env_id
            if env_id:
                env_query = select(AutoTestEnvironment).where(AutoTestEnvironment.id == env_id)
                if self.user_id is not None:
                    env_query = env_query.where(AutoTestEnvironment.user_id == self.user_id)
                result = await db.execute(env_query)
                env = result.scalar_one_or_none()

            # 将 env 数据提取为普通字典，避免 DetachedInstanceError
            if env:
                env_data = {
                    "id": env.id,
                    "env_name": env.env_name,
                    "base_url": env.base_url,
                    "variables": env.variables if isinstance(env.variables, dict) else {},
                    "headers": env.headers if isinstance(getattr(env, 'headers', None), dict) else {},
                }

            # 创建执行记录
            execution = TestSuiteExecution(
                suite_id=self.suite_id,
                env_id=env_id,
                status="running",
                total_cases=len(suite_cases),
                started_at=datetime.now(timezone.utc),
                user_id=self.user_id,
            )
            db.add(execution)
            await db.commit()
            await db.refresh(execution)
            execution_id = execution.id

        # 执行每个用例
        passed = 0
        failed = 0
        case_results = []

        for idx, sc_data in enumerate(suite_cases_data):
            case_id = sc_data["case_id"]
            if self.progress_callback:
                self.progress_callback(idx, len(suite_cases_data), f"执行用例 {idx + 1}/{len(suite_cases_data)}")

            try:
                async with AsyncSessionLocal() as db:
                    case_query = select(AutoTestCase).where(AutoTestCase.id == case_id)
                    if self.user_id is not None:
                        case_query = case_query.where(AutoTestCase.user_id == self.user_id)
                    result = await db.execute(case_query)
                    case = result.scalar_one_or_none()

                    if not case:
                        case_results.append({
                            "case_id": case_id,
                            "status": "error",
                            "error": "用例不存在",
                        })
                        failed += 1
                        continue

                    # 在当前会话内重新加载 env，避免传递分离的 ORM 对象
                    run_env = None
                    if env_data and env_data.get("id"):
                        env_query = select(AutoTestEnvironment).where(AutoTestEnvironment.id == env_data["id"])
                        if self.user_id is not None:
                            env_query = env_query.where(AutoTestEnvironment.user_id == self.user_id)
                        env_result = await db.execute(env_query)
                        run_env = env_result.scalar_one_or_none()

                    # 执行用例
                    run_result = await quick_run_case(case, run_env, user_id=self.user_id)

                    # 保存历史记录
                    history = AutoTestHistory(
                        case_id=case.id,
                        status="success" if run_result["success"] else "failed",
                        execution_time=run_result.get("execution_time", 0),
                        response_data=run_result.get("response"),
                        error_message=run_result.get("error"),
                        user_id=self.user_id,
                    )
                    db.add(history)
                    await db.commit()

                    if run_result["success"]:
                        passed += 1
                    else:
                        failed += 1

                    case_results.append({
                        "case_id": case.id,
                        "case_name": case.name,
                        "status": "success" if run_result["success"] else "failed",
                        "execution_time": run_result.get("execution_time", 0),
                        "status_code": run_result.get("status_code"),
                        "error": run_result.get("error"),
                    })

            except Exception as e:
                _logger.error(f"用例 {case_id} 执行异常: {e}")
                failed += 1
                case_results.append({
                    "case_id": case_id,
                    "status": "error",
                    "error": str(e),
                })

            if self.progress_callback:
                self.progress_callback(idx + 1, len(suite_cases_data), f"完成用例 {idx + 1}/{len(suite_cases_data)}")

        duration_ms = int((time.time() - start_time) * 1000)
        status = "success" if failed == 0 else "failed"

        # 更新执行记录
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(TestSuiteExecution).where(TestSuiteExecution.id == execution_id)
            )
            exec_record = result.scalar_one_or_none()
            if exec_record:
                exec_record.status = status
                exec_record.passed_cases = passed
                exec_record.failed_cases = failed
                exec_record.duration_ms = duration_ms
                exec_record.finished_at = datetime.now(timezone.utc)
                await db.commit()

        return {
            "execution_id": execution_id,
            "suite_id": self.suite_id,
            "suite_name": suite_name,
            "status": status,
            "total_cases": len(suite_cases_data),
            "passed_cases": passed,
            "failed_cases": failed,
            "duration_ms": duration_ms,
            "case_results": case_results,
        }
